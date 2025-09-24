from datetime import datetime, timezone
from typing import List, Dict

from app import sheets, rules
from app.config import TTL_HOURS, OWNER_EMAIL, BASE_URL
from app.emailer import send_email
from app.hitl_tokens import make_token


def run_cycle(ttl_hours: int = TTL_HOURS) -> List[Dict]:
    rows = sheets.read_inventory()
    now = datetime.now(timezone.utc)
    return [r for r in rows if rules.needs_reorder(r, now, ttl_hours)]


def build_approval_email_body(row: Dict, confirm_url: str, reject_url: str) -> str:
    return (
        f"🔔 Reorder Approval Needed\n\n"
        f"SKU: {row.get('item_sku')}\n"
        f"Item: {row.get('item_name')}\n"
        f"On hand: {row.get('on_hand_qty')} (threshold: {row.get('reorder_threshold')})\n"
        f"Suggested order qty: {row.get('order_qty')}\n\n"
        f"Supplier: {row.get('supplier_name')} <{row.get('supplier_email')}>\n\n"
        f"[Confirm] {confirm_url}\n"
        f"[Reject]  {reject_url}\n"
    )


async def kick_off_approvals(candidates: List[Dict]):
    for r in candidates:
        token = make_token({
            "sku": r.get("item_sku"),
            "qty": r.get("order_qty"),
            "supplier_email": r.get("supplier_email"),
            "supplier_name": r.get("supplier_name"),
            "item_name": r.get("item_name"),
        })
        confirm_url = f"{BASE_URL}/approve?token={token}"
        reject_url = f"{BASE_URL}/approve?token={token}"

        body = build_approval_email_body(r, confirm_url, reject_url)
        await send_email(
            to_email=OWNER_EMAIL,
            subject=f"[Approval] Reorder {r.get('item_sku')} — {r.get('item_name')}",
            body=body
        )


def draft_po_text(payload: Dict) -> str:
    return (
        f"Purchase Order (Draft)\n"
        f"SKU: {payload.get('sku')}\n"
        f"Item: {payload.get('item_name', '')}\n"
        f"Quantity: {payload.get('qty')}\n"
        f"Ship-to: <YOUR ADDRESS HERE>\n"
        f"Provider: {payload.get('supplier_name')} <{payload.get('supplier_email')}>\n"
    )
