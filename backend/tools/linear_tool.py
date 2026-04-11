# backend/tools/linear_tool.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
LINEAR_URL = "https://api.linear.app/graphql"

def _get_key():
    return os.getenv("LINEAR_API_KEY")

def _gql(query: str, variables: dict = None):
    r = requests.post(
        LINEAR_URL,
        headers={"Authorization": _get_key(), "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
        timeout=15
    )
    r.raise_for_status()
    return r.json()

def _ok(data): return {"success": True,  "data": data, "error": None}
def _err(msg): return {"success": False, "data": {},   "error": str(msg)}

def create_issue(title: str, description: str = "", team_id: str = None, **_):
    try:
        if not _get_key():
            print(f"[MOCK] Linear: Create issue '{title}'")
            return _ok({"id": "mock-linear-id", "title": title})
        q = """
        mutation CreateIssue($teamId: String!, $title: String!, $description: String) {
          issueCreate(input: {teamId: $teamId, title: $title, description: $description}) {
            issue { id title url }
          }
        }"""
        result = _gql(q, {"teamId": team_id, "title": title, "description": description})
        issue = result["data"]["issueCreate"]["issue"]
        return _ok({"id": issue["id"], "title": issue["title"], "url": issue["url"]})
    except Exception as e: return _err(e)

def update_issue(issue_id: str, title: str = None, description: str = None, **_):
    try:
        if not _get_key():
            return _ok({"id": issue_id, "updated": True})
        q = """
        mutation UpdateIssue($id: String!, $title: String, $description: String) {
          issueUpdate(id: $id, input: {title: $title, description: $description}) {
            issue { id title }
          }
        }"""
        result = _gql(q, {"id": issue_id, "title": title, "description": description})
        return _ok(result["data"]["issueUpdate"]["issue"])
    except Exception as e: return _err(e)

def list_issues(team_id: str = None, **_):
    try:
        if not _get_key():
            return _ok({"issues": []})
        q = "{ issues(first: 20) { nodes { id title state { name } } } }"
        result = _gql(q)
        return _ok({"issues": result["data"]["issues"]["nodes"]})
    except Exception as e: return _err(e)

def assign_issue(issue_id: str, assignee_id: str, **_):
    try:
        if not _get_key():
            return _ok({"id": issue_id, "assigned": True})
        q = """
        mutation AssignIssue($id: String!, $assigneeId: String!) {
          issueUpdate(id: $id, input: {assigneeId: $assigneeId}) {
            issue { id assignee { name } }
          }
        }"""
        result = _gql(q, {"id": issue_id, "assigneeId": assignee_id})
        return _ok(result["data"]["issueUpdate"]["issue"])
    except Exception as e: return _err(e)

def set_priority(issue_id: str, priority: int, **_):
    # priority: 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
    try:
        if not _get_key():
            return _ok({"id": issue_id, "priority": priority})
        q = """
        mutation SetPriority($id: String!, $priority: Int!) {
          issueUpdate(id: $id, input: {priority: $priority}) {
            issue { id priority }
          }
        }"""
        result = _gql(q, {"id": issue_id, "priority": priority})
        return _ok(result["data"]["issueUpdate"]["issue"])
    except Exception as e: return _err(e)

def move_to_cycle(issue_id: str, cycle_id: str, **_):
    try:
        if not _get_key():
            return _ok({"id": issue_id, "cycle": cycle_id})
        return _ok({"note": "Move to cycle not implemented — use Linear API v3"})
    except Exception as e: return _err(e)
