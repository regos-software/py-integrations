"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class TaxVat(RegosModel):
    "Модель, описывающая cтавки НДС"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id ставки")
    value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    name: str | None = PydField(default=None, description="Наименование ставки НДС")
    enabled: bool | None = PydField(default=None, description="Метка о том, что ставка НДС доступна к использованию")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class TaxVatAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    name: str | None = PydField(default=None, description="Наименование ставки НДС")
    enabled: bool | None = PydField(default=None, description="Метка о том, что ставка НДС доступна к использованию")


class TaxVatDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id ставки НДС")


class TaxVatEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID группы")
    value: _Decimal | None = PydField(default=None, description="Значение ставки НДС")
    name: str | None = PydField(default=None, description="Наименование ставки НДС")
    enabled: bool | None = PydField(default=None, description="Метка о том, что ставка НДС доступна к использованию")


class TaxVatGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив id ставок НДС")
    enabled: bool | None = PydField(default=None, description="Фильтр по признаку доступности ставки НДС")


class TaxVatRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[TaxVat] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


TaxVatAddRequest: TypeAlias = TaxVatAdd
TaxVatAddResponse: TypeAlias = InsertResult
TaxVatDeleteRequest: TypeAlias = TaxVatDelete
TaxVatDeleteResponse: TypeAlias = UpdateResult
TaxVatEditRequest: TypeAlias = TaxVatEdit
TaxVatEditResponse: TypeAlias = UpdateResult
TaxVatGetRequest: TypeAlias = TaxVatGet
TaxVatGetResponse: TypeAlias = TaxVatRegosArrayResult


_MODEL_NAMES = ['TaxVat', 'TaxVatAdd', 'TaxVatDelete', 'TaxVatEdit', 'TaxVatGet', 'TaxVatRegosArrayResult']


__all__ = [
    'TaxVat',
    'TaxVatAdd',
    'TaxVatDelete',
    'TaxVatEdit',
    'TaxVatGet',
    'TaxVatRegosArrayResult',
    'TaxVatGetRequest',
    'TaxVatGetResponse',
    'TaxVatAddRequest',
    'TaxVatAddResponse',
    'TaxVatEditRequest',
    'TaxVatEditResponse',
    'TaxVatDeleteRequest',
    'TaxVatDeleteResponse'
]
