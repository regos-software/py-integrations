from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, AddResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.common.sort_orders import SortOrders
from schemas.api.references.fields import FieldValueAdd

from .partner_group import PartnerGroup


class LegalStatus(str, Enum):
    """Partner legal status."""

    Legal = "Legal"
    Natural = "Natural"


def _normalize_legal_status(value):
    if isinstance(value, LegalStatus) or value is None:
        return value
    if isinstance(value, int):
        return {1: LegalStatus.Legal, 2: LegalStatus.Natural}.get(value, value)
    if isinstance(value, str):
        normalized = value.strip()
        for item in LegalStatus:
            if item.value.lower() == normalized.lower():
                return item
    return value


class Partner(BaseSchema):
    """Partner read model."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Partner id.")
    group: Optional[PartnerGroup] = PydField(default=None, description="Partner group.")
    legal_status: LegalStatus = PydField(..., description="Legal status.")
    name: str = PydField(..., description="Partner name.")
    fullname: Optional[str] = PydField(default=None, description="Full name.")
    boss_name: Optional[str] = PydField(default=None, description="Manager name.")
    address: Optional[str] = PydField(default=None, description="Address.")
    phones: Optional[str] = PydField(default=None, description="Phones.")
    email: Optional[str] = PydField(default=None, description="Email.")
    description: Optional[str] = PydField(default=None, description="Description.")
    inn: Optional[str] = PydField(default=None, description="Taxpayer id.")
    bank_name: Optional[str] = PydField(default=None, description="Bank name.")
    mfo: Optional[str] = PydField(default=None, description="Bank MFO.")
    rs: Optional[str] = PydField(default=None, description="Bank account.")
    oked: Optional[str] = PydField(default=None, description="OKED.")
    vat_index: Optional[str] = PydField(default=None, description="VAT index.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")

    @field_validator("legal_status", mode="before")
    @classmethod
    def _normalize_legal_status(cls, value):
        return _normalize_legal_status(value)

    @field_validator(
        "name",
        "fullname",
        "boss_name",
        "address",
        "phones",
        "email",
        "description",
        "inn",
        "bank_name",
        "mfo",
        "rs",
        "oked",
        "vat_index",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class PartnerGetRequest(BaseSchema):
    """Request for Partner/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Partner ids.")
    group_ids: Optional[List[int]] = PydField(default=None, description="Partner group ids.")
    legal_status: Optional[LegalStatus] = PydField(default=None, description="Legal status.")
    legal_statuses: Optional[List[LegalStatus]] = PydField(
        default=None,
        description="Legacy plural legal status filter.",
    )
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sort orders.")
    filters: Optional[List[Filter]] = PydField(default=None, description="Additional filters.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Limit.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Offset.")

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    @field_validator("legal_status", mode="before")
    @classmethod
    def _normalize_legal_status(cls, value):
        return _normalize_legal_status(value)

    @field_validator("legal_statuses", mode="before")
    @classmethod
    def _normalize_legal_statuses(cls, value):
        if value is None:
            return value
        return [_normalize_legal_status(item) for item in value]


class PartnerGetResponse(APIBaseResponse[List[Partner]]):
    """Response for Partner/Get."""

    model_config = ConfigDict(extra="ignore")


class PartnerAddRequest(BaseSchema):
    """Request for Partner/Add."""

    model_config = ConfigDict(extra="forbid")

    group_id: int = PydField(default=1, ge=0, description="Partner group id.")
    legal_status: LegalStatus = PydField(default=LegalStatus.Legal, description="Legal status.")
    name: str = PydField(..., min_length=1, description="Partner name.")
    fullname: Optional[str] = PydField(default=None, description="Full name.")
    boss_name: Optional[str] = PydField(default=None, description="Manager name.")
    address: Optional[str] = PydField(default=None, description="Address.")
    phones: Optional[str] = PydField(default=None, description="Phones.")
    email: Optional[str] = PydField(default=None, description="Email.")
    description: Optional[str] = PydField(default=None, description="Description.")
    inn: Optional[str] = PydField(default=None, description="Taxpayer id.")
    bank_name: Optional[str] = PydField(default=None, description="Bank name.")
    mfo: Optional[str] = PydField(default=None, description="Bank MFO.")
    rs: Optional[str] = PydField(default=None, description="Bank account.")
    oked: Optional[str] = PydField(default=None, description="OKED.")
    vat_index: Optional[str] = PydField(default=None, description="VAT index.")
    fields: Optional[List[FieldValueAdd]] = PydField(default=None, description="Custom fields.")

    @field_validator("legal_status", mode="before")
    @classmethod
    def _normalize_legal_status(cls, value):
        return _normalize_legal_status(value)

    @field_validator(
        "name",
        "fullname",
        "boss_name",
        "address",
        "phones",
        "email",
        "description",
        "inn",
        "bank_name",
        "mfo",
        "rs",
        "oked",
        "vat_index",
        mode="before",
    )
    @classmethod
    def _strip_add_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class PartnerAddResponse(APIBaseResponse[AddResult]):
    """Response for Partner/Add."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "LegalStatus",
    "Partner",
    "PartnerAddRequest",
    "PartnerAddResponse",
    "PartnerGetRequest",
    "PartnerGetResponse",
]
