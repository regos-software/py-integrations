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
    stock: Optional[Stock] = PydField(default=None, description="Склад кассы.")
    key: Optional[str] = PydField(default=None, description="Ключ безопасности кассы.")
    price_type: Optional[PriceType] = PydField(default=None, description="Вид цены.")
    description: Optional[str] = None
    virtual: Optional[bool] = None
    auto_close: Optional[bool] = None
    max_cheque_quantity_in_session: Optional[int] = None
    last_update: Optional[int] = None
    user_accept: Optional[User] = None


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
