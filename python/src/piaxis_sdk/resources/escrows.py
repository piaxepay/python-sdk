from __future__ import annotations

from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import (
    EscrowCreateInput,
    EscrowDisputeInput,
    EscrowReleaseInput,
    FulfillEscrowTermInput,
    PiaxisRequestOptions,
    ReverseEscrowInput,
)


class EscrowsResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def create(
        self,
        payload: EscrowCreateInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/escrows/",
            body=payload,
            request_options=request_options,
        )

    def get(
        self,
        escrow_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            f"/escrows/{escrow_id}",
            request_options=request_options,
        )

    def status(
        self,
        escrow_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            f"/escrows/{escrow_id}/status",
            request_options=request_options,
        )

    def release(
        self,
        escrow_id: str,
        *,
        payload: EscrowReleaseInput | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            f"/escrows/{escrow_id}/release",
            body=payload or {},
            request_options=request_options,
        )

    def fulfill_term(
        self,
        escrow_id: str,
        term_id: str,
        payload: FulfillEscrowTermInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        resolved_payload = dict(payload)
        resolved_payload.setdefault("term_id", term_id)
        return self._http.post(
            f"/escrows/{escrow_id}/terms/{term_id}/fulfill",
            body=resolved_payload,
            request_options=request_options,
        )

    def reverse(
        self,
        escrow_id: str,
        payload: ReverseEscrowInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            f"/escrows/{escrow_id}/reverse",
            body=payload,
            request_options=request_options,
        )

    def dispute(
        self,
        escrow_id: str,
        payload: EscrowDisputeInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            f"/escrows/{escrow_id}/disputes",
            body=payload,
            request_options=request_options,
        )
