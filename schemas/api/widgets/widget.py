"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Widget(RegosModel):
    "Модель, описывающая виджет"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID виджета")
    name: str | None = PydField(default=None, description="Наименование виджета")
    widget_type: WidgetType | None = PydField(default=None, description="Тип виджета")
    dashboard_id: int | None = PydField(default=None, description="ID дашборда, к которому привязан виджет")
    row: int | None = PydField(default=None, description="Строка, в которой находится виджет")
    column: int | None = PydField(default=None, description="Колонка в строке в которой находится виджет. Нумерация начинается с 0")
    width: int | None = PydField(default=None, description="Ширина виджета - количество ячеек, которое занимает виджет (от 1 да 3)")
    height: int | None = PydField(default=None, description="Высота виджета - количество строк, которое занимает виджет")
    firm_id: int | None = PydField(default=None, description="ID предприятия, 0 - предприятие не указано")
    stock_id: int | None = PydField(default=None, description="ID склада, 0 склад не указан")
    connected_integration_id: str | None = PydField(default=None, description="ID подключенной интеграции. Для widget_type = Integration (19) обязателен; интеграция должна быть активной и поддерживать обработчик Widget")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в unix time")


class WidgetAdd(RegosModel):
    "Модель для добавления виджета"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    dashboard_id: int | None = PydField(default=None, description="ID дашборда")
    widget_type: WidgetTypesEnum | None = PydField(default=None, description="Тип виджета")
    name: str | None = PydField(default=None, description="Наименование виджета, не более 100 символов")
    row: int | None = PydField(default=None, description="Строка расположения")
    column: int | None = PydField(default=None, description="Колонка расположения. Нумерация начинается с 0")
    width: int | None = PydField(default=None, description="Ширина виджета")
    height: int | None = PydField(default=None, description="Высота виджета")
    firm_id: int | None = PydField(default=None, description="ID предприятия, 0 - предприятие не указано")
    stock_id: int | None = PydField(default=None, description="ID склада, 0 - склад не указан")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Интеграция должна быть активной и поддерживать обработчик Widget")


class WidgetEdit(RegosModel):
    "Модель редактирования виджета"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="-")
    name: str | None = PydField(default=None, description="-")


class WidgetGet(RegosModel):
    "Модель для получения данных"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id виджетов")
    dashboard_id: int | None = PydField(default=None, description="id дашборда")


class WidgetRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Widget] | Error | None = PydField(default=None, description="Массив результата.")


class WidgetSetFilters(RegosModel):
    "Модель для установки фильтров виджета"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="-")
    firm_id: int | None = PydField(default=None, description="-")
    stock_id: int | None = PydField(default=None, description="-")


class WidgetSetPosition(RegosModel):
    "Модель для установки позиции виджета"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID виджета")
    row: int | None = PydField(default=None, description="Строка, в которой находится виджет. null - не изменяется")
    column: int | None = PydField(default=None, description="Колонка в строке, в которой находится виджет. null - не изменяется")
    width: int | None = PydField(default=None, description="Ширина виджета в колонках. null - не изменяется")
    height: int | None = PydField(default=None, description="Высота виджета в строках. null - не изменяется")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, SingleObjectResult, UpdateResult
from schemas.api.widgets.widget_type import WidgetType, WidgetTypesEnum


WidgetAddRequest: TypeAlias = list[WidgetAdd]
WidgetAddResponse: TypeAlias = UpdateResult
WidgetDeleteRequest: TypeAlias = list[Base_ID]
WidgetDeleteResponse: TypeAlias = UpdateResult
WidgetEditRequest: TypeAlias = WidgetEdit
WidgetEditResponse: TypeAlias = UpdateResult
WidgetGetRequest: TypeAlias = WidgetGet
WidgetGetResponse: TypeAlias = WidgetRegosArrayResult
WidgetSetFiltersRequest: TypeAlias = WidgetSetFilters
WidgetSetFiltersResponse: TypeAlias = SingleObjectResult
WidgetSetPositionRequest: TypeAlias = list[WidgetSetPosition]
WidgetSetPositionResponse: TypeAlias = SingleObjectResult


_MODEL_NAMES = ['Widget', 'WidgetAdd', 'WidgetEdit', 'WidgetGet', 'WidgetRegosArrayResult', 'WidgetSetFilters', 'WidgetSetPosition']


__all__ = [
    'Widget',
    'WidgetAdd',
    'WidgetEdit',
    'WidgetGet',
    'WidgetRegosArrayResult',
    'WidgetSetFilters',
    'WidgetSetPosition',
    'WidgetGetRequest',
    'WidgetGetResponse',
    'WidgetAddRequest',
    'WidgetAddResponse',
    'WidgetEditRequest',
    'WidgetEditResponse',
    'WidgetDeleteRequest',
    'WidgetDeleteResponse',
    'WidgetSetFiltersRequest',
    'WidgetSetFiltersResponse',
    'WidgetSetPositionRequest',
    'WidgetSetPositionResponse'
]
