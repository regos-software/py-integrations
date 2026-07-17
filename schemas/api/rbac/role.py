"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Role(RegosModel):
    "Модель, описывающая роль и её параметры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id роли")
    name: str | None = PydField(default=None, description="Наименование роли")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time")


class RoleAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование роли")
    description: str | None = PydField(default=None, description="Примечание")


class RoleDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id роли")


class RoleEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID роли")
    name: str | None = PydField(default=None, description="Наименование роли")
    description: str | None = PydField(default=None, description="Примечание")


class RoleGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id ролей")
    sort_orders: list[Role_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям name, description")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RoleRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Role] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class Role_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: Role_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class Role_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Description = "Description"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


RoleAddRequest: TypeAlias = RoleAdd
RoleAddResponse: TypeAlias = InsertResult
RoleDeleteRequest: TypeAlias = RoleDelete
RoleDeleteResponse: TypeAlias = UpdateResult
RoleEditRequest: TypeAlias = RoleEdit
RoleEditResponse: TypeAlias = UpdateResult
RoleGetRequest: TypeAlias = RoleGet
RoleGetResponse: TypeAlias = RoleRegosOffsettedArrayResult


_MODEL_NAMES = ['Role', 'RoleAdd', 'RoleDelete', 'RoleEdit', 'RoleGet', 'RoleRegosOffsettedArrayResult', 'Role_SortOrder']


__all__ = [
    'Role',
    'RoleAdd',
    'RoleDelete',
    'RoleEdit',
    'RoleGet',
    'RoleRegosOffsettedArrayResult',
    'Role_SortOrder',
    'Role_SortOrderColumn',
    'RoleGetRequest',
    'RoleGetResponse',
    'RoleAddRequest',
    'RoleAddResponse',
    'RoleEditRequest',
    'RoleEditResponse',
    'RoleDeleteRequest',
    'RoleDeleteResponse'
]
