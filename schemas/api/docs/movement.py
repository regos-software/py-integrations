from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from schemas.api.rbac.user import User
from schemas.api.references.partner import Partner
from schemas.api.references.stock import Stock
from schemas.api.references.currency import Currency

from schemas.api.references.price_type import PriceType
from schemas.api.references.tax import VatCalculationType
from schemas.api.base import APIBaseResponse


# ==== Модели ====


class DocMovement(BaseModel):
    """Документ отгрузки контрагенту"""

    id: int
    date: int  # unixtime sec
    code: str
    partner: Partner
    stock: Stock
    contract: Optional[str] = None
    seller: Optional[User] = None
    currency: Currency
    #   contract: DocContractShort
    description: Optional[str] = None
    amount: Decimal
    exchange_rate: Decimal
    additional_expenses_amount: Decimal = Decimal("0")
    vat_calculation_type: VatCalculationType
    attached_user: Optional[User] = None
    price_type: Optional[PriceType] = None
    blocked: bool
    current_user_blocked: Optional[bool] = None
    performed: bool
    deleted_mark: bool
    last_update: int  # unixtime sec


class DocPurchaseSortOrder(BaseModel):
    column: Optional[str] = None
    direction: Optional[str] = None


class DocMovementGetRequest(BaseModel):
    """ """

    # Период
    start_date: Optional[int] = None  # unixtime sec
    end_date: Optional[int] = None  # unixtime sec
    # Фильтры по идентификаторам
    ids: Optional[List[int]] = None
    firm_sender_ids: Optional[List[int]] = None
    firm_receiver_ids: Optional[List[int]] = None
    stock_sender_ids: Optional[List[int]] = None
    stock_receiver_ids: Optional[List[int]] = None
    attached_user_ids: Optional[List[int]] = None
    performed: Optional[bool] = None
    blocked: Optional[bool] = None
    deleted_mark: Optional[bool] = None
    search: Optional[str] = None

    sort_orders: Optional[List[DocPurchaseSortOrder]] = None
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_dates(cls, values: "DocMovementGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


class DocMovementGetResponse(APIBaseResponse[List[DocMovement]]):
    """Ответ на запрос /v1/DocMovement/Get."""

    pass


class DocMovementAddRequest(BaseModel):
    """
        Параметры создания документа оптовой продажи.
        {
        "date": 1534151629,
        "stock_sender_id": 2,
        "stock_receiver_id":3,
        "description": "example",
        "attached_user_id": 2
    }
    """

    date: int = Field(..., ge=0, description="Дата документа (Unix).")
    stock_sender_id: int = Field(..., ge=1, description="ID склада-отправителя.")
    stock_receiver_id: int = Field(..., ge=1, description="ID склада-получателя.")
    description: Optional[str] = Field(default=None, description="Описание документа.")
    attached_user_id: Optional[int] = Field(
        default=None, ge=1, description="ID прикреплённого пользователя."
    )


__all__ = [
    "DocMovement",
    "DocMovementGetRequest",
    "DocMovementGetResponse",
    "DocMovementAddRequest",
]
