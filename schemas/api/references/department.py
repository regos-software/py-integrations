"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Department(RegosModel):
    "Модель, описывающая отделы для номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id отдела")
    name: str | None = PydField(default=None, description="Наименование отдела")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи")


class DepartmentAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование отдела")


class DepartmentDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id отдела")


class DepartmentEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID отдела")
    name: str | None = PydField(default=None, description="Наименование отдела")


class DepartmentGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id отделов")
    sort_orders: list[DepartmentSortOrder] | None = PydField(default=None, description="Сортировки выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DepartmentRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Department] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DepartmentSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DepartmentSortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DepartmentSortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


DepartmentAddRequest: TypeAlias = DepartmentAdd
DepartmentAddResponse: TypeAlias = InsertResult
DepartmentDeleteRequest: TypeAlias = DepartmentDelete
DepartmentDeleteResponse: TypeAlias = UpdateResult
DepartmentEditRequest: TypeAlias = DepartmentEdit
DepartmentEditResponse: TypeAlias = UpdateResult
DepartmentGetRequest: TypeAlias = DepartmentGet
DepartmentGetResponse: TypeAlias = DepartmentRegosOffsettedArrayResult


_MODEL_NAMES = ['Department', 'DepartmentAdd', 'DepartmentDelete', 'DepartmentEdit', 'DepartmentGet', 'DepartmentRegosOffsettedArrayResult', 'DepartmentSortOrder']


__all__ = [
    'Department',
    'DepartmentAdd',
    'DepartmentDelete',
    'DepartmentEdit',
    'DepartmentGet',
    'DepartmentRegosOffsettedArrayResult',
    'DepartmentSortOrder',
    'DepartmentSortOrderColumn',
    'DepartmentGetRequest',
    'DepartmentGetResponse',
    'DepartmentAddRequest',
    'DepartmentAddResponse',
    'DepartmentEditRequest',
    'DepartmentEditResponse',
    'DepartmentDeleteRequest',
    'DepartmentDeleteResponse'
]
