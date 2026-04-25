from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping, TypedDict

Amount = int | float | str | Decimal
PaymentMethod = str


class PiaxisRequestOptions(TypedDict, total=False):
    headers: Mapping[str, str]
    timeout: float


class TermInput(TypedDict, total=False):
    type: str
    data: dict[str, Any]
    expiry_date: str | None


class EscrowAllocationInput(TypedDict, total=False):
    allocation_key: str
    amount: Amount
    seller_reference: str
    description: str
    metadata: dict[str, Any]


class DisbursementRecipientInput(TypedDict, total=False):
    recipient_id: str
    email: str
    phone_number: str
    amount: Amount
    reference: str


class UserLocationInput(TypedDict):
    latitude: float
    longitude: float


class OAuthAuthorizeParams(TypedDict):
    merchant_id: str
    external_user_id: str
    redirect_uri: str
    state: str | None
    code_challenge: str | None
    code_challenge_method: str | None


class TokenExchangeInput(TypedDict, total=False):
    grant_type: str
    code: str
    redirect_uri: str
    client_id: str
    client_secret: str
    code_verifier: str
    refresh_token: str


class EscrowCreateInput(TypedDict, total=False):
    receiver_id: str
    amount: Amount
    currency_code: str
    payment_method: PaymentMethod
    terms: list["TermInput"]
    external_user_id: str
    user_info: dict[str, Any]
    user_location: UserLocationInput
    external_order_id: str
    allocations: list[EscrowAllocationInput]
    metadata: dict[str, Any]


class EscrowReleaseInput(TypedDict, total=False):
    verification_code: str
    verification_method: str
    user_info: dict[str, Any]
    amount: Amount
    allocation_keys: list[str]
    force: bool
    reason: str


class FulfillEscrowTermInput(TypedDict, total=False):
    term_id: str
    term_type: str
    data: dict[str, Any]
    user_info: dict[str, Any]


class ReverseEscrowInput(TypedDict, total=False):
    reason: str
    verification_code: str
    verification_method: str
    user_info: dict[str, Any]
    amount: Amount
    allocation_keys: list[str]


class EscrowDisputeInput(TypedDict, total=False):
    reason: str
    initiator_role: str
    user_info: dict[str, Any]


class RequestOtpInput(TypedDict, total=False):
    email: str
    phone_number: str


class PaymentCreateInput(TypedDict, total=False):
    amount: Amount
    currency: str
    payment_method: PaymentMethod
    recipient_id: str
    user_info: dict[str, Any]
    products: list[dict[str, Any]]
    customer_pays_fees: bool


class MerchantPaymentsListParams(TypedDict, total=False):
    status: str
    payment_method: str
    from_date: str
    to_date: str
    limit: int
    offset: int


class DisbursementCreateInput(TypedDict, total=False):
    recipients: list[DisbursementRecipientInput]
    currency: str
    payment_method: PaymentMethod
    description: str


class EscrowDisbursementRecipientInput(TypedDict, total=False):
    recipient_id: str
    email: str
    phone_number: str
    amount: Amount
    terms: list[TermInput]
    reference: str


class EscrowDisbursementCreateInput(TypedDict, total=False):
    recipients: list[EscrowDisbursementRecipientInput]
    currency: str
    payment_method: PaymentMethod
    description: str
    user_location: UserLocationInput
