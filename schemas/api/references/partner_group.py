"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PartnerGroup(RegosModel):
    "Модель, описывающая группы контрагентов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) групп")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time")


class PartnerGroupAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")


class PartnerGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PartnerGroup] | Error | None = PydField(default=None, description="Объект результата.")


class PartnerGroupDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")


class PartnerGroupEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id группы")
    parent_id: int | None = PydField(default=None, description="id родительской группы")
    name: str | None = PydField(default=None, description="Имя группы")


class PartnerGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительских групп")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


PartnerGroupAddRequest: TypeAlias = PartnerGroupAdd
PartnerGroupAddResponse: TypeAlias = InsertResult
PartnerGroupDeleteRequest: TypeAlias = PartnerGroupDelete
PartnerGroupDeleteResponse: TypeAlias = UpdateResult
PartnerGroupEditRequest: TypeAlias = PartnerGroupEdit
PartnerGroupEditResponse: TypeAlias = UpdateResult
PartnerGroupGetRequest: TypeAlias = PartnerGroupGet
PartnerGroupGetResponse: TypeAlias = PartnerGroupArrayRegosObjectResult


_MODEL_NAMES = ['PartnerGroup', 'PartnerGroupAdd', 'PartnerGroupArrayRegosObjectResult', 'PartnerGroupDelete', 'PartnerGroupEdit', 'PartnerGroupGet']


__all__ = [
    'PartnerGroup',
    'PartnerGroupAdd',
    'PartnerGroupArrayRegosObjectResult',
    'PartnerGroupDelete',
    'PartnerGroupEdit',
    'PartnerGroupGet',
    'PartnerGroupGetRequest',
    'PartnerGroupGetResponse',
    'PartnerGroupAddRequest',
    'PartnerGroupAddResponse',
    'PartnerGroupEditRequest',
    'PartnerGroupEditResponse',
    'PartnerGroupDeleteRequest',
    'PartnerGroupDeleteResponse'
]
