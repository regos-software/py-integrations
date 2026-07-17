"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ItemOperation(RegosModel):
    "Модель, описывающая историю операций с номенклатурой"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата операции в Unix time в секундах")
    document_id: int | None = PydField(default=None, description="ID документа")
    document_type: DocumentType | None = PydField(default=None, description="Тип документа")
    document_type_name: str | None = PydField(default=None, description="Наименование типа документа")
    document_code: str | None = PydField(default=None, description="Код документа")
    doc_type_name: str | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_type_name")
    doc_code: str | None = PydField(default=None, description="Устаревшее поле. Поддерживается до 16.05.2027. Используйте document_code")
    stock: Stock | None = PydField(default=None, description="Склад")
    quantity: _Decimal | None = PydField(default=None, description="Количество")
    cost: _Decimal | None = PydField(default=None, description="Значение себестоимости")
    additional_expenses_amount: _Decimal | None = PydField(default=None, description="Сумма дополнительных расходов на операцию. Расчитывается на основании документов дополнителных операций")
    price: _Decimal | None = PydField(default=None, description="Значение цены")
    price2: _Decimal | None = PydField(default=None, description="Значение цены без скидки")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты на момент операции")
    positive: bool | None = PydField(default=None, description="Метка операции прихода (true - приход, false - расход)")
    vat_value: _Decimal | None = PydField(default=None, description="Значение НДС")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")


class ItemOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    sort_orders: list[ItemOprOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    start_date: int | None = PydField(default=None, description="Дата начала периода в Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в Unix time в секундах")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ItemOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, VatCalculationTypeEnum
from schemas.api.docs.document_type import DocumentType
from schemas.api.references.item import ItemOprOrder
from schemas.api.references.stock import Stock


ItemOperationGetRequest: TypeAlias = ItemOperationGet
ItemOperationGetResponse: TypeAlias = ItemOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['ItemOperation', 'ItemOperationGet', 'ItemOperationRegosOffsettedArrayResult']


__all__ = [
    'ItemOperation',
    'ItemOperationGet',
    'ItemOperationRegosOffsettedArrayResult',
    'ItemOperationGetRequest',
    'ItemOperationGetResponse'
]
