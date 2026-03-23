# Piaxis Python SDK

Official Python SDK for the Piaxis partner API.

- Package: `piaxis-sdk`
- Repository: `https://github.com/piaxepay/python-sdk`
- API docs: `https://docs.gopiaxis.com/api/payments/`
- TypeScript SDK: `https://github.com/piaxepay/typescript-sdk`

## Install

```bash
pip install piaxis-sdk
```

## Quick Start

```python
from piaxis_sdk import PiaxisClient

client = PiaxisClient(api_key="your_api_key")

payment = client.create_payment(
    {
        "amount": "15000",
        "currency": "UGX",
        "payment_method": "mtn",
        "user_info": {
            "email": "buyer@example.com",
            "phone_number": "+256700000000",
            "otp": "123456",
        },
    }
)

print(payment["payment_id"])
```

Environment-based setup:

```python
from piaxis_sdk import PiaxisClient

client = PiaxisClient.from_env()
```

Supported environment variables:

- `PIAXIS_API_KEY`
- `PIAXIS_ACCESS_TOKEN`
- `PIAXIS_API_BASE_URL`

The default base URL is `https://api.gopiaxis.com/api`.

## Supported Operations

Full public `paymentAPI` coverage:

- Auth: `build_authorize_url(...)`, `authorize_test(...)`, `exchange_token(...)`
- Escrows: `create_escrow(...)`, `get_escrow(...)`, `get_escrow_status(...)`, `release_escrow(...)`, `fulfill_escrow_term(...)`, `reverse_escrow(...)`, `dispute_escrow(...)`
- OTP: `request_otp(...)`
- Payments: `create_payment(...)`, `get_payment(...)`, `list_merchant_payments(...)`
- Disbursements: `disburse(...)`, `disbursements.get(...)`, `disbursements.list(...)`, `disbursements.cancel(...)`
- Escrow disbursements: `escrow_disburse(...)`, `escrow_disbursements.get(...)`, `escrow_disbursements.list(...)`, `escrow_disbursements.release(...)`, `escrow_disbursements.cancel(...)`

## Examples

- `examples/oauth_flow.py`
- `examples/direct_payment.py`
- `examples/escrow_flow.py`
- `examples/disbursement_flow.py`

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip build twine
python3 -m pip install -e .
python3 -m compileall src
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m build
python3 -m twine check dist/*
```

## Publishing

Steady-state releases should go through the GitHub Actions trusted publisher in
`.github/workflows/release-python.yml`.

```bash
git tag v0.2.0
git push origin v0.2.0
```

Bootstrap note:

- Initial recovery uploads can still be done with `twine upload dist/*`, but
  once PyPI trusted publishing is configured the workflow should be the default
  path.
