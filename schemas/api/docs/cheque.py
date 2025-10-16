"""Схемы документов розничных чеков."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional, Union

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import BaseSchema
from schemas.api.rbac.user import User
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_return_reason import RetailReturnReason


class SortColumn(str, Enum):
    """Доступные колонки сортировки чеков."""

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
    """Направление сортировки."""

    ASC = "ASC"
    DESC = "DESC"


class DocCheque(BaseSchema):
    """Рид-модель розничного чека."""

    model_config = ConfigDict(extra="ignore")

    uuid: str = PydField(..., description="UUID документа чека.")
    date: int = PydField(..., ge=0, description="Дата создания (Unix).")
    code: str = PydField(..., description="Номер чека.")
    status: Union[str, int] = PydField(
        "none", description="Статус чека (исторически строка или код)."
    )
    session: str = PydField(..., description="UUID кассовой сессии.")
    cashier: Optional[User] = PydField(
        default=None, description="Кассир, оформивший чек."
    )
    is_return: bool = PydField(..., description="Признак возвратного чека.")
    seller: Optional[User] = PydField(
        default=None, description="Продавец, проведший чек."
    )
    return_reason: Optional[RetailReturnReason] = PydField(
        default=None, description="Причина возврата."
    )
    card: Optional[RetailCard] = PydField(
        default=None, description="Применённая карта лояльности."
    )
    amount: Decimal = PydField(..., description="Сумма чека.")
    agregate_status: Optional[Union[str, int]] = PydField(
        default=None, description="Агрегированный статус (bc)."
    )
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего изменения (Unix)."
    )


class SortOrder(BaseSchema):
    """Правило сортировки чеков."""

    model_config = ConfigDict(extra="forbid")

    column: SortColumn = PydField(..., description="Колонка сортировки.")
    direction: SortDirection = PydField(
        ..., description="Направление сортировки (ASC|DESC)."
    )


class DocChequeGetRequest(BaseSchema):
    """Фильтры получения розничных чеков."""

    model_config = ConfigDict(extra="forbid")

    uuids: Optional[List[str]] = PydField(
        default=None, description="Фильтр по списку UUID чеков."
    )
    cashier_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID кассиров."
    )
    seller_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID продавцов."
    )
    card_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID карт лояльности."
    )
    customer_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по ID покупателей."
    )
    session_uuid: Optional[str] = PydField(
        default=None, description="UUID кассовой сессии."
    )
    status: Optional[str] = PydField(default=None, description="Статус чека.")
    statuses: Optional[Union[str, List[str]]] = PydField(
        default=None, description="Несколько статусов для фильтрации."
    )
    is_return: Optional[bool] = PydField(
        default=None, description="Фильтр по признаку возврата."
    )
    is_fiscal: Optional[bool] = PydField(
        default=None, description="Фильтр по фискальным чекам."
    )
    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Начало периода (Unix)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="Конец периода (Unix)."
    )
    doc_order_delivery_id: Optional[int] = PydField(
        default=None, ge=1, description="ID доставки заказа."
    )
    return_reason: Optional[int] = PydField(
        default=None, ge=1, description="ID причины возврата."
    )
    sort_orders: Optional[List[SortOrder]] = PydField(
        default=None, description="Список правил сортировки."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Количество записей в выдаче."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Смещение для пагинации."
    )

    @model_validator(mode="after")
    def _validate_dates(cls, values: "DocChequeGetRequest"):
        if (
            values.start_date
            and values.end_date
            and values.end_date < values.start_date
        ):
            raise ValueError("end_date не может быть меньше start_date")
        return values


__all__ = [
    "DocCheque",
    "DocChequeGetRequest",
    "SortColumn",
    "SortDirection",
    "SortOrder",
]
