import base64
import hashlib
import hmac
import json
import time

from app.config import HITL_SIGNING_KEY


def make_token(payload: dict, ttl_sec: int = 24 * 3600):
    data = dict(payload)
    data["exp"] = int(time.time()) + ttl_sec
    raw = json.dumps(data, separators=(",", ":")).encode()
    sig = hmac.new(HITL_SIGNING_KEY.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + sig).decode()


def verify_token(token: str):
    try:
        blob = base64.urlsafe_b64decode(token.encode())
        raw, sig = blob.rsplit(b".", 1)
        expected = hmac.new(HITL_SIGNING_KEY.encode(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(raw.decode())
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
