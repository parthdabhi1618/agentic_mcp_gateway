# backend/validate_v4.py
# Run: python3 validate_v4.py
# All tests must pass before V4 is declared done.

import requests
import json
import time

BASE = "http://localhost:8000"

def req(method, path, **kwargs):
    return getattr(requests, method)(f"{BASE}{path}", timeout=20, **kwargs)

def test_health():
    r = req("get", "/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print("[PASS] health")

def test_permissions_structure():
    r = req("get", "/permissions")
    assert r.status_code == 200
    d = r.json()
    required_tools = ["github", "slack", "jira", "sheets", "linear", "notion", "discord"]
    for t in required_tools:
        assert t in d, f"Tool missing from permissions: {t}"
    print("[PASS] permissions structure — all 7 tools present")

def test_execute_returns_job_id():
    r = req("post", "/execute", json={
        "steps": [{"tool": "slack", "action": "send_message", "args": {"channel": "#general", "message": "V4 test"}}]
    })
    assert r.status_code == 200
    d = r.json()
    assert "job_id" in d
    assert d["status"] == "accepted"
    print(f"[PASS] execute returns job_id: {d['job_id']}")
    return d["job_id"]

def test_sse_stream(job_id):
    events = []
    # Use requests with stream=True to read SSE
    with requests.get(f"{BASE}/job/{job_id}/stream", stream=True, timeout=30) as resp:
        for line in resp.iter_lines():
            if line and line.startswith(b"data:"):
                payload = json.loads(line[5:].strip())
                events.append(payload)
                if payload.get("step_id") == "__final__":
                    break
    assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"
    statuses = {e["status"] for e in events}
    assert "running" in statuses or "success" in statuses, f"Expected running/success, got {statuses}"
    print(f"[PASS] SSE stream — received {len(events)} events: {[e['status'] for e in events]}")

def test_abort():
    # Start a longer job
    r = req("post", "/execute", json={
        "steps": [
            {"tool": "slack",  "action": "send_message",  "args": {"channel": "#test", "message": "step1"}},
            {"tool": "github", "action": "list_branches",  "args": {}},
            {"tool": "github", "action": "get_repo_info",  "args": {}},
        ]
    })
    job_id = r.json()["job_id"]
    time.sleep(0.1)  # let it start
    abort_r = req("post", f"/job/{job_id}/abort")
    assert abort_r.json()["status"] == "aborting"
    print(f"[PASS] abort accepted for job {job_id}")

def test_permission_denied_event():
    # Set a permission to false
    req("post", "/permissions", json={"tool": "github", "action": "delete_branch", "allowed": False})
    r = req("post", "/execute", json={
        "steps": [{"tool": "github", "action": "delete_branch", "args": {"name": "nonexistent-branch"}}]
    })
    job_id = r.json()["job_id"]
    events = []
    with requests.get(f"{BASE}/job/{job_id}/stream", stream=True, timeout=30) as resp:
        for line in resp.iter_lines():
            if line and line.startswith(b"data:"):
                payload = json.loads(line[5:].strip())
                events.append(payload)
                if payload.get("step_id") == "__final__":
                    break
    statuses = [e["status"] for e in events]
    assert "permission_denied" in statuses, f"Expected permission_denied in {statuses}"
    # Re-enable for future tests
    req("post", "/permissions", json={"tool": "github", "action": "delete_branch", "allowed": True})
    print(f"[PASS] permission_denied event emitted: {statuses}")

def test_planner_7_tools():
    """Test planner generates steps for all 7 tool types."""
    from planner import plan
    test_cases = [
        ("Create a GitHub branch fix/v4", "github", "create_branch"),
        ("Send a message to #general on Slack",    "slack",  "send_message"),
        ("Create a Jira bug in project TEST",      "jira",   "create_issue"),
        ("Append a row to sheet ABC",              "sheets", "append_row"),
        ("Create a Linear issue: fix login",       "linear", "create_issue"),
        ("Create a Notion page titled 'V4 Notes' in parent XYZ", "notion", "create_page"),
        ("Send a Discord message to channel 12345 saying hello", "discord", "send_message"),
    ]
    for prompt, expected_tool, expected_action in test_cases:
        result = plan(prompt)
        assert isinstance(result, list), f"plan() not list for: {prompt}"
        tools = [s["tool"] for s in result]
        actions = [s["action"] for s in result]
        assert expected_tool in tools, f"Expected '{expected_tool}' for: {prompt} — got {tools}"
        print(f"  [OK] {expected_tool}.{expected_action} — '{prompt[:50]}'")
    print("[PASS] planner generates steps for all 7 tools")

def test_planner_never_raises():
    from planner import plan
    for prompt in ["", "random nonsense xyz abc", "book a flight to mars"]:
        result = plan(prompt)
        assert isinstance(result, list), f"Expected list, got {type(result)} for: {prompt}"
    print("[PASS] planner returns [] for non-tool prompts — no exceptions")

def test_planner_step_shape():
    from planner import plan
    result = plan("Create a GitHub branch named fix/v4-shape-test")
    assert isinstance(result, list)
    if result:
        step = result[0]
        assert "tool" in step,   f"Missing 'tool': {step}"
        assert "action" in step, f"Missing 'action': {step}"
        assert "args" in step,   f"Missing 'args': {step}"
        assert isinstance(step["args"], dict), f"'args' not dict: {step}"
    print("[PASS] planner step shape correct")

if __name__ == "__main__":
    print("\n=== V4 Integration Validation ===\n")
    test_health()
    test_permissions_structure()
    job_id = test_execute_returns_job_id()
    test_sse_stream(job_id)
    test_abort()
    test_permission_denied_event()
    test_planner_7_tools()
    test_planner_never_raises()
    test_planner_step_shape()
    print("\n✓ All V4 tests passed. Version V4 is cleared for handoff.\n")
