"""Connect a Shopify shop to a Piaxis store and inspect a checkout session.

Prerequisites: the platform has the Shopify integration enabled, and the
Piaxis store holds the ``shopify_payments`` entitlement. The connecting user
must be the store owner.
"""

import os

from piaxis_sdk import PiaxisClient


piaxis = PiaxisClient(
    access_token=os.environ["PIAXIS_ACCESS_TOKEN"],  # store owner session
    base_url=os.getenv("PIAXIS_API_BASE_URL", "https://sandbox.api.gopiaxis.com/api"),
)

# 1. Start the install. payment_mode decides where checkout money goes:
#    "direct" -> straight to store settlement; "escrow" -> held in a Piaxis
#    escrow until the normal release lifecycle completes.
connect = piaxis.connect_shopify(
    {
        "store_id": os.environ["PIAXIS_STORE_ID"],
        "shop_domain": "your-shop.myshopify.com",
        "payment_mode": "direct",
    }
)
print("Send the merchant's browser to:", connect["install_url"])

# 2. After the merchant approves on Shopify, the connection activates via the
#    OAuth callback. Buyers then pay on the hosted page at checkout; each
#    payment session can be inspected for support/reporting:
session_id = os.getenv("PIAXIS_SHOPIFY_SESSION_ID")
if session_id:
    session = piaxis.get_shopify_session(session_id)
    print(
        "Session",
        session["session_id"],
        "->",
        session["status"],
        session["amount"],
        session["currency"],
    )

# 3. Disconnect whenever needed; the stored shop token is dropped immediately.
# piaxis.disconnect_shopify("your-shop.myshopify.com")
