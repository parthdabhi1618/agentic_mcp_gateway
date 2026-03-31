# Agentic MCP Gateway

Agentic MCP Gateway is an AI-powered workflow orchestration app. A user describes a workflow in plain English, the planner converts that request into structured tool steps, and the backend executes those steps across services like GitHub, Slack, Jira, and Sheets.

## Repo Structure

```text
agentic-mcp-gateway/
├── frontend/   # React + Vite UI
└── backend/    # FastAPI backend, planner, executor, integrations
```

## Features

- Natural-language workflow input
- Tool planning through Ollama
- GitHub, Slack, Jira, and Sheets integration paths
- Execution trace and status logs
- History sidebar with restore support
- Retry logic and graceful failure handling
- Contract-safe API responses

## Prerequisites

- Node.js 18+
- Python 3.11+
- Ollama installed locally
- An available Ollama model such as `qwen3:4b`

## Environment Setup

Copy the backend env template and fill what you need:

```bash
cd backend
cp .env.example .env
```

Only GitHub and Slack require real credentials for live success.
Jira and Sheets support demo-safe behavior when credentials are missing.

## Run The Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at:

```text
http://localhost:8000
```

Useful endpoints:
- `GET /health`
- `POST /run`
- `GET /docs`

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend usually runs at:

```text
http://localhost:5173
```

## Run Ollama

Example:

```bash
ollama serve
```

If needed:

```bash
ollama pull qwen3:4b
```

## Demo Prompts

- `Create a GitHub branch named fix/login`
- `Send a message to #general saying the gateway is live`
- `Create a branch fix/login and tell the team on Slack`
- `Create GitHub branch fix/critical, notify #alerts on Slack, and create a Jira bug in project DEMO`
- `Book a meeting room`

## Testing

From `backend/`:

```bash
python test_executor_local.py
python test_planner.py
python validate_integration.py
```

## Notes

- `.env` is intentionally not included in this repo
- `node_modules`, `dist`, caches, and local artifacts are excluded
- context files, SOPs, and private hackathon notes are intentionally not included
