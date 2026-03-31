import requests
import os
from dotenv import load_dotenv

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN")

def send_message(channel: str, message: str, **kwargs):
    """Sends a message to a Slack channel."""
    if not SLACK_TOKEN:
        raise ValueError("SLACK_TOKEN not set in .env")

    r = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
        json={"channel": channel, "text": message},
        timeout=10
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise ValueError(f"Slack API error: {data.get('error', 'unknown')}")
