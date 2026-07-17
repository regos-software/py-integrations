"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ItemPrice(RegosModel):
    "Модель, описывающая цены номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="Id номенклатуры")
    price_type: PriceType | None = PydField(default=None, description="Тип цены")
    value: _Decimal | None = PydField(default=None, description="Значение цены")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class ItemPriceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_ids: list[int] | None = PydField(default=None, description="Массив id номенклатуры")
    price_type_ids: list[int] | None = PydField(default=None, description="Массив id типа цены")


class ItemPriceRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemPrice] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.references.item import ItemPreCostArrayRegosObjectResult, ItemPreCostGet
from schemas.api.references.price_type import PriceType


ItemPriceGetPreCostRequest: TypeAlias = ItemPreCostGet
ItemPriceGetPreCostResponse: TypeAlias = ItemPreCostArrayRegosObjectResult
ItemPriceGetRequest: TypeAlias = ItemPriceGet
ItemPriceGetResponse: TypeAlias = ItemPriceRegosArrayResult


_MODEL_NAMES = ['ItemPrice', 'ItemPriceGet', 'ItemPriceRegosArrayResult']


__all__ = [
    'ItemPrice',
    'ItemPriceGet',
    'ItemPriceRegosArrayResult',
    'ItemPriceGetRequest',
    'ItemPriceGetResponse',
    'ItemPriceGetPreCostRequest',
    'ItemPriceGetPreCostResponse'
]
