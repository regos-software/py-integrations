"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailCustomerGroup(RegosModel):
    "Модель, описывающая группы покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")
    parent_id: int | None = PydField(default=None, description="Id родительской группы")
    name: str | None = PydField(default=None, description="Наименование группы")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) групп")


class RetailCustomerGroupAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской группы. По умолчанию 0")
    name: str | None = PydField(default=None, description="Наименование группы")


class RetailCustomerGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCustomerGroup] | Error | None = PydField(default=None, description="Объект результата.")


class RetailCustomerGroupDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id группы в системе")


class RetailCustomerGroupEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID группы")
    parent_id: int | None = PydField(default=None, description="ID родительской группы")
    name: str | None = PydField(default=None, description="Имя группы")


class RetailCustomerGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительских групп")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


RetailCustomerGroupAddRequest: TypeAlias = RetailCustomerGroupAdd
RetailCustomerGroupAddResponse: TypeAlias = InsertResult
RetailCustomerGroupDeleteRequest: TypeAlias = RetailCustomerGroupDelete
RetailCustomerGroupDeleteResponse: TypeAlias = UpdateResult
RetailCustomerGroupEditRequest: TypeAlias = RetailCustomerGroupEdit
RetailCustomerGroupEditResponse: TypeAlias = UpdateResult
RetailCustomerGroupGetRequest: TypeAlias = RetailCustomerGroupGet
RetailCustomerGroupGetResponse: TypeAlias = RetailCustomerGroupArrayRegosObjectResult


_MODEL_NAMES = ['RetailCustomerGroup', 'RetailCustomerGroupAdd', 'RetailCustomerGroupArrayRegosObjectResult', 'RetailCustomerGroupDelete', 'RetailCustomerGroupEdit', 'RetailCustomerGroupGet']


__all__ = [
    'RetailCustomerGroup',
    'RetailCustomerGroupAdd',
    'RetailCustomerGroupArrayRegosObjectResult',
    'RetailCustomerGroupDelete',
    'RetailCustomerGroupEdit',
    'RetailCustomerGroupGet',
    'RetailCustomerGroupGetRequest',
    'RetailCustomerGroupGetResponse',
    'RetailCustomerGroupAddRequest',
    'RetailCustomerGroupAddResponse',
    'RetailCustomerGroupEditRequest',
    'RetailCustomerGroupEditResponse',
    'RetailCustomerGroupDeleteRequest',
    'RetailCustomerGroupDeleteResponse'
]
