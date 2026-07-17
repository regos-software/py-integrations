"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class SizeChart(RegosModel):
    "Модель, описывающая размеры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id размера")
    name: str | None = PydField(default=None, description="Наименование размера")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class SizeChartAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование размер")


class SizeChartDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID размера")


class SizeChartEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID размера")
    name: str | None = PydField(default=None, description="Наименование размера")


class SizeChartGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id размеров")
    sort_orders: list[SizeChartSortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class SizeChartRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[SizeChart] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class SizeChartSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: SizeChartSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class SizeChartSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


SizeChartAddRequest: TypeAlias = SizeChartAdd
SizeChartAddResponse: TypeAlias = InsertResult
SizeChartDeleteRequest: TypeAlias = SizeChartDelete
SizeChartDeleteResponse: TypeAlias = UpdateResult
SizeChartEditRequest: TypeAlias = SizeChartEdit
SizeChartEditResponse: TypeAlias = UpdateResult
SizeChartGetRequest: TypeAlias = SizeChartGet
SizeChartGetResponse: TypeAlias = SizeChartRegosOffsettedArrayResult


_MODEL_NAMES = ['SizeChart', 'SizeChartAdd', 'SizeChartDelete', 'SizeChartEdit', 'SizeChartGet', 'SizeChartRegosOffsettedArrayResult', 'SizeChartSortOrder']


__all__ = [
    'SizeChart',
    'SizeChartAdd',
    'SizeChartDelete',
    'SizeChartEdit',
    'SizeChartGet',
    'SizeChartRegosOffsettedArrayResult',
    'SizeChartSortOrder',
    'SizeChartSortOrderColumn',
    'SizeChartGetRequest',
    'SizeChartGetResponse',
    'SizeChartAddRequest',
    'SizeChartAddResponse',
    'SizeChartEditRequest',
    'SizeChartEditResponse',
    'SizeChartDeleteRequest',
    'SizeChartDeleteResponse'
]
