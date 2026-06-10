"""Tests for action_executor — Abhay"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from modules.action_executor import execute

def test_unknown_action():
    result = asyncio.run(execute({"action": "fly_to_moon", "repo": "org/repo"}))
    assert result["success"] == False
    assert "Unknown action" in result["error"]

def test_execute_requires_repo():
    result = asyncio.run(execute({"action": "create_issue", "repo": "", "title": "Test", "body": "Body"}))
    assert result["success"] == False
