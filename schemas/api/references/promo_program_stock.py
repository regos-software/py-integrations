"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Promo_ProgramStock(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    program_id: int | None = PydField(default=None)
    stock: Stock | None = PydField(default=None, description="Модель, описывающая склады")
    last_update: int | None = PydField(default=None)


class Promo_ProgramStockRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Promo_ProgramStock] | Error | None = PydField(default=None, description="Массив результата.")


class Promo_ProgramStock_Get(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    program_id: int | None = PydField(default=None, description="ID промоакции")


class Promo_ProgramStock_Remove(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    program_id: int | None = PydField(default=None, description="Id промоакции")
    stock_id: int | None = PydField(default=None, description="Id склада")


class Promo_ProgramStock_Set(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    program_id: int | None = PydField(default=None, description="ID промоакции")
    stock_id: int | None = PydField(default=None, description="ID склада")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.references.stock import Stock


PromoProgramStockDeleteRequest: TypeAlias = list[Promo_ProgramStock_Remove]
PromoProgramStockDeleteResponse: TypeAlias = UpdateResult
PromoProgramStockGetRequest: TypeAlias = Promo_ProgramStock_Get
PromoProgramStockGetResponse: TypeAlias = Promo_ProgramStockRegosArrayResult
PromoProgramStockSetRequest: TypeAlias = list[Promo_ProgramStock_Set]
PromoProgramStockSetResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['Promo_ProgramStock', 'Promo_ProgramStockRegosArrayResult', 'Promo_ProgramStock_Get', 'Promo_ProgramStock_Remove', 'Promo_ProgramStock_Set']


__all__ = [
    'Promo_ProgramStock',
    'Promo_ProgramStockRegosArrayResult',
    'Promo_ProgramStock_Get',
    'Promo_ProgramStock_Remove',
    'Promo_ProgramStock_Set',
    'PromoProgramStockGetRequest',
    'PromoProgramStockGetResponse',
    'PromoProgramStockSetRequest',
    'PromoProgramStockSetResponse',
    'PromoProgramStockDeleteRequest',
    'PromoProgramStockDeleteResponse'
]
