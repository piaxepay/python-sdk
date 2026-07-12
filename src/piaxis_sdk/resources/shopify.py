"""Shopify Payments App integration helpers.

Merchant-side lifecycle for connecting a Shopify shop to a Piaxis store.
The integration is additive and gated server-side: the platform must have
Shopify enabled and the store must hold the ``shopify_payments`` entitlement.

The webhook and OAuth-callback endpoints are Shopify-facing and are not
exposed here; the buyer's hosted payment page drives its own session calls.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..http_client import PiaxisHttpClient
from ..types import PiaxisRequestOptions, ShopifyConnectInput


class ShopifyResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def connect(
        self,
        payload: ShopifyConnectInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        """Begin the install for a shop.

        Returns ``{"install_url": ..., "shop_domain": ..., "payment_mode": ...}``;
        send the merchant's browser to ``install_url`` (Shopify's authorize
        page). ``payment_mode`` chooses where collected money goes:
        ``"direct"`` (store settlement) or ``"escrow"`` (held in a Piaxis
        escrow until release).
        """
        return self._http.post(
            "/platforms/shopify/connect",
            body=dict(payload),
            request_options=request_options,
        )

    def disconnect(
        self,
        shop_domain: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        """Revoke the integration for a shop; its stored token is dropped."""
        return self._http.request(
            "DELETE",
            f"/platforms/shopify/connect/{quote(shop_domain, safe='')}",
            request_options=request_options,
        )

    def get_session(
        self,
        session_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        """Public status of one payment session (support/reporting).

        The response is the same public-safe shape the hosted payment page
        consumes: status, amount, currency, available methods, reject reason.
        """
        return self._http.get(
            f"/platforms/shopify/sessions/{quote(session_id, safe='')}",
            request_options=request_options,
        )
