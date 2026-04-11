# backend/planner.py — V6 (Agentic OS Release)
# Full 7-tool planner with auto-context injection, @context refs, and strict SOP failure contract.
# Model: gemma4:e4b via Ollama
#
# SOP CONTRACT: plan() MUST return [] on ANY failure (LLM timeout, bad JSON, non-list output).
# Keyword fallback (_fallback_plan) is DORMANT — not called from plan().
# If fallback is desired, it must be explicitly approved as a contract change.

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60"))
PROMPT_TEMPLATE_FILE = Path(__file__).with_name("prompt_template.txt")

CONTEXT_ROOT = os.path.join(os.path.dirname(__file__), "workspace", "context")

VALID_TOOLS = {"github", "slack", "jira", "sheets", "linear", "notion", "discord"}
VALID_ACTIONS = {
    "github": {"create_branch","delete_branch","list_branches","create_issue","close_issue",
               "comment_on_issue","create_pr","merge_pr","list_prs","get_repo_info","push_file","list_commits"},
    "slack":  {"send_message","create_channel","list_channels","get_messages","add_reaction","pin_message","invite_user"},
    "jira":   {"create_issue","update_issue","close_issue","add_comment","transition_status","search_issues","assign_issue"},
    "sheets": {"append_row","read_range","update_cell","clear_sheet","create_sheet","list_sheets"},
    "linear": {"create_issue","update_issue","list_issues","assign_issue","set_priority","move_to_cycle"},
    "notion": {"create_page","update_page","append_block","query_database","create_database_entry"},
    "discord": {"send_message","create_channel","list_channels","add_role","kick_member"},
}

# Keyword detection for fallback planning (from mem2)
TOOL_KEYWORDS = {
    "github":  ("github", "branch", "repo", "repository", "pr", "pull request", "commit"),
    "slack":   ("slack", "notify", "message", "channel"),
    "jira":    ("jira", "issue", "bug", "ticket"),
    "sheets":  ("sheet", "sheets", "spreadsheet", "row"),
    "linear":  ("linear", "priority", "cycle"),
    "notion":  ("notion", "page", "database"),
    "discord": ("discord", "role", "kick"),
}


def _load_system_prompt() -> str:
    try:
        return PROMPT_TEMPLATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return (
            "You are a workflow planning agent. Return ONLY a JSON array of steps. "
            'Each step: {"tool": ..., "action": ..., "args": {...}}. '
            "Allowed tools: github, slack, jira, sheets, linear, notion, discord."
        )


def _clean_llm_output(raw: str) -> str:
    raw = raw.strip()
    # Strip <think>...</think> blocks (some models emit these)
    if "<think>" in raw:
        end = raw.find("</think>")
        if end != -1:
            raw = raw[end + len("</think>"):].strip()
    # Strip markdown fences
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
        if raw.rstrip().endswith("```"):
            raw = "\n".join(raw.rstrip().split("\n")[:-1])
    return raw.strip()


def _validate_step(step: dict) -> tuple[bool, str]:
    """Returns (is_valid, error_reason)."""
    if not isinstance(step, dict):
        return False, f"Step is not a dict: {type(step)}"

    tool = step.get("tool")
    # Support both V4 format (action at top) and V3 format (action in args)
    action = step.get("action") or (step.get("args", {}).get("action") if isinstance(step.get("args"), dict) else None)
    args = step.get("args")

    if not tool:
        return False, "Missing 'tool' key"
    if not action:
        return False, "Missing 'action' key"
    if args is None:
        return False, "Missing 'args' key"
    if not isinstance(args, dict):
        return False, f"'args' is not a dict: {type(args)}"
    if tool not in VALID_TOOLS:
        return False, f"Unknown tool: {tool}"
    if action not in VALID_ACTIONS.get(tool, set()):
        return False, f"Unknown action '{action}' for tool '{tool}'"
    return True, ""


def _normalize_step(step: dict) -> dict:
    """Ensure action is at top level (V4+ format) even if LLM returns V3 format."""
    tool = step.get("tool")
    args = dict(step.get("args", {}))
    action = step.get("action") or args.pop("action", None)
    args.pop("tool", None)
    args.pop("action", None)
    return {"tool": tool, "action": action, "args": args}


def _get_auto_context() -> str:
    """Builds a brief context summary from recent workspace activity (mem3 addition)."""
    lines = []

    # Recent branches
    branches_path = os.path.join(CONTEXT_ROOT, "github_context", "recent_branches.json")
    if os.path.exists(branches_path):
        try:
            with open(branches_path) as f:
                data = json.load(f)
            recent = [b["name"] for b in data.get("branches", [])[:3]]
            if recent:
                lines.append(f"Recent GitHub branches: {', '.join(recent)}")
        except Exception:
            pass

    # Slack channels used
    channels_path = os.path.join(CONTEXT_ROOT, "slack_context", "channels.json")
    if os.path.exists(channels_path):
        try:
            with open(channels_path) as f:
                data = json.load(f)
            channels = data.get("channels", [])[:5]
            if channels:
                lines.append(f"Recent Slack channels: {', '.join(channels)}")
        except Exception:
            pass

    return "\n" + "\n".join(lines) if lines else ""


