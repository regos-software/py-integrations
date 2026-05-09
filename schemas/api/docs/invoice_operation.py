from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.references.item import Item
from schemas.api.references.tax import VatCalculationType


class InvoiceOperation(BaseSchema):
    """Invoice operation read model."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Operation id.")
    document_id: int = PydField(..., ge=1, description="Invoice id.")
    item: Optional[Item] = PydField(default=None, description="Item.")
    quantity: Optional[Decimal] = PydField(default=None, description="Quantity.")
    price: Optional[Decimal] = PydField(default=None, description="Price.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    total: Optional[Decimal] = PydField(default=None, description="Total.")
    vat_value: Optional[Decimal] = PydField(default=None, description="VAT value.")
    vat_amount: Optional[Decimal] = PydField(default=None, description="VAT amount.")
    vat_calculation_type: Optional[VatCalculationType] = PydField(default=None, description="VAT type.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")


class InvoiceOperationGetRequest(BaseSchema):
    """Request for InvoiceOperation/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Operation ids.")
    item_ids: Optional[List[int]] = PydField(default=None, description="Item ids.")
    document_ids: List[int] = PydField(..., min_length=1, max_length=1, description="Invoice ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Limit.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Offset.")

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class InvoiceOperationAdd(BaseSchema):
    """Request row for InvoiceOperation/Add."""

    model_config = ConfigDict(extra="forbid")

    document_id: int = PydField(..., ge=1, description="Invoice id.")
    item_id: int = PydField(..., ge=1, description="Item id.")
    quantity: Optional[Decimal] = PydField(default=None, description="Quantity.")
    price: Optional[Decimal] = PydField(default=None, description="Price.")
    vat_value: Optional[Decimal] = PydField(default=None, description="VAT value.")


InvoiceOperationAddRequest = List[InvoiceOperationAdd]


class InvoiceOperationGetResponse(APIBaseResponse[List[InvoiceOperation]]):
    """Response for InvoiceOperation/Get."""

    model_config = ConfigDict(extra="ignore")


class InvoiceOperationAddResponse(APIBaseResponse[ArrayResult]):
    """Response for InvoiceOperation/Add."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "InvoiceOperation",
    "InvoiceOperationAdd",
    "InvoiceOperationAddRequest",
    "InvoiceOperationAddResponse",
    "InvoiceOperationGetRequest",
    "InvoiceOperationGetResponse",
]
