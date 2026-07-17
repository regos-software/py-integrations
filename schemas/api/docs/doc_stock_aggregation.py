"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocStockAggregation(RegosModel):
    "Модель, описывающая документы агрегированных операций по складу"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа агрегированных операций по складу")
    code: str | None = PydField(default=None, description="Код документа")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock: Stock | None = PydField(default=None, description="Склад")
    amount: _Decimal | None = PydField(default=None, description="Сумма цен номенклатуры")
    amount2: _Decimal | None = PydField(default=None, description="Сумма цен номенклатуры без скидки")
    performed: bool | None = PydField(default=None, description="Метка о то, что документ проведен")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocStockAggregationColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocStockAggregationColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocStockAggregationColumns(str, Enum):
    Default = "Default"
    Uuid = "Uuid"
    Code = "Code"
    Date = "Date"
    StockName = "StockName"
    Amount = "Amount"
    Amount2 = "Amount2"
    Performed = "Performed"
    LastUpdate = "LastUpdate"


class DocStockAggregationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов агрегированных операций по складу")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    sort_orders: list[DocStockAggregationColumn] | None = PydField(default=None, description="Сортировка выходных данных")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocStockAggregationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocStockAggregation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error
from schemas.api.references.stock import Stock


DocStockAggregationGetRequest: TypeAlias = DocStockAggregationGet
DocStockAggregationGetResponse: TypeAlias = DocStockAggregationRegosOffsettedArrayResult


_MODEL_NAMES = ['DocStockAggregation', 'DocStockAggregationColumn', 'DocStockAggregationGet', 'DocStockAggregationRegosOffsettedArrayResult']


__all__ = [
    'DocStockAggregation',
    'DocStockAggregationColumn',
    'DocStockAggregationColumns',
    'DocStockAggregationGet',
    'DocStockAggregationRegosOffsettedArrayResult',
    'DocStockAggregationGetRequest',
    'DocStockAggregationGetResponse'
]
