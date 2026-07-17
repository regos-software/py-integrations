"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Dashboard(RegosModel):
    "Модель, описывающая дашборд"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID дашборда")
    period: DashboardPeriodEnum | None = PydField(default=None, description="Период дашборда: <None | 1> - Период дашборда не задан, виджеты считаются по периоду по умолчаннию, <Yesterday\n| 2> - Вчерашний день, <Today | 3> - Текущий день, <Week | 4> - Неделя, включая текущий день, <Month |\n5> - Месяц, включая текущий день")
    name: str | None = PydField(default=None, description="Наименование дашборда")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    stock_id: int | None = PydField(default=None, description="ID склада")
    is_fixed: bool | None = PydField(default=None, description="Фиксированный")
    is_default: bool | None = PydField(default=None, description="дашборд по умолчанию")
    is_creator: bool | None = PydField(default=None, description="Является ли данный пользователь создателем дашборда")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в unix time в секндах")


class DashboardAdd(RegosModel):
    "Модель для добавления дашборда"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="-")
    firm_id: int | None = PydField(default=None, description="-")
    stock_id: int | None = PydField(default=None, description="-")


class DashboardEdit(RegosModel):
    "Модель для редактирования дашборда"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="-")
    name: str | None = PydField(default=None, description="-")
    is_fixed: bool | None = PydField(default=None, description="-")


class DashboardGet(RegosModel):
    "Модель для получения данных"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID")
    sort_orders: list[DashboardSortOrder] | None = PydField(default=None, description="Сортировка выходных данных")


class DashboardPeriodEnum(str, Enum):
    "Периоды  дашборда"
    None_ = "None"
    Yesterday = "Yesterday"
    Today = "Today"
    Week = "Week"
    Month = "Month"


class DashboardRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Dashboard] | Error | None = PydField(default=None, description="Массив результата.")


class DashboardSetFilters(RegosModel):
    "Модель для установки фильтров дашборда"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID дашборда")
    firm_id: int | None = PydField(default=None, description="ID предприятия. 0 - предприятие не указано")
    stock_id: int | None = PydField(default=None, description="ID склада. 0 - склад не указан")
    period: DashboardPeriodEnum | None = PydField(default=None, description="Период дашборда: <None | 1> - Период дашборда не задан, виджеты считаются по периоду по умолчаннию, <Yesterday\n| 2> - Вчерашний день, <Today | 3> - Текущий день, <Week | 4> - Неделя, включая текущий день, <Month |\n5> - Месяц, включая текущий день")


class DashboardSortOrder(RegosModel):
    "Модель описание сортировок по Dashboard"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DashboardSortOrderColumn | None = PydField(default=None, description="Колонки для сортировки Dashboard")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DashboardSortOrderColumn(str, Enum):
    "Колонки для сортировки Dashboard"
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Creator = "Creator"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, ColumnSortOrderDirection, Error, InsertResult, SingleObjectResult, UpdateResult


DashboardAddRequest: TypeAlias = DashboardAdd
DashboardAddResponse: TypeAlias = InsertResult
DashboardDeleteRequest: TypeAlias = Base_ID
DashboardDeleteResponse: TypeAlias = UpdateResult
DashboardEditRequest: TypeAlias = DashboardEdit
DashboardEditResponse: TypeAlias = UpdateResult
DashboardGetRequest: TypeAlias = DashboardGet
DashboardGetResponse: TypeAlias = DashboardRegosArrayResult
DashboardSetFiltersRequest: TypeAlias = DashboardSetFilters
DashboardSetFiltersResponse: TypeAlias = SingleObjectResult


_MODEL_NAMES = ['Dashboard', 'DashboardAdd', 'DashboardEdit', 'DashboardGet', 'DashboardRegosArrayResult', 'DashboardSetFilters', 'DashboardSortOrder']


__all__ = [
    'Dashboard',
    'DashboardAdd',
    'DashboardEdit',
    'DashboardGet',
    'DashboardPeriodEnum',
    'DashboardRegosArrayResult',
    'DashboardSetFilters',
    'DashboardSortOrder',
    'DashboardSortOrderColumn',
    'DashboardGetRequest',
    'DashboardGetResponse',
    'DashboardAddRequest',
    'DashboardAddResponse',
    'DashboardEditRequest',
    'DashboardEditResponse',
    'DashboardDeleteRequest',
    'DashboardDeleteResponse',
    'DashboardSetFiltersRequest',
    'DashboardSetFiltersResponse'
]
