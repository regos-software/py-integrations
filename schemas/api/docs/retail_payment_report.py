"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailPaymentReport(RegosModel):
    "> Раздел устарел. Поддерживается до 03.04.2027. Используйте Report/AddRequest"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    payment_type: PaymentType | None = PydField(default=None, description="Форма оплаты")
    data: list[RetailPaymentReportData] | None = PydField(default=None, description="Данные отчета")
    payment_amount: _Decimal | None = PydField(default=None, description="Сумма")


class RetailPaymentReportData(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    value: _Decimal | None = PydField(default=None, description="Значение на дату")
    date: str | None = PydField(default=None, description="Дата")


class RetailPaymentReportGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: str | None = PydField(default=None, description="Начальная дата")
    end_date: str | None = PydField(default=None, description="Конечная дата")
    period_interval: RetailPaymentReport_PeriodInterval | None = PydField(default=None, description="Тип периода")
    operating_cash_ids: list[int] | None = PydField(default=None, description="ID касс по которым выбираются данные")


class RetailPaymentReportRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailPaymentReport] | Error | None = PydField(default=None, description="Массив результата.")


class RetailPaymentReport_PeriodInterval(str, Enum):
    Default = "Default"
    Month = "Month"
    Week = "Week"
    Day = "Day"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.references.payment_type import PaymentType


RetailPaymentReportGetRequest: TypeAlias = RetailPaymentReportGet
RetailPaymentReportGetResponse: TypeAlias = RetailPaymentReportRegosArrayResult


_MODEL_NAMES = ['RetailPaymentReport', 'RetailPaymentReportData', 'RetailPaymentReportGet', 'RetailPaymentReportRegosArrayResult']


__all__ = [
    'RetailPaymentReport',
    'RetailPaymentReportData',
    'RetailPaymentReportGet',
    'RetailPaymentReportRegosArrayResult',
    'RetailPaymentReport_PeriodInterval',
    'RetailPaymentReportGetRequest',
    'RetailPaymentReportGetResponse'
]
