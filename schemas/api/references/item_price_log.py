"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ItemPriceLog(RegosModel):
    "Модель, описывающая историю изменения цен номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id цены номенклатуры")
    item_id: int | None = PydField(default=None, description="Id номенклатуры")
    document_date: int | None = PydField(default=None, description="Дата документа, согласно которому изменялась цена")
    document_type_id: int | None = PydField(default=None, description="Id типа документа, согласно которому изменялась цена")
    document_id: int | None = PydField(default=None, description="Id документа, согласно которому изменялась цена")
    document_type_name: str | None = PydField(default=None, description="Код типа документа, согласно которому изменялась цена")
    document_type_name_var: str | None = PydField(default=None, description="Ключ перевода типа документа, согласно которому изменялась цена")
    document_code: str | None = PydField(default=None, description="Код документа, согласно которому изменялась цена")
    doc_date: int | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_date")
    doc_type_name: str | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_type_name")
    doc_type_name_var: str | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_type_name_var")
    doc_code: str | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_code")
    value: _Decimal | None = PydField(default=None, description="Значение цены")
    price_type: PriceType | None = PydField(default=None, description="Тип цены")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class ItemPriceLogGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_ids: list[int] | None = PydField(default=None, description="Массив id номенклатуры")
    price_type_ids: list[int] | None = PydField(default=None, description="Массив id типа цены")


class ItemPriceLogRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemPriceLog] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.references.price_type import PriceType


ItemPriceLogGetRequest: TypeAlias = ItemPriceLogGet
ItemPriceLogGetResponse: TypeAlias = ItemPriceLogRegosArrayResult


_MODEL_NAMES = ['ItemPriceLog', 'ItemPriceLogGet', 'ItemPriceLogRegosArrayResult']


__all__ = [
    'ItemPriceLog',
    'ItemPriceLogGet',
    'ItemPriceLogRegosArrayResult',
    'ItemPriceLogGetRequest',
    'ItemPriceLogGetResponse'
]
