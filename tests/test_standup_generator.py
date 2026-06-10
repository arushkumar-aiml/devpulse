"""Tests for standup_generator — Ayushi"""
import pytest
from modules.standup_generator import _build_prompt

def test_prompt_contains_username():
    data = {"commits":3,"lines_added":100,"lines_removed":10,"mrs_opened":1,"mrs_merged":0,
            "issues_opened":0,"issues_closed":0,"repos_touched":["org/repo"],"activity_score":30,"last_active":None}
    prompt = _build_prompt("alice", data)
    assert "alice" in prompt

def test_prompt_contains_commit_count():
    data = {"commits":5,"lines_added":0,"lines_removed":0,"mrs_opened":0,"mrs_merged":0,
            "issues_opened":0,"issues_closed":0,"repos_touched":[],"activity_score":15,"last_active":None}
    prompt = _build_prompt("bob", data)
    assert "5" in prompt
