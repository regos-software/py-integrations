"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RolePermission(RegosModel):
    "Модель, описывающая права доступа роли"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id записи в таблице")
    role: Role | None = PydField(default=None, description="Роль")
    permission: Permission | None = PydField(default=None, description="Право доступа")
    value: bool | None = PydField(default=None, description="Разрешение или запрет права доступа для роли")


class RolePermissionEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID записи")
    role_id: int | None = PydField(default=None, description="ID роли")
    permission_id: int | None = PydField(default=None, description="ID права доступа")
    value: bool | None = PydField(default=None, description="Разрешение или запрет права доступа для роли")


class RolePermissionGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    role_id: int | None = PydField(default=None, description="ID роли")
    permission_id: int | None = PydField(default=None, description="ID права доступа")
    group_id: int | None = PydField(default=None, description="ID группы прав доступа")
    value: bool | None = PydField(default=None, description="Нужное значение прав доступа - получить список только с определённым значением, если это поле отправлено")
    sort_orders: list[RolePermission_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: name - Наименование, description - Примечание")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RolePermissionRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RolePermission] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RolePermission_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: RolePermission_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class RolePermission_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    RoleName = "RoleName"
    PermissionName = "PermissionName"
    PermissionGroupName = "PermissionGroupName"
    Value = "Value"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, Permission, UpdateResult
from schemas.api.rbac.role import Role


RolePermissionEditRequest: TypeAlias = list[RolePermissionEdit]
RolePermissionEditResponse: TypeAlias = UpdateResult
RolePermissionGetRequest: TypeAlias = RolePermissionGet
RolePermissionGetResponse: TypeAlias = RolePermissionRegosOffsettedArrayResult


_MODEL_NAMES = ['RolePermission', 'RolePermissionEdit', 'RolePermissionGet', 'RolePermissionRegosOffsettedArrayResult', 'RolePermission_SortOrder']


__all__ = [
    'RolePermission',
    'RolePermissionEdit',
    'RolePermissionGet',
    'RolePermissionRegosOffsettedArrayResult',
    'RolePermission_SortOrder',
    'RolePermission_SortOrderColumn',
    'RolePermissionGetRequest',
    'RolePermissionGetResponse',
    'RolePermissionEditRequest',
    'RolePermissionEditResponse'
]
