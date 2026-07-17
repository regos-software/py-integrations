"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Cheque(RegosModel):
    "Чек"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="идентификатор")
    date: int | None = PydField(default=None, description="дата создания")
    code: str | None = PydField(default=None, description="код")
    status: SaleStatus | None = PydField(default=None, description="статус")
    session_uuid: str | None = PydField(default=None, description="идентификатор смены куда привязан чек")
    session_code: str | None = PydField(default=None, description="код смены куда относится чек")
    cashier: User | None = PydField(default=None, description="Модель, описывающая пользователя и его параметры")
    cashier_id: int | None = PydField(default=None, description="id кассира создавщий чек")
    seller: User | None = PydField(default=None, description="Модель, описывающая пользователя и его параметры")
    seller_id: int | None = PydField(default=None, description="id продавца (который привязан к чеку)")
    is_return: bool | None = PydField(default=None, description="флаг чек возрата (если true)")
    return_reason: RetailReturnReason | None = PydField(default=None, description="модель причины возврата (если указывается причина в возврате)")
    card_id: int | None = PydField(default=None, description="id карты покупателя")
    card: RetailCard | None = PydField(default=None, description="карты покупателя")
    doc_order_delivery_id: int | None = PydField(default=None, description="привязка id док. заказа на доставку (если есть такое)")
    amount: _Decimal | None = PydField(default=None, description="сумма чека")
    amount2: _Decimal | None = PydField(default=None, description="сумма чека без скидки")
    payments_amount: _Decimal | None = PydField(default=None, description="сумма оплат чека")
    card_discount_percent: _Decimal | None = PydField(default=None)
    debt_payment: bool | None = PydField(default=None, description="метка, является ли чек чеком оплаты долга (true) или нет (false)")
    debt_uuid: str | None = PydField(default=None, description="идентификатор чека по которому долг")
    refund_info: RefundInfo | None = PydField(default=None, description="Фискальные данные для чека возврата")


class ChequeArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Cheque] | Error | None = PydField(default=None, description="Объект результата.")


class ChequeGet(RegosModel):
    "модель получения чеков"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")
    code: str | None = PydField(default=None, description="Код чека")
    session_uuid: str | None = PydField(default=None, description="UUID смены, к которой привязан чек")
    cashier_id: int | None = PydField(default=None, description="ID кассира")
    seller_id: int | None = PydField(default=None, description="ID продавца")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")
    doc_order_delivery_id: int | None = PydField(default=None, description="ID документа заказа")
    statuses: list[SaleStatus] | None = PydField(default=None, description="Статус чека: , <Opened | 1> - открыт, <Paying | 2> - на оплате, <Closed | 3> - закрыт, <Delayed |\n4> - отложен, <DelayedPayment | 5> - отложен на оплате, <Canceled | 6> - аннулирован")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    is_return: bool | None = PydField(default=None, description="Метка о том, что чек является чеком возврата")
    return_reason: int | None = PydField(default=None, description="ID причины возврата")


class ChequePrint_RequestModel(RegosModel):
    "модель запроса, для печати (закрытых) чеков"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_uuid: str | None = PydField(default=None, description="UUID чека")


class ChequePrint_ResponseModel(RegosModel):
    "модель ответа, печати (закрытых) чеков"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    print_data: str | None = PydField(default=None, description="чек pdf варианта обвертнутый в base64")


class ChequePrint_ResponseModelRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: ChequePrint_ResponseModel | Error | None = PydField(default=None, description="Объект результата.")


class ChequeRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Cheque | Error | None = PydField(default=None, description="Объект результата.")


class ChequeTestPrintRequestModel(RegosModel):
    "модель запроса, для печати (закрытых) чеков"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    operating_cash_id: int | None = PydField(default=None, description="-")


class ChequeUuid(RegosModel):
    "общий модель для нескольких методов чека\n           (где требуется только идентификатор).\n           pay, close, delay, continue_delayed, cancel"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")


class Cheque_AddPayDebt(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    debt_uuid: str | None = PydField(default=None, description="UUID долга")
    amount: _Decimal | None = PydField(default=None, description="Сумма платежа")


class Cheque_AddRetailCard(RegosModel):
    "модель для добавления карты покупателя на чек"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассового чека")
    barcode_value: str | None = PydField(default=None, description="Штрих-код карты покупателя")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")


class Cheque_SetAmountDiscount(RegosModel):
    "изменеие суммы чека (сумовая скидка)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассового чека")
    value: _Decimal | None = PydField(default=None, description="Значение суммы скидки")


