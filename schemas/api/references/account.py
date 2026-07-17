"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Account(RegosModel):
    "Модель, описывающая счета"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счета")
    code: str | None = PydField(default=None, description="Код счета")
    name: str | None = PydField(default=None, description="Наименование счета")
    currency: Currency | None = PydField(default=None, description="Валюта счета")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class AccountAdd(RegosModel):
    "Модель добавления счета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: str | None = PydField(default=None, description="Код счета")
    name: str | None = PydField(default=None, description="Наименование счета")
    currency_id: int | None = PydField(default=None, description="Id валюты счета")


class AccountDelete(RegosModel):
    "Модель удаления счета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID счета")


class AccountEdit(RegosModel):
    "Модель изменения счета."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id счета")
    code: str | None = PydField(default=None, description="Код счета")
    name: str | None = PydField(default=None, description="Наименование счета")
    currency_id: int | None = PydField(default=None, description="Id валюты счета")


class AccountGet(RegosModel):
    "Модель запроса списка счетов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив id счетов")
    firm_id: int | None = PydField(default=None, description="id предприятия")
    currency_ids: list[int] | None = PydField(default=None, description="массив id валют")
    sort_orders: list[AccountSortOrder] | None = PydField(default=None, description="Сортировка выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полю name")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class AccountRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Account] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class AccountSortOrder(RegosModel):
    "Настройка сортировки списка счетов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: AccountSortOrderColumn | None = PydField(default=None, description="Колонка сортировки.")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки.")


class AccountSortOrderColumn(str, Enum):
    "Колонки сортировки при получении счетов."
    Default = "Default"
    Id = "Id"
    Name = "Name"
    Code = "Code"
    CurrencyName = "CurrencyName"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.references.currency import Currency


AccountAddRequest: TypeAlias = AccountAdd
AccountAddResponse: TypeAlias = InsertResult
AccountDeleteRequest: TypeAlias = AccountDelete
AccountDeleteResponse: TypeAlias = UpdateResult
AccountEditRequest: TypeAlias = AccountEdit
AccountEditResponse: TypeAlias = UpdateResult
AccountGetRequest: TypeAlias = AccountGet
AccountGetResponse: TypeAlias = AccountRegosOffsettedArrayResult


_MODEL_NAMES = ['Account', 'AccountAdd', 'AccountDelete', 'AccountEdit', 'AccountGet', 'AccountRegosOffsettedArrayResult', 'AccountSortOrder']


__all__ = [
    'Account',
    'AccountAdd',
    'AccountDelete',
    'AccountEdit',
    'AccountGet',
    'AccountRegosOffsettedArrayResult',
    'AccountSortOrder',
    'AccountSortOrderColumn',
    'AccountGetRequest',
    'AccountGetResponse',
    'AccountAddRequest',
    'AccountAddResponse',
    'AccountEditRequest',
    'AccountEditResponse',
    'AccountDeleteRequest',
    'AccountDeleteResponse'
]
