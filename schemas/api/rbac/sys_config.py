"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class SysConfig(RegosModel):
    "Модель, описывающая настройки системы"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id настройки")
    key: str | None = PydField(default=None, description="Ключ настройки")
    value: str | None = PydField(default=None, description="Значение ключа настройки")
    name: str | None = PydField(default=None, description="Наименование ключа")
    name_var: str | None = PydField(default=None, description="Наименование (ключ из переводов)")
    dataType: DataType | None = PydField(default=None, description="Тип данных, использующийся в значении ключа value: <Integer | 1> - Целое число, <Float | 2> - Число с\nплавающей точкой, <String | 3> - Строка, <DateTime | 4> - Дата и время")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class SysConfigArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[SysConfig] | Error | None = PydField(default=None, description="Объект результата.")


class SysConfigEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ настройки")
    value: str | None = PydField(default=None, description="Значение ключа настройки")


class SysConfigGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id настроек")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import DataType, Error, UpdateResult


SysConfigEditRequest: TypeAlias = list[SysConfigEdit]
SysConfigEditResponse: TypeAlias = UpdateResult
SysConfigGetRequest: TypeAlias = SysConfigGet
SysConfigGetResponse: TypeAlias = SysConfigArrayRegosObjectResult


_MODEL_NAMES = ['SysConfig', 'SysConfigArrayRegosObjectResult', 'SysConfigEdit', 'SysConfigGet']


__all__ = [
    'SysConfig',
    'SysConfigArrayRegosObjectResult',
    'SysConfigEdit',
    'SysConfigGet',
    'SysConfigGetRequest',
    'SysConfigGetResponse',
    'SysConfigEditRequest',
    'SysConfigEditResponse'
]
