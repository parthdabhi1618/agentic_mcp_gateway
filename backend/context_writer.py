# backend/context_writer.py (V5 — mem3)
# Writes structured context to disk after job completion.
# Session logs: workspace/context/session_context/session_YYYY-MM-DD.json
# Tool context: workspace/context/<tool>_context/<file>.json

import json
import os
from datetime import datetime, date


CONTEXT_ROOT = os.path.join(os.path.dirname(__file__), "workspace", "context")


def _ensure(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_json(path: str, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def _write_json(path: str, data):
    _ensure(path)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_session_log(job_id: str, prompt: str, events: list):
    """Append this job's outcome to today's session log."""
    log_path = os.path.join(CONTEXT_ROOT, "session_context", f"session_{date.today()}.json")
    log = _read_json(log_path, {"sessions": []})
    log["sessions"].append({
        "job_id": job_id,
        "prompt": prompt,
        "timestamp": datetime.utcnow().isoformat(),
        "steps_count": len([e for e in events if e.get("step_id") != "__final__"]),
        "tools_used": list({e.get("tool") for e in events if e.get("tool") not in (None, "system")}),
        "final_status": next((e["status"] for e in reversed(events)
                               if e.get("step_id") == "__final__"), "unknown")
    })
    _write_json(log_path, log)


def write_tool_context(tool: str, action: str, args: dict, result: dict):
    """Write tool-specific context based on successful action outcomes."""
    if tool == "github":
        _write_github_context(action, args, result)
    elif tool == "slack":
        _write_slack_context(action, args, result)
    elif tool == "notion":
        _write_notion_context(action, args, result)
    elif tool == "linear":
        _write_linear_context(action, args, result)


def _write_github_context(action: str, args: dict, result: dict):
    branches_path = os.path.join(CONTEXT_ROOT, "github_context", "recent_branches.json")
    prs_path      = os.path.join(CONTEXT_ROOT, "github_context", "open_prs.json")

    if action == "create_branch":
        data = _read_json(branches_path, {"branches": []})
        entry = {"name": args.get("name"), "created_at": datetime.utcnow().isoformat()}
        data["branches"] = [entry] + [b for b in data["branches"] if b["name"] != args.get("name")]
        data["branches"] = data["branches"][:20]
        _write_json(branches_path, data)

    elif action == "create_pr":
        data = _read_json(prs_path, {"prs": []})
        data["prs"].append({
            "number":     result.get("pr_number"),
            "url":        result.get("url"),
            "head":       args.get("head"),
            "base":       args.get("base"),
            "title":      args.get("title"),
            "created_at": datetime.utcnow().isoformat()
        })
        data["prs"] = data["prs"][-20:]
        _write_json(prs_path, data)


def _write_slack_context(action: str, args: dict, result: dict):
    channels_path = os.path.join(CONTEXT_ROOT, "slack_context", "channels.json")
    if action in ("send_message", "create_channel"):
        channel = args.get("channel") or args.get("name")
        if channel:
            data = _read_json(channels_path, {"channels": []})
            if channel not in data["channels"]:
                data["channels"].append(channel)
            _write_json(channels_path, data)


def _write_notion_context(action: str, args: dict, result: dict):
    pages_path = os.path.join(CONTEXT_ROOT, "notion_context", "pages.json")
    if action == "create_page":
        data = _read_json(pages_path, {"pages": []})
        data["pages"].append({
            "id": result.get("id"),
            "title": args.get("title"),
            "url": result.get("url"),
            "created_at": datetime.utcnow().isoformat()
        })
        data["pages"] = data["pages"][-50:]
        _write_json(pages_path, data)


def _write_linear_context(action: str, args: dict, result: dict):
    issues_path = os.path.join(CONTEXT_ROOT, "linear_context", "recent_issues.json")
    if action == "create_issue":
        data = _read_json(issues_path, {"issues": []})
        data["issues"].append({
            "id": result.get("id"),
            "title": args.get("title"),
            "url": result.get("url"),
            "created_at": datetime.utcnow().isoformat()
        })
        data["issues"] = data["issues"][-50:]
        _write_json(issues_path, data)


def process_job_events(job_id: str, prompt: str, events: list):
    """
    Call this after a job completes.
    Writes session log + tool-specific context for all successful steps.
    """
    write_session_log(job_id, prompt, events)
    for event in events:
        if event.get("status") == "success" and event.get("step_id") != "__final__":
            write_tool_context(
                tool=event.get("tool", ""),
                action=event.get("action", ""),
                args=event.get("args", {}),
                result=event.get("result", {})
            )
