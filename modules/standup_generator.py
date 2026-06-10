"""
modules/standup_generator.py
Author: Ayushi (@ayushishuklaME)
Calls Gemini API to generate natural language standup per developer.
Compatible: Python 3.13+
"""

import os
import asyncio
import google.generativeai as genai
from datetime import date
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
MODEL = "gemini-2.0-flash"


def _build_prompt(username: str, data: dict) -> str:
    today = date.today().strftime("%B %d, %Y")
    return f"""You are a helpful engineering assistant writing a daily standup for a developer.

Today's date: {today}
Developer: {username}

Activity data (last 7 days):
- Commits pushed: {data.get('commits', 0)}
- Lines added: {data.get('lines_added', 0)}
- Lines removed: {data.get('lines_removed', 0)}
- Merge Requests opened: {data.get('mrs_opened', 0)}
- Merge Requests merged: {data.get('mrs_merged', 0)}
- Issues opened: {data.get('issues_opened', 0)}
- Issues closed: {data.get('issues_closed', 0)}
- Repos touched: {', '.join(data.get('repos_touched', [])) or 'none'}
- Activity score: {data.get('activity_score', 0)}/100
- Last active: {data.get('last_active', 'unknown')}

Write a professional standup update in this exact format:
**Yesterday:** (what they worked on based on the data)
**Today:** (logical next steps based on their recent activity)
**Blockers:** (mention if activity score is low or no recent commits — otherwise "None")

Keep it concise, 2-3 sentences per section. Sound human, not robotic.
Do NOT mention raw numbers — translate them into natural language."""


async def generate_standup_for_user(username: str, data: dict) -> dict:
    """Generate standup for a single user."""
    prompt = _build_prompt(username, data)
    try:
        model = genai.GenerativeModel(MODEL)
        response = await asyncio.to_thread(model.generate_content, prompt)
        standup_text = response.text.strip()
    except Exception as e:
        standup_text = (
            f"**Yesterday:** {username} made {data.get('commits',0)} commits.\n"
            f"**Today:** Continuing development work.\n"
            f"**Blockers:** Unable to generate AI summary — {str(e)}"
        )

    return {
        "username": username,
        "standup":  standup_text,
        "date":     date.today().isoformat(),
        "stats": {
            "commits":       data.get("commits", 0),
            "activity_score": data.get("activity_score", 0),
            "last_active":   data.get("last_active"),
        },
    }


async def generate_standups(analysis_result: dict) -> dict:
    """
    Main entry point called by LangGraph orchestrator.

    Args:
        analysis_result: output from contribution_analyzer.analyze()

    Returns:
        {
          "date": "2026-06-10",
          "standups": [
              { "username": "alice", "standup": "...", "stats": {...} },
              ...
          ],
          "team_summary": "Overall team was highly active today..."
        }
    """
    contributors = analysis_result.get("contributors", {})

    if not contributors:
        return {
            "date": date.today().isoformat(),
            "standups": [],
            "team_summary": "No contributor data available.",
        }

    # Generate all standups concurrently
    tasks = [
        generate_standup_for_user(username, data)
        for username, data in contributors.items()
    ]
    standups = await asyncio.gather(*tasks)

    # Sort by activity score descending
    standups_sorted = sorted(standups, key=lambda x: x["stats"]["activity_score"], reverse=True)

    # Generate team summary
    summary_result = analysis_result.get("summary", {})
    top = summary_result.get("top_contributor", "the team")
    total_commits = summary_result.get("total_commits", 0)
    total_mrs = summary_result.get("total_mrs", 0)

    try:
        model = genai.GenerativeModel(MODEL)
        team_prompt = f"""Write a 2-sentence team standup summary for an engineering manager.
Team stats today: {total_commits} total commits, {total_mrs} merge requests, 
top contributor: {top}, {len(contributors)} active developers.
Be encouraging and specific. No bullet points — just 2 clean sentences."""
        resp = await asyncio.to_thread(model.generate_content, team_prompt)
        team_summary = resp.text.strip()
    except Exception:
        team_summary = (
            f"The team made {total_commits} commits and {total_mrs} merge requests today. "
            f"Top contributor: {top}."
        )

    return {
        "date":         date.today().isoformat(),
        "standups":     standups_sorted,
        "team_summary": team_summary,
    }


if __name__ == "__main__":
    import json
    # Mock data for standalone testing
    mock_analysis = {
        "contributors": {
            "alice": {"commits": 5, "lines_added": 230, "lines_removed": 40,
                      "mrs_opened": 1, "mrs_merged": 2, "issues_opened": 0,
                      "issues_closed": 1, "repos_touched": ["myorg/backend"],
                      "last_active": "2026-06-10T09:00:00+00:00", "activity_score": 72},
            "bob":   {"commits": 2, "lines_added": 80,  "lines_removed": 10,
                      "mrs_opened": 0, "mrs_merged": 1, "issues_opened": 1,
                      "issues_closed": 0, "repos_touched": ["myorg/frontend"],
                      "last_active": "2026-06-09T17:00:00+00:00", "activity_score": 24},
        },
        "summary": {"total_commits": 7, "total_mrs": 4, "total_issues": 2, "top_contributor": "alice"},
    }
    result = asyncio.run(generate_standups(mock_analysis))
    print(json.dumps(result, indent=2))
