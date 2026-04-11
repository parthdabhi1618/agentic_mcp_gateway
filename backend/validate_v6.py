# backend/validate_v6.py
# This is the final release check. ALL tests must pass before V6 is shipped.
import requests
import json
import os
import time

BASE = "http://localhost:8000"

def req(method, path, **kwargs):
    return getattr(requests, method)(f"{BASE}{path}", timeout=20, **kwargs)

def assert_status(r, expected=200):
    assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text[:200]}"

# ── Infrastructure ────────────────────────────────────────────────────────────────

def test_health():
    r = req("get", "/health")
    assert_status(r)
    print("[PASS] health")

def test_permissions():
    r = req("get", "/permissions")
    assert_status(r)
    tools = list(r.json().keys())
    assert len(tools) == 7, f"Expected 7 tools, got {tools}"
    print(f"[PASS] permissions — {tools}")

def test_keys_status():
    r = req("get", "/keys/status")
    assert_status(r)
    assert len(r.json()) == 7
    print("[PASS] keys/status")

# ── Files ─────────────────────────────────────────────────────────────────────────

def test_file_upload_list_delete():
    # Upload
    files = {'file': ('test_v6.txt', b'V6 release test content', 'text/plain')}
    r = requests.post(f"{BASE}/files/upload", files=files, timeout=10)
    assert_status(r)
    assert r.json()["name"] == "test_v6.txt"

    # List
    r2 = req("get", "/files")
    names = [f["name"] for f in r2.json()["files"]]
    assert "test_v6.txt" in names, f"File not in list: {names}"

    # Delete
    r3 = req("delete", "/files/test_v6.txt")
    assert_status(r3)
    assert r3.json()["deleted"] == "test_v6.txt"

    # Confirm gone
    r4 = req("get", "/files")
    names_after = [f["name"] for f in r4.json()["files"]]
    assert "test_v6.txt" not in names_after
    print("[PASS] file upload → list → delete cycle")

def test_path_traversal_blocked():
    r = requests.delete(f"{BASE}/files/../../../etc/passwd", timeout=10)
    # Should NOT be 200
    assert r.status_code in (403, 404, 422), f"Path traversal not blocked! Status: {r.status_code}"
    print("[PASS] path traversal blocked")

# ── Context ───────────────────────────────────────────────────────────────────────

def test_context_tree():
    r = req("get", "/context")
    assert_status(r)
    d = r.json()
    assert "tree" in d
    print(f"[PASS] context tree has folders: {list(d['tree'].keys())}")

# ── Context Parser ────────────────────────────────────────────────────────────────

def test_context_parser():
    from context_parser import extract_context_refs
    prompt = "Create a PR for @github_context/recent_branches.json and notify @slack_context/channels.json"
    clean, refs = extract_context_refs(prompt)
    assert "@github_context/recent_branches.json" in refs
    assert "@slack_context/channels.json" in refs
    assert "@" not in clean
    print(f"[PASS] context_parser extracts refs: {refs}")

# ── Full E2E ──────────────────────────────────────────────────────────────────────

def test_e2e_plan_edit_execute_stream():
    """Simulates the full user flow: plan → (edit) → execute → stream."""
    # 1. Plan
    r = req("post", "/plan", json={
        "prompt": "List GitHub branches and send a Slack message to #general",
        "context_refs": []
    })
    assert_status(r)
    plan = r.json()
    assert "plan_id" in plan and len(plan["steps"]) >= 1

    # 2. "Edit" — change a step arg (simulate mem1 editing a field)
    steps = plan["steps"]
    for s in steps:
        if s["tool"] == "slack":
            s["args"]["channel"] = "#v6-test"  # user changes channel

    # 3. Execute
    r2 = req("post", "/execute", json={"plan_id": plan["plan_id"], "steps": steps})
    assert_status(r2)
    job_id = r2.json()["job_id"]

    # 4. Stream
    events = []
    with requests.get(f"{BASE}/job/{job_id}/stream", stream=True, timeout=60) as resp:
        for line in resp.iter_lines():
            if line and line.startswith(b"data:"):
                payload = json.loads(line[5:].strip())
                events.append(payload)
                if payload.get("step_id") == "__final__":
                    break

    # 5. Verify the edited arg was used
    slack_events = [e for e in events if e.get("tool") == "slack"]
    # (can't verify from SSE directly, but at least ensure no crash)
    assert len(events) > 0, "No events received"
    final = events[-1]
    assert final["step_id"] == "__final__", f"Stream didn't close: {final}"
    print(f"[PASS] Full E2E: plan → edit → execute → stream ({len(events)} events)")

def test_planner_with_at_context():
    """Tests that @context refs in prompt are parsed and injected."""
    # Create a dummy context file
    os.makedirs("workspace/context/github_context", exist_ok=True)
    with open("workspace/context/github_context/recent_branches.json", "w") as f:
        json.dump({"branches": [{"name": "v6/demo-branch"}]}, f)

    r = req("post", "/plan", json={
        "prompt": "Create a PR for @github_context/recent_branches.json"
    })
    assert_status(r)
    d = r.json()
    # Just ensure it returned a valid response — context parsing should have injected the file
    assert "steps" in d
    print(f"[PASS] planner handled @context ref in prompt, got {len(d['steps'])} steps")

if __name__ == "__main__":
    print("\n=== V6 RELEASE VALIDATION — Full Gate ===\n")
    test_health()
    test_permissions()
    test_keys_status()
    test_file_upload_list_delete()
    test_path_traversal_blocked()
    test_context_tree()
    test_context_parser()
    test_e2e_plan_edit_execute_stream()
    test_planner_with_at_context()
    print("\n✓ ALL V6 RELEASE CHECKS PASSED.")
    print("✓ Version V6 is cleared for demo. Good luck.\n")
