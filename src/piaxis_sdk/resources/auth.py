from __future__ import annotations

from urllib.parse import urlencode, urlparse
from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import OAuthAuthorizeParams, PiaxisRequestOptions, TokenExchangeInput


class AuthResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def build_authorize_url(self, params: OAuthAuthorizeParams) -> str:
        self._validate_redirect_uri(params["redirect_uri"])
        query = urlencode(
            {
                "merchant_id": params["merchant_id"],
                "external_user_id": params["external_user_id"],
                "redirect_uri": params["redirect_uri"],
                "state": params.get("state"),
                "code_challenge": params.get("code_challenge"),
                "code_challenge_method": params.get("code_challenge_method"),
            }
        )
        return f"{self._http._base_url}/authorize?{query}"

    def authorize_test(
        self,
        params: OAuthAuthorizeParams,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        self._validate_redirect_uri(params["redirect_uri"])
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
                "state": params.get("state"),
                "code_challenge": params.get("code_challenge"),
                "code_challenge_method": params.get("code_challenge_method"),
            },
            request_options=options,
        )

    def exchange_token(
        self,
        payload: TokenExchangeInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        self._validate_redirect_uri(payload["redirect_uri"])
        return self._http.post_form(
            "/token",
            form={
                "grant_type": payload.get("grant_type", "authorization_code"),
                "code": payload["code"],
                "redirect_uri": payload["redirect_uri"],
                "client_id": payload["client_id"],
                "client_secret": payload["client_secret"],
                "code_verifier": payload.get("code_verifier"),
            },
            request_options=request_options,
        )

    def refresh_token(
        self,
        payload: TokenExchangeInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post_form(
            "/token",
            form={
                "grant_type": "refresh_token",
                "refresh_token": payload["refresh_token"],
                "client_id": payload["client_id"],
                "client_secret": payload["client_secret"],
            },
            request_options=request_options,
        )

    def _validate_redirect_uri(self, redirect_uri: str) -> None:
        parsed = urlparse(redirect_uri)
        localhost_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme == "https":
            return
        if parsed.scheme == "http" and parsed.hostname in localhost_hosts:
            return
        raise ValueError("redirect_uri must use HTTPS unless targeting localhost.")
