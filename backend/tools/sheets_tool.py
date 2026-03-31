import os
from dotenv import load_dotenv

load_dotenv()

def append_row(sheet_id: str, values: list, **kwargs):
    """Appends a row to Google Sheets. Mock implementation."""
    print(f"[MOCK] Sheets: Appending to {sheet_id}: {values}")
