"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocOrderDelivery(RegosModel):
    "Модель, описывающая документы розничных заказов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    date: int | None = PydField(default=None, description="Дата документа")
    code: str | None = PydField(default=None, description="Код документа")
    stock: Stock | None = PydField(default=None, description="Склад")
    customer: RetailCustomer | None = PydField(default=None, description="Покупатель")
    card: RetailCard | None = PydField(default=None, description="Карта покупателя полностью")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа розничного заказа")
    status: DocumentStatus | None = PydField(default=None, description="Статус документа (Список статусов)")
    delivery_date: int | None = PydField(default=None, description="Дата доставки заказа в формате unix time")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    address: str | None = PydField(default=None, description="Адрес доставки заказа")
    phone: str | None = PydField(default=None, description="Телефон")
    external_code: str | None = PydField(default=None, description="Код заказа во внешней системе")
    from_: DeliveryFrom | None = PydField(default=None, alias="from", description="Источник розничных заказов")
    location: Location | None = PydField(default=None, description="Локация для доставки")
    delivery_type: DeliveryType | None = PydField(default=None, description="Тип доставки")
    courier: DeliveryCourier | None = PydField(default=None, description="Курьер")
    price_type: PriceType | None = PydField(default=None, description="Вид цены")
    qrcodeurl: str | None = PydField(default=None, description="Ссылка на фискальный чек в ОФД, которая печатается в чеке в qr коде. Если данная ссылка есть, значит чек фискализирован и повторно фискализироваться не будет")
    payment_type: PaymentType | None = PydField(default=None, description="Тип оплаты заказа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocOrderDeliveryActualize(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа розничного заказа")
    data: list[DocOrderDeliveryActualizeData] | None = PydField(default=None, description="Данные заказа")


