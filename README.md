# 🚀 DevPulse

> **Your team's GitLab — analyzed, summarized, and acted upon by AI.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite)](https://vitejs.dev)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?logo=google)](https://ai.google.dev)
[![GitLab MCP](https://img.shields.io/badge/GitLab-MCP_Server-FC6D26?logo=gitlab)](https://gitlab.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-black)](https://langchain-ai.github.io/langgraph/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Agent_Builder-4285F4?logo=googlecloud)](https://cloud.google.com)

---

## 🧠 What is DevPulse?

DevPulse is an **AI-powered developer operations agent** that connects to your team's GitLab repositories and does what no dashboard can — it *thinks*, *summarizes*, and *acts*.

Every morning, engineering teams waste 20–30 minutes in standups discussing what everyone already committed to GitLab. PRs go stale. Pipelines fail silently. Issues pile up unassigned. DevPulse eliminates all of that.

**In one click, DevPulse:**
- Fetches every team member's commits, PRs, and merge requests from GitLab
- Generates a human-quality AI standup for each developer
- Detects blockers: stale PRs, failed CI pipelines, unassigned critical issues
- Takes real action: creates GitLab issues, assigns them, posts comments — autonomously

---

## ❌ The Problem

| Pain Point | Reality |
|------------|---------|
| Daily standups | 20 min meeting to share what's already in git |
| Stale PRs | PRs sit unreviewed for days, blocking entire features |
| Silent CI failures | Pipelines fail, no one notices until deploy day |
| Unassigned issues | Bugs rot in the backlog with no owner |
| Manager visibility | No real-time view of team health without digging through GitLab |

---

## ✅ The Solution

DevPulse is a **multi-step reasoning agent** that:

```
FETCH → ANALYZE → DETECT → GENERATE → ACT
```

1. **FETCH** — Pulls live data from GitLab via MCP server
2. **ANALYZE** — Scores each developer's contribution activity
3. **DETECT** — Finds blockers with a priority score (1–10)
4. **GENERATE** — Writes AI standups using Gemini 2.0 Flash
5. **ACT** — Creates issues, assigns owners, posts comments on GitLab

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DevPulse Agent                           │
│                                                                 │
│   React + Vite Frontend (GitHub Pages)                          │
│   ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────────┐  │
│   │ Activity │ │   Standup    │ │ Blockers │ │  Fix It Btn │  │
│   │   Feed   │ │   Report     │ │   List   │ │  (Actions)  │  │
│   └────┬─────┘ └──────┬───────┘ └────┬─────┘ └──────┬──────┘  │
│        └──────────────┴──────────────┴───────────────┘         │
│                              │                                  │
│                    FastAPI Backend (Python)                      │
│                    POST /analyze                                 │
│                    GET  /standup                                 │
│                    GET  /blockers                                │
│                    POST /action                                  │
│                              │                                  │
│              ┌───────────────▼────────────────┐                 │
│              │     LangGraph Orchestrator      │                 │
│              │         (agent/main.py)         │                 │
│              │                                 │                 │
│              │  Node 1: fetch_data             │                 │
│              │     ↓                           │                 │
│              │  Node 2: analyze_contributions  │                 │
│              │     ↓                           │                 │
│              │  Node 3: detect_blockers        │                 │
│              │     ↓                           │                 │
│              │  Node 4: generate_standups      │                 │
│              │     ↓                           │                 │
│              │  Node 5: execute_actions        │                 │
│              └──────┬──────────────┬───────────┘                │
│                     │              │                             │
│            ┌────────▼──┐    ┌──────▼────────┐                  │
│            │  Gemini   │    │  GitLab MCP   │                  │
│            │ 2.0 Flash │    │    Server     │                  │
│            │ (Reason)  │    │ (Take Action) │                  │
│            └───────────┘    └───────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI Brain | Gemini 2.0 Flash | Natural language reasoning + standup generation |
| Agent Framework | LangGraph + Google Cloud Agent Builder | Multi-step agent orchestration |
| GitLab Integration | GitLab MCP Server | Fetch data + take real actions |
| Backend | Python 3.11 + FastAPI | REST API serving agent results |
| Frontend | React 18 + Vite 5 | Real-time dashboard UI |
| Deployment | GitHub Pages + Vercel | Hosted public URL |
| Auth | Personal Access Tokens | Secure GitLab + GitHub access |

---

## 🔌 GitLab MCP Integration

DevPulse uses the **GitLab MCP (Model Context Protocol) Server** as its primary action layer. This is not a superficial integration — MCP is the reason DevPulse can *act*, not just *report*.

### What MCP enables:

| Action | MCP Tool Used | Module |
|--------|--------------|--------|
| List merge requests | `list_merge_requests` | `contribution_analyzer.py` |
| Get commits per user | `list_commits` | `contribution_analyzer.py` |
| Fetch pipeline status | `get_pipeline` | `blocker_detection.py` |
| List open issues | `list_issues` | `blocker_detection.py` |
| **Create new issue** | `create_issue` | `action_executor.py` |
| **Assign issue** | `update_issue` | `action_executor.py` |
| **Post comment** | `create_note` | `action_executor.py` |

The last three are **write actions** — this is what makes DevPulse a true agent, not just a dashboard.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- GitLab Personal Access Token (with `api` scope)
- Gemini API Key ([get one free](https://aistudio.google.com))

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/devpulse.git
cd devpulse
```

### 2. Set up environment
```bash
cp .env.example .env
# Fill in your keys in .env
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend
```bash
cd agent
uvicorn server:app --reload --port 8000
```

### 5. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

### 6. Open the dashboard
```
http://localhost:5173
```

Enter your GitLab group/username and click **Analyze**. DevPulse does the rest.

---

## 📁 Project Structure

```
devpulse/
├── agent/
│   ├── main.py              # LangGraph orchestrator (Arush)
│   └── server.py            # FastAPI REST API (Arush)
├── modules/
│   ├── contribution_analyzer.py   # Commits/PRs per user (Adeel)
│   ├── standup_generator.py       # AI standup writer (Ayushi)
│   ├── blocker_detection.py       # Stale PR + CI detector (Aniket)
│   └── action_executor.py         # GitLab MCP actions (Abhay)
├── frontend/
│   └── src/                 # React + Vite dashboard (Arush)
├── tests/                   # Unit tests per module
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🏆 Judging Criteria — How DevPulse Wins

| Criterion | How DevPulse Addresses It |
|-----------|--------------------------|
| **Uses Gemini** | Gemini 2.0 Flash drives all reasoning, standup generation, and blocker prioritization |
| **Uses GitLab MCP** | 7 MCP tools used — including 3 write actions (create, assign, comment) |
| **Multi-step agent** | 5-node LangGraph pipeline: fetch → analyze → detect → generate → act |
| **Takes real actions** | Creates GitLab issues, assigns users, posts comments autonomously |
| **Practical value** | Solves a real daily pain point for every engineering team |
| **Completeness** | Full stack: working frontend, backend, agent, tests, CI/CD |

---

## 👥 Team

| Member | GitHub | Role |
|--------|--------|------|
| **Arush Kumar** | [@arushkumar-aiml](https://github.com/arushkumar-aiml) | Agent Orchestration + LangGraph + Frontend |
| **Adeel** | [@adeelad726](https://github.com/adeelad726) | Contribution Analyzer |
| **Ayushi Shukla** | [@ayushishuklaME](https://github.com/ayushishuklaME) | AI Standup Generator |
| **Aniket** | [@aniketgit-hub101](https://github.com/aniketgit-hub101) | Blocker Detection |
| **Abhay Shukla** | [@abhyashukla16](https://github.com/abhyashukla16) | Action Executor (GitLab MCP) |

---

## 🔑 Environment Variables

```env
GEMINI_API_KEY=        # Google AI Studio API key
GITLAB_TOKEN=          # GitLab PAT with api scope
GITLAB_URL=            # e.g. https://gitlab.com
GITHUB_TOKEN=          # GitHub PAT (for contribution data)
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

```
MIT License
Copyright (c) 2026 DevPulse Team
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software...
```

---

## 🔮 What's Next

- Slack/Discord integration for standup delivery
- Weekly trend reports with Gemini analysis
- GitHub support alongside GitLab
- Team velocity scoring dashboard
- Auto-PR reviewer assignment based on expertise

---

<p align="center">
  Built with ❤️ for the <strong>Google Cloud Rapid Agent Hackathon 2026</strong><br/>
  Track: GitLab | Prize: $5000
</p>
