# backend/main.py — V6 (Agentic OS Release)
# Full Plan/Execute + @context Injection + File Manager + Context Vault
# Merged from: mem2 (backend/endpoints) + mem3 (context_parser, planner integration)
#
# This is the FINAL merged main.py for the V6 release.

import asyncio
import uuid
import os
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import aiofiles
from datetime import datetime

import permissions as perm
import jobs
import vault
import scheduler as sched
from executor import run_job
from planner import plan as do_plan
from context_parser import extract_context_refs
import requests as http_requests

perm.load_permissions()
vault.inject_env_from_vault()

app = FastAPI(title="Agentic MCP Gateway V6")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Workspace directories ──────────────────────────────────────────────────────

WORKSPACE_DIRS = [
    "workspace/context/github_context",
    "workspace/context/slack_context",
    "workspace/context/session_context",
    "workspace/context/task_context",
    "workspace/context/notion_context",
    "workspace/context/linear_context",
    "workspace/files/uploads",
    "workspace/files/generated",
]
FILES_UPLOAD_DIR = "workspace/files/uploads"
FILES_GENERATED_DIR = "workspace/files/generated"
CONTEXT_ROOT = "workspace/context"

# ── Lifecycle ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    for d in WORKSPACE_DIRS:
        os.makedirs(d, exist_ok=True)
    sched.start()

@app.on_event("shutdown")
async def shutdown():
    sched.stop()

# ── Models ─────────────────────────────────────────────────────────────────────

class StepInput(BaseModel):
    step_id: Optional[str] = None
    tool: str
    action: Optional[str] = None
    args: Optional[dict] = {}
    requires_permission: Optional[bool] = None

class ExecuteRequest(BaseModel):
    plan_id: Optional[str] = None
    steps: List[StepInput]
    execution_mode: Optional[str] = "run_now"
    prompt: Optional[str] = ""

class PermissionUpdate(BaseModel):
    tool: str
    action: str
    allowed: bool
    scope: Optional[str] = "always"

# ── V5: Plan models ───────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    prompt: str
    context_refs: Optional[List[str]] = []
    tool_scope: Optional[List[str]] = None

class PlanStep(BaseModel):
    step_id: str
    tool: str
    action: str
    args: dict
    requires_permission: bool = False

class PlanResponse(BaseModel):
    plan_id: str
    steps: List[PlanStep]
    validation: dict

# ── V5: Vault models ──────────────────────────────────────────────────────────

class KeyConnectRequest(BaseModel):
    tool: str
    key: str

# ── V5: Scheduler models ──────────────────────────────────────────────────────

class ScheduleConfig(BaseModel):
    type: str          # "once" | "recurring"
    run_at: Optional[str] = None    # ISO-8601 for once
    cron: Optional[str] = None      # cron string for recurring

class ScheduleRequest(BaseModel):
    plan_id: Optional[str] = None
    steps: List[dict]
    schedule: ScheduleConfig

# ── Health ──────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "6"}

# ── V6: Plan endpoint (with @context parsing) ─────────────────────────────────

@app.post("/plan", response_model=PlanResponse)
def plan_endpoint(req: PlanRequest):
    """V6 planning endpoint. Parses @context refs from prompt, returns plan_id + enriched steps."""
    # V6: Extract @context mentions from the raw prompt
    clean_prompt, auto_refs = extract_context_refs(req.prompt)
    # Merge with any explicitly passed context_refs
    all_refs = list(set(auto_refs + (req.context_refs or [])))

    steps_raw = do_plan(clean_prompt, context_refs=all_refs)

    steps = []
    for i, raw in enumerate(steps_raw):
        tool   = raw.get("tool", "")
        action = raw.get("action") or raw.get("args", {}).get("action", "")
        args   = {k: v for k, v in raw.get("args", raw).items() if k not in ("tool", "action")}
        requires = not perm.is_allowed(tool, action)
        steps.append(PlanStep(
            step_id=str(uuid.uuid4()),
            tool=tool,
            action=action,
            args=args,
            requires_permission=requires
        ))

    return PlanResponse(
        plan_id=str(uuid.uuid4()),
        steps=steps,
        validation={"valid": True, "issues": []}
    )

