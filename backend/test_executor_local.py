import json

from executor import execute_steps

print("--- Running Executor Direct Test ---")

fake_planned_steps = [
    {
        "tool": "github",
        "args": {"action": "create_branch", "name": "fix/demo", "from_branch": "main"},
    },
    {
        "tool": "slack",
        "args": {"action": "send_message", "channel": "#general", "message": "Local tests are running"},
    },
    {
        "tool": "jira",
        "args": {"action": "create_issue", "project": "DEMO", "summary": "Demo issue"},
    },
    {
        "tool": "sheets",
        "args": {"action": "append_row", "sheet_id": "demo-sheet", "values": ["Tested", "Success"]},
    },
    {
        "tool": "unknown_tool",
        "args": {"action": "do_something"},
    },
]

print(f"Total steps planned: {len(fake_planned_steps)}")

logs = execute_steps(fake_planned_steps)

print("\n--- Execution Logs ---")
print(json.dumps(logs, indent=2))
print(f"\nTotal steps executed (should match planned): {len(logs)}")

if len(fake_planned_steps) == len(logs):
    print("TEST PASSED: steps count equals logs count.")
else:
    print("TEST FAILED: counts mismatch.")
