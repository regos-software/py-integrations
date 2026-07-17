"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailCustomer(RegosModel):
    "Модель, описывающая покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id покупателя")
    region: Region | None = PydField(default=None, description="Регион проживания")
    group: RetailCustomerGroup | None = PydField(default=None, description="Группа покупателей")
    full_name: str | None = PydField(default=None, description="ФИО")
    last_purchase: int | None = PydField(default=None, description="последняя покупка покупателем")
    debt: _Decimal | None = PydField(default=None, description="Долг")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    main_phone: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    refer_id: int | None = PydField(default=None)
    description: str | None = PydField(default=None)


class RetailCustomerAdd(RegosModel):
    "Модель для добавления розничного покупателя.\n           Наследуется от Regos_API.Models.Catalog.RetailCustomerBase"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None, description="ID группы покупателя в системе")
    region_id: int | None = PydField(default=None, description="ID регион проживания")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    main_phone: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    refer_id: int | None = PydField(default=None)
    description: str | None = PydField(default=None)


class RetailCustomerDebtAdd(RegosModel):
    "Добавление долга покупателю"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID розничного покупателя")
    uuid: str | None = PydField(default=None, description="UUID чека продажи по которому долг")
    date: int | None = PydField(default=None, description="Дата в unix time чека продажи по которому долг")
    amount: _Decimal | None = PydField(default=None, description="Общая сумма чека продажи по которому долг")
    paid: _Decimal | None = PydField(default=None, description="Оплаченная сумма чека продажи по которому долг (сумм оплат, кроме оплаты в долг)")


class RetailCustomerDebtPayment(RegosModel):
    "Оплата долга розничным покумателем"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id записи")
    payment_uuid: str | None = PydField(default=None, description="uuid чека продажи, который оплачивает долг")
    debt_uuid: str | None = PydField(default=None, description="uuid чека продажи, по которому долг")
    date: int | None = PydField(default=None, description="Дата в unixtime оплаты")
    amount: _Decimal | None = PydField(default=None, description="Сумма оплаты")
    last_update: int | None = PydField(default=None, description="Дата и время в unixtime последнего обновления записи")


class RetailCustomerDebtPaymentAdd(RegosModel):
    "Добавление оплаты долга покупателю"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID розничного покупателя")
    debt_uuid: str | None = PydField(default=None, description="UUID чека продажи, по которому долг")
    payment_uuid: str | None = PydField(default=None, description="UUID чека продажи, который оплачивает долг")
    date: int | None = PydField(default=None, description="Дата в unix time чека продажи по которому долг")
    amount: _Decimal | None = PydField(default=None, description="Общая сумма чека продажи по которому долг")


class RetailCustomerDebtPaymentRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCustomerDebtPayment] | Error | None = PydField(default=None, description="Массив результата.")


class RetailCustomerDebtPaymentsdGet(RegosModel):
    "Запрос списка оплат по долгам розничного покупателя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    ids: list[int] | None = PydField(default=None, description="Массив ID долгов покупателя")


class RetailCustomerDebtRecord(RegosModel):
    "Описание записи о долге"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id записи")
    uuid: str | None = PydField(default=None, description="uuid чека продажи, по которому долг")
    code: str | None = PydField(default=None, description="Номер (код) чека продажи, по которому долг")
    date: int | None = PydField(default=None, description="Дата в unixtime чека продажи, по которому долг")
    amount: _Decimal | None = PydField(default=None, description="Сумма чека продажи, по которому долг")
    payments_amount: _Decimal | None = PydField(default=None, description="Сумма оплат по чеку")
    last_update: int | None = PydField(default=None, description="Дата и время в unixtime последнего обновления записи")


class RetailCustomerDebtRecordGet(RegosModel):
    "Запрос списка долгов розничного покупателя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    ids: list[int] | None = PydField(default=None, description="Массив ID долгов покупателя")
    uuids: list[str] | None = PydField(default=None, description="Массив uuid чеков продаж по которым долги")
    is_debts: bool | None = PydField(default=None, description="Статус долга: true - не погашен, false - погашен")


class RetailCustomerDebtRecordRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCustomerDebtRecord] | Error | None = PydField(default=None, description="Массив результата.")


class RetailCustomerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id покупателя")


class RetailCustomerDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id покупателя")


class RetailCustomerEdit(RegosModel):
    "Модель для редактирования розничного покупателя.\n           Наследуется от Regos_API.Models.Catalog.RetailCustomerBase"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID покупателя")
    group_id: int | None = PydField(default=None, description="ID группы покупателя в системе")
    region_id: int | None = PydField(default=None, description="ID региона")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")
    first_name: str | None = PydField(default=None)
    last_name: str | None = PydField(default=None)
    middle_name: str | None = PydField(default=None)
    sex: SexEnum | None = PydField(default=None, description="enum для перечесление пола")
    date_of_birth: str | None = PydField(default=None)
    address: str | None = PydField(default=None)
    main_phone: str | None = PydField(default=None)
    phones: str | None = PydField(default=None)
    email: str | None = PydField(default=None)
    refer_id: int | None = PydField(default=None)
    description: str | None = PydField(default=None)


