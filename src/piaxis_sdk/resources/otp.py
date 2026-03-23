from __future__ import annotations

from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import PiaxisRequestOptions, RequestOtpInput


class OtpResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def request(
        self,
        payload: RequestOtpInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/request-otp",
            body=payload,
            request_options=request_options,
        )