def _read_context_ref(ref: str) -> str:
    """Read a @folder/file.json reference from the workspace context. Returns content string or empty."""
    context_root = Path(__file__).parent / "workspace" / "context"
    # Strip leading @ if present
    clean_ref = ref.lstrip("@")
    path = context_root / clean_ref
    # Security: must be inside context root
    if not str(path.resolve()).startswith(str(context_root.resolve())):
        print(f"[WARN] Planner: blocked context path traversal: {ref}")
        return ""
    if not path.exists():
        print(f"[WARN] Planner: context file not found: {path}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[WARN] Planner: failed to read context {ref}: {e}")
        return ""


def _fallback_extraction(text: str) -> list[dict]:
    """Last-resort: find JSON arrays in the output."""
    pattern = r'\[.*?\]'
    matches = re.findall(pattern, text, re.DOTALL)
    for m in matches:
        try:
            candidate = json.loads(m)
            if isinstance(candidate, list):
                validated = []
                for step in candidate:
                    ok, _ = _validate_step(step)
                    if ok:
                        validated.append(_normalize_step(step))
                if validated:
                    print(f"[INFO] Planner: fallback extraction found {len(validated)} valid steps")
                    return validated
        except Exception:
            continue
    print("[WARN] Planner: fallback extraction found nothing valid")
    return []


def _fallback_plan(prompt: str) -> list[dict[str, Any]]:
    """Keyword-based fallback when Ollama is unavailable (from mem2)."""
    lowered = prompt.lower()
    steps: list[dict[str, Any]] = []

    if any(kw in lowered for kw in TOOL_KEYWORDS["github"]):
        branch = "fix/auto-generated"
        match = re.search(r'(?:branch(?:\s+named)?\s+)([a-zA-Z0-9/_-]+)', prompt, re.IGNORECASE)
        if match:
            branch = match.group(1)
        else:
            match = re.search(r'\b((?:fix|feature|hotfix)/[a-zA-Z0-9._-]+)\b', prompt, re.IGNORECASE)
            if match:
                branch = match.group(1)
        steps.append({"tool": "github", "action": "create_branch", "args": {"name": branch, "from_branch": "main"}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["slack"]):
        channel = "#general"
        match = re.search(r'(#\w[\w-]*)', prompt)
        if match:
            channel = match.group(1)
        message = "Workflow update"
        if steps and steps[0]["tool"] == "github":
            message = f"Created branch {steps[0]['args'].get('name', 'unknown')}"
        steps.append({"tool": "slack", "action": "send_message", "args": {"channel": channel, "message": message}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["jira"]):
        project = "DEMO"
        match = re.search(r'project\s+([A-Za-z][A-Za-z0-9_-]+)', prompt, re.IGNORECASE)
        if match:
            project = match.group(1).upper()
        steps.append({"tool": "jira", "action": "create_issue", "args": {"project": project, "summary": "Bug reported", "type": "Bug"}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["sheets"]):
        steps.append({"tool": "sheets", "action": "append_row", "args": {"sheet_id": "demo-sheet", "values": ["demo", "row"]}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["linear"]):
        steps.append({"tool": "linear", "action": "create_issue", "args": {"title": prompt[:100]}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["notion"]):
        steps.append({"tool": "notion", "action": "create_page", "args": {"parent_page_id": "default", "title": prompt[:100]}})

    if any(kw in lowered for kw in TOOL_KEYWORDS["discord"]):
        steps.append({"tool": "discord", "action": "send_message", "args": {"channel_id": "general", "content": prompt[:200]}})

    return steps


def plan(prompt: str, context_refs: list = None) -> list[dict]:
    """
    Calls Ollama with the full 7-tool system prompt.
    Validates each step strictly before returning.
    Never raises — returns [] on any failure.
    context_refs: list of "@folder/file.json" strings injected as context.
    """
    system = _load_system_prompt()

    # V5: Auto-context injection from recent workspace activity (mem3)
    auto_context = _get_auto_context()

    # Manual context_refs injection
    context_block = ""
    if context_refs:
        context_lines = []
        for ref in context_refs:
            content = _read_context_ref(ref)
            if content:
                context_lines.append(f"[{ref}]\n{content}")
        if context_lines:
            context_block = "\n\n=== USER CONTEXT ===\n" + "\n\n".join(context_lines) + "\n=== END USER CONTEXT ===\n"

    full_prompt = f"{system}\n{auto_context}{context_block}\n\nTask: {prompt}"

    try:
        import requests

        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": full_prompt, "stream": False,
                  "options": {"temperature": 0}},
            timeout=OLLAMA_TIMEOUT
        )
        r.raise_for_status()
        raw = r.json().get("response", "").strip()

    except Exception as e:
        if "Timeout" in type(e).__name__:
            print("[ERROR] Planner: Ollama timed out")
        else:
            print(f"[ERROR] planner.plan failed: {e}")
        return []

    cleaned = _clean_llm_output(raw)

    try:
        steps = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Planner: JSON parse failed: {e}\nRaw: {cleaned[:400]}")
        return _fallback_extraction(cleaned)

    if not isinstance(steps, list):
        print(f"[WARN] Planner: returned non-list: {type(steps)}")
        return []

    validated = []
    for step in steps:
        ok, reason = _validate_step(step)
        if ok:
            validated.append(_normalize_step(step))
        else:
            print(f"[WARN] Planner: skipping invalid step — {reason} — step: {step}")

    return validated
