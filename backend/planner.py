"""V3 planner powered by Ollama.

This file is the backend-facing copy of mem3's planner so mem2 can import it
directly from the FastAPI app.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during lightweight local checks
    def load_dotenv() -> bool:
        return False

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "40"))
VALID_TOOL_ACTIONS = {
    "github": {"create_branch"},
    "slack": {"send_message"},
    "jira": {"create_issue"},
    "sheets": {"append_row"},
}
TOOL_KEYWORDS = {
    "github": ("github", "branch", "repo", "repository"),
    "slack": ("slack", "notify", "message", "channel"),
    "jira": ("jira", "issue", "bug", "ticket"),
    "sheets": ("sheet", "sheets", "spreadsheet", "row"),
}


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).with_name("prompt_template.txt")
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except OSError:
        return (
            "You are a workflow planning agent. Return ONLY a JSON array of steps. "
            "Each step must contain tool and args. Args must contain action. "
            "Allowed tools: github, slack, jira, sheets."
        )


SYSTEM_PROMPT = _load_system_prompt()


def _clean_llm_output(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            if lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1])
            else:
                text = "\n".join(lines[1:])
    return text.strip()


def _extract_json_array(raw: str) -> str:
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError("No JSON array found", raw, 0)
    return raw[start : end + 1]


def _normalize_branch_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9/_-]+", "-", name.strip().lower()).strip("-")
    return cleaned or "fix/auto-generated"


def _normalize_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue

        tool = step.get("tool")
        args = step.get("args")
        if tool not in VALID_TOOL_ACTIONS or not isinstance(args, dict):
            continue

        action = args.get("action")
        if action not in VALID_TOOL_ACTIONS[tool]:
            continue

        next_args = dict(args)

        if tool == "github" and action == "create_branch":
            name = str(next_args.get("name", "")).strip()
            if not name:
                continue
            next_args["name"] = _normalize_branch_name(name)
            next_args["from_branch"] = str(next_args.get("from_branch") or "main")

        elif tool == "slack" and action == "send_message":
            channel = str(next_args.get("channel", "")).strip()
            message = str(next_args.get("message", "")).strip()
            if not channel or not message:
                continue
            if not channel.startswith("#"):
                channel = f"#{channel.lstrip('#')}"
            next_args["channel"] = channel
            next_args["message"] = message

        elif tool == "jira" and action == "create_issue":
            project = str(next_args.get("project", "")).strip()
            summary = str(next_args.get("summary", "")).strip()
            if not project or not summary:
                continue
            next_args["project"] = project.upper()
            next_args["summary"] = summary
            next_args["type"] = str(next_args.get("type") or "Bug")

        elif tool == "sheets" and action == "append_row":
            sheet_id = str(next_args.get("sheet_id", "")).strip()
            values = next_args.get("values")
            if not sheet_id or not isinstance(values, list):
                continue
            next_args["sheet_id"] = sheet_id

        normalized.append({"tool": tool, "args": next_args})

    return normalized


def _prompt_mentions_known_tool(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keywords in TOOL_KEYWORDS.values() for keyword in keywords)


def _extract_branch_name(prompt: str) -> str:
    patterns = [
        r"(?:branch(?: named)?|create (?:a )?branch)\s+([a-zA-Z0-9/_-]+)",
        r"\b((?:fix|feature|hotfix|chore|bugfix)/[a-zA-Z0-9._-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return _normalize_branch_name(match.group(1))
    return "fix/auto-generated"


def _extract_slack_channel(prompt: str) -> str:
    match = re.search(r"(#\w[\w-]*)", prompt)
    if match:
        return match.group(1)

    match = re.search(r"(?:channel|slack|notify|message)\s+(?:to\s+)?([a-zA-Z][\w-]*)", prompt, re.IGNORECASE)
    if match:
        return f"#{match.group(1).lstrip('#')}"

    return "#general"


def _extract_jira_project(prompt: str) -> str:
    match = re.search(r"project\s+([A-Za-z][A-Za-z0-9_-]+)", prompt, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "DEMO"


def _extract_sheet_id(prompt: str) -> str:
    match = re.search(r"sheet\s+([A-Za-z0-9_-]+)", prompt, re.IGNORECASE)
    if match:
        return match.group(1)
    return "demo-sheet"


def _extract_sheet_values(prompt: str) -> list[str]:
    match = re.search(r"values?\s+(.+)", prompt, re.IGNORECASE)
    if not match:
        return ["demo", "row"]

    raw_values = match.group(1)
    parts = [part.strip(" .") for part in re.split(r",| and ", raw_values) if part.strip(" .")]
    return parts or ["demo", "row"]


def _fallback_plan(prompt: str) -> list[dict[str, Any]]:
    lowered = prompt.lower()
    if not _prompt_mentions_known_tool(prompt):
        return []

    steps: list[dict[str, Any]] = []
    branch_name = ""

    if any(keyword in lowered for keyword in TOOL_KEYWORDS["github"]):
        branch_name = _extract_branch_name(prompt)
        steps.append(
            {
                "tool": "github",
                "args": {
                    "action": "create_branch",
                    "name": branch_name,
                    "from_branch": "main",
                },
            }
        )

    if any(keyword in lowered for keyword in TOOL_KEYWORDS["slack"]):
        channel = _extract_slack_channel(prompt)
        message = "Workflow update"
        if branch_name:
            message = f"Created branch {branch_name}"
        elif "live" in lowered:
            message = "The gateway is live"
        elif "deploy" in lowered or "deployment" in lowered:
            message = "Deployment update"

        steps.append(
            {
                "tool": "slack",
                "args": {
                    "action": "send_message",
                    "channel": channel,
                    "message": message,
                },
            }
        )

    if any(keyword in lowered for keyword in TOOL_KEYWORDS["jira"]):
        project = _extract_jira_project(prompt)
        summary = "Bug reported"
        if branch_name:
            summary = f"Track work for {branch_name}"
        elif "critical" in lowered:
            summary = "Critical bug"

        steps.append(
            {
                "tool": "jira",
                "args": {
                    "action": "create_issue",
                    "project": project,
                    "summary": summary,
                    "type": "Bug",
                },
            }
        )

    if any(keyword in lowered for keyword in TOOL_KEYWORDS["sheets"]):
        steps.append(
            {
                "tool": "sheets",
                "args": {
                    "action": "append_row",
                    "sheet_id": _extract_sheet_id(prompt),
                    "values": _extract_sheet_values(prompt),
                },
            }
        )

    return _validate_steps(steps, prompt)


def _enrich_steps(steps: list[dict[str, Any]], prompt: str) -> list[dict[str, Any]]:
    enriched = [{"tool": step["tool"], "args": dict(step["args"])} for step in steps]

    branch_name = ""
    for step in enriched:
        if step["tool"] == "github" and step["args"].get("action") == "create_branch":
            branch_name = str(step["args"].get("name", "")).strip()
            break

    for step in enriched:
        args = step["args"]
        tool = step["tool"]

        if tool == "slack" and branch_name:
            message = str(args.get("message", "")).strip()
            if branch_name not in message:
                args["message"] = f"{message} (branch: {branch_name})"

        if tool == "jira" and branch_name:
            summary = str(args.get("summary", "")).strip()
            if branch_name not in summary:
                args["summary"] = f"{summary} [{branch_name}]"

        if tool == "sheets":
            values = args.get("values")
            if isinstance(values, list) and branch_name and branch_name not in [str(v) for v in values]:
                args["values"] = list(values) + [branch_name]
            elif isinstance(values, list) and prompt and len(values) == 0:
                args["values"] = [prompt]

    return enriched


def _validate_steps(steps: Any, prompt: str) -> list[dict[str, Any]]:
    if not isinstance(steps, list):
        return []

    normalized = _normalize_steps(steps)
    return _enrich_steps(normalized, prompt)


def plan(prompt: str) -> list[dict[str, Any]]:
    """Return tool steps for a natural-language task.

    This function must never raise; it returns [] on any failure.
    """

    task = prompt.strip() if isinstance(prompt, str) else ""
    if not task:
        return []

    full_prompt = f"{SYSTEM_PROMPT}\n\nTask: {task}"

    try:
        import requests

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()

        raw = response.json().get("response", "")
        cleaned = _clean_llm_output(raw)
        json_blob = _extract_json_array(cleaned)
        parsed = json.loads(json_blob)
        validated = _validate_steps(parsed, task)
        if validated:
            return validated
        return _fallback_plan(task)
    except Exception as exc:
        print(f"[ERROR] planner.plan failed: {exc}")
        return _fallback_plan(task)
