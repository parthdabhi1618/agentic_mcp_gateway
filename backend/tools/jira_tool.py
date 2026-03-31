import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_URL   = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

def create_issue(project: str, summary: str, type: str = "Bug", **kwargs):
    """Creates a Jira issue. Falls back to mock if credentials not set."""
    if not JIRA_URL or not JIRA_EMAIL or not JIRA_TOKEN:
        # Mock mode
        print(f"[MOCK] Jira: Creating {type} in {project}: {summary}")
        return

    r = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        auth=(JIRA_EMAIL, JIRA_TOKEN),
        json={
            "fields": {
                "project": {"key": project},
                "summary": summary,
                "issuetype": {"name": type}
            }
        },
        timeout=10
    )
    r.raise_for_status()
    issue = r.json()
    print(f"[Jira] Created issue: {issue.get('key')}")