class Cheque_SetDocOrderDelivery(RegosModel):
    "модель для привязки к чеку (id) док.заказа на доставку"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассового чека")
    doc_order_delivery_id: int | None = PydField(default=None, description="ID документа заказа")


class Cheque_SetIsReturn(RegosModel):
    "модель изменеия чека продаж на чек возврата"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассового чека")
    is_return: bool | None = PydField(default=None, description="Тип чека true - Чек возврата, false - Чек продажи")
    return_reason_id: int | None = PydField(default=None, description="ID причины возврата")


class Cheque_SetPercentDiscount(RegosModel):
    "модель установки %-скидки"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассового чека")
    percent: _Decimal | None = PydField(default=None, description="Процент скидки")


class RefundInfo(RegosModel):
    "Фискальные данные для чека возврата"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    terminal_id: str | None = PydField(default=None, description="ID фискального модуля")
    receipt_no: str | None = PydField(default=None, description="номер чека в ПОФМ")
    datetime: _DateTime | None = PydField(default=None, description="Дата и время чека")
    fiscal_sign: str | None = PydField(default=None, description="Фискальный признак")
    qrcode_url: str | None = PydField(default=None)


class RemoveSeller(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="-")


class SaleStatus(str, Enum):
    "статусы/стадии чека"
    Default = "Default"
    Opened = "Opened"
    Paying = "Paying"
    Closed = "Closed"
    Delayed = "Delayed"
    DelayedPayment = "DelayedPayment"
    Canceled = "Canceled"


