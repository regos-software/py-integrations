"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocRetailPayment(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID платежа")
    has_storno: bool | None = PydField(default=None, description="плтаёж сторнированный или нет")
    storno_uuid: str | None = PydField(default=None, description="UUID сторнированного платежа")
    document: str | None = PydField(default=None, description="UUID документа продажи")
    order: int | None = PydField(default=None, description="позиция в документе оплаты")
    type: PaymentType | None = PydField(default=None, description="вид оплаты")
    payment_type: PaymentType | None = PydField(default=None, description="вид оплаты")
    value: _Decimal | None = PydField(default=None, description="Значение")
    has_change: bool | None = PydField(default=None, description="имеет ли сдачу")
    change_uuid: str | None = PydField(default=None, description="UUID платежа со сдачей")


class DocRetailPaymentGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    doc_sale_uuid: str | None = PydField(default=None, description="UUID документа розничной продажи")
    uuids: list[str] | None = PydField(default=None, description="Массив UUID операций платежей")


class DocRetailPaymentRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocRetailPayment] | Error | None = PydField(default=None, description="Массив результата.")


class Payment(RegosModel):
    "модель позиции-оплаты"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="идентификатор позиции-оплаты")
    has_storno: bool | None = PydField(default=None, description="флаг, что это позиция сторнирована")
    storno_uuid: str | None = PydField(default=None, description="идентификатор сторнированного позиции-оплаты. (ссылка/связка на него)")
    document_uuid: str | None = PydField(default=None, description="идентификатор чека куда относится позиция-оплаты")
    order: int | None = PydField(default=None, description="порядковый номер позиции-оплаты для сортировки")
    type: PaymentType | None = PydField(default=None, description="форма оплаты")
    value: _Decimal | None = PydField(default=None, description="значение (позиции)оплаты")
    payment_id: str | None = PydField(default=None, description="id платежа в vcr, если бьла оплата через платёжную систему")
    has_change: bool | None = PydField(default=None, description="флаг, что это позиция имеет сдачу")
    change_uuid: str | None = PydField(default=None, description="идентификатор позиции-оплаты куда ссылается позиция сдачи")


class PaymentAdd(RegosModel):
    "модель для добавления позиции-оплаты"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    type_id: int | None = PydField(default=None, description="ID формы оплаты")
    value: _Decimal | None = PydField(default=None, description="Сумма оплаты")
    data: str | None = PydField(default=None, description="Данные платёжных систем")


class PaymentArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Payment] | Error | None = PydField(default=None, description="Объект результата.")


class PaymentGet(RegosModel):
    "модель выборки позиции-оплат"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="Массив UUID позиций оплаты кассового чека")
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    payment_type_ids: list[int] | None = PydField(default=None, description="Массив ID типов оплат")
    exclude_storno: bool | None = PydField(default=None, description="Исключать сторнированную и сторнирующую позиции оплаты")


class PaymentStorno(RegosModel):
    "модель сторнирования позиции-оплаты"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID сторнируемой позиции оплаты кассового чека")
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")


class PosPaymentSystemGet(RegosModel):
    "Модель для получения id платёжной системы по форме оплаты"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_uuid: str | None = PydField(default=None, description="UUID кассового чека")
    payment_type_id: int | None = PydField(default=None, description="ID формы оплаты")


class PosPaymentSystemID(RegosModel):
    "Модель ответа id платёжной системы"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    payment_system_id: int | None = PydField(default=None, description="Id платёжной системы")


class PosPaymentSystemIDRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: PosPaymentSystemID | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result
from schemas.api.references.payment_type import PaymentType


ChequePaymentOperationAddRequest: TypeAlias = PaymentAdd
ChequePaymentOperationAddResponse: TypeAlias = Insert_uuid_Result
ChequePaymentOperationGetPaymentSystemIdRequest: TypeAlias = PosPaymentSystemGet
ChequePaymentOperationGetPaymentSystemIdResponse: TypeAlias = PosPaymentSystemIDRegosObjectResult
ChequePaymentOperationGetRequest: TypeAlias = DocRetailPaymentGet
ChequePaymentOperationGetResponse: TypeAlias = DocRetailPaymentRegosArrayResult
ChequePaymentOperationPosGetRequest: TypeAlias = PaymentGet
ChequePaymentOperationPosGetResponse: TypeAlias = PaymentArrayRegosObjectResult
ChequePaymentOperationStornoRequest: TypeAlias = PaymentStorno
ChequePaymentOperationStornoResponse: TypeAlias = Insert_uuid_Result


_MODEL_NAMES = ['DocRetailPayment', 'DocRetailPaymentGet', 'DocRetailPaymentRegosArrayResult', 'Payment', 'PaymentAdd', 'PaymentArrayRegosObjectResult', 'PaymentGet', 'PaymentStorno', 'PosPaymentSystemGet', 'PosPaymentSystemID', 'PosPaymentSystemIDRegosObjectResult']


__all__ = [
    'DocRetailPayment',
    'DocRetailPaymentGet',
    'DocRetailPaymentRegosArrayResult',
    'Payment',
    'PaymentAdd',
    'PaymentArrayRegosObjectResult',
    'PaymentGet',
    'PaymentStorno',
    'PosPaymentSystemGet',
    'PosPaymentSystemID',
    'PosPaymentSystemIDRegosObjectResult',
    'ChequePaymentOperationPosGetRequest',
    'ChequePaymentOperationPosGetResponse',
    'ChequePaymentOperationAddRequest',
    'ChequePaymentOperationAddResponse',
    'ChequePaymentOperationStornoRequest',
    'ChequePaymentOperationStornoResponse',
    'ChequePaymentOperationGetPaymentSystemIdRequest',
    'ChequePaymentOperationGetPaymentSystemIdResponse',
    'ChequePaymentOperationGetRequest',
    'ChequePaymentOperationGetResponse'
]
