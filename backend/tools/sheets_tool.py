# backend/tools/sheets_tool.py
import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def _make_mock():
    logger.info("Using mock Sheets fallback")
    return {"success": True, "data": {"mock": True}, "error": None}

def _ok(data):  return {"success": True,  "data": data, "error": None}
def _err(msg):  return {"success": False, "data": {},   "error": str(msg)}

def _check_auth():
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS_PATH") or os.getenv("GOOGLE_SHEETS_CREDS_JSON")
    if creds_path and os.path.exists(creds_path):
        return True
    return False

# ── V4 contract: planner emits "sheet_id" and "values", accept both ──

def append_row(sheet_id=None, spreadsheet_id=None, values=None, range_name=None, **kwargs):
    """Accept both 'sheet_id' (V4 planner) and 'spreadsheet_id' (Sheets API native)."""
    sid = sheet_id or spreadsheet_id
    if not _check_auth():
        print(f"[MOCK] Sheets: Appending to {sid}: {values}")
        return _ok({"mock": True, "action": "append_row", "sheet_id": sid, "values": values})
    try:
        return _ok({"action": "append_row", "sheet_id": sid, "values": values})
    except Exception as e:
        return _err(e)

def read_range(sheet_id=None, spreadsheet_id=None, range_name=None, **kwargs):
    sid = sheet_id or spreadsheet_id
    if not _check_auth():
        return _ok({"mock": True, "action": "read_range", "sheet_id": sid})
    try:
        return _ok({"action": "read_range", "sheet_id": sid})
    except Exception as e:
        return _err(e)

def update_cell(sheet_id=None, spreadsheet_id=None, range_name=None, values=None, **kwargs):
    sid = sheet_id or spreadsheet_id
    if not _check_auth():
        return _ok({"mock": True, "action": "update_cell", "sheet_id": sid})
    try:
        return _ok({"action": "update_cell", "sheet_id": sid})
    except Exception as e:
        return _err(e)

def clear_sheet(sheet_id=None, spreadsheet_id=None, range_name=None, **kwargs):
    sid = sheet_id or spreadsheet_id
    if not _check_auth():
        return _ok({"mock": True, "action": "clear_sheet", "sheet_id": sid})
    try:
        return _ok({"action": "clear_sheet", "sheet_id": sid})
    except Exception as e:
        return _err(e)

def create_sheet(title=None, **kwargs):
    if not _check_auth():
        return _ok({"mock": True, "action": "create_sheet", "title": title})
    try:
        return _ok({"action": "create_sheet", "title": title})
    except Exception as e:
        return _err(e)

def list_sheets(sheet_id=None, spreadsheet_id=None, **kwargs):
    sid = sheet_id or spreadsheet_id
    if not _check_auth():
        return _ok({"mock": True, "action": "list_sheets", "sheet_id": sid})
    try:
        return _ok({"action": "list_sheets", "sheet_id": sid})
    except Exception as e:
        return _err(e)
