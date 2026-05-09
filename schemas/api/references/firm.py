from __future__ import annotations

from typing import List, Optional

from pydantic import AliasChoices, ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders

from .firm_group import FirmGroup


class Firm(BaseSchema):
    """Firm read model returned by RegosAPI."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Firm id.")
    group: Optional[FirmGroup] = PydField(default=None, description="Firm group.")
    name: Optional[str] = PydField(default=None, description="Firm name.")
    full_name: Optional[str] = PydField(
        default=None,
        validation_alias=AliasChoices("full_name", "fullname", "fullName"),
        description="Firm full name.",
    )
    boss_name: Optional[str] = PydField(default=None, description="Manager name.")
    address: Optional[str] = PydField(default=None, description="Address.")
    phones: Optional[str] = PydField(default=None, description="Phones.")
    description: Optional[str] = PydField(default=None, description="Description.")
    inn: Optional[str] = PydField(default=None, description="Taxpayer id.")
    bank_name: Optional[str] = PydField(default=None, description="Bank name.")
    mfo: Optional[str] = PydField(default=None, description="Bank MFO.")
    rs: Optional[str] = PydField(default=None, description="Bank account.")
    oked: Optional[str] = PydField(default=None, description="OKED.")
    vat_index: Optional[str] = PydField(default=None, description="VAT index.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")

    @property
    def fullname(self) -> Optional[str]:
        return self.full_name

    @field_validator(
        "name",
        "full_name",
        "boss_name",
        "address",
        "phones",
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


class FirmGetRequest(BaseSchema):
    """Request for Firm/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Firm ids.")
    group_ids: Optional[List[int]] = PydField(default=None, description="Firm group ids.")
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sort orders.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    limit: Optional[int] = PydField(default=None, ge=1, le=10000, description="Limit.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Offset.")

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class FirmGetResponse(APIBaseResponse[List[Firm]]):
    """Response for Firm/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Firm",
    "FirmGetRequest",
    "FirmGetResponse",
]
