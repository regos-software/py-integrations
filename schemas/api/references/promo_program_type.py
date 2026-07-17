"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PromoProgramType(RegosModel):
    "Модель, описывающая типы промоакций"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id типа промоакции")
    name: str | None = PydField(default=None, description="Наименование типа промоакции")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class PromoProgramTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="id типа промоакции")


class PromoProgramTypeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PromoProgramType] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


PromoProgramTypeGetRequest: TypeAlias = PromoProgramTypeGet
PromoProgramTypeGetResponse: TypeAlias = PromoProgramTypeRegosArrayResult


_MODEL_NAMES = ['PromoProgramType', 'PromoProgramTypeGet', 'PromoProgramTypeRegosArrayResult']


__all__ = [
    'PromoProgramType',
    'PromoProgramTypeGet',
    'PromoProgramTypeRegosArrayResult',
    'PromoProgramTypeGetRequest',
    'PromoProgramTypeGetResponse'
]
