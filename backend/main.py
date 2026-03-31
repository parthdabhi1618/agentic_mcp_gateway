from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import RunRequest, RunResponse, Step, Log
from planner import plan
from executor import execute_steps

app = FastAPI(title="Agentic MCP Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Agentic MCP Gateway is running. Visit /docs for the Swagger UI or /health to check status."}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run", response_model=RunResponse)
def run(request: RunRequest):
    try:
        steps = plan(request.prompt)
    except Exception as exc:
        print(f"[ERROR] Planner failed: {exc}")
        steps = []

    logs = execute_steps(steps)

    return RunResponse(
        steps=[Step(**step) for step in steps],
        logs=[Log(**log) for log in logs],
    )
