# backend/permissions.py
import json
import os

PERMISSIONS_FILE = "permissions.json"

DEFAULT_PERMISSIONS = {
    "github":  {"create_branch": True, "delete_branch": False, "list_branches": True,
                "create_issue": True,  "close_issue": True,   "comment_on_issue": True,
                "create_pr": True,     "merge_pr": False,     "list_prs": True,
                "get_repo_info": True, "push_file": True,     "list_commits": True},
    "slack":   {"send_message": True, "create_channel": True, "list_channels": True,
                "get_messages": True, "add_reaction": True,  "pin_message": True, "invite_user": False},
    "jira":    {"create_issue": True, "update_issue": True,  "close_issue": True,
                "add_comment": True,  "transition_status": True, "search_issues": True, "assign_issue": True},
    "sheets":  {"append_row": True,  "read_range": True, "update_cell": True,
                "clear_sheet": False, "create_sheet": True, "list_sheets": True},
    "linear":  {"create_issue": True, "update_issue": True, "list_issues": True,
                "assign_issue": True, "set_priority": True,  "move_to_cycle": True},
    "notion":  {"create_page": True, "update_page": True,   "append_block": True,
                "query_database": True, "create_database_entry": True},
    "discord": {"send_message": True, "create_channel": True, "list_channels": True,
                "add_role": False,   "kick_member": False},
}

_permissions: dict = {}

def load_permissions():
    global _permissions
    if os.path.exists(PERMISSIONS_FILE):
        with open(PERMISSIONS_FILE) as f:
            _permissions = json.load(f)
    else:
        _permissions = {tool: dict(actions) for tool, actions in DEFAULT_PERMISSIONS.items()}
        _save()

def _save():
    with open(PERMISSIONS_FILE, "w") as f:
        json.dump(_permissions, f, indent=2)

def get_all():
    return _permissions

def is_allowed(tool: str, action: str) -> bool:
    return _permissions.get(tool, {}).get(action, False)

def set_permission(tool: str, action: str, allowed: bool):
    if tool not in _permissions:
        _permissions[tool] = {}
    _permissions[tool][action] = allowed
    _save()
