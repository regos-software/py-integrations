"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailCardGroup(RegosModel):
    "Модель, описывающая группы карт покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) групп")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class RetailCardGroupAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской группы. Значение по умолчанию 0 - корневая группа")
    name: str | None = PydField(default=None, description="Наименование группы")


class RetailCardGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardGroup] | Error | None = PydField(default=None, description="Объект результата.")


class RetailCardGroupDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")


class RetailCardGroupEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID группы")
    parent_id: int | None = PydField(default=None, description="ID родительской группы")
    name: str | None = PydField(default=None, description="Имя группы")


class RetailCardGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительских групп")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


RetailCardGroupAddRequest: TypeAlias = RetailCardGroupAdd
RetailCardGroupAddResponse: TypeAlias = InsertResult
RetailCardGroupDeleteRequest: TypeAlias = RetailCardGroupDelete
RetailCardGroupDeleteResponse: TypeAlias = UpdateResult
RetailCardGroupEditRequest: TypeAlias = RetailCardGroupEdit
RetailCardGroupEditResponse: TypeAlias = UpdateResult
RetailCardGroupGetRequest: TypeAlias = RetailCardGroupGet
RetailCardGroupGetResponse: TypeAlias = RetailCardGroupArrayRegosObjectResult


_MODEL_NAMES = ['RetailCardGroup', 'RetailCardGroupAdd', 'RetailCardGroupArrayRegosObjectResult', 'RetailCardGroupDelete', 'RetailCardGroupEdit', 'RetailCardGroupGet']


__all__ = [
    'RetailCardGroup',
    'RetailCardGroupAdd',
    'RetailCardGroupArrayRegosObjectResult',
    'RetailCardGroupDelete',
    'RetailCardGroupEdit',
    'RetailCardGroupGet',
    'RetailCardGroupGetRequest',
    'RetailCardGroupGetResponse',
    'RetailCardGroupAddRequest',
    'RetailCardGroupAddResponse',
    'RetailCardGroupEditRequest',
    'RetailCardGroupEditResponse',
    'RetailCardGroupDeleteRequest',
    'RetailCardGroupDeleteResponse'
]
