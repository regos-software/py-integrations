"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocPaymentAggregation(RegosModel):
    "Модель, описывающая документы агрегированных платежей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа агрегированных платежей")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    type: PaymentType | None = PydField(default=None, description="Форма оплаты")
    amount: _Decimal | None = PydField(default=None, description="Сумма оплат")
    performed: bool | None = PydField(default=None, description="Метка о том, что документ проведен")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocPaymentAggregationColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocPaymentAggregationColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocPaymentAggregationColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    FirmName = "FirmName"
    Date = "Date"
    Code = "Code"
    TypeName = "TypeName"
    Amount = "Amount"
    Performed = "Performed"
    LastUpdate = "LastUpdate"


class DocPaymentAggregationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов агрегированных платежей")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предпреятий")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах. Учитывается только при одновременной передаче end_date")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах. Учитывается только при одновременной передаче start_date")
    sort_orders: list[DocPaymentAggregationColumn] | None = PydField(default=None, description="Сортировка выходных данных")
    performed: bool | None = PydField(default=None, description="Состояние проведение документа: true - Проведён, false - Не проведён")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию и максимум задаются серверной настройкой query_limit")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocPaymentAggregationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocPaymentAggregation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error
from schemas.api.references.firm import Firm
from schemas.api.references.payment_type import PaymentType


DocPaymentAggregationGetRequest: TypeAlias = DocPaymentAggregationGet
DocPaymentAggregationGetResponse: TypeAlias = DocPaymentAggregationRegosOffsettedArrayResult


_MODEL_NAMES = ['DocPaymentAggregation', 'DocPaymentAggregationColumn', 'DocPaymentAggregationGet', 'DocPaymentAggregationRegosOffsettedArrayResult']


__all__ = [
    'DocPaymentAggregation',
    'DocPaymentAggregationColumn',
    'DocPaymentAggregationColumns',
    'DocPaymentAggregationGet',
    'DocPaymentAggregationRegosOffsettedArrayResult',
    'DocPaymentAggregationGetRequest',
    'DocPaymentAggregationGetResponse'
]
