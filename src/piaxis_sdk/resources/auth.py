from __future__ import annotations

from urllib.parse import urlencode
from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import OAuthAuthorizeParams, PiaxisRequestOptions, TokenExchangeInput


class AuthResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def build_authorize_url(self, params: OAuthAuthorizeParams) -> str:
        query = urlencode(
            {
                "merchant_id": params["merchant_id"],
                "external_user_id": params["external_user_id"],
                "redirect_uri": params["redirect_uri"],
            }
        )
        return f"{self._http._base_url}/authorize?{query}"

    def authorize_test(
        self,
        params: OAuthAuthorizeParams,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        headers = dict(request_options["headers"]) if request_options and "headers" in request_options else {}
        headers["x-test-request"] = "true"
        options = dict(request_options or {})
        options["headers"] = headers
        return self._http.get(
            "/authorize",
            query={
                "merchant_id": params["merchant_id"],
                "external_user_id": params["external_user_id"],
                "redirect_uri": params["redirect_uri"],
            },
            request_options=options,
        )

    def exchange_token(
        self,
        payload: TokenExchangeInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/token",
            query={
                "grant_type": payload.get("grant_type", "authorization_code"),
                "code": payload["code"],
                "redirect_uri": payload["redirect_uri"],
                "client_id": payload["client_id"],
                "client_secret": payload["client_secret"],
            },
            request_options=request_options,
        )
