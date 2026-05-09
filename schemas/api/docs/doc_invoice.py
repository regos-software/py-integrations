from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator, model_validator

from schemas.api.base import APIBaseResponse, AddResult, BaseSchema
from schemas.api.common.sort_orders import SortOrders
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner
from schemas.api.references.tax import VatCalculationType


class DocInvoiceType(str, Enum):
    """Invoice document type."""

    Default = "Default"
    Income = "Income"
    Outcome = "Outcome"
    Corrective = "Corrective"


class DocInvoiceStatus(str, Enum):
    """Invoice exchange status."""

    Default = "Default"
    New = "New"
    InSentProgress = "InSentProgress"
    Sent = "Sent"
    InReceivedProgress = "InReceivedProgress"
    Received = "Received"
    ErrorSent = "ErrorSent"
    ErrorReceived = "ErrorReceived"
    Unknown = "Unknown"


def _normalize_invoice_type(value):
    if isinstance(value, DocInvoiceType) or value is None:
        return value
    if isinstance(value, int):
        return {
            0: DocInvoiceType.Default,
            1: DocInvoiceType.Income,
            2: DocInvoiceType.Outcome,
            3: DocInvoiceType.Corrective,
        }.get(value, value)
    if isinstance(value, str):
        normalized = value.strip()
        for item in DocInvoiceType:
            if item.value.lower() == normalized.lower():
                return item
    return value


def _normalize_invoice_status(value):
    if isinstance(value, DocInvoiceStatus) or value is None:
        return value
    if isinstance(value, int):
        return {
            0: DocInvoiceStatus.Default,
            1: DocInvoiceStatus.New,
            2: DocInvoiceStatus.InSentProgress,
            3: DocInvoiceStatus.Sent,
            4: DocInvoiceStatus.InReceivedProgress,
            5: DocInvoiceStatus.Received,
            6: DocInvoiceStatus.ErrorSent,
            7: DocInvoiceStatus.ErrorReceived,
            8: DocInvoiceStatus.Unknown,
        }.get(value, value)
    if isinstance(value, str):
        normalized = value.strip()
        for item in DocInvoiceStatus:
            if item.value.lower() == normalized.lower():
                return item
    return value


