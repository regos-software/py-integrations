"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class EditedExchangeRateLog(RegosModel):
    "Модель, описывающая лог изменений курса валюты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID зиписи лога")
    user: User | None = PydField(default=None, description="Пользователь, вносивший изменение")
    currency: Currency | None = PydField(default=None, description="Валюта")
    date: int | None = PydField(default=None, description="Дата внесения изменения в курс валюты в unix time")
    value: _Decimal | None = PydField(default=None, description="Значение курса")
    last_update: int | None = PydField(default=None, description="Дата изменени в unix time")


class EditedExchangeRateLogGet(RegosModel):
    "Модель запроса истории изменения курса."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    currency_id: int | None = PydField(default=None, description="ID вылюты")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class EditedExchangeRateLogRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[EditedExchangeRateLog] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency


EditedExchangeRateLogGetRequest: TypeAlias = EditedExchangeRateLogGet
EditedExchangeRateLogGetResponse: TypeAlias = EditedExchangeRateLogRegosOffsettedArrayResult


_MODEL_NAMES = ['EditedExchangeRateLog', 'EditedExchangeRateLogGet', 'EditedExchangeRateLogRegosOffsettedArrayResult']


__all__ = [
    'EditedExchangeRateLog',
    'EditedExchangeRateLogGet',
    'EditedExchangeRateLogRegosOffsettedArrayResult',
    'EditedExchangeRateLogGetRequest',
    'EditedExchangeRateLogGetResponse'
]
