from __future__ import annotations

from urllib.parse import urlparse
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
        piaxis_client_id: str | None = None,
        timeout: float = 30.0,
        app_name: str | None = None,
        app_version: str | None = None,
    ) -> None:
        self._base_url = self._validate_base_url(base_url)
        self._api_key = api_key
        self._access_token = access_token
        self._piaxis_client_id = piaxis_client_id
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

    def post_form(
        self,
        path: str,
        *,
        form: Mapping[str, Any],
        query: Mapping[str, Any] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.request(
            "POST",
            path,
            form=form,
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
        form: Mapping[str, Any] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        if body is not None and form is not None:
            raise ValueError("Only one of body or form may be supplied.")
        headers = self._build_headers(request_options.get("headers") if request_options else None)
        timeout = request_options.get("timeout", self._default_timeout) if request_options else None
        normalized_path = path if path.startswith("/") else f"/{path}"

        request_kwargs: dict[str, Any] = {
            "params": self._compact_query(query),
            "headers": headers,
            "timeout": timeout,
        }
        if form is not None:
            request_kwargs["data"] = self._compact_query(form)
        else:
            request_kwargs["json"] = body

        response = self._client.request(method, normalized_path, **request_kwargs)

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

        if self._piaxis_client_id:
            merged["X-piaxis-Client-ID"] = self._piaxis_client_id

        if self._app_name:
            version_suffix = f"/{self._app_version}" if self._app_version else ""
            merged["x-piaxis-sdk-client"] = f"{self._app_name}{version_suffix}"

        return merged

    def _validate_base_url(self, base_url: str) -> str:
        parsed = urlparse(base_url.rstrip("/"))
        if parsed.scheme == "https":
            return base_url.rstrip("/")

        localhost_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme == "http" and parsed.hostname in localhost_hosts:
            return base_url.rstrip("/")

        raise ValueError("PiaxisClient base_url must use HTTPS unless targeting localhost.")

    def _compact_query(self, query: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if not query:
            return None
        return {key: value for key, value in query.items() if value is not None}
