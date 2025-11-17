from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema
from schemas.api.references.stock import Stock
from schemas.api.references.price_type import PriceType
from schemas.api.rbac.user import User


class OperatingCash(BaseSchema):
    """
    Касса розничной торговли.
    """

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID розничной кассы.")
    stock: Stock = PydField(..., description="Склад.")
    key: str = PydField(..., description="Ключ безопасности кассы.")
    price_type: PriceType = PydField(..., description="Вид цены.")
    description: Optional[str] = PydField(
        default=None, description="Дополнительное описание."
    )
    virtual: bool = PydField(..., description="Признак виртуальной кассы.")
    auto_close: bool = PydField(..., description="Автоматическое закрытие смены.")
    max_cheque_quantity_in_session: int = PydField(
        ..., description="Макс. число чеков за смену."
    )
    last_update: int = PydField(
        ..., ge=0, description="Дата последнего изменения (Unix, сек)."
    )
    user_accept: User = PydField(
        ..., description="Пользователь, принявший кассу в работу."
    )


class OperatingCashSortColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    StockName = "StockName"
    Key = "Key"
    PriceTypeName = "PriceTypeName"
    Virtual = "Virtual"
    AutoClose = "AutoClose"
    UserAcceptName = "UserAcceptName"
    LastUpdate = "LastUpdate"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class OperatingCashSortOrder(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    column: Optional[OperatingCashSortColumn] = PydField(
        default=None, description="Колонка сортировки."
    )
    direction: Optional[SortDirection] = PydField(
        default=None, description="Направление сортировки."
    )


class OperatingCashGetRequest(BaseSchema):
    """
    Входная модель для OperatingCash/Get.
    """

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Массив id касс."
    )
    firm_ids: Optional[List[int]] = PydField(
        default=None, description="Массив id предприятий."
    )
    stock_ids: Optional[List[int]] = PydField(
        default=None, description="Массив id складов."
    )
    price_type_ids: Optional[List[int]] = PydField(
        default=None, description="Массив id видов цен."
    )
    is_virtual: Optional[bool] = PydField(
        default=None, description="Виртуальная касса (true/false)."
    )
    accepted_user_id: Optional[int] = PydField(
        default=None, description="ID пользователя, принявшего кассу."
    )
    sort_orders: Optional[List[OperatingCashSortOrder]] = PydField(
        default=None, description="Список правил сортировки."
    )
    search: Optional[str] = PydField(
        default=None,
        description="Поиск: id, key, stock_name, user_accept_name.",
    )
    limit: Optional[int] = PydField(
        default=None, description="Количество элементов выборки."
    )
    offset: Optional[int] = PydField(
        default=None, description="Смещение от начала выборки."
    )


__all__ = [
    "OperatingCash",
    "OperatingCashGetRequest",
    "OperatingCashSortColumn",
    "SortDirection",
    "OperatingCashSortOrder",
]
