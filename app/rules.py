from datetime import datetime, timedelta, timezone

from dateutil import parser as dtparse


def needs_reorder(row, now=None, ttl_hours: int = 24) -> bool:
    now = now or datetime.now(timezone.utc)
    try:
        qty = int(str(row.get("on_hand_qty", "0")).strip() or "0")
        thr = int(str(row.get("reorder_threshold", "0")).strip() or "0")
        last_checked_raw = str(row.get("last_checked", "")).strip()
        last_checked = dtparse.isoparse(last_checked_raw)
        if last_checked.tzinfo is None:
            last_checked = last_checked.replace(tzinfo=timezone.utc)
        older_than_ttl = (now - last_checked.astimezone(timezone.utc)) > timedelta(hours=ttl_hours)
        return qty < thr and older_than_ttl
    except Exception:
        return False
