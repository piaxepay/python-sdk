from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import TypedDict


class PkcePair(TypedDict):
    code_verifier: str
    code_challenge: str
    code_challenge_method: str


def generate_pkce_pair() -> PkcePair:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }


def verify_webhook_signature(
    raw_body: bytes | str,
    *,
    secret: str,
    signature: str | None = None,
    signature_v2: str | None = None,
    timestamp: str | int | None = None,
    tolerance_seconds: int = 300,
) -> bool:
    body_bytes = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")

    if signature_v2:
        if timestamp in (None, ""):
            return False
        try:
            timestamp_int = int(timestamp)
        except (TypeError, ValueError):
            return False
        if tolerance_seconds > 0 and abs(int(time.time()) - timestamp_int) > tolerance_seconds:
            return False

        signed_payload = f"{timestamp_int}.".encode("utf-8") + body_bytes
        expected_v2 = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_v2, signature_v2)

    if not signature:
        return False

    expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
