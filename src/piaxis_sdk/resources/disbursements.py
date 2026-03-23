from __future__ import annotations

from typing import Any

from ..http_client import PiaxisHttpClient
from ..types import DisbursementCreateInput, PiaxisRequestOptions


class DisbursementsResource:
    def __init__(self, http_client: PiaxisHttpClient) -> None:
        self._http = http_client

    def create(
        self,
        payload: DisbursementCreateInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.post(
            "/disbursements",
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
            f"/disbursements/{disbursement_id}",
            request_options=request_options,
        )

    def list(
        self,
        *,
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self._http.get(
            "/disbursements",
            query={
                "status": status,
                "from_date": from_date,
                "to_date": to_date,
                "limit": limit,
                "offset": offset,
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
            f"/disbursements/{disbursement_id}/cancel",
            body={"reason": reason},
            request_options=request_options,
        )
