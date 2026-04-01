# Piaxis Python SDK

Official Python SDK for the Piaxis partner/payments API.

- Package: `piaxis-sdk`
- PyPI: `https://pypi.org/project/piaxis-sdk/`
- Repository: `https://github.com/piaxepay/python-sdk`
- REST API docs: `https://api.gopiaxis.com/api/docs/`
- TypeScript SDK: `https://github.com/piaxepay/typescript-sdk`

## What this SDK covers

This SDK is the Python client for the public partner/payments surface exposed at `api.gopiaxis.com`.

It currently covers:

- OAuth authorize URL generation and token exchange for `piaxis_external`
- OTP requests
- Direct payments
- Escrows and escrow actions
- Direct disbursements
- Escrow disbursements
- Shared transport concerns like auth headers, timeouts, and structured API errors

It does not attempt to wrap every backend endpoint in `piaxis-api`, such as internal dashboard, admin, or other non-public surfaces. For fields or endpoints not yet promoted into the SDK surface, use the raw REST documentation at `https://api.gopiaxis.com/api/docs/`.

## Install

```bash
pip install piaxis-sdk
```

Python `3.10+` is required.

## Choose your auth mode

Use one of these two authentication modes:

- `api_key`: merchant-owned operations like OTP, direct payments, escrows, and disbursements
- `access_token`: end-user-authorized `piaxis_external` payments after the OAuth flow completes

Environment variables supported by `PiaxisClient.from_env()`:

- `PIAXIS_API_KEY`
- `PIAXIS_ACCESS_TOKEN`
- `PIAXIS_API_BASE_URL`

Base URLs:

- Sandbox: `https://sandbox.api.gopiaxis.com/api`
- Production: `https://api.gopiaxis.com/api`

`PiaxisClient.from_env()` requires either `PIAXIS_API_KEY` or `PIAXIS_ACCESS_TOKEN`.

```bash
export PIAXIS_API_KEY="your_sandbox_api_key"
export PIAXIS_API_BASE_URL="https://sandbox.api.gopiaxis.com/api"
```

```python
from piaxis_sdk import PiaxisClient

client = PiaxisClient.from_env()
```

## Direct payment flow

Typical mobile-money flow:

1. Request an OTP for the customer.
2. Create the payment with `payment_method="mtn"` or `payment_method="airtel"`.
3. Poll `get_payment(...)` and/or consume your webhook events until the payment settles.

```python
import os

from piaxis_sdk import PiaxisClient


with PiaxisClient.from_env() as client:
    otp = client.request_otp(
        {
            "email": "buyer@example.com",
            "phone_number": "+256700000000",
        }
    )

    payment = client.create_payment(
        {
            "amount": "15000",
            "currency": "UGX",
            "payment_method": "mtn",
            "user_info": {
                "email": "buyer@example.com",
                "phone_number": "+256700000000",
                "otp": os.getenv("PIAXIS_TEST_OTP", "123456"),
            },
            "customer_pays_fees": True,
        }
    )

    print("otp:", otp)
    print("payment:", payment)
    print("latest:", client.get_payment(payment["payment_id"]))
```

Notes:

- `user_info`, `products`, and `terms[*].data` follow the raw API payload shape from the REST docs.
- Many payment methods are asynchronous. Plan for polling and webhooks instead of assuming the create call means “completed”.

## OAuth and `piaxis_external` flow

Use this when the payer must authorize access to an external Piaxis wallet.

```python
import os

from piaxis_sdk import PiaxisClient


base_url = os.getenv("PIAXIS_API_BASE_URL", "https://sandbox.api.gopiaxis.com/api")

auth_client = PiaxisClient(base_url=base_url)

authorize_url = auth_client.build_authorize_url(
    merchant_id=os.environ["PIAXIS_MERCHANT_ID"],
    external_user_id="customer-123",
    redirect_uri=os.environ["PIAXIS_REDIRECT_URI"],
)

print("redirect the customer to:", authorize_url)

tokens = auth_client.exchange_token(
    code=os.environ["PIAXIS_AUTH_CODE"],
    redirect_uri=os.environ["PIAXIS_REDIRECT_URI"],
    client_id=os.environ["PIAXIS_OAUTH_CLIENT_ID"],
    client_secret=os.environ["PIAXIS_OAUTH_CLIENT_SECRET"],
)

payer_client = PiaxisClient(
    access_token=tokens["access_token"],
    base_url=base_url,
)

payment = payer_client.create_payment(
    {
        "amount": "15000",
        "currency": "UGX",
        "payment_method": "piaxis_external",
        "recipient_id": os.environ.get("PIAXIS_RECIPIENT_ID"),
        "customer_pays_fees": True,
    }
)

print(payment)
```

If you want to test the authorize step without a browser redirect, use `authorize_test(...)`.

## Escrow flow

Escrows are a separate flow from direct payments. The common lifecycle is:

1. `create_escrow(...)`
2. `get_escrow(...)` or `get_escrow_status(...)`
3. `fulfill_escrow_term(...)`, `release_escrow(...)`, `reverse_escrow(...)`, or `dispute_escrow(...)` depending on your business rules

```python
import os

from piaxis_sdk import PiaxisClient


with PiaxisClient.from_env() as client:
    escrow = client.create_escrow(
        {
            "receiver_id": os.environ["PIAXIS_RECEIVER_ID"],
            "amount": "50000",
            "currency_code": "UGX",
            "payment_method": "mtn",
            "user_info": {
                "email": "buyer@example.com",
                "phone_number": "+256700000000",
                "otp": os.getenv("PIAXIS_TEST_OTP", "123456"),
            },
            "terms": [{"type": "manual_release", "data": {}}],
        }
    )

    print(client.get_escrow_status(escrow["id"]))
    print(
        client.release_escrow(
            escrow["id"],
            payload={"force": True, "reason": "Sandbox manual release"},
        )
    )
```

