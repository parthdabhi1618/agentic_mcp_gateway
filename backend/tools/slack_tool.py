# backend/tools/slack_tool.py
import os
import requests
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def _get_headers():
    token = os.getenv("SLACK_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return {}

def _make_mock():
    logger.info("Using mock Slack fallback")
    return {"success": True, "data": {"mock": True}, "error": None}

def _check_auth():
    return bool(os.getenv("SLACK_TOKEN"))

def _ok(data):  return {"success": True,  "data": data, "error": None}
def _err(msg):  return {"success": False, "data": {},   "error": str(msg)}

# ── V4 contract: planner emits "message", not "text" ──────────────────────────

def send_message(channel=None, message=None, text=None, **kwargs):
    """Accept both 'message' (V4 planner) and 'text' (Slack API native)."""
    content = message or text or ""
    if not _check_auth():
        print(f"[MOCK] Slack: Send to {channel}: {content}")
        return _make_mock()
    try:
        url = "https://slack.com/api/chat.postMessage"
        res = requests.post(url, headers=_get_headers(), json={"channel": channel, "text": content}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"):
            return _err(data.get("error", "unknown"))
        return _ok(data)
    except Exception as e:
        return _err(e)

def create_channel(name=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = "https://slack.com/api/conversations.create"
        res = requests.post(url, headers=_get_headers(), json={"name": name}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)

def list_channels(**kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = "https://slack.com/api/conversations.list"
        res = requests.get(url, headers=_get_headers(), timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)

# ── V4 contract: planner emits "channel_id", accept both ──────────────────────

def get_messages(channel=None, channel_id=None, **kwargs):
    """Accept both 'channel' and 'channel_id' for V4 planner compat."""
    ch = channel_id or channel
    if not _check_auth(): return _make_mock()
    try:
        url = f"https://slack.com/api/conversations.history?channel={ch}"
        res = requests.get(url, headers=_get_headers(), timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)

def add_reaction(channel=None, timestamp=None, name=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = "https://slack.com/api/reactions.add"
        res = requests.post(url, headers=_get_headers(), json={"channel": channel, "timestamp": timestamp, "name": name}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)

def pin_message(channel=None, timestamp=None, **kwargs):
    if not _check_auth(): return _make_mock()
    try:
        url = "https://slack.com/api/pins.add"
        res = requests.post(url, headers=_get_headers(), json={"channel": channel, "timestamp": timestamp}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)

# ── V4 contract: planner emits "user_id", accept both ──────────────────────────

def invite_user(channel=None, user_id=None, users=None, **kwargs):
    """Accept both 'user_id' (V4 planner) and 'users' (Slack API native)."""
    user_val = user_id or users
    if not _check_auth(): return _make_mock()
    try:
        url = "https://slack.com/api/conversations.invite"
        res = requests.post(url, headers=_get_headers(), json={"channel": channel, "users": user_val}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if not data.get("ok"): return _err(data.get("error"))
        return _ok(data)
    except Exception as e:
        return _err(e)
