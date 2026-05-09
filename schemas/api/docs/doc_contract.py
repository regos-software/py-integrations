from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator, model_validator

from schemas.api.base import APIBaseResponse, AddResult, BaseSchema
from schemas.api.common.sort_orders import SortOrders
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner


class ContractDirection(str, Enum):
    """Contract direction."""

    All = "All"
    Income = "Income"
    Outcome = "Outcome"


def _normalize_contract_direction(value):
    if isinstance(value, ContractDirection) or value is None:
        return value
    if isinstance(value, int):
        return {0: ContractDirection.All, 1: ContractDirection.Income, 2: ContractDirection.Outcome}.get(value, value)
    if isinstance(value, str):
        normalized = value.strip()
        for item in ContractDirection:
            if item.value.lower() == normalized.lower():
                return item
    return value


class DocContract(BaseSchema):
    """Contract read model."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Contract id.")
    code: Optional[str] = PydField(default=None, description="Contract code.")
    name: Optional[str] = PydField(default=None, description="Contract name.")
    date: Optional[int] = PydField(default=None, ge=0, description="Contract date.")
    start_date: Optional[int] = PydField(default=None, ge=0, description="Start date.")
    end_date: Optional[int] = PydField(default=None, ge=0, description="End date.")
    partner: Optional[Partner] = PydField(default=None, description="Partner.")
    firm: Optional[Firm] = PydField(default=None, description="Firm.")
    direction: Optional[ContractDirection] = PydField(default=None, description="Direction.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    currency: Optional[Currency] = PydField(default=None, description="Currency.")
    details: Optional[str] = PydField(default=None, description="Details.")
    description: Optional[str] = PydField(default=None, description="Description.")
    attached_user: Optional[User] = PydField(default=None, description="Attached user.")
    active: Optional[bool] = PydField(default=None, description="Active flag.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, value):
        return _normalize_contract_direction(value)


class DocContractShort(BaseSchema):
    """Short contract read model."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Contract id.")
    code: Optional[str] = PydField(default=None, description="Contract code.")
    name: Optional[str] = PydField(default=None, description="Contract name.")
    date: Optional[int] = PydField(default=None, ge=0, description="Contract date.")
    start_date: Optional[int] = PydField(default=None, ge=0, description="Start date.")
    end_date: Optional[int] = PydField(default=None, ge=0, description="End date.")
    partner_id: Optional[int] = PydField(default=None, ge=1, description="Partner id.")
    partner_name: Optional[str] = PydField(default=None, description="Partner name.")
    firm_id: Optional[int] = PydField(default=None, ge=1, description="Firm id.")
    direction: Optional[ContractDirection] = PydField(default=None, description="Direction.")
    currency_id: Optional[int] = PydField(default=None, ge=1, description="Currency id.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    details: Optional[str] = PydField(default=None, description="Details.")
    description: Optional[str] = PydField(default=None, description="Description.")
    attached_user_id: Optional[int] = PydField(default=None, ge=1, description="Attached user id.")
    active: Optional[bool] = PydField(default=None, description="Active flag.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    last_update: Optional[int] = PydField(default=None, ge=0, description="Last update.")

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, value):
        return _normalize_contract_direction(value)


class DocContractGetRequest(BaseSchema):
    """Request for DocContract/Get and DocContract/GetShort."""

    model_config = ConfigDict(extra="forbid")

    direction: Optional[ContractDirection] = PydField(default=None, description="Direction.")
    start_date: Optional[int] = PydField(default=None, ge=0, description="Start date.")
    end_date: Optional[int] = PydField(default=None, ge=0, description="End date.")
    ids: Optional[List[int]] = PydField(default=None, description="Contract ids.")
    firm_ids: Optional[List[int]] = PydField(default=None, description="Firm ids.")
    partner_ids: Optional[List[int]] = PydField(default=None, description="Partner ids.")
    attached_user_ids: Optional[List[int]] = PydField(default=None, description="Attached user ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sort orders.")
    active: Optional[bool] = PydField(default=None, description="Active flag.")
    deleted_mark: Optional[bool] = PydField(default=None, description="Deleted mark.")
    limit: Optional[int] = PydField(default=None, ge=1, le=10000, description="Limit.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Offset.")

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, value):
        return _normalize_contract_direction(value)

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be less than start_date")
        return self


class DocContractAddRequest(BaseSchema):
    """Request for DocContract/Add."""

    model_config = ConfigDict(extra="forbid")

    code: str = PydField(..., min_length=1, description="Contract code.")
    date: int = PydField(..., ge=0, description="Contract date.")
    direction: ContractDirection = PydField(..., description="Direction.")
    name: str = PydField(..., min_length=1, description="Contract name.")
    firm_id: int = PydField(..., ge=1, description="Firm id.")
    partner_id: int = PydField(..., ge=1, description="Partner id.")
    amount: Decimal = PydField(..., description="Amount.")
    currency_id: int = PydField(..., ge=1, description="Currency id.")
    start_date: int = PydField(..., ge=0, description="Start date.")
    end_date: int = PydField(..., ge=0, description="End date.")
    details: str = PydField(..., min_length=1, description="Details.")
    description: Optional[str] = PydField(default=None, description="Description.")
    attached_user_id: Optional[int] = PydField(default=None, ge=1, description="Attached user id.")
    active: Optional[bool] = PydField(default=None, description="Active flag.")

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_direction(cls, value):
        return _normalize_contract_direction(value)

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be less than start_date")
        return self


class DocContractGetResponse(APIBaseResponse[List[DocContract]]):
    """Response for DocContract/Get."""

    model_config = ConfigDict(extra="ignore")


class DocContractGetShortResponse(APIBaseResponse[List[DocContractShort]]):
    """Response for DocContract/GetShort."""

    model_config = ConfigDict(extra="ignore")


class DocContractAddResponse(APIBaseResponse[AddResult]):
    """Response for DocContract/Add."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ContractDirection",
    "DocContract",
    "DocContractAddRequest",
    "DocContractAddResponse",
    "DocContractGetRequest",
    "DocContractGetResponse",
    "DocContractGetShortResponse",
    "DocContractShort",
]
