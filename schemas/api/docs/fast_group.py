"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RegosOnlineFastGroup(RegosModel):
    "Группа быстрых товаров"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id")
    name: str | None = PydField(default=None, description="название")


class RegosOnlineFastGroupAdd(RegosModel):
    "Добавление группы быстрых товаров"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    name: str | None = PydField(default=None, description="Наименование группы быстрых товаров")


class RegosOnlineFastGroupArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RegosOnlineFastGroup] | Error | None = PydField(default=None, description="Объект результата.")


class RegosOnlineFastGroupEdit(RegosModel):
    "Редактирование группы быстрых товаров"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID группы быстрых товаров")
    name: str | None = PydField(default=None, description="Наименование группы быстрых товаров")


class RegosOnlineFastGroupGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id групп быстрых товаров")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, InsertResult, SingleObjectResult


FastGroupAddRequest: TypeAlias = RegosOnlineFastGroupAdd
FastGroupAddResponse: TypeAlias = InsertResult
FastGroupDeleteRequest: TypeAlias = Base_ID
FastGroupDeleteResponse: TypeAlias = SingleObjectResult
FastGroupEditRequest: TypeAlias = RegosOnlineFastGroupEdit
FastGroupEditResponse: TypeAlias = SingleObjectResult
FastGroupGetRequest: TypeAlias = RegosOnlineFastGroupGet
FastGroupGetResponse: TypeAlias = RegosOnlineFastGroupArrayRegosObjectResult


_MODEL_NAMES = ['RegosOnlineFastGroup', 'RegosOnlineFastGroupAdd', 'RegosOnlineFastGroupArrayRegosObjectResult', 'RegosOnlineFastGroupEdit', 'RegosOnlineFastGroupGet']


__all__ = [
    'RegosOnlineFastGroup',
    'RegosOnlineFastGroupAdd',
    'RegosOnlineFastGroupArrayRegosObjectResult',
    'RegosOnlineFastGroupEdit',
    'RegosOnlineFastGroupGet',
    'FastGroupGetRequest',
    'FastGroupGetResponse',
    'FastGroupAddRequest',
    'FastGroupAddResponse',
    'FastGroupEditRequest',
    'FastGroupEditResponse',
    'FastGroupDeleteRequest',
    'FastGroupDeleteResponse'
]
