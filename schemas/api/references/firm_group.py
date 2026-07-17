"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class FirmGroup(RegosModel):
    "Модель, описывающая группы предприятий"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) групп")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class FirmGroupAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")


class FirmGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[FirmGroup] | Error | None = PydField(default=None, description="Объект результата.")


class FirmGroupDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")


class FirmGroupEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id группы")
    parent_id: int | None = PydField(default=None, description="id родительской группы")
    name: str | None = PydField(default=None, description="Имя группы")


class FirmGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительских групп")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


FirmGroupAddRequest: TypeAlias = FirmGroupAdd
FirmGroupAddResponse: TypeAlias = InsertResult
FirmGroupDeleteRequest: TypeAlias = FirmGroupDelete
FirmGroupDeleteResponse: TypeAlias = UpdateResult
FirmGroupEditRequest: TypeAlias = FirmGroupEdit
FirmGroupEditResponse: TypeAlias = UpdateResult
FirmGroupGetRequest: TypeAlias = FirmGroupGet
FirmGroupGetResponse: TypeAlias = FirmGroupArrayRegosObjectResult


_MODEL_NAMES = ['FirmGroup', 'FirmGroupAdd', 'FirmGroupArrayRegosObjectResult', 'FirmGroupDelete', 'FirmGroupEdit', 'FirmGroupGet']


__all__ = [
    'FirmGroup',
    'FirmGroupAdd',
    'FirmGroupArrayRegosObjectResult',
    'FirmGroupDelete',
    'FirmGroupEdit',
    'FirmGroupGet',
    'FirmGroupGetRequest',
    'FirmGroupGetResponse',
    'FirmGroupAddRequest',
    'FirmGroupAddResponse',
    'FirmGroupEditRequest',
    'FirmGroupEditResponse',
    'FirmGroupDeleteRequest',
    'FirmGroupDeleteResponse'
]
