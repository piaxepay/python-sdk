from __future__ import annotations

from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import EscrowDisbursementCreateInput, PiaxisRequestOptions


class EscrowDisbursementsResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def create(
        self,
        payload: EscrowDisbursementCreateInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/escrow-disbursements",
            body=payload,
            request_options=request_options,
        )

    def get(
        self,
        disbursement_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            f"/escrow-disbursements/{disbursement_id}",
            request_options=request_options,
        )

    def list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            "/escrow-disbursements",
            query={
                "status": status,
                "limit": limit,
                "offset": offset,
            },
            request_options=request_options,
        )

    def release(
        self,
        disbursement_id: str,
        *,
        force: bool = False,
        reason: str | None = None,
        escrow_ids: list[str] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            f"/escrow-disbursements/{disbursement_id}/release",
            body={
                "force": force,
                "reason": reason,
                "escrow_ids": escrow_ids,
            },
            request_options=request_options,
        )

    def cancel(
        self,
        disbursement_id: str,
        *,
        reason: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            f"/escrow-disbursements/{disbursement_id}/cancel",
            body={"reason": reason},
            request_options=request_options,
        )
