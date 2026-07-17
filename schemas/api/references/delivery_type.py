"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DeliveryType(RegosModel):
    "Модель, описывающая способ доставки"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id стособа доставки")
    name: str | None = PydField(default=None, description="Наименование способа доставки")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DeliveryTypeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование способа доставки")


class DeliveryTypeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id способа доставки")


class DeliveryTypeEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id способа доставки")
    name: str | None = PydField(default=None, description="Наименование способа доставки")


class DeliveryTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id способов доставки")
    sort_orders: list[DeliveryType_SortOrder] | None = PydField(default=None, description="Сортировки выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DeliveryTypeRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DeliveryType] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DeliveryType_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DeliveryType_SortOrderColumn | None = PydField(default=None, description="Колонка сортировки")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки")


class DeliveryType_SortOrderColumn(str, Enum):
    "Колонки для сортировки"
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


DeliveryTypeAddRequest: TypeAlias = DeliveryTypeAdd
DeliveryTypeAddResponse: TypeAlias = InsertResult
DeliveryTypeDeleteRequest: TypeAlias = DeliveryTypeDelete
DeliveryTypeDeleteResponse: TypeAlias = UpdateResult
DeliveryTypeEditRequest: TypeAlias = DeliveryTypeEdit
DeliveryTypeEditResponse: TypeAlias = UpdateResult
DeliveryTypeGetRequest: TypeAlias = DeliveryTypeGet
DeliveryTypeGetResponse: TypeAlias = DeliveryTypeRegosOffsettedArrayResult


_MODEL_NAMES = ['DeliveryType', 'DeliveryTypeAdd', 'DeliveryTypeDelete', 'DeliveryTypeEdit', 'DeliveryTypeGet', 'DeliveryTypeRegosOffsettedArrayResult', 'DeliveryType_SortOrder']


__all__ = [
    'DeliveryType',
    'DeliveryTypeAdd',
    'DeliveryTypeDelete',
    'DeliveryTypeEdit',
    'DeliveryTypeGet',
    'DeliveryTypeRegosOffsettedArrayResult',
    'DeliveryType_SortOrder',
    'DeliveryType_SortOrderColumn',
    'DeliveryTypeGetRequest',
    'DeliveryTypeGetResponse',
    'DeliveryTypeAddRequest',
    'DeliveryTypeAddResponse',
    'DeliveryTypeEditRequest',
    'DeliveryTypeEditResponse',
    'DeliveryTypeDeleteRequest',
    'DeliveryTypeDeleteResponse'
]