class RetailCustomerGet(RegosModel):
    "модель для получения списка розничных прокупателей"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id покупателей")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп покупателей")
    region_ids: list[int] | None = PydField(default=None, description="Массив id регионов")
    refer_ids: list[int] | None = PydField(default=None, description="Массив id реферальных покупателей (от которых пришли выбираемые покупатели)")
    gender: SexEnum | None = PydField(default=None, description="Пол покупателя: none = 1 (не указан), male = 2 (мужской), female = 3 (женский)")
    sort_orders: list[RetailCustomer_SortOrder] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: first_name - имя, middle_name - отчество, last_name - фамилия, main_phone - основной телефон, phones - доп телефоны, region_name - наименование региона")
    main_phone: str | None = PydField(default=None, description="Основной телефон покупателя")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailCustomerItemPurchases(RegosModel):
    "Описание покупок прозничного покупателя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item: Item | None = PydField(default=None, description="номенклатура")
    price: _Decimal | None = PydField(default=None)
    quantity: _Decimal | None = PydField(default=None, description="кол-во")
    amount: _Decimal | None = PydField(default=None, description="сумма (со скидкой)")
    amount2: _Decimal | None = PydField(default=None, description="сумма (без скидки)")


class RetailCustomerItemPurchasesArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCustomerItemPurchases] | Error | None = PydField(default=None, description="Объект результата.")


class RetailCustomerPurchaseInfo(RegosModel):
    "Модель для вывода информации о топ покупаках покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    FavoritePurchases: list[RetailCustomerItemPurchases] | None = PydField(default=None, description="Предпочитаемые покупки покупателя (топ)за период")
    AvgChequeAmount: _Decimal | None = PydField(default=None, description="Средний чек покупателя за период")
    ChequeQuantity: int | None = PydField(default=None, description="Общее количество чеков покупателя за период")
    LastPurchaseDate: int | None = PydField(default=None, description="Дата последнией покупки покупателем")
    SaleChequeQuantity: int | None = PydField(default=None, description="Количество чеков продаж покупателя")
    ReturnChequeQuantity: int | None = PydField(default=None, description="Количество чеков возвратов покупателя")


class RetailCustomerPurchaseInfoRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: RetailCustomerPurchaseInfo | Error | None = PydField(default=None, description="Объект результата.")


class RetailCustomerPurchaseInfoRequest(RegosModel):
    "модель для запроса информации по покупкам покупателя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    stock_id: int | None = PydField(default=None, description="ID склада")


class RetailCustomerPurchaseRequest(RegosModel):
    "Модель запроса данных о покупках покупателем на кассе"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    price_type_id: int | None = PydField(default=None, description="ID типа цены для расчёта покупок")


class RetailCustomerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCustomer] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailCustomer_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: RetailCustomer_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class RetailCustomer_SortOrderColumn(str, Enum):
    default = "default"
    id = "id"
    group_name = "group.name"
    first_name = "first_name"
    middle_name = "middle_name"
    last_name = "last_name"
    sex = "sex"
    date_of_birth = "date_of_birth"
    region_name = "region.name"
    address = "address"
    main_phone = "main_phone"
    phones = "phones"
    refer_id = "refer_id"
    last_update = "last_update"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, DecimalRegosObjectResult, Error, InsertResult, Int64RegosObjectResult, SexEnum, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.item import Item
from schemas.api.references.region import Region
from schemas.api.references.retail_customer_group import RetailCustomerGroup


RetailCustomerAddDebtPaymentRequest: TypeAlias = RetailCustomerDebtPaymentAdd
RetailCustomerAddDebtPaymentResponse: TypeAlias = InsertResult
RetailCustomerAddDebtRequest: TypeAlias = RetailCustomerDebtAdd
RetailCustomerAddDebtResponse: TypeAlias = InsertResult
RetailCustomerAddRequest: TypeAlias = RetailCustomerAdd
RetailCustomerAddResponse: TypeAlias = InsertResult
RetailCustomerDeleteMarkRequest: TypeAlias = RetailCustomerDeleteMark
RetailCustomerDeleteMarkResponse: TypeAlias = UpdateResult
RetailCustomerDeleteRequest: TypeAlias = RetailCustomerDelete
RetailCustomerDeleteResponse: TypeAlias = UpdateResult
RetailCustomerEditRequest: TypeAlias = RetailCustomerEdit
RetailCustomerEditResponse: TypeAlias = UpdateResult
RetailCustomerGetAvgChequeAmountRequest: TypeAlias = RetailCustomerPurchaseRequest
RetailCustomerGetAvgChequeAmountResponse: TypeAlias = DecimalRegosObjectResult
RetailCustomerGetChequeCountRequest: TypeAlias = RetailCustomerPurchaseRequest
RetailCustomerGetChequeCountResponse: TypeAlias = Int64RegosObjectResult
RetailCustomerGetDebtsPaymentHistoryRequest: TypeAlias = RetailCustomerDebtPaymentsdGet
RetailCustomerGetDebtsPaymentHistoryResponse: TypeAlias = RetailCustomerDebtPaymentRegosArrayResult
RetailCustomerGetDebtsRequest: TypeAlias = RetailCustomerDebtRecordGet
RetailCustomerGetDebtsResponse: TypeAlias = RetailCustomerDebtRecordRegosArrayResult
RetailCustomerGetFavoritePurchasesRequest: TypeAlias = RetailCustomerPurchaseRequest
RetailCustomerGetFavoritePurchasesResponse: TypeAlias = RetailCustomerItemPurchasesArrayRegosObjectResult
RetailCustomerGetLastPurchaseDateRequest: TypeAlias = RetailCustomerPurchaseRequest
RetailCustomerGetLastPurchaseDateResponse: TypeAlias = Int64RegosObjectResult
RetailCustomerGetPurchaseInfoRequest: TypeAlias = RetailCustomerPurchaseInfoRequest
RetailCustomerGetPurchaseInfoResponse: TypeAlias = RetailCustomerPurchaseInfoRegosObjectResult
RetailCustomerGetRequest: TypeAlias = RetailCustomerGet
RetailCustomerGetResponse: TypeAlias = RetailCustomerRegosOffsettedArrayResult