class DocOrderDeliveryActualizeData(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    item_id: int | None = PydField(default=None, description="ID номенклатуры")
    quantity: _Decimal | None = PydField(default=None, description="Количество")
    price: _Decimal | None = PydField(default=None, description="Количество")
    deleted: bool | None = PydField(default=None, description="Метка удаления")


class DocOrderDeliveryAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа розничного заказа в формате unix time в секундах")
    delivery_date: int | None = PydField(default=None, description="Дата доставки розничного заказа в формате unix time в секундах")
    address: str | None = PydField(default=None, description="Адрес доставки заказа")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    phone: str | None = PydField(default=None, description="Телефон")
    external_code: str | None = PydField(default=None, description="Код заказа во внешней системе")
    from_id: int | None = PydField(default=None, description="ID источника розничных заказов")
    stock_id: int | None = PydField(default=None, description="ID склада")
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")
    delivery_type_id: int | None = PydField(default=None, description="ID типа доставки")
    payment_type_id: int | None = PydField(default=None, description="ID типа оплаты")
    courier_id: int | None = PydField(default=None, description="ID курьера")
    location: Location | None = PydField(default=None, description="Локация для доставки")
    qrcodeurl: str | None = PydField(default=None, description="Cсылка на фискальный чек (печатается в qr коде чека)")


class DocOrderDeliveryAddFull(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document: DocOrderDeliveryAdd | None = PydField(default=None, description="Новый документ розничного заказа")
    operations: list[OrderDeliveryOperationAdd] | None = PydField(default=None, description="Массив операций документа розничного заказа")


class DocOrderDeliveryColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocOrderDeliveryColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocOrderDeliveryColumns(str, Enum):
    Default = "Default"
    Date = "Date"
    Code = "Code"
    Stock = "Stock"
    OperatingCash = "OperatingCash"
    Customer = "Customer"
    Card = "Card"
    CurrencyName = "CurrencyName"
    From = "From"


class DocOrderDeliveryDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")


class DocOrderDeliveryDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")


class DocOrderDeliveryEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    date: int | None = PydField(default=None, description="Дата документа розничного заказа в формате unix time в секундах")
    delivery_date: int | None = PydField(default=None, description="Дата доставки розничного заказа в формате unix time в секундах")
    address: str | None = PydField(default=None, description="Адрес доставки заказа")
    external_code: str | None = PydField(default=None, description="Код заказа во внешней системе")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    phone: str | None = PydField(default=None, description="Телефон")
    from_id: int | None = PydField(default=None, description="ID источника розничных заказов")
    stock_id: int | None = PydField(default=None, description="ID склада")
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")
    delivery_type_id: int | None = PydField(default=None, description="ID типа доставки")
    payment_type_id: int | None = PydField(default=None, description="ID типа оплаты")
    courier_id: int | None = PydField(default=None, description="ID курьера")
    location: Location | None = PydField(default=None, description="Локация для доставки")
    qrcodeurl: str | None = PydField(default=None, description="ссылка на фискальный чек (печатается в qr-коде)")


class DocOrderDeliveryGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    code: str | None = PydField(default=None, description="Код документа розничных заказов")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов розничных заказов")
    status_ids: list[int] | None = PydField(default=None, description="Массив ID статусов документов")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    customer_ids: list[int] | None = PydField(default=None, description="Массив ID покупателей")
    operating_cash_ids: list[int] | None = PydField(default=None, description="Массив ID касс")
    from_ids: list[int] | None = PydField(default=None, description="Массив ID источников розничных заказов")
    external_code: str | None = PydField(default=None, description="Код заказа во внешней системе")
    sort_orders: list[DocOrderDeliveryColumn] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Строка для поиска")
    deleted_mark: bool | None = PydField(default=None, description="Пометка на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    blocked: bool | None = PydField(default=None, description="Блокировка документа: true - Заблокирован, false - Не заблокирован")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocOrderDeliveryLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов розничного заказа")


class DocOrderDeliveryRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocOrderDelivery] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocOrderDeliveryReturnProcessing(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_id: int | None = PydField(default=None, description="ID документа розничного заказа")
    data: list[DocOrderDeliveryReturnProcessingData] | None = PydField(default=None, description="Массив данных розничного заказа для возврата")


class DocOrderDeliveryReturnProcessingData(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции")
    quantity: _Decimal | None = PydField(default=None, description="Количество")


class DocOrderDeliverySetStock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    stock_id: int | None = PydField(default=None, description="ID склада для документа розничного заказа")


class DocOrderDeliveryStatusEnum(str, Enum):
    "New, Approved, Processing, Prepare_pay, Finished,\nCanceled, Prepare_pay_return, CanceledByPosSale, CanceledByPosReturn"
    Default = "Default"
    New = "New"
    Approved = "Approved"
    Processing = "Processing"
    Paying = "Paying"
    Finished = "Finished"
    Canceled = "Canceled"
    ReturnPaying = "ReturnPaying"
    ReturnProcessing = "ReturnProcessing"


class DocOrderDelivery_Beginning(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")


class DocOrderDelivery_SetCourier(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    courier_id: int | None = PydField(default=None, description="ID способа доставки")


class DocOrderDelivery_SetFiscalInfo(RegosModel):
    "Модель для устанвоки фискальной информации к розничному заказу"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    qrcodeurl: str | None = PydField(default=None, description="Ссылка на фискальный чек (печатается в qr коде чека)")


class DocOrderDelivery_SetOperatingCash(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы на которой будет осуществляться продажа или возврат розничного заказа")


class DocOrderDelivery_SetRetailCard(RegosModel):
    "Модель для добавления карты покупателя к документу заказа"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")


class DocOrderDelivery_SetStatus(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа розничного заказа")
    status: DocOrderDeliveryStatusEnum | None = PydField(default=None, description="Статус документа розничного заказа: New - Новый, Approved - Утверждён, Processing - В обработке, Paying -\nОплата(продажа), Finished - Завершён, Canceled - Отменён, ReturnPaying - Оплата(возврат), ReturnProcessing - В процессе\n(возврат)")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, Int64RegosObjectResult, Location, UpdateResult
from schemas.api.docs.document_status import DocumentStatus
from schemas.api.docs.order_delivery_operation import OrderDeliveryOperationAdd
from schemas.api.references.delivery_courier import DeliveryCourier
from schemas.api.references.delivery_from import DeliveryFrom
from schemas.api.references.delivery_type import DeliveryType
from schemas.api.references.payment_type import PaymentType
from schemas.api.references.price_type import PriceType
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_customer import RetailCustomer
from schemas.api.references.stock import Stock


DocOrderDeliveryActualizeRequest: TypeAlias = DocOrderDeliveryActualize
DocOrderDeliveryActualizeResponse: TypeAlias = UpdateResult
DocOrderDeliveryAddFullRequest: TypeAlias = DocOrderDeliveryAddFull
DocOrderDeliveryAddFullResponse: TypeAlias = InsertResult
DocOrderDeliveryAddRequest: TypeAlias = DocOrderDeliveryAdd
DocOrderDeliveryAddResponse: TypeAlias = InsertResult
DocOrderDeliveryDeleteMarkRequest: TypeAlias = DocOrderDeliveryDeleteMark
DocOrderDeliveryDeleteMarkResponse: TypeAlias = UpdateResult
DocOrderDeliveryDeleteRequest: TypeAlias = DocOrderDeliveryDelete
DocOrderDeliveryDeleteResponse: TypeAlias = UpdateResult
DocOrderDeliveryEditRequest: TypeAlias = DocOrderDeliveryEdit
DocOrderDeliveryEditResponse: TypeAlias = UpdateResult
DocOrderDeliveryGetCountRequest: TypeAlias = DocOrderDeliveryGet
DocOrderDeliveryGetCountResponse: TypeAlias = Int64RegosObjectResult
DocOrderDeliveryGetRequest: TypeAlias = DocOrderDeliveryGet
DocOrderDeliveryGetResponse: TypeAlias = DocOrderDeliveryRegosOffsettedArrayResult
DocOrderDeliveryLockRequest: TypeAlias = DocOrderDeliveryLockAndUnlock
DocOrderDeliveryLockResponse: TypeAlias = UpdateResult
DocOrderDeliveryReturnRequest: TypeAlias = DocOrderDeliveryReturnProcessing
DocOrderDeliveryReturnResponse: TypeAlias = UpdateResult
DocOrderDeliverySetCourierRequest: TypeAlias = DocOrderDelivery_SetCourier
DocOrderDeliverySetCourierResponse: TypeAlias = UpdateResult
DocOrderDeliverySetFiscalInfoRequest: TypeAlias = DocOrderDelivery_SetFiscalInfo
DocOrderDeliverySetFiscalInfoResponse: TypeAlias = UpdateResult
DocOrderDeliverySetOperatingCashRequest: TypeAlias = DocOrderDelivery_SetOperatingCash
DocOrderDeliverySetOperatingCashResponse: TypeAlias = UpdateResult
DocOrderDeliverySetRetailCardRequest: TypeAlias = DocOrderDelivery_SetRetailCard
DocOrderDeliverySetRetailCardResponse: TypeAlias = UpdateResult
DocOrderDeliverySetStatusRequest: TypeAlias = DocOrderDelivery_SetStatus
DocOrderDeliverySetStatusResponse: TypeAlias = UpdateResult
DocOrderDeliverySetStockRequest: TypeAlias = DocOrderDeliverySetStock
DocOrderDeliverySetStockResponse: TypeAlias = UpdateResult
DocOrderDeliveryToBeginningRequest: TypeAlias = DocOrderDelivery_Beginning
DocOrderDeliveryToBeginningResponse: TypeAlias = UpdateResult
DocOrderDeliveryUnlockRequest: TypeAlias = DocOrderDeliveryLockAndUnlock
DocOrderDeliveryUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocOrderDelivery', 'DocOrderDeliveryActualize', 'DocOrderDeliveryActualizeData', 'DocOrderDeliveryAdd', 'DocOrderDeliveryAddFull', 'DocOrderDeliveryColumn', 'DocOrderDeliveryDelete', 'DocOrderDeliveryDeleteMark', 'DocOrderDeliveryEdit', 'DocOrderDeliveryGet', 'DocOrderDeliveryLockAndUnlock', 'DocOrderDeliveryRegosOffsettedArrayResult', 'DocOrderDeliveryReturnProcessing', 'DocOrderDeliveryReturnProcessingData', 'DocOrderDeliverySetStock', 'DocOrderDelivery_Beginning', 'DocOrderDelivery_SetCourier', 'DocOrderDelivery_SetFiscalInfo', 'DocOrderDelivery_SetOperatingCash', 'DocOrderDelivery_SetRetailCard', 'DocOrderDelivery_SetStatus']


__all__ = [
    'DocOrderDelivery',
    'DocOrderDeliveryActualize',
    'DocOrderDeliveryActualizeData',
    'DocOrderDeliveryAdd',
    'DocOrderDeliveryAddFull',
    'DocOrderDeliveryColumn',
    'DocOrderDeliveryColumns',
    'DocOrderDeliveryDelete',
    'DocOrderDeliveryDeleteMark',
    'DocOrderDeliveryEdit',
    'DocOrderDeliveryGet',
    'DocOrderDeliveryLockAndUnlock',
    'DocOrderDeliveryRegosOffsettedArrayResult',
    'DocOrderDeliveryReturnProcessing',
    'DocOrderDeliveryReturnProcessingData',
    'DocOrderDeliverySetStock',
    'DocOrderDeliveryStatusEnum',
    'DocOrderDelivery_Beginning',
    'DocOrderDelivery_SetCourier',
    'DocOrderDelivery_SetFiscalInfo',
    'DocOrderDelivery_SetOperatingCash',
    'DocOrderDelivery_SetRetailCard',
    'DocOrderDelivery_SetStatus',
    'DocOrderDeliveryGetRequest',
    'DocOrderDeliveryGetResponse',
    'DocOrderDeliveryGetCountRequest',
    'DocOrderDeliveryGetCountResponse',
    'DocOrderDeliveryAddRequest',
    'DocOrderDeliveryAddResponse',
    'DocOrderDeliveryAddFullRequest',
    'DocOrderDeliveryAddFullResponse',
    'DocOrderDeliveryEditRequest',
    'DocOrderDeliveryEditResponse',
    'DocOrderDeliveryDeleteMarkRequest',
    'DocOrderDeliveryDeleteMarkResponse',
    'DocOrderDeliveryDeleteRequest',
    'DocOrderDeliveryDeleteResponse',
    'DocOrderDeliveryLockRequest',
    'DocOrderDeliveryLockResponse',
    'DocOrderDeliveryUnlockRequest',
    'DocOrderDeliveryUnlockResponse',
    'DocOrderDeliverySetStatusRequest',
    'DocOrderDeliverySetStatusResponse',
    'DocOrderDeliverySetFiscalInfoRequest',
    'DocOrderDeliverySetFiscalInfoResponse',
    'DocOrderDeliveryToBeginningRequest',
    'DocOrderDeliveryToBeginningResponse',
    'DocOrderDeliverySetStockRequest',
    'DocOrderDeliverySetStockResponse',
    'DocOrderDeliverySetOperatingCashRequest',
    'DocOrderDeliverySetOperatingCashResponse',
    'DocOrderDeliverySetCourierRequest',
    'DocOrderDeliverySetCourierResponse',
    'DocOrderDeliverySetRetailCardRequest',
    'DocOrderDeliverySetRetailCardResponse',
    'DocOrderDeliveryReturnRequest',
    'DocOrderDeliveryReturnResponse',
    'DocOrderDeliveryActualizeRequest',
    'DocOrderDeliveryActualizeResponse'
]
