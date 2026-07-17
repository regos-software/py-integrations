"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class AccountBalance(RegosModel):
    "Модель, описывающая счета"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    balance: _Decimal | None = PydField(default=None, description="Баланс счёта")
    id: int | None = PydField(default=None, description="ID счета")
    code: str | None = PydField(default=None, description="Код счета")
    name: str | None = PydField(default=None, description="Наименование счета")
    currency: Currency | None = PydField(default=None, description="Валюта счета")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class AccountBalanceRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[AccountBalance] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.references.account import AccountGet
from schemas.api.references.currency import Currency


AccountBalanceGetRequest: TypeAlias = AccountGet
AccountBalanceGetResponse: TypeAlias = AccountBalanceRegosOffsettedArrayResult


_MODEL_NAMES = ['AccountBalance', 'AccountBalanceRegosOffsettedArrayResult']


__all__ = [
    'AccountBalance',
    'AccountBalanceRegosOffsettedArrayResult',
    'AccountBalanceGetRequest',
    'AccountBalanceGetResponse'
]
