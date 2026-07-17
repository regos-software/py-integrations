"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailReturnReason(RegosModel):
    "Модель, описывающая причины возвратов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id причины возврата")
    name: str | None = PydField(default=None, description="Наименование причины возврата")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    enabled: bool | None = PydField(default=None, description="Метка о том, что причина возврата доступна для использования")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class RetailReturnReasonAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование причины возврата")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    enabled: bool | None = PydField(default=None, description="Метка о том, что причина возврата доступна для использования")


class RetailReturnReasonDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id причины возврата")


class RetailReturnReasonEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id причины возврата")
    name: str | None = PydField(default=None, description="Наименование причины возврата")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    enabled: bool | None = PydField(default=None, description="Метка о том, что причина возврата доступна для использования")


class RetailReturnReasonGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id причин возврата")
    enabled: bool | None = PydField(default=None, description="Метка о том, что причина возврата доступна для использования")
    sort_orders: list[RetailReturnReason_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailReturnReasonRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailReturnReason] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailReturnReason_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: RetailReturnReason_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class RetailReturnReason_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Description = "Description"
    Enabled = "Enabled"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


RetailReturnReasonAddRequest: TypeAlias = RetailReturnReasonAdd
RetailReturnReasonAddResponse: TypeAlias = InsertResult
RetailReturnReasonDeleteRequest: TypeAlias = RetailReturnReasonDelete
RetailReturnReasonDeleteResponse: TypeAlias = UpdateResult
RetailReturnReasonEditRequest: TypeAlias = RetailReturnReasonEdit
RetailReturnReasonEditResponse: TypeAlias = UpdateResult
RetailReturnReasonGetRequest: TypeAlias = RetailReturnReasonGet
RetailReturnReasonGetResponse: TypeAlias = RetailReturnReasonRegosOffsettedArrayResult


_MODEL_NAMES = ['RetailReturnReason', 'RetailReturnReasonAdd', 'RetailReturnReasonDelete', 'RetailReturnReasonEdit', 'RetailReturnReasonGet', 'RetailReturnReasonRegosOffsettedArrayResult', 'RetailReturnReason_SortOrder']


__all__ = [
    'RetailReturnReason',
    'RetailReturnReasonAdd',
    'RetailReturnReasonDelete',
    'RetailReturnReasonEdit',
    'RetailReturnReasonGet',
    'RetailReturnReasonRegosOffsettedArrayResult',
    'RetailReturnReason_SortOrder',
    'RetailReturnReason_SortOrderColumn',
    'RetailReturnReasonGetRequest',
    'RetailReturnReasonGetResponse',
    'RetailReturnReasonAddRequest',
    'RetailReturnReasonAddResponse',
    'RetailReturnReasonEditRequest',
    'RetailReturnReasonEditResponse',
    'RetailReturnReasonDeleteRequest',
    'RetailReturnReasonDeleteResponse'
]
