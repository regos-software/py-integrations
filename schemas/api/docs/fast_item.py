"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RegosOnlineFastItem(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id")
    item_id: int | None = PydField(default=None, description="id номенклатуры")
    name: str | None = PydField(default=None, description="наименование номенклатуры")
    code: int | None = PydField(default=None, description="Код номенклатуры")
    articul: str | None = PydField(default=None, description="Артикул номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    image_url: str | None = PydField(default=None, description="URL изображения")


class RegosOnlineFastItemAdd(RegosModel):
    "Добавление быстрого товара"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    group_id: int | None = PydField(default=None, description="ID группы быстрых товаров")


class RegosOnlineFastItemArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RegosOnlineFastItem] | Error | None = PydField(default=None, description="Объект результата.")


class RegosOnlineFastItemGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп быстрых товаров")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, InsertResult, SingleObjectResult


FastItemAddRequest: TypeAlias = RegosOnlineFastItemAdd
FastItemAddResponse: TypeAlias = InsertResult
FastItemDeleteRequest: TypeAlias = Base_ID
FastItemDeleteResponse: TypeAlias = SingleObjectResult
FastItemGetRequest: TypeAlias = RegosOnlineFastItemGet
FastItemGetResponse: TypeAlias = RegosOnlineFastItemArrayRegosObjectResult


_MODEL_NAMES = ['RegosOnlineFastItem', 'RegosOnlineFastItemAdd', 'RegosOnlineFastItemArrayRegosObjectResult', 'RegosOnlineFastItemGet']


__all__ = [
    'RegosOnlineFastItem',
    'RegosOnlineFastItemAdd',
    'RegosOnlineFastItemArrayRegosObjectResult',
    'RegosOnlineFastItemGet',
    'FastItemGetRequest',
    'FastItemGetResponse',
    'FastItemAddRequest',
    'FastItemAddResponse',
    'FastItemDeleteRequest',
    'FastItemDeleteResponse'
]
