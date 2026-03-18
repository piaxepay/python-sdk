from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PiaxisApiError(Exception):
    message: str
    status_code: int
    code: str | None = None
    details: Any = None
    request_id: str | None = None

    def __str__(self) -> str:
        return self.message

    @classmethod
    def from_response(
        cls,
        *,
        status_code: int,
        payload: Any,
        request_id: str | None = None,
    ) -> "PiaxisApiError":
        detail = payload.get("detail", payload) if isinstance(payload, dict) else payload

        if isinstance(detail, str):
            return cls(
                message=detail,
                status_code=status_code,
                details=payload,
                request_id=request_id,
            )

        if isinstance(detail, dict):
            code = detail.get("code")
            message = detail.get("message") or f"Request failed with status {status_code}"
            return cls(
                message=str(message),
                status_code=status_code,
                code=str(code) if code is not None else None,
                details=payload,
                request_id=request_id,
            )

        return cls(
            message=f"Request failed with status {status_code}",
            status_code=status_code,
            details=payload,
            request_id=request_id,
        )
