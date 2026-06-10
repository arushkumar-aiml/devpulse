"""
agent/server.py
Author: Arush (@arushkumar-aiml)
FastAPI backend — REST API for DevPulse agent.
Compatible: Python 3.13+
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.main import run_pipeline
from modules.action_executor import execute as execute_action

load_dotenv()

# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 DevPulse Agent Server starting...")
    yield
    print("👋 DevPulse Agent Server shutting down.")


# ── App ───────────────────────────────────────────────────────────

app = FastAPI(
    title       = "DevPulse API",
    description = "AI-powered developer operations agent",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# In-memory cache for last pipeline result
_last_result: dict = {}


# ── Request / Response Models ─────────────────────────────────────

class AnalyzeRequest(BaseModel):
    repos:      list[str]
    since_days: int  = 7
    auto_fix:   bool = False


class ActionRequest(BaseModel):
    action:   str
    repo:     str
    title:    str | None = None
    body:     str | None = None
    issue_id: int | None = None
    assignee: str | None = None
    comment:  str | None = None
    labels:   list[str] | None = None
    blocker:  dict | None = None


# ── Routes ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name":    "DevPulse API",
        "version": "1.0.0",
        "status":  "running",
        "endpoints": ["/analyze", "/standup", "/blockers", "/action", "/summary"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Trigger full agent pipeline — fetch → analyze → detect → generate → act."""
    global _last_result

    if not req.repos:
        raise HTTPException(status_code=400, detail="repos list cannot be empty")

    result = await run_pipeline(
        repos      = req.repos,
        since_days = req.since_days,
        auto_fix   = req.auto_fix,
    )

    _last_result = result

    return {
        "success":       True,
        "repos":         req.repos,
        "agent_summary": result.get("agent_summary", ""),
        "contributors":  result.get("analysis_result", {}).get("contributors", {}),
        "summary":       result.get("analysis_result", {}).get("summary", {}),
        "blocker_count": result.get("blocker_result", {}).get("total_blockers", 0),
        "standup_count": len(result.get("standup_result", {}).get("standups", [])),
        "actions_taken": len(result.get("action_results", [])),
    }


@app.get("/standup")
async def get_standup():
    """Return the most recently generated standup report."""
    standup = _last_result.get("standup_result", {})
    if not standup:
        raise HTTPException(status_code=404, detail="No standup available. Run /analyze first.")
    return standup


@app.get("/blockers")
async def get_blockers():
    """Return current detected blockers."""
    blockers = _last_result.get("blocker_result", {})
    if not blockers:
        raise HTTPException(status_code=404, detail="No blocker data available. Run /analyze first.")
    return blockers


@app.get("/summary")
async def get_summary():
    """Return Gemini agent summary from last run."""
    if not _last_result:
        raise HTTPException(status_code=404, detail="No data available. Run /analyze first.")
    return {
        "agent_summary":  _last_result.get("agent_summary", ""),
        "analysis":       _last_result.get("analysis_result", {}).get("summary", {}),
        "action_results": _last_result.get("action_results", []),
    }


@app.post("/action")
async def run_action(req: ActionRequest):
    """Trigger a specific GitLab action via MCP action executor."""
    command = req.model_dump(exclude_none=True)
    result  = await execute_action(command)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.server:app", host="0.0.0.0", port=8000, reload=True)
