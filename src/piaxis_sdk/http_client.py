from __future__ import annotations

from typing import Any, Mapping

import httpx

from .errors import PiaxisApiError
from .types import PiaxisRequestOptions


class PiaxisHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: float = 30.0,
        app_name: str | None = None,
        app_version: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._access_token = access_token
        self._default_timeout = timeout
        self._app_name = app_name
        self._app_version = app_version
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def get(
        self,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.request(
            "GET",
            path,
            query=query,
            request_options=request_options,
        )

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        query: Mapping[str, Any] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.request(
            "POST",
            path,
            body=body,
            query=query,
            request_options=request_options,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        headers = self._build_headers(request_options.get("headers") if request_options else None)
        timeout = request_options.get("timeout", self._default_timeout) if request_options else None
        normalized_path = path if path.startswith("/") else f"/{path}"

        response = self._client.request(
            method,
            normalized_path,
            params=self._compact_query(query),
            json=body,
            headers=headers,
            timeout=timeout,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.is_error:
            raise PiaxisApiError.from_response(
                status_code=response.status_code,
                payload=payload,
                request_id=response.headers.get("x-request-id"),
            )

        return payload

    def _build_headers(self, headers: Mapping[str, str] | None = None) -> dict[str, str]:
        merged = {
            "Accept": "application/json",
        }

        if headers:
            merged.update(dict(headers))

        if self._api_key:
            merged["api-key"] = self._api_key

        if self._access_token:
            token = (
                self._access_token
                if self._access_token.startswith("Bearer ")
                else f"Bearer {self._access_token}"
            )
            merged["Authorization"] = token

        if self._app_name:
            version_suffix = f"/{self._app_version}" if self._app_version else ""
            merged["x-piaxis-sdk-client"] = f"{self._app_name}{version_suffix}"

        return merged

    def _compact_query(self, query: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if not query:
            return None
        return {key: value for key, value in query.items() if value is not None}
