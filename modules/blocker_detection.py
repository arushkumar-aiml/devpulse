"""
modules/blocker_detection.py
Author: Aniket (@aniketgit-hub101)
Detects stale PRs, failed pipelines, unassigned issues and scores them 1-10.
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

STALE_MR_DAYS      = 3
STALE_ISSUE_DAYS   = 5
CRITICAL_MR_DAYS   = 7


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


async def fetch_open_mrs(client: httpx.AsyncClient, project_id: int) -> list:
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    return await _get(client, url, {"state": "opened", "scope": "all"})


async def fetch_open_issues(client: httpx.AsyncClient, project_id: int) -> list:
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues"
    return await _get(client, url, {"state": "opened", "scope": "all"})


async def fetch_pipelines(client: httpx.AsyncClient, project_id: int) -> list:
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines"
    return await _get(client, url, {"per_page": 20})


async def fetch_pipeline_detail(client: httpx.AsyncClient, project_id: int, pipeline_id: int) -> dict:
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
    return await _get(client, url)


def _days_since(ts_str: str | None) -> float:
    if not ts_str:
        return 0
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds() / 86400
    except Exception:
        return 0


def _priority_score(blocker_type: str, age_days: float, extra: dict) -> int:
    """
    Returns priority score 1-10.
    10 = drop everything, 1 = low priority.
    """
    score = 1

    if blocker_type == "stale_mr":
        if age_days >= CRITICAL_MR_DAYS:  score = 9
        elif age_days >= 5:               score = 7
        else:                             score = 5
        if extra.get("has_conflicts"):    score = min(10, score + 1)

    elif blocker_type == "failed_pipeline":
        branch = extra.get("branch", "")
        if branch in ("main", "master", "production"): score = 10
        elif "release" in branch:                       score = 8
        else:                                           score = 6

    elif blocker_type == "unassigned_issue":
        labels = [l.lower() for l in extra.get("labels", [])]
        if "critical" in labels or "blocker" in labels: score = 9
        elif "bug" in labels:                            score = 6
        elif age_days >= STALE_ISSUE_DAYS:               score = 4
        else:                                            score = 2

    return max(1, min(10, score))


def detect_stale_mrs(mrs: list, repo: str) -> list:
    blockers = []
    for mr in mrs:
        age = _days_since(mr.get("updated_at"))
        if age >= STALE_MR_DAYS:
            has_conflicts = mr.get("has_conflicts", False)
            blockers.append({
                "type":        "stale_mr",
                "repo":        repo,
                "id":          mr.get("iid"),
                "title":       mr.get("title", "Untitled MR"),
                "url":         mr.get("web_url", ""),
                "author":      (mr.get("author") or {}).get("username", "unknown"),
                "assignee":    (mr.get("assignee") or {}).get("username"),
                "age_days":    round(age, 1),
                "has_conflicts": has_conflicts,
                "description": f"MR open for {round(age,1)} days without update",
                "priority":    _priority_score("stale_mr", age, {"has_conflicts": has_conflicts}),
            })
    return blockers


def detect_unassigned_issues(issues: list, repo: str) -> list:
    blockers = []
    for issue in issues:
        if issue.get("assignee") or issue.get("assignees"):
            continue
        age    = _days_since(issue.get("updated_at"))
        labels = issue.get("labels", [])
        blockers.append({
            "type":        "unassigned_issue",
            "repo":        repo,
            "id":          issue.get("iid"),
            "title":       issue.get("title", "Untitled Issue"),
            "url":         issue.get("web_url", ""),
            "author":      (issue.get("author") or {}).get("username", "unknown"),
            "assignee":    None,
            "age_days":    round(age, 1),
            "labels":      labels,
            "description": f"Issue unassigned for {round(age,1)} days",
            "priority":    _priority_score("unassigned_issue", age, {"labels": labels}),
        })
    return blockers


def detect_failed_pipelines(pipelines: list, repo: str) -> list:
    blockers = []
    seen_branches: set[str] = set()
    for pl in pipelines:
        status = pl.get("status", "")
        branch = pl.get("ref", "")
        if status in ("failed", "canceled") and branch not in seen_branches:
            seen_branches.add(branch)
            age = _days_since(pl.get("updated_at"))
            blockers.append({
                "type":        "failed_pipeline",
                "repo":        repo,
                "id":          pl.get("id"),
                "title":       f"Pipeline #{pl.get('id')} failed on {branch}",
                "url":         pl.get("web_url", ""),
                "author":      None,
                "assignee":    None,
                "age_days":    round(age, 1),
                "branch":      branch,
                "status":      status,
                "description": f"Pipeline {status} on branch '{branch}'",
                "priority":    _priority_score("failed_pipeline", age, {"branch": branch}),
            })
    return blockers


async def detect_blockers_for_project(
    client: httpx.AsyncClient,
    project_id: int,
    repo_name: str,
) -> list:
    mrs, issues, pipelines = await asyncio.gather(
        fetch_open_mrs(client, project_id),
        fetch_open_issues(client, project_id),
        fetch_pipelines(client, project_id),
    )

    blockers = []
    blockers.extend(detect_stale_mrs(mrs, repo_name))
    blockers.extend(detect_unassigned_issues(issues, repo_name))
    blockers.extend(detect_failed_pipelines(pipelines, repo_name))

    return blockers


async def fetch_project_id(client: httpx.AsyncClient, namespace_path: str) -> int | None:
    encoded = namespace_path.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded}"
    try:
        data = await _get(client, url)
        return data.get("id")
    except Exception:
        return None


async def detect(repos: list[str]) -> dict:
    """
    Main entry point called by LangGraph orchestrator.

    Returns:
        {
          "total_blockers": int,
          "critical_count": int,   (priority >= 8)
          "blockers": [ { type, repo, title, priority, url, ... }, ... ],
          "by_type": { "stale_mr": int, "failed_pipeline": int, "unassigned_issue": int }
        }
    """
    all_blockers: list[dict] = []

    async with httpx.AsyncClient() as client:
        for repo_path in repos:
            project_id = await fetch_project_id(client, repo_path)
            if not project_id:
                print(f"[blocker] WARNING: could not resolve '{repo_path}' — skipping")
                continue
            blockers = await detect_blockers_for_project(client, project_id, repo_path)
            all_blockers.extend(blockers)

    # Sort by priority descending
    all_blockers.sort(key=lambda b: b["priority"], reverse=True)

    by_type = {"stale_mr": 0, "failed_pipeline": 0, "unassigned_issue": 0}
    for b in all_blockers:
        by_type[b["type"]] = by_type.get(b["type"], 0) + 1

    return {
        "total_blockers": len(all_blockers),
        "critical_count": sum(1 for b in all_blockers if b["priority"] >= 8),
        "blockers":        all_blockers,
        "by_type":         by_type,
    }


if __name__ == "__main__":
    import json
    TEST_REPOS = [r.strip() for r in os.getenv("TEST_REPOS", "").split(",") if r.strip()]
    if not TEST_REPOS:
        print("Set TEST_REPOS=namespace/project in .env")
    else:
        result = asyncio.run(detect(TEST_REPOS))
        print(json.dumps(result, indent=2))