_MODEL_NAMES = ['RetailCustomer', 'RetailCustomerAdd', 'RetailCustomerDebtAdd', 'RetailCustomerDebtPayment', 'RetailCustomerDebtPaymentAdd', 'RetailCustomerDebtPaymentRegosArrayResult', 'RetailCustomerDebtPaymentsdGet', 'RetailCustomerDebtRecord', 'RetailCustomerDebtRecordGet', 'RetailCustomerDebtRecordRegosArrayResult', 'RetailCustomerDelete', 'RetailCustomerDeleteMark', 'RetailCustomerEdit', 'RetailCustomerGet', 'RetailCustomerItemPurchases', 'RetailCustomerItemPurchasesArrayRegosObjectResult', 'RetailCustomerPurchaseInfo', 'RetailCustomerPurchaseInfoRegosObjectResult', 'RetailCustomerPurchaseInfoRequest', 'RetailCustomerPurchaseRequest', 'RetailCustomerRegosOffsettedArrayResult', 'RetailCustomer_SortOrder']


__all__ = [
    'RetailCustomer',
    'RetailCustomerAdd',
    'RetailCustomerDebtAdd',
    'RetailCustomerDebtPayment',
    'RetailCustomerDebtPaymentAdd',
    'RetailCustomerDebtPaymentRegosArrayResult',
    'RetailCustomerDebtPaymentsdGet',
    'RetailCustomerDebtRecord',
    'RetailCustomerDebtRecordGet',
    'RetailCustomerDebtRecordRegosArrayResult',
    'RetailCustomerDelete',
    'RetailCustomerDeleteMark',
    'RetailCustomerEdit',
    'RetailCustomerGet',
    'RetailCustomerItemPurchases',
    'RetailCustomerItemPurchasesArrayRegosObjectResult',
    'RetailCustomerPurchaseInfo',
    'RetailCustomerPurchaseInfoRegosObjectResult',
    'RetailCustomerPurchaseInfoRequest',
    'RetailCustomerPurchaseRequest',
    'RetailCustomerRegosOffsettedArrayResult',
    'RetailCustomer_SortOrder',
    'RetailCustomer_SortOrderColumn',
    'RetailCustomerGetRequest',
    'RetailCustomerGetResponse',
    'RetailCustomerAddRequest',
    'RetailCustomerAddResponse',
    'RetailCustomerEditRequest',
    'RetailCustomerEditResponse',
    'RetailCustomerDeleteMarkRequest',
    'RetailCustomerDeleteMarkResponse',
    'RetailCustomerDeleteRequest',
    'RetailCustomerDeleteResponse',
    'RetailCustomerGetFavoritePurchasesRequest',
    'RetailCustomerGetFavoritePurchasesResponse',
    'RetailCustomerGetAvgChequeAmountRequest',
    'RetailCustomerGetAvgChequeAmountResponse',
    'RetailCustomerGetLastPurchaseDateRequest',
    'RetailCustomerGetLastPurchaseDateResponse',
    'RetailCustomerGetChequeCountRequest',
    'RetailCustomerGetChequeCountResponse',
    'RetailCustomerGetPurchaseInfoRequest',
    'RetailCustomerGetPurchaseInfoResponse',
    'RetailCustomerGetDebtsRequest',
    'RetailCustomerGetDebtsResponse',
    'RetailCustomerGetDebtsPaymentHistoryRequest',
    'RetailCustomerGetDebtsPaymentHistoryResponse',
    'RetailCustomerAddDebtRequest',
    'RetailCustomerAddDebtResponse',
    'RetailCustomerAddDebtPaymentRequest',
    'RetailCustomerAddDebtPaymentResponse'
]
