"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Country(RegosModel):
    "Модель, описывающая существующие страны в системе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID языка")
    name: str | None = PydField(default=None, description="Наименование страны")
    fullname: str | None = PydField(default=None, description="Полное наименование страны")
    code: str | None = PydField(default=None, description="Код страны по стандарту ISO 639-3")
    alfa2: str | None = PydField(default=None, description="Двузначный код страны")
    alfa3: str | None = PydField(default=None, description="Трехзначный код страны")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления записи в формате Unix time в секундах")


class CountryAdd(RegosModel):
    "Модель добавления страны."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование страны")
    fullname: str | None = PydField(default=None, description="Полное наименование страны")
    code: str | None = PydField(default=None, description="Код страны по стандарту ISO 639-3")
    alfa2: str | None = PydField(default=None, description="Двузначный код страны")
    alfa3: str | None = PydField(default=None, description="Трехзначный код страны")


class CountryDelete(RegosModel):
    "Модель удаления страны."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id страны")


class CountryEdit(RegosModel):
    "Модель изменения страны."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id страны")
    name: str | None = PydField(default=None, description="Наименование страны")
    fullname: str | None = PydField(default=None, description="Полное наименование страны")
    code: str | None = PydField(default=None, description="Код страны по стандарту ISO 639-3")
    alfa2: str | None = PydField(default=None, description="Двузначный код страны")
    alfa3: str | None = PydField(default=None, description="Трехзначный код страны")


class CountryGet(RegosModel):
    "Модель запроса списка стран."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id стран")
    code: list[str] | None = PydField(default=None, description="Массив кодов стран")
    sort_orders: list[CountrySortOrder] | None = PydField(default=None, description="Сортировки выходных данных")
    search: str | None = PydField(default=None, description="Строка поиска по полям name, fullname, alfa2, alfa3")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CountryRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Country] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class CountrySortOrder(RegosModel):
    "Настройка сортировки списка стран."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: CountrySortOrderColumn | None = PydField(default=None, description="Колонка сортировки.")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки.")


class CountrySortOrderColumn(str, Enum):
    "Колонки сортировки стран."
    Default = "Default"
    Id = "Id"
    Name = "Name"
    FullName = "FullName"
    Code = "Code"
    Alfa2 = "Alfa2"
    Alfa3 = "Alfa3"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


CountryAddRequest: TypeAlias = CountryAdd
CountryAddResponse: TypeAlias = InsertResult
CountryDeleteRequest: TypeAlias = CountryDelete
CountryDeleteResponse: TypeAlias = UpdateResult
CountryEditRequest: TypeAlias = CountryEdit
CountryEditResponse: TypeAlias = UpdateResult
CountryGetRequest: TypeAlias = CountryGet
CountryGetResponse: TypeAlias = CountryRegosOffsettedArrayResult


_MODEL_NAMES = ['Country', 'CountryAdd', 'CountryDelete', 'CountryEdit', 'CountryGet', 'CountryRegosOffsettedArrayResult', 'CountrySortOrder']


__all__ = [
    'Country',
    'CountryAdd',
    'CountryDelete',
    'CountryEdit',
    'CountryGet',
    'CountryRegosOffsettedArrayResult',
    'CountrySortOrder',
    'CountrySortOrderColumn',
    'CountryGetRequest',
    'CountryGetResponse',
    'CountryAddRequest',
    'CountryAddResponse',
    'CountryEditRequest',
    'CountryEditResponse',
    'CountryDeleteRequest',
    'CountryDeleteResponse'
]
