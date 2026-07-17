"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class UserRole(RegosModel):
    "Модель, описывающая роли пользователя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id записи в таблице")
    user_id: int | None = PydField(default=None, description="Id пользователя в системе")
    role: Role | None = PydField(default=None, description="Роль")


class UserRoleGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя в системе")


class UserRoleRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[UserRole] | Error | None = PydField(default=None, description="Массив результата.")


class UserRoleRemove(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id роли пользователя")


class UserRoleSet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя")
    role_id: int | None = PydField(default=None, description="ID роли")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.rbac.role import Role


UserRoleGetRequest: TypeAlias = UserRoleGet
UserRoleGetResponse: TypeAlias = UserRoleRegosArrayResult
UserRoleRemoveRequest: TypeAlias = UserRoleRemove
UserRoleRemoveResponse: TypeAlias = UpdateResult
UserRoleSetRequest: TypeAlias = UserRoleSet
UserRoleSetResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['UserRole', 'UserRoleGet', 'UserRoleRegosArrayResult', 'UserRoleRemove', 'UserRoleSet']


__all__ = [
    'UserRole',
    'UserRoleGet',
    'UserRoleRegosArrayResult',
    'UserRoleRemove',
    'UserRoleSet',
    'UserRoleGetRequest',
    'UserRoleGetResponse',
    'UserRoleSetRequest',
    'UserRoleSetResponse',
    'UserRoleRemoveRequest',
    'UserRoleRemoveResponse'
]
