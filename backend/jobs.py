# backend/jobs.py
import uuid
import asyncio
from typing import AsyncGenerator
from datetime import datetime

# In-memory job store { job_id: { "status": str, "cancel": bool, "events": [] } }
_jobs: dict = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "accepted", "cancel": False, "events": [], "queue": asyncio.Queue()}
    return job_id

def get_job(job_id: str):
    return _jobs.get(job_id)

def cancel_job(job_id: str):
    if job_id in _jobs:
        _jobs[job_id]["cancel"] = True

def is_cancelled(job_id: str) -> bool:
    return _jobs.get(job_id, {}).get("cancel", False)

async def push_event(job_id: str, event: dict):
    import json
    if job_id in _jobs:
        _jobs[job_id]["events"].append(event)
        await _jobs[job_id]["queue"].put(json.dumps(event))

async def event_stream(job_id: str) -> AsyncGenerator[str, None]:
    job = _jobs.get(job_id)
    if not job:
        yield "data: {\"error\": \"job not found\"}\n\n"
        return

    import json
    while True:
        try:
            item = await asyncio.wait_for(job["queue"].get(), timeout=30.0)
            yield f"data: {item}\n\n"
            parsed = json.loads(item)
            if parsed.get("step_id") == "__final__":
                break
        except asyncio.TimeoutError:
            yield "data: {\"keepalive\": true}\n\n"
