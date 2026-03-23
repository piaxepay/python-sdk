from __future__ import annotations

from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import MerchantPaymentsListParams, PaymentCreateInput, PiaxisRequestOptions


class PaymentsResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def create(
        self,
        payload: PaymentCreateInput,
        *,
        mfa_code: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/payments/create",
            body=payload,
            query={"mfa_code": mfa_code},
            request_options=request_options,
        )

    def get(
        self,
        payment_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            f"/payments/{payment_id}",
            request_options=request_options,
        )

    def list(
        self,
        params: MerchantPaymentsListParams | None = None,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            "/merchant-payments",
            query=params or {},
            request_options=request_options,
        )
