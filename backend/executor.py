from __future__ import annotations

import time
from typing import Any

from tools.github_tool import create_branch
from tools.slack_tool import send_message
from tools.jira_tool import create_issue
from tools.sheets_tool import append_row


TOOL_MAP = {
    "github": {
        "create_branch": create_branch,
    },
    "slack": {
        "send_message": send_message,
    },
    "jira": {
        "create_issue": create_issue,
    },
    "sheets": {
        "append_row": append_row,
    },
}


def execute_step(
    tool: str, action: str, args: dict[str, Any], retries: int = 2, delay: float = 1.0
) -> str:
    """Execute a single step and return only success or failed."""
    handler = TOOL_MAP.get(tool, {}).get(action)
    if not handler:
        print(f"[WARN] No handler for {tool}.{action}")
        return "failed"

    kwargs = {key: value for key, value in args.items() if key != "action"}

    for attempt in range(retries + 1):
        try:
            handler(**kwargs)
            return "success"
        except Exception as exc:
            print(f"[ERROR] {tool}.{action} attempt {attempt + 1} failed: {exc}")
            if attempt < retries:
                time.sleep(delay)

    return "failed"


def execute_steps(steps: list[dict[str, Any]]) -> list[dict[str, str]]:
    logs: list[dict[str, str]] = []
    for step in steps:
        tool = step.get("tool", "")
        args = step.get("args", {})
        action = args.get("action", "") if isinstance(args, dict) else ""
        status = execute_step(tool, action, args if isinstance(args, dict) else {})
        logs.append({"step": f"{tool}.{action}", "status": status})
    return logs
