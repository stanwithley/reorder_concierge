from datetime import datetime, timezone
from typing import List, Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

from app.config import SHEET_ID, GOOGLE_CREDS_PATH, INVENTORY_SHEET_NAME, PO_LOG_SHEET_NAME


def _client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scopes)
    return gspread.authorize(creds)


def _open_sheet():
    gc = _client()
    return gc.open_by_key(SHEET_ID)


def read_inventory() -> List[Dict]:
    sh = _open_sheet()
    try:
        ws = sh.worksheet(INVENTORY_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.sheet1
    values = ws.get_all_values()
    if not values:
        return []
    headers = [h.strip() for h in values[0]]
    rows = []
    for raw in values[1:]:
        item = {headers[i]: (raw[i] if i < len(raw) else "") for i in range(len(headers))}
        rows.append(item)
    return rows


def _find_row_index_by_sku(ws, headers: List[str], sku: str) -> Optional[int]:
    sku_col_idx = headers.index("item_sku") if "item_sku" in headers else None
    if sku_col_idx is None:
        return None
    all_vals = ws.get_all_values()
    for idx, row in enumerate(all_vals[1:], start=2):
        val = row[sku_col_idx] if sku_col_idx < len(row) else ""
        if val == sku:
            return idx
    return None


def update_inventory_last_checked_and_note(sku: str, note: str = ""):
    sh = _open_sheet()
    try:
        ws = sh.worksheet(INVENTORY_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.sheet1

    values = ws.get_all_values()
    if not values:
        return False
    headers = [h.strip() for h in values[0]]
    row_idx = _find_row_index_by_sku(ws, headers, sku)
    if row_idx is None:
        return False

    def col_letter(i):
        return chr(ord('A') + i)

    now_iso = datetime.now(timezone.utc).isoformat()
    updates = []

    if "last_checked" in headers:
        col = headers.index("last_checked")
        updates.append((f"{col_letter(col)}{row_idx}", now_iso))

    if note and "notes" in headers:
        col = headers.index("notes")
        updates.append((f"{col_letter(col)}{row_idx}", note))

    for addr, val in updates:
        ws.update_acell(addr, val)

    return True


def ensure_po_log_sheet():
    sh = _open_sheet()
    try:
        ws = sh.worksheet(PO_LOG_SHEET_NAME)
        return ws
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=PO_LOG_SHEET_NAME, rows=1000, cols=10)


def append_po_log(entry: Dict):
    ws = ensure_po_log_sheet()
    headers = ["po_id", "sku", "qty", "created_at", "status", "owner_decision", "supplier_email", "metadata"]
    try:
        existing = ws.get_all_values()
        if not existing:
            ws.append_row(headers, value_input_option="RAW")
    except Exception:
        pass

    row = [str(entry.get(k, "")) for k in headers]
    ws.append_row(row, value_input_option="RAW")
