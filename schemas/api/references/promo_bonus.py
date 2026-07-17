"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PromoBonusCancelPayment(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID операции платежа с карты покупателя")


class PromoBonusCreateEnrollment(RegosModel):
    "Зачисление"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    card_id: int | None = PydField(default=None, description="Id карты покупателя")
    promo_id: int | None = PydField(default=None, description="Id промоакции")
    document_uuid: str | None = PydField(default=None, description="Uuid документа розничной продажи (чека), по которому создаётся платёж")
    is_return: bool | None = PydField(default=None, description="Метка о том, что операция зачисления является возвратом (списание)")
    amount: _Decimal | None = PydField(default=None, description="Сумма к зачислению")


class PromoBonusCreateManualOperation(RegosModel):
    "списание/зачисление бонуса в ручную"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    card_id: int | None = PydField(default=None, description="Id карты покупателя")
    promo_id: int | None = PydField(default=None, description="Id промоакции")
    value: _Decimal | None = PydField(default=None, description="Сумма списания")
    description: str | None = PydField(default=None, description="Дополнительно описание")
    exp_date: int | None = PydField(default=None, description="Дата окончания начисления бонуса в формате unix time в секундах")


class PromoBonusCreatePayment(RegosModel):
    "создание платежа бонусами"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    card_id: int | None = PydField(default=None, description="-")
    promo_id: int | None = PydField(default=None, description="-")
    document_uuid: str | None = PydField(default=None, description="-")
    is_return: bool | None = PydField(default=None, description="-")
    value: _Decimal | None = PydField(default=None, description="-")


class PromoBonusGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="-")


class PromoBonusPerformEnrollment(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID операции зачисления на карту покупателя")


class PromoBonusPerformPayment(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID операции платежа с карты покупателя")


class PromoBonusType(str, Enum):
    Default = "Default"
    Income = "Income"
    Outcome = "Outcome"


class PromoBonusesRemainder(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    value: _Decimal | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class PromoBonusesRemainderGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    card_id: int | None = PydField(default=None, description="Id карты покупателя")
    promo_id: int | None = PydField(default=None, description="Id промоакции")


class PromoBonusesRemainderRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: PromoBonusesRemainder | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result, UpdateResult
from schemas.api.references.retail_card import RetailCardOperationRegosObjectResult


PromoBonusCancelPaymentRequest: TypeAlias = PromoBonusCancelPayment
PromoBonusCancelPaymentResponse: TypeAlias = UpdateResult
PromoBonusCreateEnrollmentRequest: TypeAlias = PromoBonusCreateEnrollment
PromoBonusCreateEnrollmentResponse: TypeAlias = Insert_uuid_Result
PromoBonusCreateManualIncomeOperationRequest: TypeAlias = PromoBonusCreateManualOperation
PromoBonusCreateManualIncomeOperationResponse: TypeAlias = UpdateResult
PromoBonusCreateManualOutcomeOperationRequest: TypeAlias = PromoBonusCreateManualOperation
PromoBonusCreateManualOutcomeOperationResponse: TypeAlias = UpdateResult
PromoBonusCreatePaymentRequest: TypeAlias = PromoBonusCreatePayment
PromoBonusCreatePaymentResponse: TypeAlias = Insert_uuid_Result
PromoBonusGetRequest: TypeAlias = PromoBonusGet
PromoBonusGetResponse: TypeAlias = RetailCardOperationRegosObjectResult
PromoBonusPerformEnrollmentRequest: TypeAlias = PromoBonusPerformEnrollment
PromoBonusPerformEnrollmentResponse: TypeAlias = UpdateResult
PromoBonusPerformPaymentRequest: TypeAlias = PromoBonusPerformPayment
PromoBonusPerformPaymentResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['PromoBonusCancelPayment', 'PromoBonusCreateEnrollment', 'PromoBonusCreateManualOperation', 'PromoBonusCreatePayment', 'PromoBonusGet', 'PromoBonusPerformEnrollment', 'PromoBonusPerformPayment', 'PromoBonusesRemainder', 'PromoBonusesRemainderGet', 'PromoBonusesRemainderRegosObjectResult']


__all__ = [
    'PromoBonusCancelPayment',
    'PromoBonusCreateEnrollment',
    'PromoBonusCreateManualOperation',
    'PromoBonusCreatePayment',
    'PromoBonusGet',
    'PromoBonusPerformEnrollment',
    'PromoBonusPerformPayment',
    'PromoBonusType',
    'PromoBonusesRemainder',
    'PromoBonusesRemainderGet',
    'PromoBonusesRemainderRegosObjectResult',
    'PromoBonusCreatePaymentRequest',
    'PromoBonusCreatePaymentResponse',
    'PromoBonusPerformPaymentRequest',
    'PromoBonusPerformPaymentResponse',
    'PromoBonusCreateEnrollmentRequest',
    'PromoBonusCreateEnrollmentResponse',
    'PromoBonusPerformEnrollmentRequest',
    'PromoBonusPerformEnrollmentResponse',
    'PromoBonusCancelPaymentRequest',
    'PromoBonusCancelPaymentResponse',
    'PromoBonusCreateManualIncomeOperationRequest',
    'PromoBonusCreateManualIncomeOperationResponse',
    'PromoBonusCreateManualOutcomeOperationRequest',
    'PromoBonusCreateManualOutcomeOperationResponse',
    'PromoBonusGetRequest',
    'PromoBonusGetResponse'
]
