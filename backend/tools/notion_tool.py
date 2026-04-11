# backend/tools/notion_tool.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
def _get_token():
    return os.getenv("NOTION_TOKEN")

def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def _ok(data): return {"success": True,  "data": data, "error": None}
def _err(msg): return {"success": False, "data": {},   "error": str(msg)}

def create_page(parent_page_id: str, title: str, content: str = "", **_):
    try:
        if not _get_token():
            print(f"[MOCK] Notion: Create page '{title}'")
            return _ok({"id": "mock-notion-page-id", "title": title})
        payload = {
            "parent": {"page_id": parent_page_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": [{"object": "block", "type": "paragraph",
                          "paragraph": {"rich_text": [{"text": {"content": content}}]}}] if content else []
        }
        r = requests.post("https://api.notion.com/v1/pages", headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        return _ok({"id": r.json()["id"], "url": r.json().get("url", "")})
    except Exception as e: return _err(e)

def update_page(page_id: str, title: str = None, **_):
    try:
        if not _get_token():
            return _ok({"id": page_id, "updated": True})
        payload = {}
        if title:
            payload["properties"] = {"title": {"title": [{"text": {"content": title}}]}}
        r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        return _ok({"id": page_id})
    except Exception as e: return _err(e)

def append_block(page_id: str, content: str, block_type: str = "paragraph", **_):
    try:
        if not _get_token():
            return _ok({"appended": True})
        payload = {"children": [{"object": "block", "type": block_type,
                                  block_type: {"rich_text": [{"text": {"content": content}}]}}]}
        r = requests.patch(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        return _ok({"page_id": page_id, "block_type": block_type})
    except Exception as e: return _err(e)

def query_database(database_id: str, filter_dict: dict = None, **_):
    try:
        if not _get_token():
            return _ok({"results": []})
        payload = {}
        if filter_dict:
            payload["filter"] = filter_dict
        r = requests.post(f"https://api.notion.com/v1/databases/{database_id}/query",
                          headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        results = r.json().get("results", [])
        return _ok({"count": len(results), "results": results[:5]})  # limit response size
    except Exception as e: return _err(e)

def create_database_entry(database_id: str, properties: dict, **_):
    try:
        if not _get_token():
            return _ok({"id": "mock-entry-id"})
        payload = {"parent": {"database_id": database_id}, "properties": properties}
        r = requests.post("https://api.notion.com/v1/pages", headers=_headers(), json=payload, timeout=15)
        r.raise_for_status()
        return _ok({"id": r.json()["id"]})
    except Exception as e: return _err(e)
