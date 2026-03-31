import json

from planner import _validate_steps, plan


SHAPE_TEST_CASES = [
    (
        [
            {
                "tool": "github",
                "args": {"action": "create_branch", "name": "Fix Login", "from_branch": ""},
            },
            {
                "tool": "slack",
                "args": {"action": "send_message", "channel": "general", "message": "branch created"},
            },
            {
                "tool": "jira",
                "args": {"action": "create_issue", "project": "demo", "summary": "Login issue"},
            },
        ],
        "Create a branch Fix Login and tell general on Slack",
    ),
    ([], "Book a meeting room"),
]


LIVE_PROMPTS = [
    "Create a GitHub branch named fix/login",
    "Notify general on Slack that the gateway is live",
    "Create a GitHub branch fix/crash and notify alerts on Slack",
    "Create GitHub branch fix/critical, notify #alerts on Slack, and create a Jira bug in project DEMO",
    "Book a meeting room",
    "",
]


def test_validation_shape() -> None:
    for raw_steps, prompt in SHAPE_TEST_CASES:
        validated = _validate_steps(raw_steps, prompt)
        assert isinstance(validated, list), "Validated steps must be a list"
        for step in validated:
            assert "tool" in step and "args" in step
            assert isinstance(step["args"], dict)
            assert "action" in step["args"]
            assert step["tool"] in {"github", "slack", "jira", "sheets"}

    github_step = _validate_steps(
        [{"tool": "github", "args": {"action": "create_branch", "name": "Fix Login"}}],
        "Create Fix Login",
    )[0]
    assert github_step["args"]["name"] == "fix-login"
    assert github_step["args"]["from_branch"] == "main"

    slack_step = _validate_steps(
        [{"tool": "slack", "args": {"action": "send_message", "channel": "general", "message": "hi"}}],
        "notify general",
    )[0]
    assert slack_step["args"]["channel"] == "#general"


def main() -> None:
    test_validation_shape()
    print("VALIDATION TESTS PASSED")

    for prompt in LIVE_PROMPTS:
        result = plan(prompt)
        print(f"\nPrompt: {prompt!r}")
        print(json.dumps(result, indent=2))
        assert isinstance(result, list), "plan() must always return a list"
        for step in result:
            assert "tool" in step and "args" in step, "Each step needs tool + args"
            assert isinstance(step["args"], dict), "args must be a dict"
            assert "action" in step["args"], "args must include action"
    print("\nLIVE CALL SHAPE ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
