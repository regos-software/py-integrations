"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PermissionGroup(RegosModel):
    "Модель, описывающая группы прав доступа пользователей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы прав доступа")
    parent_id: int | None = PydField(default=None, description="Id родительской группы прав доступа")
    name: str | None = PydField(default=None, description="Наименование группы прав доступа")
    order: int | None = PydField(default=None, description="Порядковый номер права доступа")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class PermissionGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп прав доступа пользователей")


class PermissionGroupRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PermissionGroup] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


PermissionGroupGetRequest: TypeAlias = PermissionGroupGet
PermissionGroupGetResponse: TypeAlias = PermissionGroupRegosArrayResult


_MODEL_NAMES = ['PermissionGroup', 'PermissionGroupGet', 'PermissionGroupRegosArrayResult']


__all__ = [
    'PermissionGroup',
    'PermissionGroupGet',
    'PermissionGroupRegosArrayResult',
    'PermissionGroupGetRequest',
    'PermissionGroupGetResponse'
]
