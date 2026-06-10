"""
modules/contribution_analyzer.py
Author: Adeel (@adeelad726)
Fetches commits, PRs, merge requests from GitLab and returns per-user JSON summary.
Compatible: Python 3.13+
"""

import os
import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

GITLAB_URL   = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
HEADERS      = {"PRIVATE-TOKEN": GITLAB_TOKEN}


async def _get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> list | dict:
    results = []
    page = 1
    while True:
        p = {"per_page": 100, "page": page, **(params or {})}
        resp = await client.get(url, headers=HEADERS, params=p, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


async def fetch_project_id(client: httpx.AsyncClient, namespace_path: str) -> int | None:
    encoded = namespace_path.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded}"
    try:
        data = await _get(client, url)
        return data.get("id")
    except Exception:
        return None


async def fetch_commits(client: httpx.AsyncClient, project_id: int, since_days: int = 7) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
    url   = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits"
    return await _get(client, url, {"since": since, "with_stats": "true"})


async def fetch_merge_requests(client: httpx.AsyncClient, project_id: int, since_days: int = 7) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
    url   = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    return await _get(client, url, {"state": "all", "updated_after": since, "scope": "all"})


async def fetch_issues(client: httpx.AsyncClient, project_id: int, since_days: int = 7) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
    url   = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues"
    return await _get(client, url, {"state": "all", "updated_after": since, "scope": "all"})


def _empty_user(username: str) -> dict:
    return {
        "username": username, "commits": 0, "lines_added": 0, "lines_removed": 0,
        "mrs_opened": 0, "mrs_merged": 0, "mrs_closed": 0,
        "issues_opened": 0, "issues_closed": 0,
        "repos_touched": [], "last_active": None, "activity_score": 0,
    }


def _update_ts(record: dict, ts_str: str | None):
    if not ts_str:
        return
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if record["last_active"] is None or ts > record["last_active"]:
            record["last_active"] = ts
    except Exception:
        pass


def _score(u: dict) -> int:
    s = (u["commits"]*3 + u["lines_added"]*0.01 + u["mrs_opened"]*5 +
         u["mrs_merged"]*8 + u["issues_opened"]*2 + u["issues_closed"]*4)
    return min(100, int(s))


def aggregate_contributions(repo_name: str, commits: list, mrs: list, issues: list) -> dict:
    users: dict[str, dict] = {}

    for c in commits:
        uname = (c.get("author_name") or "unknown").strip()
        if uname not in users:
            users[uname] = _empty_user(uname)
        u = users[uname]
        u["commits"] += 1
        stats = c.get("stats") or {}
        u["lines_added"]   += stats.get("additions", 0)
        u["lines_removed"] += stats.get("deletions", 0)
        if repo_name not in u["repos_touched"]:
            u["repos_touched"].append(repo_name)
        _update_ts(u, c.get("committed_date"))

    for mr in mrs:
        author = (mr.get("author") or {}).get("username", "unknown")
        if author not in users:
            users[author] = _empty_user(author)
        u = users[author]
        state = mr.get("state", "")
        if state == "opened":   u["mrs_opened"] += 1
        elif state == "merged": u["mrs_merged"] += 1
        elif state == "closed": u["mrs_closed"] += 1
        if repo_name not in u["repos_touched"]:
            u["repos_touched"].append(repo_name)
        _update_ts(u, mr.get("updated_at"))

    for issue in issues:
        author = (issue.get("author") or {}).get("username", "unknown")
        if author not in users:
            users[author] = _empty_user(author)
        u = users[author]
        if issue.get("state") == "closed": u["issues_closed"] += 1
        else: u["issues_opened"] += 1
        _update_ts(u, issue.get("updated_at"))

    for u in users.values():
        u["activity_score"] = _score(u)
        if isinstance(u["last_active"], datetime):
            u["last_active"] = u["last_active"].isoformat()

    return users


async def analyze(repos: list[str], since_days: int = 7) -> dict:
    all_users: dict[str, dict] = {}

    async with httpx.AsyncClient() as client:
        for repo_path in repos:
            project_id = await fetch_project_id(client, repo_path)
            if not project_id:
                print(f"[analyzer] WARNING: could not resolve '{repo_path}' — skipping")
                continue

            commits, mrs, issues = await asyncio.gather(
                fetch_commits(client, project_id, since_days),
                fetch_merge_requests(client, project_id, since_days),
                fetch_issues(client, project_id, since_days),
            )

            for uname, data in aggregate_contributions(repo_path, commits, mrs, issues).items():
                if uname not in all_users:
                    all_users[uname] = data
                else:
                    e = all_users[uname]
                    for key in ["commits","lines_added","lines_removed","mrs_opened","mrs_merged","mrs_closed","issues_opened","issues_closed"]:
                        e[key] += data[key]
                    for r in data["repos_touched"]:
                        if r not in e["repos_touched"]:
                            e["repos_touched"].append(r)
                    if data["last_active"] and (not e["last_active"] or data["last_active"] > e["last_active"]):
                        e["last_active"] = data["last_active"]

    for u in all_users.values():
        u["activity_score"] = _score(u)

    total_commits = sum(u["commits"] for u in all_users.values())
    total_mrs     = sum(u["mrs_opened"] + u["mrs_merged"] for u in all_users.values())
    total_issues  = sum(u["issues_opened"] + u["issues_closed"] for u in all_users.values())
    top = max(all_users.values(), key=lambda u: u["activity_score"], default=None)

    return {
        "repos_analyzed": repos,
        "since_days": since_days,
        "contributors": all_users,
        "summary": {
            "total_commits": total_commits,
            "total_mrs": total_mrs,
            "total_issues": total_issues,
            "top_contributor": top["username"] if top else None,
        },
    }


if __name__ == "__main__":
    import json
    TEST_REPOS = [r.strip() for r in os.getenv("TEST_REPOS", "").split(",") if r.strip()]
    if not TEST_REPOS:
        print("Set TEST_REPOS=namespace/project in .env")
    else:
        result = asyncio.run(analyze(TEST_REPOS))
        print(json.dumps(result, indent=2, default=str))
