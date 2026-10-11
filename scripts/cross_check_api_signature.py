"""Opt-in cross-check: real SDK requests against the Piaxis API's own signature validator.

Runs the API's ``security.external_api_auth.validate_external_api_signature`` (with
``require_signature=True``) behind a real uvicorn server on an ephemeral loopback
port, then drives real SDK methods over HTTP. Run with the API's virtualenv so
Starlette/uvicorn match the API lock, and with an empty environment:

    git -C ../piaxis-api archive origin/master security piaxis helpers | tar -x -C /tmp/api
    env -i PATH="$PATH" HOME="$HOME" PIAXIS_API_DIR=/tmp/api \
        ../piaxis-api/.venv/bin/python scripts/cross_check_api_signature.py

Exit codes: 0 all cases matched, 1 a case mismatched, 2 SKIPPED (PIAXIS_API_DIR unset).
A skip is not a pass. Only throwaway, randomly generated secrets are used.
"""

from __future__ import annotations

import base64
import os
import secrets
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

API_DIR = os.environ.get("PIAXIS_API_DIR")
if not API_DIR:
    print("SKIPPED: set PIAXIS_API_DIR to an export of piaxis-api (security/, piaxis/, helpers/).")
    sys.exit(2)

# Never let the API settings discover a real env file: test mode, throwaway secrets,
# and a fresh empty working directory for pydantic's relative ".env" lookup.
os.environ.pop("piaxis_ENV_FILE", None)
os.environ["PIAXE_TEST_MODE"] = "1"
for name in ("SECRET_KEY", "REFRESH_TOKEN_SECRET_KEY"):
    os.environ[name] = secrets.token_urlsafe(48)
os.environ["FERNET_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
os.chdir(tempfile.mkdtemp(prefix="piaxis-sigcheck-"))

sys.path.insert(0, str(Path(API_DIR).resolve()))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import starlette  # noqa: E402
import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from piaxis_sdk import PiaxisApiError, PiaxisClient  # noqa: E402
from security.external_api_auth import validate_external_api_signature  # noqa: E402

KEY = "pk_test_" + secrets.token_hex(16)

app = FastAPI()


# Middleware, not a route: a "{rest:path}" route does not match a decoded newline
# and would 404 before the validator runs.
@app.middleware("http")
async def validate_everything(request: Request, call_next):
    try:
        await validate_external_api_signature(request=request, merchant_secret=KEY, require_signature=True)
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return JSONResponse({"ok": True, "method": request.method, "path": request.url.path})


def start_server(http_impl: str) -> tuple[uvicorn.Server, threading.Thread, int]:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, http=http_impl, log_level="warning", lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started:
        if time.time() > deadline:
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.05)
    return server, thread, port


def run_cases(port: int) -> list[tuple[str, object, object, str]]:
    base = f"http://127.0.0.1:{port}/api"

    def client(**kwargs) -> PiaxisClient:
        kwargs.setdefault("api_key", KEY)
        return PiaxisClient(base_url=kwargs.pop("base_url", base), piaxis_client_id="client-1", **kwargs)

    good = client()
    cases = [
        ("GET get_payment", 200, lambda: good.get_payment("pay_123")),
        ("GET list_merchant_payments ?query", 200,
         lambda: good.list_merchant_payments({"status": "pending", "limit": 20, "offset": 0})),
        ("POST create_payment non-ASCII JSON", 200, lambda: good.create_payment(
            {"amount": "15000", "currency": "UGX", "payment_method": "mtn",
             "user_info": {"phone_number": "+256700000000"}, "description": "Café – Kampala ✓ 日本"})),
        ("POST create_escrow", 200, lambda: good.create_escrow(
            {"amount": "50000", "currency_code": "UGX", "payment_method": "mtn",
             "metadata": {"note": "Ünïcødé"}, "terms": [{"type": "manual_release", "data": {}}]})),
        ("POST exchange_token form", 200, lambda: good.exchange_token(
            code="auth code/1", redirect_uri="https://merchant.example.com/cb?x=1&y=é",
            client_id="client_123", client_secret="secret_456")),
        ("DELETE disconnect_shopify encoded segment", 200,
         lambda: good.disconnect_shopify("demo shop/ü.myshopify.com")),
        ("DELETE http.request pre-encoded path", 200,
         lambda: good._http.request("DELETE", "/payments/pay%20%C3%A9%2Fx", query={"reason": "a b"})),
        ("DELETE disconnect_shopify decoded '?'", 200, lambda: good.disconnect_shopify("a?b.myshopify.com")),
        ("DELETE disconnect_shopify decoded '#'", 200, lambda: good.disconnect_shopify("a#b.myshopify.com")),
        *[(f"DELETE http.request {raw}", 200, lambda raw=raw: good._http.request("DELETE", raw, query={"q": "1"}))
          for raw in ("/payments/a%09b", "/payments/a%0Ab%0Dc", "/payments/a%zzb", "/payments/a%FFb")],
        ("GET base_url /edge/v2/api prefix", 200,
         lambda: client(base_url=f"http://127.0.0.1:{port}/edge/v2/api").get_payment("pay_9")),
        ("NEG wrong key", (401, "INVALID_REQUEST_SIGNATURE"),
         lambda: client(api_key="pk_test_wrong_" + secrets.token_hex(8)).get_payment("pay_123")),
        ("NEG clock skewed -600s", (401, "STALE_REQUEST_SIGNATURE"),
         lambda: client(clock=lambda: time.time() - 600).get_payment("pay_123")),
        ("NEG clock skewed +600s POST", (401, "STALE_REQUEST_SIGNATURE"),
         lambda: client(clock=lambda: time.time() + 600).create_payment(
             {"amount": "1", "currency": "UGX", "payment_method": "mtn"})),
        ("NEG access_token only (unsigned)", (400, "MISSING_REQUEST_SIGNATURE"),
         lambda: client(api_key=None, access_token="tok").get_payment("pay_123")),
    ]
    results = []
    for name, expected, call in cases:
        try:
            body = call()
            actual: object = 200
            info = f"server path={body.get('path')!r}"
        except PiaxisApiError as exc:
            actual = (exc.status_code, exc.code)
            info = exc.message
        results.append((name, expected, actual, info))
    return results


def main() -> int:
    print(f"python {sys.version.split()[0]}, starlette {starlette.__version__}, uvicorn {uvicorn.__version__}")
    failed = 0
    for http_impl in ("h11", "httptools"):
        server, thread, port = start_server(http_impl)
        try:
            for name, expected, actual, info in run_cases(port):
                ok = expected == actual
                failed += not ok
                print(f"[{'PASS' if ok else 'FAIL'}] {http_impl:9} {name}: expected={expected} actual={actual} {info}")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
    print("RESULT:", "FAIL" if failed else "PASS", f"({failed} mismatches)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
