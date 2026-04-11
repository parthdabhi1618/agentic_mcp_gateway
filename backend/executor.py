# backend/executor.py — V5 Final (Merged from mem2 + mem3)
# Added context_writer hook at end of run_job to write structured context after completion.

import uuid
from datetime import datetime, timezone
from jobs import push_event, is_cancelled
import permissions as perm

from tools.github_tool  import (create_branch, delete_branch, list_branches, create_issue as gh_create_issue,
                                 close_issue as gh_close_issue, comment_on_issue, create_pr, merge_pr,
                                 list_prs, get_repo_info, push_file, list_commits)
from tools.slack_tool   import (send_message as slack_send, create_channel as slack_create_channel,
                                 list_channels as slack_list_channels, get_messages, add_reaction,
                                 pin_message, invite_user)
from tools.jira_tool    import (create_issue as jira_create, update_issue as jira_update,
                                 close_issue as jira_close, add_comment, transition_status,
                                 search_issues, assign_issue)
from tools.sheets_tool  import (append_row, read_range, update_cell, clear_sheet, create_sheet, list_sheets)
from tools.linear_tool  import (create_issue as linear_create, update_issue as linear_update,
                                 list_issues as linear_list, assign_issue as linear_assign,
                                 set_priority, move_to_cycle)
from tools.notion_tool  import (create_page, update_page, append_block, query_database, create_database_entry)
from tools.discord_tool import (send_message as discord_send, create_channel as discord_create,
                                 list_channels as discord_list, add_role, kick_member)

TOOL_MAP = {
    "github": {
        "create_branch": create_branch, "delete_branch": delete_branch, "list_branches": list_branches,
        "create_issue": gh_create_issue, "close_issue": gh_close_issue, "comment_on_issue": comment_on_issue,
        "create_pr": create_pr, "merge_pr": merge_pr, "list_prs": list_prs,
        "get_repo_info": get_repo_info, "push_file": push_file, "list_commits": list_commits,
    },
    "slack": {
        "send_message": slack_send, "create_channel": slack_create_channel,
        "list_channels": slack_list_channels, "get_messages": get_messages,
        "add_reaction": add_reaction, "pin_message": pin_message, "invite_user": invite_user,
    },
    "jira": {
        "create_issue": jira_create, "update_issue": jira_update, "close_issue": jira_close,
        "add_comment": add_comment, "transition_status": transition_status,
        "search_issues": search_issues, "assign_issue": assign_issue,
    },
    "sheets": {
        "append_row": append_row, "read_range": read_range, "update_cell": update_cell,
        "clear_sheet": clear_sheet, "create_sheet": create_sheet, "list_sheets": list_sheets,
    },
    "linear": {
        "create_issue": linear_create, "update_issue": linear_update, "list_issues": linear_list,
        "assign_issue": linear_assign, "set_priority": set_priority, "move_to_cycle": move_to_cycle,
    },
    "notion": {
        "create_page": create_page, "update_page": update_page, "append_block": append_block,
        "query_database": query_database, "create_database_entry": create_database_entry,
    },
    "discord": {
        "send_message": discord_send, "create_channel": discord_create,
        "list_channels": discord_list, "add_role": add_role, "kick_member": kick_member,
    },
}

def _make_event(job_id, step_id, tool, action, status, result=None, error=None, args=None):
    event = {
        "job_id": job_id,
        "step_id": step_id,
        "tool": tool,
        "action": action,
        "status": status,
        "result": result or {},
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # V5: include args in event for context_writer to use
    if args is not None:
        event["args"] = args
    return event

async def run_job(job_id: str, steps: list):
    import asyncio
    import jobs

    for i, step in enumerate(steps):
        tool   = step.get("tool", "")
        action = step.get("action", step.get("args", {}).get("action", ""))
        args   = {k: v for k, v in step.get("args", step).items() if k not in ("tool", "action")}
        step_id = step.get("step_id", f"step_{i}")

        # Check cancellation
        if is_cancelled(job_id):
            await push_event(job_id, _make_event(job_id, step_id, tool, action, "aborted"))
            continue

        # Check permissions
        if not perm.is_allowed(tool, action):
            await push_event(job_id, _make_event(job_id, step_id, tool, action, "permission_denied"))
            # Pause: wait up to 60s for a grant, then skip
            for _ in range(60):
                await asyncio.sleep(1)
                if perm.is_allowed(tool, action):
                    break
            else:
                continue  # timed out, skip step

        # Emit running
        await push_event(job_id, _make_event(job_id, step_id, tool, action, "running"))

        handler = TOOL_MAP.get(tool, {}).get(action)
        if not handler:
            await push_event(job_id, _make_event(job_id, step_id, tool, action, "failed",
                                                   error=f"Unknown tool/action: {tool}.{action}"))
            continue

        try:
            result = await asyncio.get_event_loop().run_in_executor(None, lambda: handler(**args))
        except Exception as exc:
            result = {"success": False, "data": {}, "error": str(exc)}

        status = "success" if result.get("success") else "failed"
        await push_event(job_id, _make_event(job_id, step_id, tool, action, status,
                                              result=result.get("data", {}),
                                              error=result.get("error"),
                                              args=args))

    # Final sentinel event
    await push_event(job_id, _make_event(job_id, "__final__", "system", "complete", "success"))

    # V5: Write context after job completion (mem3 addition)
    try:
        from context_writer import process_job_events
        job = jobs.get_job(job_id)
        if job:
            all_events = job["events"]
            prompt = job.get("_prompt", "")
            process_job_events(job_id, prompt, all_events)
    except Exception as e:
        print(f"[WARN] Context writer failed: {e}")
