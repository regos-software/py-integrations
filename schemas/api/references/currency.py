"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Currency(RegosModel):
    "Модель, описывающая валюты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id валюты")
    code_num: int | None = PydField(default=None, description="Цифровой код валюты")
    code_chr: str | None = PydField(default=None, description="Буквенный код валюты")
    name: str | None = PydField(default=None, description="Наименование валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты по отношению к основной")
    is_base: bool | None = PydField(default=None, description="Метка валюты о том, что валюта основная")
    deleted: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class CurrencyAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code_num: int | None = PydField(default=None, description="Цифровой код валюты")
    code_chr: str | None = PydField(default=None, description="Буквенный код валюты")
    name: str | None = PydField(default=None, description="Наименование валюты")


class CurrencyDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id валюты")


class CurrencyEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id валюты")
    code_num: int | None = PydField(default=None, description="Цифровой код валюты")
    code_chr: str | None = PydField(default=None, description="Буквенный код валюты")
    name: str | None = PydField(default=None, description="Наименование валюты")


class CurrencyEditExchangeRate(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты по отношению к основной")


class CurrencyGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив с ID валют")
    sort_orders: list[CurrencySortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по: name (наименование), code_chr (Буквенный код)")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CurrencyRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Currency] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class CurrencySortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: CurrencySortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class CurrencySortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    Name = "Name"
    CodeNum = "CodeNum"
    CodeChr = "CodeChr"
    ExchangeRate = "ExchangeRate"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


CurrencyAddRequest: TypeAlias = CurrencyAdd
CurrencyAddResponse: TypeAlias = InsertResult
CurrencyDeleteRequest: TypeAlias = CurrencyDelete
CurrencyDeleteResponse: TypeAlias = UpdateResult
CurrencyEditExchangeRateRequest: TypeAlias = CurrencyEditExchangeRate
CurrencyEditExchangeRateResponse: TypeAlias = UpdateResult
CurrencyEditRequest: TypeAlias = CurrencyEdit
CurrencyEditResponse: TypeAlias = UpdateResult
CurrencyGetRequest: TypeAlias = CurrencyGet
CurrencyGetResponse: TypeAlias = CurrencyRegosOffsettedArrayResult


_MODEL_NAMES = ['Currency', 'CurrencyAdd', 'CurrencyDelete', 'CurrencyEdit', 'CurrencyEditExchangeRate', 'CurrencyGet', 'CurrencyRegosOffsettedArrayResult', 'CurrencySortOrder']


__all__ = [
    'Currency',
    'CurrencyAdd',
    'CurrencyDelete',
    'CurrencyEdit',
    'CurrencyEditExchangeRate',
    'CurrencyGet',
    'CurrencyRegosOffsettedArrayResult',
    'CurrencySortOrder',
    'CurrencySortOrderColumn',
    'CurrencyGetRequest',
    'CurrencyGetResponse',
    'CurrencyAddRequest',
    'CurrencyAddResponse',
    'CurrencyEditRequest',
    'CurrencyEditResponse',
    'CurrencyDeleteRequest',
    'CurrencyDeleteResponse',
    'CurrencyEditExchangeRateRequest',
    'CurrencyEditExchangeRateResponse'
]
