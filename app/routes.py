import json
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse

from app import sheets
from app.config import TTL_HOURS, OWNER_EMAIL
from app.emailer import send_email
from app.hitl_tokens import verify_token
from app.orchestrator import run_cycle, kick_off_approvals, draft_po_text

router = APIRouter()


@router.get("/healthz")
def healthz():
    return {"ok": True}


@router.get("/admin/run-once")
async def run_once(
        ttl_hours: int = Query(TTL_HOURS, ge=0, description="TTL hours for last_checked"),
        dry_run: bool = Query(False, description="If true, do not send approval emails"),
):
    candidates = run_cycle(ttl_hours=ttl_hours)
    simplified = [
        {
            "item_sku": r.get("item_sku"),
            "item_name": r.get("item_name"),
            "supplier_name": r.get("supplier_name"),
            "supplier_email": r.get("supplier_email"),
            "on_hand_qty": r.get("on_hand_qty"),
            "reorder_threshold": r.get("reorder_threshold"),
            "order_qty": r.get("order_qty"),
            "last_checked": r.get("last_checked"),
        }
        for r in candidates
    ]
    if not dry_run and simplified:
        await kick_off_approvals(candidates)
    return {"count": len(simplified), "candidates": simplified, "emails_sent": (not dry_run and len(simplified))}


@router.get("/approve", response_class=HTMLResponse)
def approve_get(token: str):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(400, "invalid or expired token")
    return f"""
    <html><body>
    <h3>Approve SKU {payload.get('sku')}</h3>
    <form method="post" action="/api/approval/resolve?token={token}">
      <button name="decision" value="confirm">Confirm</button>
      <button name="decision" value="reject">Reject</button>
    </form>
    </body></html>
    """


@router.post("/api/approval/resolve")
async def approve_resolve(token: str, decision: str = "confirm"):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(400, "invalid or expired token")

    sku = payload.get("sku")
    qty = payload.get("qty")
    supplier_email = payload.get("supplier_email")
    supplier_name = payload.get("supplier_name")
    item_name = payload.get("item_name", "")

    if decision == "confirm":
        po = draft_po_text(payload)
        try:
            await send_email(
                to_email=supplier_email,
                cc=OWNER_EMAIL,
                subject=f"[PO] {sku} — {item_name} (Qty {qty})",
                body=po
            )
            status = "sent"
        except Exception as e:
            await send_email(
                to_email=OWNER_EMAIL,
                subject=f"[ALERT] Supplier email failed for {sku}",
                body=f"Error: {e}\n\nPO draft:\n{po}"
            )
            status = "failed"

        entry = {
            "po_id": f"{sku}-{int(datetime.now(timezone.utc).timestamp())}",
            "sku": sku,
            "qty": qty,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "owner_decision": "confirmed",
            "supplier_email": supplier_email,
            "metadata": json.dumps({"item_name": item_name}),
        }
        sheets.append_po_log(entry)
        sheets.update_inventory_last_checked_and_note(sku, note="Confirmed by owner")
        return {"status": "ok", "result": "confirmed", "po_status": status}

    elif decision == "reject":
        sheets.update_inventory_last_checked_and_note(sku, note="Rejected by owner")
        entry = {
            "po_id": f"{sku}-{int(datetime.now(timezone.utc).timestamp())}",
            "sku": sku,
            "qty": qty,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "n/a",
            "owner_decision": "rejected",
            "supplier_email": supplier_email,
            "metadata": json.dumps({"item_name": item_name}),
        }
        sheets.append_po_log(entry)
        return {"status": "ok", "result": "rejected"}

    else:
        raise HTTPException(400, "invalid decision")
