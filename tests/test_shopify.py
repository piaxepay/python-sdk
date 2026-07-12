from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from piaxis_sdk import PiaxisClient  # noqa: E402

from test_contract import FakeHttpxClient  # noqa: E402


class ShopifyHelpersTest(unittest.TestCase):
    def _client(self, responses: list[dict]) -> tuple[PiaxisClient, FakeHttpxClient]:
        client = PiaxisClient(
            api_key="key", base_url="https://sandbox.api.gopiaxis.com/api"
        )
        fake = FakeHttpxClient(responses)
        client._http._client = fake
        return client, fake

    def test_connect_posts_payload_and_returns_install_url(self) -> None:
        client, fake = self._client(
            [
                {
                    "install_url": "https://demo.myshopify.com/admin/oauth/authorize?x=1",
                    "shop_domain": "demo.myshopify.com",
                    "payment_mode": "escrow",
                }
            ]
        )
        result = client.connect_shopify(
            {
                "store_id": "store-1",
                "shop_domain": "demo.myshopify.com",
                "payment_mode": "escrow",
            }
        )
        call = fake.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/platforms/shopify/connect")
        self.assertEqual(call["json"]["shop_domain"], "demo.myshopify.com")
        self.assertEqual(call["json"]["payment_mode"], "escrow")
        self.assertIn("admin/oauth/authorize", result["install_url"])

    def test_disconnect_deletes_shop_path(self) -> None:
        client, fake = self._client(
            [{"shop_domain": "demo.myshopify.com", "status": "disabled"}]
        )
        result = client.disconnect_shopify("demo.myshopify.com")
        call = fake.calls[0]
        self.assertEqual(call["method"], "DELETE")
        self.assertEqual(call["path"], "/platforms/shopify/connect/demo.myshopify.com")
        self.assertEqual(result["status"], "disabled")

    def test_get_session_returns_public_shape(self) -> None:
        client, fake = self._client(
            [
                {
                    "session_id": "s-1",
                    "status": "resolved",
                    "amount": "10000.00",
                    "currency": "UGX",
                    "methods": [],
                    "reject_reason": None,
                }
            ]
        )
        result = client.get_shopify_session("s-1")
        call = fake.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["path"], "/platforms/shopify/sessions/s-1")
        self.assertEqual(result["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
