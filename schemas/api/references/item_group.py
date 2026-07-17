"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ItemGroup(RegosModel):
    "Модель, описывающая группы номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    path: str | None = PydField(default=None, description="Путь к группе (вложенные группы разделены символом /)")
    name: str | None = PydField(default=None, description="Наименование группы")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) групп")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class ItemGroupAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской группы. По умолчанию 0")
    name: str | None = PydField(default=None, description="Наименование группы")


class ItemGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemGroup] | Error | None = PydField(default=None, description="Объект результата.")


class ItemGroupDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")


class ItemGroupEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID группы")
    parent_id: int | None = PydField(default=None, description="ID родительской группы")
    name: str | None = PydField(default=None, description="Имя группы")


class ItemGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп номенклатуры")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительских групп номенклатуры")
    name: str | None = PydField(default=None, description="Наименование группы номенклатуры")
    path: str | None = PydField(default=None, description="Путь к группе (вложенные группы разделены символом /)")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


ItemGroupAddRequest: TypeAlias = ItemGroupAdd
ItemGroupAddResponse: TypeAlias = InsertResult
ItemGroupDeleteRequest: TypeAlias = ItemGroupDelete
ItemGroupDeleteResponse: TypeAlias = UpdateResult
ItemGroupEditRequest: TypeAlias = ItemGroupEdit
ItemGroupEditResponse: TypeAlias = UpdateResult
ItemGroupGetRequest: TypeAlias = ItemGroupGet
ItemGroupGetResponse: TypeAlias = ItemGroupArrayRegosObjectResult


_MODEL_NAMES = ['ItemGroup', 'ItemGroupAdd', 'ItemGroupArrayRegosObjectResult', 'ItemGroupDelete', 'ItemGroupEdit', 'ItemGroupGet']


__all__ = [
    'ItemGroup',
    'ItemGroupAdd',
    'ItemGroupArrayRegosObjectResult',
    'ItemGroupDelete',
    'ItemGroupEdit',
    'ItemGroupGet',
    'ItemGroupGetRequest',
    'ItemGroupGetResponse',
    'ItemGroupAddRequest',
    'ItemGroupAddResponse',
    'ItemGroupEditRequest',
    'ItemGroupEditResponse',
    'ItemGroupDeleteRequest',
    'ItemGroupDeleteResponse'
]
