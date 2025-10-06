from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from schemas.api.rbac.user import User
from schemas.api.refrences.partner import Partner
from schemas.api.refrences.stock import Stock
from schemas.api.refrences.currency import Currency

from schemas.api.refrences.price_type import PriceType
from schemas.api.refrences.tax import VatCalculationType





# ==== Модели ====

class DocPurchase(BaseModel):
    """Документ поступления от контрагента"""
    id: int
    date: int  # unixtime sec
    code: str
    partner: Partner
    stock: Stock
    currency: Currency
#   contract: DocContractShort
    description: Optional[str] = None
    amount: Decimal
    exchange_rate: Decimal
    additional_expenses_amount: Decimal
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

class DocPurchaseGetRequest(BaseModel):
    """
    Параметры запроса для /v1/DocPurchase/Get
    """
    # Период
    start_date: Optional[int] = None  # unixtime sec
    end_date: Optional[int] = None    # unixtime sec

    # Фильтры по идентификаторам
    ids: Optional[List[int]] = None
    firm_ids: Optional[List[int]] = None
    stock_ids: Optional[List[int]] = None
    partner_ids: Optional[List[int]] = None
    contract_ids: Optional[List[int]] = None
    attached_user_ids: Optional[List[int]] = None

    # Прочие фильтры
    vat_calculation_type: Optional[VatCalculationType] = None
    performed: Optional[bool] = None
    blocked: Optional[bool] = None
    deleted_mark: Optional[bool] = None
    search: Optional[str] = None

    # Сортировка и пэйджинг
    sort_orders: Optional[List[SortOrder]] = None
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_dates(cls, values: "DocPurchaseGetRequest"):
        if values.start_date and values.end_date and values.end_date < values.start_date:
            raise ValueError("end_date не может быть меньше start_date")
        return values
