from __future__ import annotations

import traceback
from urllib.parse import urlparse, urlunparse
from typing import Any, Mapping

import httpx

from .errors import PiaxisApiError
from .types import PiaxisErrorReportingOptions, PiaxisRequestOptions


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
        error_reporting: PiaxisErrorReportingOptions | None = None,
    ) -> None:
        self._base_url = self._validate_base_url(base_url)
        self._api_key = api_key
        self._access_token = access_token
        self._piaxis_client_id = piaxis_client_id
        self._default_timeout = timeout
        self._app_name = app_name
        self._app_version = app_version
        self._error_reporting = error_reporting or {}
        self._error_reporting_endpoint = self._error_reporting.get(
            "endpoint",
            self._default_error_reporting_endpoint(self._base_url),
        )
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

        try:
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
        except Exception as exc:
            self._report_sdk_error(exc, method=method, path=normalized_path)
            raise

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

    def _report_sdk_error(self, exc: Exception, *, method: str, path: str) -> None:
        if not self._error_reporting.get("enabled"):
            return

        status_code = exc.status_code if isinstance(exc, PiaxisApiError) else None
        severity = "warning" if status_code is not None and status_code < 500 else "error"
        client_name = (
            f"{self._app_name}/{self._app_version}"
            if self._app_name and self._app_version
            else self._app_name or "piaxis-python-sdk"
        )
        stack = (
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if self._error_reporting.get("include_stack")
            else None
        )

        payload = {
            "source": "python_sdk",
            "severity": severity,
            "name": type(exc).__name__[:255],
            "message": str(exc)[:4000],
            "stack": stack[:20000] if stack else None,
            "path": path[:512],
            "platform": "python",
            "user_agent": client_name,
            "metadata": {
                **self._error_reporting.get("metadata", {}),
                "method": method,
                "status": status_code,
                "code": exc.code if isinstance(exc, PiaxisApiError) else None,
                "request_id": exc.request_id if isinstance(exc, PiaxisApiError) else None,
            },
        }

        try:
            self._client.post(
                self._error_reporting_endpoint,
                json=payload,
                headers={"Accept": "application/json"},
                timeout=2.0,
            )
        except Exception:
            return

    def _default_error_reporting_endpoint(self, base_url: str) -> str:
        parsed = urlparse(base_url)
        path = parsed.path.rstrip("/")
        if path.endswith("/api"):
            path = f"{path[:-4]}/monitoring/client-errors"
        else:
            path = "/monitoring/client-errors"
        return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
