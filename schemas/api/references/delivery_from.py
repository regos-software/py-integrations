"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DeliveryFrom(RegosModel):
    "Модель, описывающая источники розничных заказов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id источника розничных заказов")
    name: str | None = PydField(default=None, description="Наименование источника розничных заказов")
    deleted: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DeliveryFromAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование источника розничных заказов")


class DeliveryFromDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id источника розничных заказов")


class DeliveryFromEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id источника розничных заказов")
    name: str | None = PydField(default=None, description="Наименование источника розничных заказов")


class DeliveryFromGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id источников розничных заказов")
    sort_orders: list[DeliveryFrom_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DeliveryFromRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DeliveryFrom] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DeliveryFrom_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DeliveryFrom_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DeliveryFrom_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


DeliveryFromAddRequest: TypeAlias = DeliveryFromAdd
DeliveryFromAddResponse: TypeAlias = InsertResult
DeliveryFromDeleteRequest: TypeAlias = DeliveryFromDelete
DeliveryFromDeleteResponse: TypeAlias = UpdateResult
DeliveryFromEditRequest: TypeAlias = DeliveryFromEdit
DeliveryFromEditResponse: TypeAlias = UpdateResult
DeliveryFromGetRequest: TypeAlias = DeliveryFromGet
DeliveryFromGetResponse: TypeAlias = DeliveryFromRegosOffsettedArrayResult


_MODEL_NAMES = ['DeliveryFrom', 'DeliveryFromAdd', 'DeliveryFromDelete', 'DeliveryFromEdit', 'DeliveryFromGet', 'DeliveryFromRegosOffsettedArrayResult', 'DeliveryFrom_SortOrder']


__all__ = [
    'DeliveryFrom',
    'DeliveryFromAdd',
    'DeliveryFromDelete',
    'DeliveryFromEdit',
    'DeliveryFromGet',
    'DeliveryFromRegosOffsettedArrayResult',
    'DeliveryFrom_SortOrder',
    'DeliveryFrom_SortOrderColumn',
    'DeliveryFromGetRequest',
    'DeliveryFromGetResponse',
    'DeliveryFromAddRequest',
    'DeliveryFromAddResponse',
    'DeliveryFromEditRequest',
    'DeliveryFromEditResponse',
    'DeliveryFromDeleteRequest',
    'DeliveryFromDeleteResponse'
]
