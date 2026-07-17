"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Color(RegosModel):
    "Модель, описывающая цвета"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id цвета")
    name: str | None = PydField(default=None, description="Наименование цвета")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class ColorAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование цвета")


class ColorDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id цвета")


class ColorEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID цвета")
    name: str | None = PydField(default=None, description="Наименование цвета")


class ColorGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id цветов")
    sort_orders: list[ColorSortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ColorRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Color] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ColorSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: ColorSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class ColorSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


ColorAddRequest: TypeAlias = ColorAdd
ColorAddResponse: TypeAlias = InsertResult
ColorDeleteRequest: TypeAlias = ColorDelete
ColorDeleteResponse: TypeAlias = UpdateResult
ColorEditRequest: TypeAlias = ColorEdit
ColorEditResponse: TypeAlias = UpdateResult
ColorGetRequest: TypeAlias = ColorGet
ColorGetResponse: TypeAlias = ColorRegosOffsettedArrayResult


_MODEL_NAMES = ['Color', 'ColorAdd', 'ColorDelete', 'ColorEdit', 'ColorGet', 'ColorRegosOffsettedArrayResult', 'ColorSortOrder']


__all__ = [
    'Color',
    'ColorAdd',
    'ColorDelete',
    'ColorEdit',
    'ColorGet',
    'ColorRegosOffsettedArrayResult',
    'ColorSortOrder',
    'ColorSortOrderColumn',
    'ColorGetRequest',
    'ColorGetResponse',
    'ColorAddRequest',
    'ColorAddResponse',
    'ColorEditRequest',
    'ColorEditResponse',
    'ColorDeleteRequest',
    'ColorDeleteResponse'
]
