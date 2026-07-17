"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Brand(RegosModel):
    "Модель, описывающая бренды"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id бренда")
    name: str | None = PydField(default=None, description="Наименование бренда")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class BrandAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование бренда. Не может быть пустым, максимальная длина — 150 символов")


class BrandDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id бренда. Значение должно быть больше 0")


class BrandEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id бренда. Значение должно быть больше 0")
    name: str | None = PydField(default=None, description="Наименование бренда. Не может быть пустым, максимальная длина — 150 символов")


class BrandGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id брендов")
    sort_orders: list[BrandSortOrder] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name. Поиск применяется, если длина строки больше порога, заданного серверными настройками")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных. Параметр ограничивается серверными настройками (например, query_limit)")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки. Если значение меньше 0, используется 0")


class BrandRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Brand] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class BrandSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: BrandSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class BrandSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


BrandAddRequest: TypeAlias = BrandAdd
BrandAddResponse: TypeAlias = InsertResult
BrandDeleteRequest: TypeAlias = BrandDelete
BrandDeleteResponse: TypeAlias = UpdateResult
BrandEditRequest: TypeAlias = BrandEdit
BrandEditResponse: TypeAlias = UpdateResult
BrandGetRequest: TypeAlias = BrandGet
BrandGetResponse: TypeAlias = BrandRegosOffsettedArrayResult


_MODEL_NAMES = ['Brand', 'BrandAdd', 'BrandDelete', 'BrandEdit', 'BrandGet', 'BrandRegosOffsettedArrayResult', 'BrandSortOrder']


__all__ = [
    'Brand',
    'BrandAdd',
    'BrandDelete',
    'BrandEdit',
    'BrandGet',
    'BrandRegosOffsettedArrayResult',
    'BrandSortOrder',
    'BrandSortOrderColumn',
    'BrandGetRequest',
    'BrandGetResponse',
    'BrandAddRequest',
    'BrandAddResponse',
    'BrandEditRequest',
    'BrandEditResponse',
    'BrandDeleteRequest',
    'BrandDeleteResponse'
]
