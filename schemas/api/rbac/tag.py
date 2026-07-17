"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Tag(RegosModel):
    "Модель, описывающая шаблоны ценников"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id ценника")
    name: str | None = PydField(default=None, description="Наименование шаблона ценника")
    data: str | None = PydField(default=None, description="Данные шаблона в текстовом формате")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime")


class TagAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование шаблона ценника")
    data: str | None = PydField(default=None, description="Данные шаблона в текстовом формате")


class TagDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id шаблона ценников")


class TagEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID шаблона ценников")
    name: str | None = PydField(default=None, description="Наименование шаблона ценников")
    data: str | None = PydField(default=None, description="Данные шаблона в текстовом формате")


class TagGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID шаблона ценников")
    include_data: bool | None = PydField(default=None, description="Включить данные шаблона цкнника в ответе: true - включить, true - не включать")


class TagRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Tag] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


TagAddRequest: TypeAlias = TagAdd
TagAddResponse: TypeAlias = InsertResult
TagDeleteRequest: TypeAlias = TagDelete
TagDeleteResponse: TypeAlias = UpdateResult
TagEditRequest: TypeAlias = TagEdit
TagEditResponse: TypeAlias = UpdateResult
TagGetRequest: TypeAlias = TagGet
TagGetResponse: TypeAlias = TagRegosArrayResult


_MODEL_NAMES = ['Tag', 'TagAdd', 'TagDelete', 'TagEdit', 'TagGet', 'TagRegosArrayResult']


__all__ = [
    'Tag',
    'TagAdd',
    'TagDelete',
    'TagEdit',
    'TagGet',
    'TagRegosArrayResult',
    'TagGetRequest',
    'TagGetResponse',
    'TagAddRequest',
    'TagAddResponse',
    'TagEditRequest',
    'TagEditResponse',
    'TagDeleteRequest',
    'TagDeleteResponse'
]
