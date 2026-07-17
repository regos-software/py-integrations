"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class BarcodeType(RegosModel):
    "Модель, описывающая типы штрих-кодов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id типа штрих-кода")
    name: str | None = PydField(default=None, description="Наименование типа штрих-кода")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class BarcodeTypeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[BarcodeType] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


BarcodeTypeGetResponse: TypeAlias = BarcodeTypeRegosArrayResult


_MODEL_NAMES = ['BarcodeType', 'BarcodeTypeRegosArrayResult']


__all__ = [
    'BarcodeType',
    'BarcodeTypeRegosArrayResult',
    'BarcodeTypeGetResponse'
]
