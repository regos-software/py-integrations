"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class RetailCard(RegosModel):
    "Модель, описывающая карты покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id карты покупателя")
    group: RetailCardGroup | None = PydField(default=None, description="Группа карт покупателей")
    customer: RetailCustomer | None = PydField(default=None, description="Покупатель")
    barcode_value: str | None = PydField(default=None, description="Штрих-код")
    barcode_type: BarcodeType | None = PydField(default=None, description="Тип штрих-кода")
    promo: PromoProgram | None = PydField(default=None, description="Промоакция, к которой привязана карта покупателя")
    bonus_amount: _Decimal | None = PydField(default=None, description="Сумма бонусов")
    date: int | None = PydField(default=None, description="Дата создания карты покупателя в формате unixtime в секундах")
    unlimited: bool | None = PydField(default=None, description="Является ли срок действия карты неограниченным: true - Неограниченный срок действия, false - Ограниченный срок действия")
    expiry_date: str | None = PydField(default=None, description="Дата истечения срока действия карты")
    last_purchase: int | None = PydField(default=None, description="Дата последней покупки")
    enabled: bool | None = PydField(default=None, description="Является ли карта покупателя активной: true - Активна, false - Не активна")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class RetailCardAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None, description="ID группы карт покупателей")
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    barcode_value: str | None = PydField(default=None, description="Штрих-код")
    barcode_type_id: int | None = PydField(default=None, description="ID типа штрих-кода")
    promo_id: int | None = PydField(default=None, description="ID промоакции")
    unlimited: bool | None = PydField(default=None, description="Является ли срок действия карты неограниченным: true - Неограниченный срок действия, false - Ограниченный срок действия")
    expiry_date: str | None = PydField(default=None, description="Дата истечения срока действия карты")
    enabled: bool | None = PydField(default=None, description="Является ли карта покупателя активной: true - Активна, false - Не активна")


class RetailCardAddWithCustomer(RegosModel):
    "Модель для добавления карты покупателя с покупателем"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="Id покупателя")
    first_name: str | None = PydField(default=None, description="Имя покупателя")
    middle_name: str | None = PydField(default=None, description="Отчество покупателя")
    last_name: str | None = PydField(default=None, description="Фамилия покупателя")
    main_phone: str | None = PydField(default=None, description="Телефон покупателя")
    sex: SexEnum | None = PydField(default=None, description="Пол покупателя: <none |1> - не указан, <male |2> - мужской, <female |3> - женский")
    date_of_birth: str | None = PydField(default=None, description="Дата рождения покупателя")
    barcode_value: str | None = PydField(default=None, description="Штрих код карты")
    barcode_type_id: int | None = PydField(default=None, description="Id типа штрих-кода")
    unlimited: bool | None = PydField(default=None, description="Является ли срок действия карты неограниченным: true - Неограниченный срок действия, false - Ограниченный срок действия")
    expiry_date: str | None = PydField(default=None, description="Дата истечения карты: ДД-ММ-ГГГГ")
    enabled: bool | None = PydField(default=None, description="Является ли карта покупателя активной: true - Активна, false - Не активна")


class RetailCardDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id карты покупателя")


class RetailCardEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID карты покупателя")
    group_id: int | None = PydField(default=None, description="ID группы карт покупателей")
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    barcode_value: str | None = PydField(default=None, description="Штрих-код")
    barcode_type_id: int | None = PydField(default=None, description="ID типа штрих-кода")
    promo_id: int | None = PydField(default=None, description="ID промоакции")
    unlimited: bool | None = PydField(default=None, description="Является ли срок действия карты неограниченным: true - Неограниченный срок действия, false - Ограниченный срок действия")
    expiry_date: str | None = PydField(default=None, description="Дата истечения срока действия карты")
    enabled: bool | None = PydField(default=None, description="Является ли карта покупателя активной: true - Активна, false - Не активна")


class RetailCardGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID карт покупателей")
    group_ids: list[int] | None = PydField(default=None, description="Массив ID групп карту покупателей")
    customer_ids: list[int] | None = PydField(default=None, description="Массив ID покупателей")
    promo_ids: list[int] | None = PydField(default=None, description="Массив ID программ лояльности")
    barcode_value: str | None = PydField(default=None, description="Штрих-код карты покупателя")
    sort_orders: list[RetailCard_SortOrder] | None = PydField(default=None, description="Сортировка выходных данных")
    search: str | None = PydField(default=None, description="Строка данных для поиска карты покупателя по номеру телефона или ФИО")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailCardOperation(RegosModel):
    "Класс описывающий операцию по карте покупателя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None)
    type: PromoBonusType | None = PydField(default=None)
    amount: _Decimal | None = PydField(default=None)
    value: _Decimal | None = PydField(default=None)
    used_value: _Decimal | None = PydField(default=None)
    is_payment: bool | None = PydField(default=None)
    date: int | None = PydField(default=None)
    exp_date: int | None = PydField(default=None)
    description: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class RetailCardOperationColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: RetailCardOperationColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class RetailCardOperationColumns(str, Enum):
    Default = "Default"
    Type = "Type"
    Date = "Date"
    Amount = "Amount"
    Value = "Value"
    ExpiryDate = "ExpiryDate"
    LastUpdate = "LastUpdate"


