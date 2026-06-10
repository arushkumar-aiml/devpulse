"""Tests for contribution_analyzer — Adeel"""
import pytest
from modules.contribution_analyzer import aggregate_contributions, _score

def test_empty_data():
    result = aggregate_contributions("org/repo", [], [], [])
    assert result == {}

def test_commit_counting():
    commits = [{"author_name": "alice", "stats": {"additions": 100, "deletions": 10}, "committed_date": "2026-06-10T10:00:00Z"}]
    result = aggregate_contributions("org/repo", commits, [], [])
    assert "alice" in result
    assert result["alice"]["commits"] == 1
    assert result["alice"]["lines_added"] == 100

def test_mr_state_counting():
    mrs = [
        {"author": {"username": "bob"}, "state": "merged", "updated_at": "2026-06-10T10:00:00Z"},
        {"author": {"username": "bob"}, "state": "opened", "updated_at": "2026-06-10T10:00:00Z"},
    ]
    result = aggregate_contributions("org/repo", [], mrs, [])
    assert result["bob"]["mrs_merged"] == 1
    assert result["bob"]["mrs_opened"] == 1

def test_activity_score_capped_at_100():
    user = {"commits":999,"lines_added":99999,"lines_removed":0,"mrs_opened":99,"mrs_merged":99,"issues_opened":0,"issues_closed":99}
    assert _score(user) == 100
