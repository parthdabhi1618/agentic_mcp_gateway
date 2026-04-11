# backend/tools/jira_tool.py
import os
import requests
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def _get_auth():
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_TOKEN")
    if email and token:
        return (email, token)
    return None

def _get_url(endpoint):
    base_url = os.getenv("JIRA_URL")
    if base_url:
        return f"{base_url.rstrip('/')}/rest/api/3/{endpoint}"
    return None

def _make_mock():
    logger.info("Using mock Jira fallback")
    return {"success": True, "data": {"mock": True}, "error": None}

def _ok(data):  return {"success": True,  "data": data, "error": None}
def _err(msg):  return {"success": False, "data": {},   "error": str(msg)}

def _check_auth():
    return bool(os.getenv("JIRA_URL") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_TOKEN"))

# ── V4 contract: planner emits "project" and "type", not "project_key"/"issue_type" ──

def create_issue(project=None, project_key=None, summary=None, description=None,
                 type=None, issue_type=None, **kwargs):
    """Accept both V4 planner names (project, type) and Jira-native names (project_key, issue_type)."""
    proj = project or project_key or "DEMO"
    itype = type or issue_type or "Task"
    desc = description or ""

    if not _check_auth():
        print(f"[MOCK] Jira: Creating {itype} in {proj}: {summary}")
        return _ok({"mock": True, "project": proj, "summary": summary, "type": itype})
    try:
        url = _get_url("issue")
        payload = {
            "fields": {
                "project": {"key": proj},
                "summary": summary,
                "issuetype": {"name": itype}
            }
        }
        if desc:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": desc}]}]
            }
        res = requests.post(url, auth=_get_auth(), json=payload,
                            headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok(res.json())
    except Exception as e:
        return _err(e)

def update_issue(issue_key=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url(f"issue/{issue_key}")
        res = requests.put(url, auth=_get_auth(), json={"fields": kwargs},
                           headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok({"issue_key": issue_key, "updated": True})
    except Exception as e:
        return _err(e)

def close_issue(issue_key=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url(f"issue/{issue_key}/transitions")
        res = requests.post(url, auth=_get_auth(),
                            json={"transition": {"id": "DONE_TRANSITION_ID"}},
                            headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok({"issue_key": issue_key, "closed": True})
    except Exception as e:
        return _err(e)

def add_comment(issue_key=None, body=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url(f"issue/{issue_key}/comment")
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}]
            }
        }
        res = requests.post(url, auth=_get_auth(), json=payload,
                            headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok(res.json())
    except Exception as e:
        return _err(e)

# ── V4 contract: planner emits "status", accept both "status" and "transition_id" ──

def transition_status(issue_key=None, status=None, transition_id=None, **kwargs):
    """Accept both 'status' (V4 planner) and 'transition_id' (Jira API native)."""
    tid = transition_id or status
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url(f"issue/{issue_key}/transitions")
        res = requests.post(url, auth=_get_auth(), json={"transition": {"id": tid}},
                            headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok({"issue_key": issue_key, "transitioned": True})
    except Exception as e:
        return _err(e)

def search_issues(jql=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url("search")
        res = requests.get(url, auth=_get_auth(), params={"jql": jql},
                           headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok(res.json())
    except Exception as e:
        return _err(e)

# ── V4 contract: planner emits "assignee", accept both "assignee" and "account_id" ──

def assign_issue(issue_key=None, assignee=None, account_id=None, **kwargs):
    """Accept both 'assignee' (V4 planner) and 'account_id' (Jira API native)."""
    aid = account_id or assignee
    if not _check_auth(): return _make_mock()
    try:
        url = _get_url(f"issue/{issue_key}/assignee")
        res = requests.put(url, auth=_get_auth(), json={"accountId": aid},
                           headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        return _ok({"issue_key": issue_key, "assigned_to": aid})
    except Exception as e:
        return _err(e)
