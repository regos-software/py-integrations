"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Producer(RegosModel):
    "Модель, описывающая производителей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id производителя")
    name: str | None = PydField(default=None, description="Наименование производителя")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class ProducerAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование производителя")


class ProducerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id производителя")


class ProducerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id производителя")
    name: str | None = PydField(default=None, description="Наименование производителя")


class ProducerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id производителей")
    sort_orders: list[ProducerSortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ProducerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Producer] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ProducerSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: ProducerSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class ProducerSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


ProducerAddRequest: TypeAlias = ProducerAdd
ProducerAddResponse: TypeAlias = InsertResult
ProducerDeleteRequest: TypeAlias = ProducerDelete
ProducerDeleteResponse: TypeAlias = UpdateResult
ProducerEditRequest: TypeAlias = ProducerEdit
ProducerEditResponse: TypeAlias = UpdateResult
ProducerGetRequest: TypeAlias = ProducerGet
ProducerGetResponse: TypeAlias = ProducerRegosOffsettedArrayResult


_MODEL_NAMES = ['Producer', 'ProducerAdd', 'ProducerDelete', 'ProducerEdit', 'ProducerGet', 'ProducerRegosOffsettedArrayResult', 'ProducerSortOrder']


__all__ = [
    'Producer',
    'ProducerAdd',
    'ProducerDelete',
    'ProducerEdit',
    'ProducerGet',
    'ProducerRegosOffsettedArrayResult',
    'ProducerSortOrder',
    'ProducerSortOrderColumn',
    'ProducerGetRequest',
    'ProducerGetResponse',
    'ProducerAddRequest',
    'ProducerAddResponse',
    'ProducerEditRequest',
    'ProducerEditResponse',
    'ProducerDeleteRequest',
    'ProducerDeleteResponse'
]
