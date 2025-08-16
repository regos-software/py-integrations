from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from schemas.api.rbac.user import User


class DocCashSessionSortColumn(str, Enum):
    Uuid = "Uuid"
    Code = "Code"
    OperatingCashId = "OperatingCashId"
    StartDate = "StartDate"
    StartUserName = "StartUserName"
    StartAmount = "StartAmount"
    CloseDate = "CloseDate"
    CloseUserName = "CloseUserName"
    Closed = "Closed"
    CloseAmount = "CloseAmount"
    LastUpdate = "LastUpdate"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class DocCashSession(BaseModel):
    uuid: str
    code: str
    operating_cash_id: int
    start_date: int
    start_user: Optional[User] = None
    start_amount: Decimal
    close_date: Optional[int] = None
    close_user: Optional[User] = None
    closed: bool
    close_amount: Optional[Decimal] = None
    last_update: int


class SortOrder(BaseModel):
    column: DocCashSessionSortColumn
    direction: SortDirection


class DocCashSessionGetRequest(BaseModel):
    uuids: Optional[List[str]] = None
    operating_cash_ids: Optional[List[int]] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    is_agregated: Optional[bool] = None
    is_close: Optional[bool] = None
    open_user_id: Optional[int] = None
    close_user_id: Optional[int] = None
    sort_orders: Optional[List[SortOrder]] = None
    limit: Optional[int] = Field(default=None, ge=1, le=10000)
    offset: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_dates(cls, values: DocCashSessionGetRequest):
        if values.start_date and values.end_date and values.end_date < values.start_date:
            raise ValueError("end_date не может быть меньше start_date")
        return values