# ── Permissions ─────────────────────────────────────────────────────────────────

@app.get("/permissions")
def get_permissions():
    return perm.get_all()

@app.post("/permissions")
def update_permission(update: PermissionUpdate):
    perm.set_permission(update.tool, update.action, update.allowed)
    return {"tool": update.tool, "action": update.action, "allowed": update.allowed}

# ── Execute ──────────────────────────────────────────────────────────────────────

@app.post("/execute")
async def execute(req: ExecuteRequest, background_tasks: BackgroundTasks):
    job_id = jobs.create_job()
    steps = [s.dict() for s in req.steps]
    # Normalise: if action is in args, hoist it up (V3 compat)
    for s in steps:
        if not s.get("action") and s.get("args", {}).get("action"):
            s["action"] = s["args"]["action"]

    # V5: Store prompt on the job for context_writer
    job = jobs.get_job(job_id)
    if job:
        job["_prompt"] = req.prompt or ""

    background_tasks.add_task(run_job, job_id, steps)
    return {"job_id": job_id, "status": "accepted"}

# ── SSE Stream ───────────────────────────────────────────────────────────────────

@app.get("/job/{job_id}/stream")
async def stream(job_id: str):
    return StreamingResponse(
        jobs.event_stream(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# ── Abort ────────────────────────────────────────────────────────────────────────

@app.post("/job/{job_id}/abort")
def abort(job_id: str):
    jobs.cancel_job(job_id)
    return {"job_id": job_id, "status": "aborting"}

# ── V5: Vault / Key Connect ─────────────────────────────────────────────────────

TOOL_TEST_ENDPOINTS = {
    "github":  lambda key: http_requests.get("https://api.github.com/user",
                              headers={"Authorization": f"Bearer {key}"}, timeout=8),
    "slack":   lambda key: http_requests.get("https://slack.com/api/auth.test",
                              headers={"Authorization": f"Bearer {key}"}, timeout=8),
    "notion":  lambda key: http_requests.get("https://api.notion.com/v1/users/me",
                              headers={"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}, timeout=8),
    "linear":  lambda key: http_requests.post("https://api.linear.app/graphql",
                              headers={"Authorization": key, "Content-Type": "application/json"},
                              json={"query": "{ viewer { id } }"}, timeout=8),
}

@app.post("/keys/connect")
def connect_key(req: KeyConnectRequest):
    """Connect an API key for a tool via the vault. Tests key if possible."""
    tester = TOOL_TEST_ENDPOINTS.get(req.tool)
    if tester:
        try:
            r = tester(req.key)
            if r.status_code in (200, 204):
                vault.save_key(req.tool, req.key)
                vault.inject_env_from_vault()
                return {"tool": req.tool, "status": "connected", "message": "Key saved and verified"}
            else:
                return {"tool": req.tool, "status": "failed", "message": f"API returned {r.status_code}"}
        except Exception as e:
            return {"tool": req.tool, "status": "failed", "message": str(e)}
    else:
        # No test endpoint defined — save anyway (jira, discord, sheets need more complex auth)
        vault.save_key(req.tool, req.key)
        vault.inject_env_from_vault()
        return {"tool": req.tool, "status": "connected", "message": "Key saved (no test available)"}

@app.get("/keys/status")
def key_status():
    """Return connection status for all 7 tools. Checks vault first, then env vars."""
    tool_env_map = {
        "github":  "GITHUB_TOKEN",
        "slack":   "SLACK_TOKEN",
        "jira":    "JIRA_TOKEN",
        "sheets":  "GOOGLE_SHEETS_CREDS_JSON",
        "linear":  "LINEAR_API_KEY",
        "notion":  "NOTION_TOKEN",
        "discord": "DISCORD_TOKEN",
    }
    try:
        vault_keys = vault.load_all_keys()
    except Exception:
        vault_keys = {}

    result = {}
    for tool, env_var in tool_env_map.items():
        if vault_keys.get(tool):
            result[tool] = "connected"
        elif os.getenv(env_var):
            result[tool] = "connected"
        else:
            result[tool] = "not_configured"
    return result

# ── V5: Scheduler ───────────────────────────────────────────────────────────────

@app.post("/schedule")
def create_schedule(req: ScheduleRequest):
    """Schedule a plan for one-time or recurring execution."""
    steps = req.steps
    schedule_id = sched.schedule_task(
        plan_id=req.plan_id or str(uuid.uuid4()),
        steps=steps,
        schedule_config=req.schedule.dict()
    )
    return {"schedule_id": schedule_id, "status": "scheduled"}

@app.get("/schedule")
def list_schedules():
    return {"tasks": sched.load_scheduled()}

# ── V6: File Management ────────────────────────────────────────────────────────
# Uses mem2's hardened implementation with path traversal protection and HTTPException

@app.get("/files")
def list_files():
    files = []
    for folder, ftype in [(FILES_UPLOAD_DIR, "upload"), (FILES_GENERATED_DIR, "generated")]:
        if os.path.exists(folder):
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    stat = os.stat(fpath)
                    files.append({
                        "name": fname,
                        "size": stat.st_size,
                        "type": ftype,
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
    return {"files": files}

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the workspace. Hardened against path traversal (mem2)."""
    filename = os.path.basename(file.filename or "upload")
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    dest = os.path.join(FILES_UPLOAD_DIR, filename)
    if not os.path.abspath(dest).startswith(os.path.abspath(FILES_UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    size = 0
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)
            size += len(chunk)
    return {"name": filename, "size": size, "status": "uploaded"}

@app.delete("/files/{filename}")
def delete_file(filename: str):
    """Delete an uploaded file. Hardened against path traversal (mem2)."""
    path = os.path.join(FILES_UPLOAD_DIR, filename)
    if not os.path.abspath(path).startswith(os.path.abspath(FILES_UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(path)
    return {"deleted": filename}

# ── V6: Context browsing ───────────────────────────────────────────────────────

@app.get("/context")
def get_context_tree():
    tree = {}
    if not os.path.exists(CONTEXT_ROOT):
        return {"tree": {}}
    for folder in os.listdir(CONTEXT_ROOT):
        folder_path = os.path.join(CONTEXT_ROOT, folder)
        if os.path.isdir(folder_path):
            tree[folder] = [
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
    return {"tree": tree}

@app.get("/context/{folder}/{filename}")
def read_context_file(folder: str, filename: str):
    """Fetch a specific context file. Returns metadata + content (mem2 enriched)."""
    import json as json_mod
    path = os.path.join(CONTEXT_ROOT, folder, filename)
    if not os.path.abspath(path).startswith(os.path.abspath(CONTEXT_ROOT)):
        return {"error": "Access denied"}
    if not os.path.exists(path):
        return {"error": "Not found"}

    stat = os.stat(path)
    metadata = {
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

    if filename.endswith(".json"):
        with open(path) as f:
            return {"folder": folder, "file": filename, "metadata": metadata, "content": json_mod.load(f)}
    with open(path) as f:
        return {"folder": folder, "file": filename, "metadata": metadata, "content": f.read()}

# ── Legacy /run (V3 compat) ──────────────────────────────────────────────────────

class RunRequest(BaseModel):
    prompt: str

@app.post("/run")
def run_legacy(req: RunRequest):
    """V3 compatibility endpoint. Deprecated in V5."""
    steps = do_plan(req.prompt)
    return {"steps": steps, "logs": []}