class DocInvoice(BaseSchema):
    """Invoice read model."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Invoice id.")
    date: Optional[int] = PydField(default=None, ge=0, description="Date.")
    code: Optional[str] = PydField(default=None, description="Invoice code.")
    invoice_type: Optional[DocInvoiceType] = PydField(default=None, description="Invoice type.")
    corrected_date: Optional[int] = PydField(default=None, ge=0, description="Corrected date.")
    corrected_code: Optional[str] = PydField(default=None, description="Corrected code.")
    contract: Optional[DocContractShort] = PydField(default=None, description="Contract.")
    firm: Optional[Firm] = PydField(default=None, description="Firm.")
    partner: Optional[Partner] = PydField(default=None, description="Partner.")
    currency: Optional[Currency] = PydField(default=None, description="Currency.")
    exchange_rate: Optional[Decimal] = PydField(default=None, description="Exchange rate.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    vat_calculation_type: Optional[VatCalculationType] = PydField(default=None, description="VAT type.")
    attached_user: Optional[User] = PydField(default=None, description="Attached user.")
    base_document_id: Optional[int] = PydField(default=None, description="Base document id.")
    document_type: Optional[int] = PydField(default=None, description="Base document type.")
    positive: Optional[bool] = PydField(default=None, description="Positive flag.")
    description: Optional[str] = PydField(default=None, description="Description.")
    uuid: Optional[str] = PydField(default=None, description="UUID.")
    external_code: Optional[str] = PydField(default=None, description="External code.")
    status: Optional[DocInvoiceStatus] = PydField(default=None, description="Exchange status.")
    error: Optional[str] = PydField(default=None, description="Exchange error.")
    blocked: Optional[bool] = PydField(default=None, description="Blocked flag.")
    current_user_blocked: Optional[bool] = PydField(default=None, description="Current user blocked flag.")
    performed: Optional[bool] = PydField(default=None, description="Performed flag.")
    sent: Optional[bool] = PydField(default=None, description="Sent flag.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")

    @field_validator("invoice_type", mode="before")
    @classmethod
    def _normalize_invoice_type(cls, value):
        return _normalize_invoice_type(value)

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value):
        return _normalize_invoice_status(value)


class DocInvoiceGetRequest(BaseSchema):
    """Request for DocInvoice/Get."""

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[int] = PydField(default=None, ge=0, description="Start date.")
    end_date: Optional[int] = PydField(default=None, ge=0, description="End date.")
    invoice_type: Optional[DocInvoiceType] = PydField(default=None, description="Invoice type.")
    ids: Optional[List[int]] = PydField(default=None, description="Invoice ids.")
    contract_ids: Optional[List[int]] = PydField(default=None, description="Contract ids.")
    firm_ids: Optional[List[int]] = PydField(default=None, description="Firm ids.")
    partner_ids: Optional[List[int]] = PydField(default=None, description="Partner ids.")
    attached_user_ids: Optional[List[int]] = PydField(default=None, description="Attached user ids.")
    performed: Optional[bool] = PydField(default=None, description="Performed flag.")
    blocked: Optional[bool] = PydField(default=None, description="Blocked flag.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    vat_calculation_type: Optional[VatCalculationType] = PydField(default=None, description="VAT type.")
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sort orders.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    limit: Optional[int] = PydField(default=None, ge=1, le=10000, description="Limit.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Offset.")

    @field_validator("invoice_type", mode="before")
    @classmethod
    def _normalize_invoice_type(cls, value):
        return _normalize_invoice_type(value)

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be less than start_date")
        return self


class DocInvoiceAddRequest(BaseSchema):
    """Request for DocInvoice/Add."""

    model_config = ConfigDict(extra="forbid")

    code: Optional[str] = PydField(default=None, description="Invoice code.")
    date: int = PydField(..., ge=0, description="Date.")
    corrected_date: Optional[int] = PydField(default=None, ge=0, description="Corrected date.")
    corrected_code: Optional[str] = PydField(default=None, description="Corrected code.")
    document_id: Optional[int] = PydField(default=None, ge=1, description="Base document id.")
    document_type_id: Optional[int] = PydField(default=None, ge=1, description="Base document type id.")
    contract_id: int = PydField(..., ge=1, description="Contract id.")
    firm_id: int = PydField(..., ge=1, description="Firm id.")
    partner_id: int = PydField(..., ge=1, description="Partner id.")
    currency_id: int = PydField(..., ge=1, description="Currency id.")
    exchange_rate: Optional[Decimal] = PydField(default=None, description="Exchange rate.")
    description: Optional[str] = PydField(default=None, description="Description.")
    positive: Optional[bool] = PydField(default=None, description="Positive flag.")
    invoice_type: Optional[DocInvoiceType] = PydField(default=None, description="Invoice type.")
    vat_calculation_type: Optional[VatCalculationType] = PydField(default=None, description="VAT type.")
    attached_user_id: Optional[int] = PydField(default=None, ge=1, description="Attached user id.")

    @field_validator("invoice_type", mode="before")
    @classmethod
    def _normalize_invoice_type(cls, value):
        return _normalize_invoice_type(value)


class DocInvoiceSetStatusRequest(BaseSchema):
    """Request for DocInvoice/SetStatus."""

    model_config = ConfigDict(extra="forbid")

    document_id: int = PydField(..., ge=1, description="Invoice id.")
    status: DocInvoiceStatus = PydField(..., description="Exchange status.")
    error_message: Optional[str] = PydField(default=None, description="Error message.")

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value):
        return _normalize_invoice_status(value)


class DocInvoiceSetExternalDataRequest(BaseSchema):
    """Request for DocInvoice/SetExternalData."""

    model_config = ConfigDict(extra="forbid")

    document_id: int = PydField(..., ge=1, description="Invoice id.")
    external_id: Optional[str] = PydField(default=None, description="External id.")
    integration_key: Optional[str] = PydField(default=None, description="Legacy integration key.")
    connected_integration_id: Optional[str] = PydField(default=None, description="Connected integration id.")
    roaming_id: Optional[str] = PydField(default=None, description="Roaming id.")

    @field_validator("external_id", "integration_key", "connected_integration_id", "roaming_id", mode="before")
    @classmethod
    def _strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _validate_integration_id(self):
        if not self.connected_integration_id and not self.integration_key:
            raise ValueError("connected_integration_id or integration_key is required")
        return self


class DocInvoiceGetResponse(APIBaseResponse[List[DocInvoice]]):
    """Response for DocInvoice/Get."""

    model_config = ConfigDict(extra="ignore")


class DocInvoiceAddResponse(APIBaseResponse[AddResult]):
    """Response for DocInvoice/Add."""

    model_config = ConfigDict(extra="ignore")


class DocInvoiceActionResponse(APIBaseResponse[Dict[str, Any]]):
    """Response for DocInvoice state-changing endpoints."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "DocInvoice",
    "DocInvoiceActionResponse",
    "DocInvoiceAddRequest",
    "DocInvoiceAddResponse",
    "DocInvoiceGetRequest",
    "DocInvoiceGetResponse",
    "DocInvoiceSetExternalDataRequest",
    "DocInvoiceSetStatusRequest",
    "DocInvoiceStatus",
    "DocInvoiceType",
]