class SetQrCodeUrl(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")
    qrcode_url: str | None = PydField(default=None, description="фискальный URL")


class SetRefundInfo(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")
    terminal_id: str | None = PydField(default=None, description="ID фискального модуля")
    receipt_no: str | None = PydField(default=None, description="номер чека в ПОФМ")
    datetime: _DateTime | None = PydField(default=None, description="Дата и время чека")
    fiscal_sign: str | None = PydField(default=None, description="Фискальный признак")
    qrcode_url: str | None = PydField(default=None)


class SetSeller(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")
    barcode: str | None = PydField(default=None, description="Штрих-код продавца")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_return_reason import RetailReturnReason


PosDocChequeAddRetailCardRequest: TypeAlias = Cheque_AddRetailCard
PosDocChequeAddRetailCardResponse: TypeAlias = ChequeArrayRegosObjectResult
PosDocChequeAddSellerRequest: TypeAlias = SetSeller
PosDocChequeAddSellerResponse: TypeAlias = UpdateResult
PosDocChequeBackToOperationsRequest: TypeAlias = ChequeUuid
PosDocChequeBackToOperationsResponse: TypeAlias = UpdateResult
PosDocChequeCancelRequest: TypeAlias = ChequeUuid
PosDocChequeCancelResponse: TypeAlias = UpdateResult
PosDocChequeCloseRequest: TypeAlias = ChequeUuid
PosDocChequeCloseResponse: TypeAlias = UpdateResult
PosDocChequeContinueDelayedRequest: TypeAlias = ChequeUuid
PosDocChequeContinueDelayedResponse: TypeAlias = UpdateResult
PosDocChequeCreateResponse: TypeAlias = Insert_uuid_Result
PosDocChequeDelayRequest: TypeAlias = ChequeUuid
PosDocChequeDelayResponse: TypeAlias = UpdateResult
PosDocChequeGetClosedResponse: TypeAlias = ChequeArrayRegosObjectResult
PosDocChequeGetPrintedRequest: TypeAlias = ChequePrint_RequestModel
PosDocChequeGetPrintedResponse: TypeAlias = ChequePrint_ResponseModelRegosObjectResult
PosDocChequeGetRequest: TypeAlias = ChequeGet
PosDocChequeGetResponse: TypeAlias = ChequeArrayRegosObjectResult
PosDocChequeGetTestPrintedRequest: TypeAlias = ChequeTestPrintRequestModel
PosDocChequeGetTestPrintedResponse: TypeAlias = ChequePrint_ResponseModelRegosObjectResult
PosDocChequeGetcurrentResponse: TypeAlias = ChequeArrayRegosObjectResult
PosDocChequePayDebtRequest: TypeAlias = Cheque_AddPayDebt
PosDocChequePayDebtResponse: TypeAlias = ChequeRegosObjectResult
PosDocChequePayRequest: TypeAlias = ChequeUuid
PosDocChequePayResponse: TypeAlias = UpdateResult
PosDocChequeRemoveSellerRequest: TypeAlias = RemoveSeller
PosDocChequeRemoveSellerResponse: TypeAlias = UpdateResult
PosDocChequeSetAmountDiscountRequest: TypeAlias = Cheque_SetAmountDiscount
PosDocChequeSetAmountDiscountResponse: TypeAlias = UpdateResult
PosDocChequeSetDocOrderDeliveryRequest: TypeAlias = Cheque_SetDocOrderDelivery
PosDocChequeSetDocOrderDeliveryResponse: TypeAlias = UpdateResult
PosDocChequeSetPercentDiscountRequest: TypeAlias = Cheque_SetPercentDiscount
PosDocChequeSetPercentDiscountResponse: TypeAlias = UpdateResult
PosDocChequeSetQrCodeUrlRequest: TypeAlias = SetQrCodeUrl
PosDocChequeSetQrCodeUrlResponse: TypeAlias = UpdateResult
PosDocChequeSetRefundInfoRequest: TypeAlias = SetRefundInfo
PosDocChequeSetRefundInfoResponse: TypeAlias = UpdateResult
PosDocChequeSetReturnRequest: TypeAlias = Cheque_SetIsReturn
PosDocChequeSetReturnResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Cheque', 'ChequeArrayRegosObjectResult', 'ChequeGet', 'ChequePrint_RequestModel', 'ChequePrint_ResponseModel', 'ChequePrint_ResponseModelRegosObjectResult', 'ChequeRegosObjectResult', 'ChequeTestPrintRequestModel', 'ChequeUuid', 'Cheque_AddPayDebt', 'Cheque_AddRetailCard', 'Cheque_SetAmountDiscount', 'Cheque_SetDocOrderDelivery', 'Cheque_SetIsReturn', 'Cheque_SetPercentDiscount', 'RefundInfo', 'RemoveSeller', 'SetQrCodeUrl', 'SetRefundInfo', 'SetSeller']


__all__ = [
    'Cheque',
    'ChequeArrayRegosObjectResult',
    'ChequeGet',
    'ChequePrint_RequestModel',
    'ChequePrint_ResponseModel',
    'ChequePrint_ResponseModelRegosObjectResult',
    'ChequeRegosObjectResult',
    'ChequeTestPrintRequestModel',
    'ChequeUuid',
    'Cheque_AddPayDebt',
    'Cheque_AddRetailCard',
    'Cheque_SetAmountDiscount',
    'Cheque_SetDocOrderDelivery',
    'Cheque_SetIsReturn',
    'Cheque_SetPercentDiscount',
    'RefundInfo',
    'RemoveSeller',
    'SaleStatus',
    'SetQrCodeUrl',
    'SetRefundInfo',
    'SetSeller',
    'PosDocChequeGetRequest',
    'PosDocChequeGetResponse',
    'PosDocChequeGetcurrentResponse',
    'PosDocChequeGetClosedResponse',
    'PosDocChequeCreateResponse',
    'PosDocChequeSetRefundInfoRequest',
    'PosDocChequeSetRefundInfoResponse',
    'PosDocChequeSetQrCodeUrlRequest',
    'PosDocChequeSetQrCodeUrlResponse',
    'PosDocChequeAddSellerRequest',
    'PosDocChequeAddSellerResponse',
    'PosDocChequeRemoveSellerRequest',
    'PosDocChequeRemoveSellerResponse',
    'PosDocChequePayRequest',
    'PosDocChequePayResponse',
    'PosDocChequeCloseRequest',
    'PosDocChequeCloseResponse',
    'PosDocChequeDelayRequest',
    'PosDocChequeDelayResponse',
    'PosDocChequeContinueDelayedRequest',
    'PosDocChequeContinueDelayedResponse',
    'PosDocChequeCancelRequest',
    'PosDocChequeCancelResponse',
    'PosDocChequeBackToOperationsRequest',
    'PosDocChequeBackToOperationsResponse',
    'PosDocChequeSetPercentDiscountRequest',
    'PosDocChequeSetPercentDiscountResponse',
    'PosDocChequeSetAmountDiscountRequest',
    'PosDocChequeSetAmountDiscountResponse',
    'PosDocChequeAddRetailCardRequest',
    'PosDocChequeAddRetailCardResponse',
    'PosDocChequeSetReturnRequest',
    'PosDocChequeSetReturnResponse',
    'PosDocChequeSetDocOrderDeliveryRequest',
    'PosDocChequeSetDocOrderDeliveryResponse',
    'PosDocChequeGetPrintedRequest',
    'PosDocChequeGetPrintedResponse',
    'PosDocChequeGetTestPrintedRequest',
    'PosDocChequeGetTestPrintedResponse',
    'PosDocChequePayDebtRequest',
    'PosDocChequePayDebtResponse'
]
