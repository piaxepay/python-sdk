# Python SDK Sandbox Onboarding

Use this guide to validate a Python integration against the Piaxis sandbox.

## Install

```bash
pip install piaxis-sdk
```

## Environment Variables

```bash
export PIAXIS_API_KEY="your_sandbox_api_key"
export PIAXIS_API_BASE_URL="https://sandbox.api.gopiaxis.com/api"
```

## Smoke Test

```python
from piaxis_sdk import PiaxisClient

client = PiaxisClient.from_env()
authorize_url = client.build_authorize_url(
    merchant_id="merchant-123",
    external_user_id="external-user-789",
    redirect_uri="https://merchant.example.com/oauth/callback",
)

print(authorize_url)
```

`redirect_uri` values used in sandbox OAuth tests must already be registered for the merchant. If you use the SDK's browserless `authorize_test(...)` helper, treat it as a merchant-admin-only test tool rather than a public client flow.

## Example Flows

- `examples/oauth_flow.py`
- `examples/direct_payment.py`
- `examples/escrow_flow.py`
- `examples/disbursement_flow.py`

## Related Resources

- API docs: `https://api.gopiaxis.com/api/docs/`
- TypeScript SDK: `https://github.com/piaxepay/typescript-sdk`
