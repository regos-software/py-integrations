"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RegosOnlineCashAmountDetailsGet(RegosModel):
    "Получение деталей по кассе из Regos Online"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Конечная дата в формате Unix time в секундах")


class RegosOnlineCashOperationAdd(RegosModel):
    "Модель для добавления кассовой операции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    payment_type_id: int | None = PydField(default=None, description="ID формы оплаты (только наличная форма оплаты)")
    value: _Decimal | None = PydField(default=None, description="Значение изымаемой суммы")
    description: str | None = PydField(default=None, description="Комментарий")


class RegosOnlineCashOperationGet(RegosModel):
    "Модель для получения операций кассового журанала из Regos Online"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Конечная дата в формате Unix time в секундах")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RegosOnlineCashOperationPaymentAdd(RegosModel):
    "Добавление операции \"платёж из кассы\""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    payment_type_id: int | None = PydField(default=None, description="ID формы оплаты (только наличная форма оплаты)")
    category_id: int | None = PydField(default=None, description="ID категории операции со счетом (статья расходов)")
    partner_id: int | None = PydField(default=None, description="ID клиента (при наличии настройки не обязательное и игнорируется)")
    value: _Decimal | None = PydField(default=None, description="Значение суммы платежа")
    description: str | None = PydField(default=None, description="Комментарий")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CashAmountDetailsRegosObjectResult, InsertResult
from schemas.api.docs.cash_operation import CashOperationRegosOffsettedArrayResult


PosCashOperationGetAmountDetailsRequest: TypeAlias = RegosOnlineCashAmountDetailsGet
PosCashOperationGetAmountDetailsResponse: TypeAlias = CashAmountDetailsRegosObjectResult
PosCashOperationGetRequest: TypeAlias = RegosOnlineCashOperationGet
PosCashOperationGetResponse: TypeAlias = CashOperationRegosOffsettedArrayResult
PosCashOperationIncomeAddRequest: TypeAlias = RegosOnlineCashOperationAdd
PosCashOperationIncomeAddResponse: TypeAlias = InsertResult
PosCashOperationOutcomeAddRequest: TypeAlias = RegosOnlineCashOperationAdd
PosCashOperationOutcomeAddResponse: TypeAlias = InsertResult
PosCashOperationPaymentAddRequest: TypeAlias = RegosOnlineCashOperationPaymentAdd
PosCashOperationPaymentAddResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['RegosOnlineCashAmountDetailsGet', 'RegosOnlineCashOperationAdd', 'RegosOnlineCashOperationGet', 'RegosOnlineCashOperationPaymentAdd']


__all__ = [
    'RegosOnlineCashAmountDetailsGet',
    'RegosOnlineCashOperationAdd',
    'RegosOnlineCashOperationGet',
    'RegosOnlineCashOperationPaymentAdd',
    'PosCashOperationGetRequest',
    'PosCashOperationGetResponse',
    'PosCashOperationGetAmountDetailsRequest',
    'PosCashOperationGetAmountDetailsResponse',
    'PosCashOperationIncomeAddRequest',
    'PosCashOperationIncomeAddResponse',
    'PosCashOperationOutcomeAddRequest',
    'PosCashOperationOutcomeAddResponse',
    'PosCashOperationPaymentAddRequest',
    'PosCashOperationPaymentAddResponse'
]
