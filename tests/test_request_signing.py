"""Merchant API request-signing contract tests.

The oracle below is transcribed from the Piaxis API, not from this SDK:
piaxepay/piaxepay revision 4baf740c, security/external_api_auth.py,
``validate_external_api_signature`` and docs/source/external_api/authentication.rst
("Request signatures"). The server path is Starlette ``request.url.path``, i.e. the
ASGI ``scope["path"]`` that uvicorn 0.27.0 builds by percent-decoding the raw
request target before the ``?`` (uvicorn/protocols/http/{h11,httptools}_impl.py).
Starlette 1.3.1 ``datastructures.URL(scope=...)`` then rebuilds
``SplitResult(scheme, netloc, path, query, "").geturl()`` and ``.path`` re-parses it
with ``urllib.parse.urlsplit``, which strips tab/CR/LF and ends the path at the
first decoded ``?`` or ``#`` (CPython 3.12, as deployed).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import SplitResult, unquote, urlsplit

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from piaxis_sdk import PiaxisClient  # noqa: E402
from piaxis_sdk.http_client import PiaxisHttpClient  # noqa: E402

from test_contract import FakeHttpxClient  # noqa: E402

KEY = "pk_test_signing_contract_key"
NOW = 1785751200
TOLERANCE = 300


def server_path(request: httpx.Request) -> str:
    """Starlette request.url.path for the request target on the wire."""
    raw_path, _, query = request.url.raw_path.partition(b"?")
    scope_path = unquote(raw_path.decode("ascii"))  # uvicorn scope["path"]
    url = SplitResult("https", request.url.netloc.decode("ascii"), scope_path, query.decode(), "").geturl()
    return urlsplit(url).path


def server_verify(request: httpx.Request, secret: str, now: int = NOW) -> str | None:
    """Return None when the API would accept the request, else its error code."""
    signature = (request.headers.get("X-piaxis-Signature") or "").strip()
    timestamp = (request.headers.get("X-piaxis-Timestamp") or "").strip()
    if not signature or not timestamp:
        return "MISSING_REQUEST_SIGNATURE"
    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return "INVALID_REQUEST_TIMESTAMP"
    if abs(now - timestamp_int) > TOLERANCE:
        return "STALE_REQUEST_SIGNATURE"
    body_hash = hashlib.sha256(request.content).hexdigest()
    payload = "\n".join([request.method.upper(), server_path(request), timestamp, body_hash])
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.removeprefix("sha256=").strip()):
        return "INVALID_REQUEST_SIGNATURE"
    return None


def make_client(*, base_url: str = "https://sandbox.api.gopiaxis.com/api", clock=lambda: NOW, **kwargs):
    client = PiaxisClient(base_url=base_url, clock=clock, **kwargs)
    fake = FakeHttpxClient([{}] * 4, base_url=base_url)
    client._http._client = fake
    return client, fake


class RequestSigningTests(unittest.TestCase):
    def assertAccepted(self, request: httpx.Request) -> None:
        self.assertIsNone(server_verify(request, KEY))

    def test_known_vector_get_with_injected_clock(self) -> None:
        # Expected value computed independently with:
        # printf 'GET\n/api/payments/pay_123\n1785751200\n<sha256("")>' | openssl dgst -sha256 -hmac pk_test_vector_key
        client, fake = make_client(api_key="pk_test_vector_key", piaxis_client_id="client-1")
        client.get_payment("pay_123")
        request = fake.requests[0]
        self.assertEqual(request.headers["X-piaxis-Timestamp"], "1785751200")
        self.assertEqual(
            request.headers["X-piaxis-Signature"],
            "sha256=87987919e806311eef023b109a3e783f08cd485c7d732671f50a3c5b7fde42c4",
        )
        self.assertEqual(request.content, b"")

    def test_fractional_clock_is_truncated_to_integer_seconds(self) -> None:
        client, fake = make_client(api_key=KEY, clock=lambda: NOW + 0.999)
        client.get_payment("pay_123")
        self.assertEqual(fake.requests[0].headers["X-piaxis-Timestamp"], str(NOW))
        self.assertAccepted(fake.requests[0])

    def test_get_with_query_signs_api_prefixed_path_without_query(self) -> None:
        client, fake = make_client(api_key=KEY, piaxis_client_id="client-1")
        client.list_merchant_payments({"status": "pending", "limit": 20, "offset": 0})
        request = fake.requests[0]
        self.assertEqual(request.url.path, "/api/merchant-payments")
        self.assertIn(b"status=pending", request.url.query)
        self.assertAccepted(request)
        self.assertEqual(request.headers["api-key"], KEY)
        self.assertEqual(request.headers["X-piaxis-Client-ID"], "client-1")

    def test_json_post_signs_exact_non_ascii_wire_bytes(self) -> None:
        client, fake = make_client(api_key=KEY, piaxis_client_id="client-1")
        payload = {
            "amount": "15000",
            "currency": "UGX",
            "payment_method": "mtn",
            "user_info": {"phone_number": "+256700000000"},
            "description": "Café order – Kampala ✓ 日本",
        }
        client.create_payment(payload)
        request = fake.requests[0]
        self.assertEqual(request.url.path, "/api/payments/create")
        self.assertIn("Café order – Kampala ✓ 日本".encode("utf-8"), request.content)
        self.assertEqual(json.loads(request.content), payload)
        self.assertAccepted(request)
        self.assertTrue(request.headers["X-Idempotency-Key"])
        self.assertEqual(request.headers["X-piaxis-Client-ID"], "client-1")
        # The signature must not survive any change to the bytes on the wire.
        tampered = httpx.Request(
            request.method, request.url, headers=request.headers,
            content=json.dumps(payload).encode("utf-8"),
        )
        self.assertNotEqual(tampered.content, request.content)
        self.assertEqual(server_verify(tampered, KEY), "INVALID_REQUEST_SIGNATURE")

    def test_escrow_create_preserves_caller_idempotency_key_and_is_signed(self) -> None:
        client, fake = make_client(api_key=KEY, piaxis_client_id="client-1")
        client.create_escrow(
            {"amount": "50000", "currency_code": "UGX", "payment_method": "mtn",
             "metadata": {"note": "Ünïcødé"}, "terms": [{"type": "manual_release", "data": {}}]},
            request_options={"headers": {"X-Idempotency-Key": "merchant-key-1"}},
        )
        request = fake.requests[0]
        self.assertEqual(request.headers["X-Idempotency-Key"], "merchant-key-1")
        self.assertAccepted(request)

    def test_form_post_token_exchange_is_signed_over_form_bytes(self) -> None:
        client, fake = make_client(api_key=KEY)
        client.exchange_token(
            code="auth code/1",
            redirect_uri="https://merchant.example.com/cb?x=1&y=é",
            client_id="client_123",
            client_secret="secret_456",
        )
        request = fake.requests[0]
        self.assertEqual(request.url.path, "/api/token")
        self.assertTrue(request.headers["content-type"].startswith("application/x-www-form-urlencoded"))
        self.assertIn(b"grant_type=authorization_code", request.content)
        self.assertAccepted(request)

    def test_delete_with_percent_encoded_segment_signs_decoded_server_path(self) -> None:
        client, fake = make_client(api_key=KEY)
        client.disconnect_shopify("demo shop/ü.myshopify.com")
        request = fake.requests[0]
        self.assertEqual(request.method, "DELETE")
        self.assertIn(b"%2F", request.url.raw_path)  # encoded on the wire
        self.assertEqual(server_path(request), "/api/platforms/shopify/connect/demo shop/ü.myshopify.com")
        self.assertAccepted(request)

    def test_direct_http_client_path_with_reserved_characters(self) -> None:
        http = PiaxisHttpClient(base_url="https://sandbox.api.gopiaxis.com/api", api_key=KEY, clock=lambda: NOW)
        http.close()
        fake = FakeHttpxClient([{}], base_url="https://sandbox.api.gopiaxis.com/api")
        http._client = fake
        http.request("DELETE", "/payments/pay%20%C3%A9%2Fx", query={"reason": "a b"})
        request = fake.requests[0]
        self.assertEqual(server_path(request), "/api/payments/pay é/x")
        self.assertAccepted(request)

    def test_decoded_query_and_fragment_delimiters_end_the_signed_path(self) -> None:
        for shop, expected in (
            ("a?b.myshopify.com", "/api/platforms/shopify/connect/a"),
            ("a#b.myshopify.com", "/api/platforms/shopify/connect/a"),
            # Regression: U+FEFF must survive decoding (the TS SDK once stripped it).
            ("a\ufeffb.myshopify.com", "/api/platforms/shopify/connect/a\ufeffb.myshopify.com"),
        ):
            with self.subTest(shop=shop):
                client, fake = make_client(api_key=KEY)
                client.disconnect_shopify(shop)
                request = fake.requests[0]
                self.assertEqual(server_path(request), expected)
                self.assertAccepted(request)

    def test_decoded_control_and_malformed_escapes_in_path(self) -> None:
        for raw, expected in (
            ("/payments/a%EF%BB%BFb", "/api/payments/a\ufeffb"),
            ("/payments/a%09b", "/api/payments/ab"),
            ("/payments/a%0Ab%0Dc", "/api/payments/abc"),
            ("/payments/a%zzb", "/api/payments/a%zzb"),
            ("/payments/a%FFb", "/api/payments/a\ufffdb"),
        ):
            with self.subTest(raw=raw):
                http = PiaxisHttpClient(base_url="https://sandbox.api.gopiaxis.com/api", api_key=KEY, clock=lambda: NOW)
                http.close()
                fake = FakeHttpxClient([{}])
                http._client = fake
                http.request("DELETE", raw, query={"q": "1"})
                request = fake.requests[0]
                self.assertEqual(server_path(request), expected)
                self.assertAccepted(request)

    def test_base_url_with_other_path_prefix(self) -> None:
        client, fake = make_client(api_key=KEY, base_url="https://gateway.example.com/edge/v2/api/")
        client.get_payment("pay_9")
        request = fake.requests[0]
        self.assertEqual(server_path(request), "/edge/v2/api/payments/pay_9")
        self.assertAccepted(request)

    def test_localhost_base_url_without_path(self) -> None:
        client, fake = make_client(api_key=KEY, base_url="http://127.0.0.1:8000")
        client.get_payment("pay_9", request_options={"timeout": 3.0})
        request = fake.requests[0]
        self.assertEqual(server_path(request), "/payments/pay_9")
        self.assertEqual(request.extensions["timeout"]["read"], 3.0)
        self.assertAccepted(request)

    def test_default_clock_is_wall_time(self) -> None:
        import time

        client = PiaxisClient(api_key=KEY, base_url="https://sandbox.api.gopiaxis.com/api")
        fake = FakeHttpxClient([{}])
        client._http._client = fake
        client.get_payment("pay_1")
        request = fake.requests[0]
        self.assertLessEqual(abs(int(request.headers["X-piaxis-Timestamp"]) - int(time.time())), 5)
        self.assertIsNone(server_verify(request, KEY, now=int(time.time())))

    def test_no_signature_without_api_key(self) -> None:
        client, fake = make_client(access_token="tok_123")
        client.get_payment("pay_1")
        client.create_payment({"amount": "1", "currency": "UGX", "payment_method": "mtn"})
        for request in fake.requests:
            self.assertNotIn("X-piaxis-Signature", request.headers)
            self.assertNotIn("X-piaxis-Timestamp", request.headers)
            self.assertNotIn("api-key", request.headers)
            self.assertEqual(request.headers["Authorization"], "Bearer tok_123")
        self.assertIn("X-Idempotency-Key", fake.requests[1].headers)

    def test_each_request_is_signed_with_its_own_timestamp(self) -> None:
        ticks = iter([NOW, NOW + 7])
        client, fake = make_client(api_key=KEY, clock=lambda: next(ticks))
        client.get_payment("pay_1")
        client.get_payment("pay_1")
        stamps = [r.headers["X-piaxis-Timestamp"] for r in fake.requests]
        self.assertEqual(stamps, [str(NOW), str(NOW + 7)])
        for request in fake.requests:
            self.assertAccepted(request)

    def test_verifier_rejects_wrong_key_and_stale_timestamps(self) -> None:
        client, fake = make_client(api_key=KEY)
        client.get_payment("pay_1")
        request = fake.requests[0]
        self.assertAccepted(request)
        self.assertEqual(server_verify(request, "pk_other_key"), "INVALID_REQUEST_SIGNATURE")
        self.assertIsNone(server_verify(request, KEY, now=NOW + TOLERANCE))
        self.assertEqual(server_verify(request, KEY, now=NOW + TOLERANCE + 1), "STALE_REQUEST_SIGNATURE")
        self.assertEqual(server_verify(request, KEY, now=NOW - TOLERANCE - 1), "STALE_REQUEST_SIGNATURE")

        skewed, skewed_fake = make_client(api_key=KEY, clock=lambda: NOW - 600)
        skewed.get_payment("pay_1")
        self.assertEqual(server_verify(skewed_fake.requests[0], KEY), "STALE_REQUEST_SIGNATURE")


if __name__ == "__main__":
    unittest.main()
