"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class StockAgregationOperation(RegosModel):
    "Модель, описывающая операции документа агрегированных операций"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID агрегированной операции")
    document_id: int | None = PydField(default=None, description="ID документа агрегированных операций")
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="Количество")
    order: int | None = PydField(default=None, description="Порядок операции")
    price: _Decimal | None = PydField(default=None, description="Стоимость со скидкой")
    price2: _Decimal | None = PydField(default=None, description="Стоимость без скидки")
    vat_value: _Decimal | None = PydField(default=None, description="Ставка НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    last_update: int | None = PydField(default=None, description="Время последнего обновления в unix time")


class StockAgregationOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID агрегированных операций")
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры")
    document_ids: list[int] | None = PydField(default=None, description="Массив ID документов (не более 1 элемента)")
    search: str | None = PydField(default=None, description="Поиск по значениям параметров: Item.name, Item.articul, Item.code, Item.barcodes")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class StockAgregationOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[StockAgregationOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, VatCalculationTypeEnum
from schemas.api.references.item import Item


StockAgregationOperationGetRequest: TypeAlias = StockAgregationOperationGet
StockAgregationOperationGetResponse: TypeAlias = StockAgregationOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['StockAgregationOperation', 'StockAgregationOperationGet', 'StockAgregationOperationRegosOffsettedArrayResult']


__all__ = [
    'StockAgregationOperation',
    'StockAgregationOperationGet',
    'StockAgregationOperationRegosOffsettedArrayResult',
    'StockAgregationOperationGetRequest',
    'StockAgregationOperationGetResponse'
]