## Disbursement flows

Use direct disbursements for payouts that do not need escrow, and escrow disbursements when each payout item must satisfy terms before release.

```python
from piaxis_sdk import PiaxisClient


with PiaxisClient.from_env() as client:
    direct = client.disburse(
        recipients=[
            {"recipient_id": "recipient-123", "amount": "100000", "reference": "supplier-001"},
            {"phone_number": "+256711111111", "amount": "50000", "reference": "supplier-002"},
        ],
        currency="UGX",
        payment_method="airtel",
        description="Weekly supplier payout",
    )

    escrow_batch = client.escrow_disburse(
        recipients=[
            {
                "recipient_id": "recipient-123",
                "amount": "100000",
                "reference": "courier-001",
                "terms": [{"type": "manual_release", "data": {}}],
            }
        ],
        currency="UGX",
        payment_method="mtn",
        description="Courier escrow batch",
        user_location={"latitude": 0.312, "longitude": 32.582},
    )

    print(direct)
    print(escrow_batch)
```

Related methods:

- `get_disbursement(...)`, `list_disbursements(...)`, `cancel_disbursement(...)`
- `get_escrow_disbursement(...)`, `list_escrow_disbursements(...)`, `release_escrow_disbursement(...)`, `cancel_escrow_disbursement(...)`

## Error handling

API failures raise `PiaxisApiError`.

```python
from piaxis_sdk import PiaxisApiError, PiaxisClient


try:
    client = PiaxisClient(api_key="invalid")
    client.list_merchant_payments()
except PiaxisApiError as exc:
    print("message:", exc.message)
    print("status:", exc.status_code)
    print("code:", exc.code)
    print("request_id:", exc.request_id)
    print("details:", exc.details)
```

Use `request_id` when talking to Piaxis support.

## Request customization

You can identify your application and override request behavior:

```python
from piaxis_sdk import PiaxisClient


client = PiaxisClient(
    api_key="your_api_key",
    base_url="https://sandbox.api.gopiaxis.com/api",
    timeout=60.0,
    app_name="orders-service",
    app_version="1.4.0",
)

payment = client.get_payment(
    "payment-id",
    request_options={
        "headers": {"x-request-id": "merchant-trace-123"},
        "timeout": 10.0,
    },
)
```

This sends:

- `api-key` or `Authorization: Bearer ...`
- `x-piaxis-sdk-client: orders-service/1.4.0` when `app_name` is set
- any extra headers you pass via `request_options`

## Method map

| Capability | Python method | REST endpoint |
| --- | --- | --- |
| Build authorize URL | `build_authorize_url(...)` | `GET /authorize` |
| Test authorize redirect | `authorize_test(...)` | `GET /authorize` with `x-test-request: true` |
| Exchange OAuth token | `exchange_token(...)` | `POST /token` |
| Request OTP | `request_otp(...)` | `POST /request-otp` |
| Create payment | `create_payment(...)` | `POST /payments/create` |
| Get payment | `get_payment(...)` | `GET /payments/{payment_id}` |
| List merchant payments | `list_merchant_payments(...)` | `GET /merchant-payments` |
| Create escrow | `create_escrow(...)` | `POST /escrows/` |
| Get escrow | `get_escrow(...)` | `GET /escrows/{escrow_id}` |
| Get escrow status | `get_escrow_status(...)` | `GET /escrows/{escrow_id}/status` |
| Release escrow | `release_escrow(...)` | `POST /escrows/{escrow_id}/release` |
| Fulfill escrow term | `fulfill_escrow_term(...)` | `POST /escrows/{escrow_id}/terms/{term_id}/fulfill` |
| Reverse escrow | `reverse_escrow(...)` | `POST /escrows/{escrow_id}/reverse` |
| Dispute escrow | `dispute_escrow(...)` | `POST /escrows/{escrow_id}/disputes` |
| Create disbursement | `disburse(...)` | `POST /disbursements` |
| Get disbursement | `get_disbursement(...)` | `GET /disbursements/{disbursement_id}` |
| List disbursements | `list_disbursements(...)` | `GET /disbursements` |
| Cancel disbursement | `cancel_disbursement(...)` | `POST /disbursements/{disbursement_id}/cancel` |
| Create escrow disbursement | `escrow_disburse(...)` | `POST /escrow-disbursements` |
| Get escrow disbursement | `get_escrow_disbursement(...)` | `GET /escrow-disbursements/{disbursement_id}` |
| List escrow disbursements | `list_escrow_disbursements(...)` | `GET /escrow-disbursements` |
| Release escrow disbursement | `release_escrow_disbursement(...)` | `POST /escrow-disbursements/{disbursement_id}/release` |
| Cancel escrow disbursement | `cancel_escrow_disbursement(...)` | `POST /escrow-disbursements/{disbursement_id}/cancel` |

## Examples and references

- Direct payment example: `https://github.com/piaxepay/python-sdk/blob/main/examples/direct_payment.py`
- OAuth example: `https://github.com/piaxepay/python-sdk/blob/main/examples/oauth_flow.py`
- Escrow example: `https://github.com/piaxepay/python-sdk/blob/main/examples/escrow_flow.py`
- Disbursement example: `https://github.com/piaxepay/python-sdk/blob/main/examples/disbursement_flow.py`
- Sandbox onboarding: `https://github.com/piaxepay/python-sdk/blob/main/SANDBOX_ONBOARDING.md`
- Repository architecture: `https://github.com/piaxepay/python-sdk/blob/main/ARCHITECTURE.md`
- REST API docs: `https://api.gopiaxis.com/api/docs/`