class RetailCardOperationGet(RegosModel):
    "Класс для запроса данных по карте покупателя"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="Массив UUID операций по картам")
    card_id: int | None = PydField(default=None, description="ID карты покупателя")
    promo_id: int | None = PydField(default=None, description="ID промоакции")
    type: PromoBonusType | None = PydField(default=None, description="Тип операции: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате Unix time в секундах")
    sort_orders: list[RetailCardOperationColumn] | None = PydField(default=None, description="Сортировка выходных данных")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class RetailCardOperationRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: RetailCardOperation | Error | None = PydField(default=None, description="Объект результата.")


class RetailCardOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCardOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailCardRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: RetailCard | Error | None = PydField(default=None, description="Объект результата.")


class RetailCardRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[RetailCard] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class RetailCard_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: RetailCard_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class RetailCard_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    GroupName = "GroupName"
    CustomerFullName = "CustomerFullName"
    Promo = "Promo"
    Date = "Date"
    ExpiryDate = "ExpiryDate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, SexEnum, UpdateResult
from schemas.api.references.barcode_type import BarcodeType
from schemas.api.references.promo_bonus import PromoBonusType, PromoBonusesRemainderGet, PromoBonusesRemainderRegosObjectResult
from schemas.api.references.promo_program import PromoProgram
from schemas.api.references.retail_card_group import RetailCardGroup
from schemas.api.references.retail_card_migration import RetailCardMigrationHistoryGet, RetailCardMigrationHistoryRegosArrayResult
from schemas.api.references.retail_customer import RetailCustomer


RetailCardAddRequest: TypeAlias = RetailCardAdd
RetailCardAddResponse: TypeAlias = InsertResult
RetailCardAddWithCustomerRequest: TypeAlias = RetailCardAddWithCustomer
RetailCardAddWithCustomerResponse: TypeAlias = RetailCardRegosObjectResult
RetailCardDeleteRequest: TypeAlias = RetailCardDelete
RetailCardDeleteResponse: TypeAlias = UpdateResult
RetailCardEditRequest: TypeAlias = RetailCardEdit
RetailCardEditResponse: TypeAlias = UpdateResult
RetailCardGetBalanceRequest: TypeAlias = PromoBonusesRemainderGet
RetailCardGetBalanceResponse: TypeAlias = PromoBonusesRemainderRegosObjectResult
RetailCardGetMigrationHistoryRequest: TypeAlias = RetailCardMigrationHistoryGet
RetailCardGetMigrationHistoryResponse: TypeAlias = RetailCardMigrationHistoryRegosArrayResult
RetailCardGetOperationsRequest: TypeAlias = RetailCardOperationGet
RetailCardGetOperationsResponse: TypeAlias = RetailCardOperationRegosOffsettedArrayResult
RetailCardGetRequest: TypeAlias = RetailCardGet
RetailCardGetResponse: TypeAlias = RetailCardRegosOffsettedArrayResult


_MODEL_NAMES = ['RetailCard', 'RetailCardAdd', 'RetailCardAddWithCustomer', 'RetailCardDelete', 'RetailCardEdit', 'RetailCardGet', 'RetailCardOperation', 'RetailCardOperationColumn', 'RetailCardOperationGet', 'RetailCardOperationRegosObjectResult', 'RetailCardOperationRegosOffsettedArrayResult', 'RetailCardRegosObjectResult', 'RetailCardRegosOffsettedArrayResult', 'RetailCard_SortOrder']


__all__ = [
    'RetailCard',
    'RetailCardAdd',
    'RetailCardAddWithCustomer',
    'RetailCardDelete',
    'RetailCardEdit',
    'RetailCardGet',
    'RetailCardOperation',
    'RetailCardOperationColumn',
    'RetailCardOperationColumns',
    'RetailCardOperationGet',
    'RetailCardOperationRegosObjectResult',
    'RetailCardOperationRegosOffsettedArrayResult',
    'RetailCardRegosObjectResult',
    'RetailCardRegosOffsettedArrayResult',
    'RetailCard_SortOrder',
    'RetailCard_SortOrderColumn',
    'RetailCardGetRequest',
    'RetailCardGetResponse',
    'RetailCardAddRequest',
    'RetailCardAddResponse',
    'RetailCardEditRequest',
    'RetailCardEditResponse',
    'RetailCardDeleteRequest',
    'RetailCardDeleteResponse',
    'RetailCardAddWithCustomerRequest',
    'RetailCardAddWithCustomerResponse',
    'RetailCardGetBalanceRequest',
    'RetailCardGetBalanceResponse',
    'RetailCardGetOperationsRequest',
    'RetailCardGetOperationsResponse',
    'RetailCardGetMigrationHistoryRequest',
    'RetailCardGetMigrationHistoryResponse'
]
