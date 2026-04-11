# backend/tools/discord_tool.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
def _get_token():
    return os.getenv("DISCORD_TOKEN")

def _get_guild():
    return os.getenv("DISCORD_GUILD_ID")

def _headers():
    return {"Authorization": f"Bot {_get_token()}", "Content-Type": "application/json"}

def _ok(data): return {"success": True,  "data": data, "error": None}
def _err(msg): return {"success": False, "data": {},   "error": str(msg)}

def send_message(channel_id: str, content: str, **_):
    try:
        if not _get_token():
            print(f"[MOCK] Discord: Send to {channel_id}: {content}")
            return _ok({"channel_id": channel_id, "sent": True})
        r = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                          headers=_headers(), json={"content": content}, timeout=10)
        r.raise_for_status()
        return _ok({"message_id": r.json()["id"]})
    except Exception as e: return _err(e)

def create_channel(name: str, channel_type: int = 0, **_):
    # type 0 = GUILD_TEXT
    try:
        if not _get_token() or not _get_guild():
            return _ok({"id": "mock-channel-id", "name": name})
        r = requests.post(f"https://discord.com/api/v10/guilds/{_get_guild()}/channels",
                          headers=_headers(), json={"name": name, "type": channel_type}, timeout=10)
        r.raise_for_status()
        return _ok({"id": r.json()["id"], "name": r.json()["name"]})
    except Exception as e: return _err(e)

def list_channels(**_):
    try:
        if not _get_token() or not _get_guild():
            return _ok({"channels": []})
        r = requests.get(f"https://discord.com/api/v10/guilds/{_get_guild()}/channels",
                         headers=_headers(), timeout=10)
        r.raise_for_status()
        channels = [{"id": c["id"], "name": c["name"], "type": c["type"]} for c in r.json()]
        return _ok({"channels": channels})
    except Exception as e: return _err(e)

def add_role(user_id: str, role_id: str, **_):
    try:
        if not _get_token() or not _get_guild():
            return _ok({"user_id": user_id, "role_id": role_id, "added": True})
        r = requests.put(
            f"https://discord.com/api/v10/guilds/{_get_guild()}/members/{user_id}/roles/{role_id}",
            headers=_headers(), timeout=10
        )
        if r.status_code == 204:
            return _ok({"user_id": user_id, "role_id": role_id, "added": True})
        r.raise_for_status()
    except Exception as e: return _err(e)

def kick_member(user_id: str, **_):
    try:
        if not _get_token() or not _get_guild():
            return _ok({"user_id": user_id, "kicked": True})
        r = requests.delete(f"https://discord.com/api/v10/guilds/{_get_guild()}/members/{user_id}",
                            headers=_headers(), timeout=10)
        if r.status_code == 204:
            return _ok({"user_id": user_id, "kicked": True})
        r.raise_for_status()
    except Exception as e: return _err(e)
