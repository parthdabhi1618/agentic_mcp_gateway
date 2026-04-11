# backend/tools/github_tool.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def _get_token():
    return os.getenv("GITHUB_TOKEN")

def _get_repo():
    return os.getenv("GITHUB_REPO")

def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def _ok(data):   return {"success": True,  "data": data, "error": None}
def _err(msg):   return {"success": False, "data": {},   "error": str(msg)}

def _base():
    return f"https://api.github.com/repos/{_get_repo()}"

def _check_auth():
    """Check if GitHub credentials are configured (token + repo)."""
    return bool(_get_token() and _get_repo())

def _make_mock(action, details=None):
    """Return mock success when GitHub is not configured."""
    print(f"[MOCK] GitHub: {action}" + (f" — {details}" if details else ""))
    data = {"mock": True, "action": action}
    if details:
        data.update(details)
    return _ok(data)

def create_branch(name: str, from_branch: str = "main", **_):
    if not _check_auth():
        return _make_mock("create_branch", {"branch": name, "from_branch": from_branch})
    try:
        ref_resp = requests.get(f"{_base()}/git/ref/heads/{from_branch}", headers=_headers(), timeout=10)
        ref_resp.raise_for_status()
        sha = ref_resp.json()["object"]["sha"]
        r = requests.post(f"{_base()}/git/refs", headers=_headers(), json={"ref": f"refs/heads/{name}", "sha": sha}, timeout=10)
        if r.status_code == 422: return _err(f"Branch '{name}' already exists")
        r.raise_for_status()
        return _ok({"branch": name, "sha": sha})
    except Exception as e: return _err(e)

def delete_branch(name: str, **_):
    if not _check_auth():
        return _make_mock("delete_branch", {"branch": name})
    try:
        r = requests.delete(f"{_base()}/git/refs/heads/{name}", headers=_headers(), timeout=10)
        r.raise_for_status()
        return _ok({"deleted": name})
    except Exception as e: return _err(e)

def list_branches(**_):
    if not _check_auth():
        return _make_mock("list_branches", {"branches": []})
    try:
        r = requests.get(f"{_base()}/branches", headers=_headers(), timeout=10)
        r.raise_for_status()
        return _ok({"branches": [b["name"] for b in r.json()]})
    except Exception as e: return _err(e)

def create_issue(title: str, body: str = "", labels: list = None, **_):
    if not _check_auth():
        return _make_mock("create_issue", {"title": title})
    try:
        payload = {"title": title, "body": body}
        if labels: payload["labels"] = labels
        r = requests.post(f"{_base()}/issues", headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()
        d = r.json()
        return _ok({"issue_number": d["number"], "url": d["html_url"]})
    except Exception as e: return _err(e)

def close_issue(issue_number: int, **_):
    if not _check_auth():
        return _make_mock("close_issue", {"issue_number": issue_number})
    try:
        r = requests.patch(f"{_base()}/issues/{issue_number}", headers=_headers(), json={"state": "closed"}, timeout=10)
        r.raise_for_status()
        return _ok({"issue_number": issue_number, "status": "closed"})
    except Exception as e: return _err(e)

def comment_on_issue(issue_number: int, body: str, **_):
    if not _check_auth():
        return _make_mock("comment_on_issue", {"issue_number": issue_number})
    try:
        r = requests.post(f"{_base()}/issues/{issue_number}/comments", headers=_headers(), json={"body": body}, timeout=10)
        r.raise_for_status()
        return _ok({"comment_id": r.json()["id"]})
    except Exception as e: return _err(e)

def create_pr(title: str, head: str, base: str = "main", body: str = "", **_):
    if not _check_auth():
        return _make_mock("create_pr", {"title": title, "head": head, "base": base})
    try:
        r = requests.post(f"{_base()}/pulls", headers=_headers(), json={"title": title, "head": head, "base": base, "body": body}, timeout=10)
        r.raise_for_status()
        d = r.json()
        return _ok({"pr_number": d["number"], "url": d["html_url"]})
    except Exception as e: return _err(e)

def merge_pr(pr_number: int, merge_method: str = "merge", **_):
    if not _check_auth():
        return _make_mock("merge_pr", {"pr_number": pr_number})
    try:
        r = requests.put(f"{_base()}/pulls/{pr_number}/merge", headers=_headers(), json={"merge_method": merge_method}, timeout=10)
        r.raise_for_status()
        return _ok({"pr_number": pr_number, "merged": True})
    except Exception as e: return _err(e)

def list_prs(state: str = "open", **_):
    if not _check_auth():
        return _make_mock("list_prs", {"prs": []})
    try:
        r = requests.get(f"{_base()}/pulls", headers=_headers(), params={"state": state}, timeout=10)
        r.raise_for_status()
        return _ok({"prs": [{"number": p["number"], "title": p["title"], "state": p["state"]} for p in r.json()]})
    except Exception as e: return _err(e)

def get_repo_info(**_):
    if not _check_auth():
        return _make_mock("get_repo_info", {"name": "unconfigured", "stars": 0, "forks": 0})
    try:
        r = requests.get(_base(), headers=_headers(), timeout=10)
        r.raise_for_status()
        d = r.json()
        return _ok({"name": d["full_name"], "stars": d["stargazers_count"], "forks": d["forks_count"], "default_branch": d["default_branch"]})
    except Exception as e: return _err(e)

def push_file(path: str, content: str, message: str, branch: str = "main", **_):
    if not _check_auth():
        return _make_mock("push_file", {"path": path, "branch": branch})
    import base64
    try:
        # Check if file exists for SHA
        existing = requests.get(f"{_base()}/contents/{path}", headers=_headers(), params={"ref": branch}, timeout=10)
        payload = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": branch}
        if existing.status_code == 200:
            payload["sha"] = existing.json()["sha"]
        r = requests.put(f"{_base()}/contents/{path}", headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()
        return _ok({"path": path, "branch": branch})
    except Exception as e: return _err(e)

def list_commits(per_page: int = 10, **_):
    if not _check_auth():
        return _make_mock("list_commits", {"commits": []})
    try:
        r = requests.get(f"{_base()}/commits", headers=_headers(), params={"per_page": per_page}, timeout=10)
        r.raise_for_status()
        return _ok({"commits": [{"sha": c["sha"][:7], "message": c["commit"]["message"].split("\n")[0]} for c in r.json()]})
    except Exception as e: return _err(e)
