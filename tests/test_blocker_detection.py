"""Tests for blocker_detection — Aniket"""
import pytest
from modules.blocker_detection import detect_stale_mrs, detect_unassigned_issues, _priority_score

def test_stale_mr_detected():
    mrs = [{"iid":1,"title":"Fix bug","state":"opened","updated_at":"2026-06-01T10:00:00Z",
            "author":{"username":"alice"},"assignee":None,"web_url":"https://gitlab.com","has_conflicts":False}]
    blockers = detect_stale_mrs(mrs, "org/repo")
    assert len(blockers) == 1
    assert blockers[0]["type"] == "stale_mr"

def test_fresh_mr_not_stale():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    mrs = [{"iid":2,"title":"New MR","state":"opened","updated_at":now,
            "author":{"username":"bob"},"assignee":None,"web_url":"","has_conflicts":False}]
    blockers = detect_stale_mrs(mrs, "org/repo")
    assert len(blockers) == 0

def test_unassigned_issue_detected():
    issues = [{"iid":1,"title":"Crash bug","state":"opened","updated_at":"2026-06-05T00:00:00Z",
               "author":{"username":"alice"},"assignee":None,"assignees":[],"web_url":"","labels":["bug"]}]
    blockers = detect_unassigned_issues(issues, "org/repo")
    assert len(blockers) == 1

def test_priority_score_bounds():
    for btype in ["stale_mr","failed_pipeline","unassigned_issue"]:
        score = _priority_score(btype, 10, {"branch":"main","labels":["bug"]})
        assert 1 <= score <= 10
