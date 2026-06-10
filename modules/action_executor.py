"""
modules/action_executor.py
Author: Abhay (@abhyashukla16)
Uses GitLab MCP / REST API to create issues, assign users, post comments.
Compatible: Python 3.13+
"""

import os
import asyncio
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITLAB_URL   = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
HEADERS      = {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}


async def fetch_project_id(client: httpx.AsyncClient, namespace_path: str) -> int | None:
    encoded = namespace_path.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded}"
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception:
        return None


async def fetch_user_id(client: httpx.AsyncClient, username: str) -> int | None:
    url = f"{GITLAB_URL}/api/v4/users"
    try:
        resp = await client.get(url, headers=HEADERS, params={"username": username}, timeout=15)
        resp.raise_for_status()
        users = resp.json()
        return users[0]["id"] if users else None
    except Exception:
        return None


# ─── ACTION 1: Create Issue ───────────────────────────────────────

async def create_issue(
    repo:     str,
    title:    str,
    body:     str,
    labels:   list[str] | None = None,
    assignee: str | None = None,
) -> dict:
    """
    Creates a new GitLab issue.
    Returns action confirmation dict.
    """
    async with httpx.AsyncClient() as client:
        project_id = await fetch_project_id(client, repo)
        if not project_id:
            return {"success": False, "error": f"Project '{repo}' not found", "action": "create_issue"}

        payload: dict = {
            "title":       title,
            "description": body,
            "labels":      ",".join(labels) if labels else "devpulse-auto",
        }

        if assignee:
            user_id = await fetch_user_id(client, assignee)
            if user_id:
                payload["assignee_ids"] = [user_id]

        url  = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues"
        resp = await client.post(url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        issue = resp.json()

        return {
            "success":    True,
            "action":     "create_issue",
            "issue_id":   issue.get("iid"),
            "issue_url":  issue.get("web_url"),
            "title":      title,
            "assignee":   assignee,
            "repo":       repo,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }


# ─── ACTION 2: Assign Issue ───────────────────────────────────────

async def assign_issue(
    repo:     str,
    issue_id: int,
    assignee: str,
) -> dict:
    """
    Assigns an existing GitLab issue to a user.
    """
    async with httpx.AsyncClient() as client:
        project_id = await fetch_project_id(client, repo)
        if not project_id:
            return {"success": False, "error": f"Project '{repo}' not found", "action": "assign_issue"}

        user_id = await fetch_user_id(client, assignee)
        if not user_id:
            return {"success": False, "error": f"User '{assignee}' not found", "action": "assign_issue"}

        url     = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues/{issue_id}"
        payload = {"assignee_ids": [user_id]}
        resp    = await client.put(url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        issue = resp.json()

        return {
            "success":   True,
            "action":    "assign_issue",
            "issue_id":  issue_id,
            "issue_url": issue.get("web_url"),
            "assignee":  assignee,
            "repo":      repo,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ─── ACTION 3: Post Comment ───────────────────────────────────────

async def post_comment(
    repo:     str,
    issue_id: int,
    comment:  str,
) -> dict:
    """
    Posts a comment on a GitLab issue.
    """
    async with httpx.AsyncClient() as client:
        project_id = await fetch_project_id(client, repo)
        if not project_id:
            return {"success": False, "error": f"Project '{repo}' not found", "action": "post_comment"}

        url     = f"{GITLAB_URL}/api/v4/projects/{project_id}/issues/{issue_id}/notes"
        payload = {"body": comment}
        resp    = await client.post(url, headers=HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        note = resp.json()

        return {
            "success":    True,
            "action":     "post_comment",
            "note_id":    note.get("id"),
            "issue_id":   issue_id,
            "comment":    comment[:100] + "..." if len(comment) > 100 else comment,
            "repo":       repo,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }


# ─── ACTION 4: Auto-fix blocker ──────────────────────────────────

async def auto_fix_blocker(blocker: dict) -> dict:
    """
    Given a blocker dict from blocker_detection.py,
    decides and executes the right action automatically.
    """
    btype  = blocker.get("type")
    repo   = blocker.get("repo")
    bid    = blocker.get("id")
    title  = blocker.get("title", "Blocker")
    author = blocker.get("author")

    if btype == "stale_mr":
        comment = (
            f"🤖 **DevPulse Alert:** This MR has been open for "
            f"{blocker.get('age_days', '?')} days without activity.\n\n"
            f"Please review or update this MR to keep the pipeline moving. "
            f"If it's blocked on something, please add a comment explaining why."
        )
        return await post_comment(repo, bid, comment)

    elif btype == "failed_pipeline":
        issue_title = f"🔴 Pipeline failure on `{blocker.get('branch','?')}` — needs immediate fix"
        issue_body  = (
            f"## Pipeline Failure Detected\n\n"
            f"**Branch:** `{blocker.get('branch','?')}`\n"
            f"**Status:** {blocker.get('status','failed')}\n"
            f"**Detected:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"**Action Required:** Investigate the failed pipeline and push a fix.\n\n"
            f"_Auto-generated by DevPulse AI Agent_"
        )
        return await create_issue(
            repo=repo, title=issue_title, body=issue_body,
            labels=["bug", "ci-failure", "devpulse-auto"],
            assignee=author,
        )

    elif btype == "unassigned_issue":
        comment = (
            f"🤖 **DevPulse Alert:** This issue has been unassigned for "
            f"{blocker.get('age_days', '?')} days.\n\n"
            f"Please assign this issue to a team member so it can be resolved promptly."
        )
        return await post_comment(repo, bid, comment)

    return {
        "success": False,
        "error":   f"Unknown blocker type: {btype}",
        "action":  "auto_fix_blocker",
    }


# ─── MAIN ENTRY POINT ────────────────────────────────────────────

async def execute(action_command: dict) -> dict:
    """
    Main entry point called by LangGraph orchestrator.

    action_command examples:
      { "action": "create_issue", "repo": "org/repo", "title": "...", "body": "...", "assignee": "alice" }
      { "action": "assign_issue", "repo": "org/repo", "issue_id": 42, "assignee": "bob" }
      { "action": "post_comment", "repo": "org/repo", "issue_id": 42, "comment": "..." }
      { "action": "auto_fix_blocker", "blocker": { ...blocker dict... } }
    """
    action = action_command.get("action")

    if action == "create_issue":
        return await create_issue(
            repo     = action_command["repo"],
            title    = action_command["title"],
            body     = action_command.get("body", ""),
            labels   = action_command.get("labels"),
            assignee = action_command.get("assignee"),
        )
    elif action == "assign_issue":
        return await assign_issue(
            repo     = action_command["repo"],
            issue_id = action_command["issue_id"],
            assignee = action_command["assignee"],
        )
    elif action == "post_comment":
        return await post_comment(
            repo     = action_command["repo"],
            issue_id = action_command["issue_id"],
            comment  = action_command["comment"],
        )
    elif action == "auto_fix_blocker":
        return await auto_fix_blocker(action_command["blocker"])
    else:
        return {"success": False, "error": f"Unknown action: {action}"}


async def execute_all_blockers(blockers_result: dict) -> list[dict]:
    """Auto-fix top 5 critical blockers (priority >= 7)."""
    critical = [b for b in blockers_result.get("blockers", []) if b["priority"] >= 7][:5]
    if not critical:
        return [{"success": True, "action": "no_action", "message": "No critical blockers found"}]
    tasks = [auto_fix_blocker(b) for b in critical]
    return await asyncio.gather(*tasks)


if __name__ == "__main__":
    import json
    # Test standalone
    test_cmd = {
        "action":  "post_comment",
        "repo":    os.getenv("TEST_REPOS", "").split(",")[0].strip(),
        "issue_id": 1,
        "comment": "Test comment from DevPulse agent.",
    }
    if not test_cmd["repo"]:
        print("Set TEST_REPOS=namespace/project in .env")
    else:
        result = asyncio.run(execute(test_cmd))
        print(json.dumps(result, indent=2))
