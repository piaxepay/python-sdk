from __future__ import annotations

import os
from typing import Any, Mapping

from .http_client import PiaxisHttpClient
from .resources.auth import AuthResource
from .resources.disbursements import DisbursementsResource
from .resources.escrows import EscrowsResource
from .resources.escrow_disbursements import EscrowDisbursementsResource
from .resources.otp import OtpResource
from .resources.payments import PaymentsResource
from .types import (
    DisbursementCreateInput,
    DisbursementRecipientInput,
    EscrowCreateInput,
    EscrowDisputeInput,
    EscrowDisbursementCreateInput,
    EscrowDisbursementRecipientInput,
    EscrowReleaseInput,
    FulfillEscrowTermInput,
    MerchantPaymentsListParams,
    OAuthAuthorizeParams,
    PaymentCreateInput,
    PiaxisRequestOptions,
    RequestOtpInput,
    ReverseEscrowInput,
    TokenExchangeInput,
    UserLocationInput,
)

DEFAULT_BASE_URL = "https://api.gopiaxis.com/api"


class PiaxisClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        app_name: str | None = None,
        app_version: str | None = None,
    ) -> None:
        self._http = PiaxisHttpClient(
            base_url=base_url,
            api_key=api_key,
            access_token=access_token,
            timeout=timeout,
            app_name=app_name,
            app_version=app_version,
        )
        self.auth = AuthResource(self._http)
        self.escrows = EscrowsResource(self._http)
        self.disbursements = DisbursementsResource(self._http)
        self.otp = OtpResource(self._http)
        self.payments = PaymentsResource(self._http)
        self.escrow_disbursements = EscrowDisbursementsResource(self._http)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        **overrides: Any,
    ) -> "PiaxisClient":
        source = env or os.environ
        api_key = source.get("PIAXIS_API_KEY")
        access_token = source.get("PIAXIS_ACCESS_TOKEN")
        base_url = source.get("PIAXIS_API_BASE_URL", DEFAULT_BASE_URL)

        if not api_key and not access_token:
            raise ValueError(
                "Set PIAXIS_API_KEY or PIAXIS_ACCESS_TOKEN before calling PiaxisClient.from_env()."
            )

        return cls(
            api_key=api_key,
            access_token=access_token,
            base_url=base_url,
            **overrides,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "PiaxisClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def disburse(
        self,
        *,
        recipients: list[DisbursementRecipientInput],
        currency: str,
        payment_method: str,
        description: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        payload: DisbursementCreateInput = {
            "recipients": recipients,
            "currency": currency,
            "payment_method": payment_method,
        }
        if description is not None:
            payload["description"] = description
        return self.disbursements.create(payload, request_options=request_options)

    def escrow_disburse(
        self,
        *,
        recipients: list[EscrowDisbursementRecipientInput],
        currency: str,
        payment_method: str,
        description: str | None = None,
        user_location: UserLocationInput | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        payload: EscrowDisbursementCreateInput = {
            "recipients": recipients,
            "currency": currency,
            "payment_method": payment_method,
        }
        if description is not None:
            payload["description"] = description
        if user_location is not None:
            payload["user_location"] = user_location
        return self.escrow_disbursements.create(payload, request_options=request_options)

    def build_authorize_url(
        self,
        *,
        merchant_id: str,
        external_user_id: str,
        redirect_uri: str,
    ) -> str:
        payload: OAuthAuthorizeParams = {
            "merchant_id": merchant_id,
            "external_user_id": external_user_id,
            "redirect_uri": redirect_uri,
        }
        return self.auth.build_authorize_url(payload)

    def authorize_test(
        self,
        *,
        merchant_id: str,
        external_user_id: str,
        redirect_uri: str,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        payload: OAuthAuthorizeParams = {
            "merchant_id": merchant_id,
            "external_user_id": external_user_id,
            "redirect_uri": redirect_uri,
        }
        return self.auth.authorize_test(payload, request_options=request_options)

    def exchange_token(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        grant_type: str = "authorization_code",
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        payload: TokenExchangeInput = {
            "grant_type": grant_type,
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        return self.auth.exchange_token(payload, request_options=request_options)

    def create_escrow(
        self,
        payload: EscrowCreateInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.create(payload, request_options=request_options)

    def get_escrow(
        self,
        escrow_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.get(escrow_id, request_options=request_options)

    def get_escrow_status(
        self,
        escrow_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.status(escrow_id, request_options=request_options)

    def release_escrow(
        self,
        escrow_id: str,
        *,
        payload: EscrowReleaseInput | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.release(
            escrow_id,
            payload=payload,
            request_options=request_options,
        )

    def fulfill_escrow_term(
        self,
        escrow_id: str,
        term_id: str,
        payload: FulfillEscrowTermInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.fulfill_term(
            escrow_id,
            term_id,
            payload,
            request_options=request_options,
        )

    def reverse_escrow(
        self,
        escrow_id: str,
        payload: ReverseEscrowInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.reverse(
            escrow_id,
            payload,
            request_options=request_options,
        )

    def dispute_escrow(
        self,
        escrow_id: str,
        payload: EscrowDisputeInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrows.dispute(
            escrow_id,
            payload,
            request_options=request_options,
        )

    def request_otp(
        self,
        payload: RequestOtpInput,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.otp.request(payload, request_options=request_options)

    def create_payment(
        self,
        payload: PaymentCreateInput,
        *,
        mfa_code: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.payments.create(
            payload,
            mfa_code=mfa_code,
            request_options=request_options,
        )

    def get_payment(
        self,
        payment_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.payments.get(payment_id, request_options=request_options)

    def list_merchant_payments(
        self,
        params: MerchantPaymentsListParams | None = None,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.payments.list(params, request_options=request_options)

    def get_disbursement(
        self,
        disbursement_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.disbursements.get(
            disbursement_id,
            request_options=request_options,
        )

    def list_disbursements(
        self,
        *,
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.disbursements.list(
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
            request_options=request_options,
        )

    def cancel_disbursement(
        self,
        disbursement_id: str,
        *,
        reason: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.disbursements.cancel(
            disbursement_id,
            reason=reason,
            request_options=request_options,
        )

    def get_escrow_disbursement(
        self,
        disbursement_id: str,
        *,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrow_disbursements.get(
            disbursement_id,
            request_options=request_options,
        )

    def list_escrow_disbursements(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrow_disbursements.list(
            status=status,
            limit=limit,
            offset=offset,
            request_options=request_options,
        )

    def release_escrow_disbursement(
        self,
        disbursement_id: str,
        *,
        force: bool = True,
        reason: str | None = None,
        escrow_ids: list[str] | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrow_disbursements.release(
            disbursement_id,
            force=force,
            reason=reason,
            escrow_ids=escrow_ids,
            request_options=request_options,
        )

    def cancel_escrow_disbursement(
        self,
        disbursement_id: str,
        *,
        reason: str | None = None,
        request_options: PiaxisRequestOptions | None = None,
    ) -> Any:
        return self.escrow_disbursements.cancel(
            disbursement_id,
            reason=reason,
            request_options=request_options,
        )
