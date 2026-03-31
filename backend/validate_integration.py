import json
from typing import Any

import requests


BASE_URL = "http://localhost:8000"
TEST_CASES = [
    ("GitHub only", "Create a GitHub branch named fix/login"),
    ("Slack only", "Send a message to #general saying the gateway is live"),
    ("GitHub + Slack", "Create a branch fix/login and tell the team on Slack"),
    (
        "Three tools",
        "Create GitHub branch fix/critical, notify #alerts on Slack, and create a Jira bug in project DEMO",
    ),
    ("Unknown prompt", "Book a meeting room"),
    ("Empty prompt", ""),
]


def assert_valid_contract(payload: dict[str, Any]) -> None:
    assert "steps" in payload, "Missing steps"
    assert "logs" in payload, "Missing logs"
    assert isinstance(payload["steps"], list), "steps must be a list"
    assert isinstance(payload["logs"], list), "logs must be a list"
    assert len(payload["steps"]) == len(payload["logs"]), "steps/logs count mismatch"

    for log in payload["logs"]:
        assert log.get("status") in {"success", "failed"}, "Invalid log status"


def main() -> None:
    for label, prompt in TEST_CASES:
        response = requests.post(
            f"{BASE_URL}/run",
            json={"prompt": prompt},
            timeout=60,
        )
        print(f"\n=== {label} ===")
        print(f"HTTP {response.status_code}")
        assert response.status_code == 200, "Backend must always return HTTP 200"

        payload = response.json()
        print(json.dumps(payload, indent=2))
        assert_valid_contract(payload)

    print("\nALL INTEGRATION TESTS PASSED")


if __name__ == "__main__":
    main()
