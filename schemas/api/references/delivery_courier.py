"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DeliveryCourier(RegosModel):
    "Модель, описывающая курьеров"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id курьера")
    name: str | None = PydField(default=None, description="Наименование курьера")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DeliveryCourierAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование курьера")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class DeliveryCourierDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id курьера")


class DeliveryCourierEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id курьера")
    name: str | None = PydField(default=None, description="Наименование курьера")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class DeliveryCourierGet(RegosModel):
    "Модель получения данных по доставщикам"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id курьеров")
    sort_orders: list[DeliveryCourier_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DeliveryCourierRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DeliveryCourier] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DeliveryCourier_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DeliveryCourier_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DeliveryCourier_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Description = "Description"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


DeliveryCourierAddRequest: TypeAlias = DeliveryCourierAdd
DeliveryCourierAddResponse: TypeAlias = InsertResult
DeliveryCourierDeleteRequest: TypeAlias = DeliveryCourierDelete
DeliveryCourierDeleteResponse: TypeAlias = UpdateResult
DeliveryCourierEditRequest: TypeAlias = DeliveryCourierEdit
DeliveryCourierEditResponse: TypeAlias = UpdateResult
DeliveryCourierGetRequest: TypeAlias = DeliveryCourierGet
DeliveryCourierGetResponse: TypeAlias = DeliveryCourierRegosOffsettedArrayResult


_MODEL_NAMES = ['DeliveryCourier', 'DeliveryCourierAdd', 'DeliveryCourierDelete', 'DeliveryCourierEdit', 'DeliveryCourierGet', 'DeliveryCourierRegosOffsettedArrayResult', 'DeliveryCourier_SortOrder']


__all__ = [
    'DeliveryCourier',
    'DeliveryCourierAdd',
    'DeliveryCourierDelete',
    'DeliveryCourierEdit',
    'DeliveryCourierGet',
    'DeliveryCourierRegosOffsettedArrayResult',
    'DeliveryCourier_SortOrder',
    'DeliveryCourier_SortOrderColumn',
    'DeliveryCourierGetRequest',
    'DeliveryCourierGetResponse',
    'DeliveryCourierAddRequest',
    'DeliveryCourierAddResponse',
    'DeliveryCourierEditRequest',
    'DeliveryCourierEditResponse',
    'DeliveryCourierDeleteRequest',
    'DeliveryCourierDeleteResponse'
]
