from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from schemas.api.rbac.user import User
from schemas.api.refrences.retail_card import RetailCard
from schemas.api.refrences.retail_return_reason import RetailReturnReason


# ==== Enums (работа только по строкам) ====



class SortColumn(str, Enum):
    Uuid = "Uuid"
    Date = "Date"
    Code = "Code"
    Status = "Status"
    Session = "Session"
    CashierName = "CashierName"
    IsRetunr = "IsRetunr"  # опечатка сохранена для совместимости
    SellerName = "SellerName"
    ReturnReasonId = "ReturnReasonId"
    RetailCardBarcodeValue = "RetailCardBarcodeValue"
    Amount = "Amount"
    AgregateStatus = "AgregateStatus"
    LastUpdate = "LastUpdate"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


# ==== Основные модели ====

class DocCheque(BaseModel):
    uuid: str
    date: int
    code: str
    status: Union[str, int] = "none"  
    session: str
    cashier: Optional[User] = None
    is_return: bool
    seller: Optional[User] = None
    return_reason: Optional[RetailReturnReason] = None
    card: Optional[RetailCard] = None
    amount: Decimal
    agregate_status: Optional[Union[str, int]] = None
    last_update: int


# ==== Сортировка ====

class SortOrder(BaseModel):
    column: SortColumn
    direction: SortDirection


# ==== Запрос ====

class DocChequeGetRequest(BaseModel):
    # Идентификаторы
    uuids: Optional[List[str]] = None
    cashier_ids: Optional[List[int]] = None
    seller_ids: Optional[List[int]] = None
    card_ids: Optional[List[int]] = None
    customer_ids: Optional[List[int]] = None
    session_uuid: Optional[str] = None

    # Статусы и признаки
    status: Optional[str] = None
    statuses: Optional[Union[str, List[str]]] = None
    is_return: Optional[bool] = None
    is_fiscal: Optional[bool] = None

    # Период
    start_date: Optional[int] = None
    end_date: Optional[int] = None

    # Доп. поля из примера
    doc_order_delivery_id: Optional[int] = None
    return_reason: Optional[int] = None

    # Сортировка и пэйджинг
    sort_orders: Optional[List[SortOrder]] = None
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_dates(cls, values: "DocChequeGetRequest"):
        if values.start_date and values.end_date and values.end_date < values.start_date:
            raise ValueError("end_date не может быть меньше start_date")
        return values
