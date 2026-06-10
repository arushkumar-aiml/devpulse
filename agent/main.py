"""
agent/main.py
Author: Arush (@arushkumar-aiml)
LangGraph orchestrator — multi-step agent pipeline.
Compatible: Python 3.13+
"""

import os
import asyncio
from typing import TypedDict, Any
from dotenv import load_dotenv

import google.generativeai as genai
from langgraph.graph import StateGraph, END

from modules.contribution_analyzer import analyze as analyze_contributions
from modules.standup_generator      import generate_standups
from modules.blocker_detection      import detect as detect_blockers
from modules.action_executor        import execute_all_blockers

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


# ── Agent State ──────────────────────────────────────────────────

class DevPulseState(TypedDict):
    repos:            list[str]
    since_days:       int
    auto_fix:         bool
    analysis_result:  dict
    standup_result:   dict
    blocker_result:   dict
    action_results:   list[dict]
    agent_summary:    str
    error:            str | None


# ── Node 1: Fetch & Analyze Contributions (Adeel's module) ───────

async def node_analyze(state: DevPulseState) -> DevPulseState:
    print("[agent] Node 1: Analyzing contributions...")
    try:
        result = await analyze_contributions(
            repos      = state["repos"],
            since_days = state.get("since_days", 7),
        )
        state["analysis_result"] = result
        print(f"[agent] Found {len(result.get('contributors', {}))} contributors")
    except Exception as e:
        state["error"] = f"Analysis failed: {str(e)}"
        state["analysis_result"] = {"contributors": {}, "summary": {}}
    return state


# ── Node 2: Detect Blockers (Aniket's module) ────────────────────

async def node_detect_blockers(state: DevPulseState) -> DevPulseState:
    print("[agent] Node 2: Detecting blockers...")
    try:
        result = await detect_blockers(repos=state["repos"])
        state["blocker_result"] = result
        print(f"[agent] Found {result.get('total_blockers', 0)} blockers, "
              f"{result.get('critical_count', 0)} critical")
    except Exception as e:
        state["error"] = f"Blocker detection failed: {str(e)}"
        state["blocker_result"] = {"total_blockers": 0, "critical_count": 0, "blockers": [], "by_type": {}}
    return state


# ── Node 3: Generate Standups (Ayushi's module) ──────────────────

async def node_generate_standups(state: DevPulseState) -> DevPulseState:
    print("[agent] Node 3: Generating standups...")
    try:
        result = await generate_standups(state["analysis_result"])
        state["standup_result"] = result
        print(f"[agent] Generated {len(result.get('standups', []))} standups")
    except Exception as e:
        state["error"] = f"Standup generation failed: {str(e)}"
        state["standup_result"] = {"date": "", "standups": [], "team_summary": ""}
    return state


# ── Node 4: Execute Actions (Abhay's module) ─────────────────────

async def node_execute_actions(state: DevPulseState) -> DevPulseState:
    if not state.get("auto_fix", False):
        print("[agent] Node 4: Auto-fix disabled — skipping actions")
        state["action_results"] = []
        return state

    print("[agent] Node 4: Executing auto-fix actions...")
    try:
        results = await execute_all_blockers(state["blocker_result"])
        state["action_results"] = results
        success_count = sum(1 for r in results if r.get("success"))
        print(f"[agent] Executed {len(results)} actions, {success_count} successful")
    except Exception as e:
        state["error"] = f"Action execution failed: {str(e)}"
        state["action_results"] = []
    return state


# ── Node 5: Gemini Summary ────────────────────────────────────────

async def node_gemini_summary(state: DevPulseState) -> DevPulseState:
    print("[agent] Node 5: Generating Gemini agent summary...")
    try:
        analysis = state.get("analysis_result", {})
        blockers = state.get("blocker_result", {})
        actions  = state.get("action_results", [])
        summary_data = analysis.get("summary", {})

        prompt = f"""You are DevPulse, an AI engineering operations agent.
Summarize what you just did in 3-4 sentences for the engineering manager.

Data:
- Repos analyzed: {analysis.get('repos_analyzed', [])}
- Contributors: {len(analysis.get('contributors', {}))}
- Total commits: {summary_data.get('total_commits', 0)}
- Total MRs: {summary_data.get('total_mrs', 0)}
- Top contributor: {summary_data.get('top_contributor', 'N/A')}
- Blockers found: {blockers.get('total_blockers', 0)} ({blockers.get('critical_count', 0)} critical)
- Actions taken: {len(actions)} auto-fixes executed

Be concise, professional, and highlight anything urgent. Start with "DevPulse Report:"."""

        model = genai.GenerativeModel("gemini-2.0-flash")
        resp  = await asyncio.to_thread(model.generate_content, prompt)
        state["agent_summary"] = resp.text.strip()
    except Exception as e:
        state["agent_summary"] = (
            f"DevPulse Report: Analyzed {len(state.get('analysis_result',{}).get('contributors',{}))} contributors, "
            f"found {state.get('blocker_result',{}).get('total_blockers',0)} blockers."
        )
    return state


# ── Conditional routing ───────────────────────────────────────────

def should_continue(state: DevPulseState) -> str:
    if state.get("error") and not state.get("analysis_result", {}).get("contributors"):
        return END
    return "detect_blockers"


# ── Build LangGraph ───────────────────────────────────────────────

def build_graph() -> Any:
    graph = StateGraph(DevPulseState)

    graph.add_node("analyze",          node_analyze)
    graph.add_node("detect_blockers",  node_detect_blockers)
    graph.add_node("generate_standups",node_generate_standups)
    graph.add_node("execute_actions",  node_execute_actions)
    graph.add_node("gemini_summary",   node_gemini_summary)

    graph.set_entry_point("analyze")
    graph.add_conditional_edges("analyze", should_continue, {
        "detect_blockers": "detect_blockers",
        END: END,
    })
    graph.add_edge("detect_blockers",   "generate_standups")
    graph.add_edge("generate_standups", "execute_actions")
    graph.add_edge("execute_actions",   "gemini_summary")
    graph.add_edge("gemini_summary",    END)

    return graph.compile()


GRAPH = build_graph()


# ── Public entry point ────────────────────────────────────────────

async def run_pipeline(repos: list[str], since_days: int = 7, auto_fix: bool = False) -> dict:
    """
    Run the full DevPulse agent pipeline.

    Args:
        repos:      list of 'namespace/project' strings
        since_days: lookback window (default 7)
        auto_fix:   if True, auto-execute fixes for critical blockers

    Returns:
        Complete state dict with analysis, standups, blockers, actions, summary
    """
    initial_state: DevPulseState = {
        "repos":            repos,
        "since_days":       since_days,
        "auto_fix":         auto_fix,
        "analysis_result":  {},
        "standup_result":   {},
        "blocker_result":   {},
        "action_results":   [],
        "agent_summary":    "",
        "error":            None,
    }

    final_state = await GRAPH.ainvoke(initial_state)
    return final_state


if __name__ == "__main__":
    import json
    TEST_REPOS = [r.strip() for r in os.getenv("TEST_REPOS", "").split(",") if r.strip()]
    if not TEST_REPOS:
        print("Set TEST_REPOS=namespace/project in .env")
    else:
        result = asyncio.run(run_pipeline(TEST_REPOS, auto_fix=False))
        print(json.dumps(result, indent=2, default=str))
