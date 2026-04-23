import os

from piaxis_sdk import PiaxisClient


piaxis = PiaxisClient(
    api_key=os.environ["PIAXIS_API_KEY"],
    base_url=os.getenv("PIAXIS_API_BASE_URL", "https://sandbox.api.gopiaxis.com/api"),
)

piaxis.request_otp(
    {
        "email": "buyer@example.com",
        "phone_number": "+256700000000",
    }
)

escrow = piaxis.create_escrow(
    {
        "receiver_id": os.environ["PIAXIS_RECEIVER_ID"],
        "amount": "50000",
        "currency_code": "UGX",
        "payment_method": "mtn",
        "external_order_id": "order-789",
        "metadata": {"channel": "marketplace"},
        "allocations": [
            {
                "allocation_key": "seller-alpha",
                "amount": "20000",
                "seller_reference": "seller-001",
                "description": "Alpha seller settlement",
            },
            {
                "allocation_key": "seller-beta",
                "amount": "30000",
                "seller_reference": "seller-002",
                "description": "Beta seller settlement",
            },
        ],
        "user_info": {
            "email": "buyer@example.com",
            "phone_number": "+256700000000",
            "otp": os.getenv("PIAXIS_TEST_OTP", "123456"),
        },
        "terms": [{"type": "manual_release", "data": {}}],
    }
)

status = piaxis.get_escrow_status(escrow["id"])
print("Escrow status:", status)
print("Allocation summary:", escrow["allocation_summary"])

released = piaxis.release_escrow(
    escrow["id"],
    payload={
        "allocation_keys": ["seller-alpha"],
        "amount": "20000",
        "reason": "Sandbox partial release for seller alpha",
    },
)

print(released)
