"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocCheque(RegosModel):
    "Модель, описывающая чеки"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID чека")
    date: int | None = PydField(default=None, description="Дата создания чека в Unix time")
    code: str | None = PydField(default=None, description="Код чека")
    status: DocChequeStatusEnum | None = PydField(default=None, description="Статус чека: <Opened | 1> - Открыт, <Paying | 2> - В процессе оплаты, <Closed | 3> - Закрыт,\n<Delayed | 4> - Отложен, <DelayedPayment | 5> - Отложен в процессе оплаты, <Canceled | 6> -\nАннулирован")
    session: str | None = PydField(default=None, description="UUID смены, к которой привязан чек")
    cashier: User | None = PydField(default=None, description="Кассир")
    is_return: bool | None = PydField(default=None, description="Метка о том, что чек является чеком возврата")
    seller: User | None = PydField(default=None, description="Продавец")
    return_reason: RetailReturnReason | None = PydField(default=None, description="Причина возврата")
    card: RetailCard | None = PydField(default=None, description="Карта покупателя")
    amount: _Decimal | None = PydField(default=None, description="Сумма чека")
    agregate_status: AgregateStatusEnum | None = PydField(default=None, description="Статус агрегации чека: <New | 1 - Новый, <Prepared | 2 - Готов к агрегации, <Agregated | 3 - Агрегирован")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocChequeColumn(RegosModel):
    "Модель колонки сортирвоки"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocChequeColumns | None = PydField(default=None, description="перечисление колонок доступных для сортировок")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocChequeColumns(str, Enum):
    "перечисление колонок доступных для сортировок"
    Default = "Default"
    Uuid = "Uuid"
    Date = "Date"
    Code = "Code"
    Status = "Status"
    Session = "Session"
    CashierName = "CashierName"
    IsRetunr = "IsRetunr"
    SellerName = "SellerName"
    ReturnReasonId = "ReturnReasonId"
    RetailCardBarcodeValue = "RetailCardBarcodeValue"
    Amount = "Amount"
    AgregateStatus = "AgregateStatus"
    LastUpdate = "LastUpdate"


class DocChequeGet(RegosModel):
    "модель получения данных"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="Массив UUID чеков")
    code: str | None = PydField(default=None, description="Код чека")
    cashier_ids: list[int] | None = PydField(default=None, description="Массив ID кассиров")
    seller_ids: list[int] | None = PydField(default=None, description="Массив ID продавцов")
    card_ids: list[int] | None = PydField(default=None, description="Массив ID карт покупателей")
    customer_ids: list[int] | None = PydField(default=None, description="Массив ID покупателей")
    session_uuid: str | None = PydField(default=None, description="UUID смены, к которой привязан чек")
    status: DocChequeStatusEnum | None = PydField(default=None, description="Статус чека: <Opened | 1> - Открыт, <Paying | 2> - В процессе оплаты, <Closed | 3> - Закрыт,\n<Delayed | 4> - Отложен, <DelayedPayment | 5> - Отложен в процессе оплаты, <Canceled | 6> -\nАннулирован")
    is_return: bool | None = PydField(default=None, description="Является ли чеком возврата: true - Чек возврата, false - Чек продажи, null - Возвращать все чеки (продажи и возврата)")
    is_fiscal: bool | None = PydField(default=None, description="Имеет ли чек фискальный признак: true - Имеет фискальный признак, false - Не имеет фискального признака null -\nВозвращать все чеки (с фискальным признаком и без). Под фискальным признаком понимается наличие QR-код с url в чеке")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    sort_orders: list[DocChequeColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocChequeOperation(RegosModel):
    "Модель, описывающая операции документа розничной продажи"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID операции")
    has_storno: bool | None = PydField(default=None, description="Метка о том, что операция является сторнирующей")
    storno_uuid: str | None = PydField(default=None, description="UUID сторнированной операции")
    document: str | None = PydField(default=None, description="UUID документа розничной продажи (чека)")
    stock_id: int | None = PydField(default=None, description="ID склада")
    item: Item | None = PydField(default=None, description="Номенклатура")
    order: int | None = PydField(default=None, description="Позиция операции в документе продажи")
    quantity: _Decimal | None = PydField(default=None, description="Количество номенклатуры")
    price: _Decimal | None = PydField(default=None, description="Цена номенклатуры")
    price2: _Decimal | None = PydField(default=None, description="Цена номенклатуры без скидки")
    promo_id: int | None = PydField(default=None, description="ID промоакции")
    vat_value: _Decimal | None = PydField(default=None, description="Значение ставки ндс в процентах")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате unix time")


class DocChequeOperationGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    doc_sale_uuid: str | None = PydField(default=None, description="UUID документа розничной продажи")
    uuids: list[str] | None = PydField(default=None, description="Массив UUID операций документа розничной продажи")


class DocChequeOperationRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocChequeOperation] | Error | None = PydField(default=None, description="Массив результата.")


class DocChequeRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocCheque] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocChequeShort(RegosModel):
    "модель для отображения чека в списке в упрощённом формате"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="uuid чека")
    operating_cash_id: int | None = PydField(default=None, description="id кассы")
    date: int | None = PydField(default=None, description="дата чека в unixtime")
    code: str | None = PydField(default=None, description="код чека")
    sale_status: DocChequeStatusEnum | None = PydField(default=None, description="статус чека")
    session_uuid: str | None = PydField(default=None, description="uuid коссовой смены")
    session_code: str | None = PydField(default=None, description="код коссовой смены")
    is_return: bool | None = PydField(default=None, description="чек взврата (true) или нет")
    amount: _Decimal | None = PydField(default=None, description="сумма чека")
    stock_id: int | None = PydField(default=None, description="id склада (места хранения)")
    stock_name: str | None = PydField(default=None, description="наименование склада")
    firm_id: int | None = PydField(default=None, description="id фирмы")
    firm_name: str | None = PydField(default=None, description="наименование предприятия")
    customer_id: int | None = PydField(default=None, description="id покупателя")
    customer_name: str | None = PydField(default=None, description="наименование покупателя")
    card_id: int | None = PydField(default=None, description="id карты лояльности")
    card_barcode: str | None = PydField(default=None, description="штрихкод карты лояльности")


class DocChequeShortGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="массив uuid чеков (необязтельное)")
    start_date: int | None = PydField(default=None, description="начальная дата в unixtime (необязательнок)")
    end_date: int | None = PydField(default=None, description="конечная дата в unixtime (необязательнок)")
    search: str | None = PydField(default=None, description="поиск (необязательнок)")
    session_uuids: list[str] | None = PydField(default=None, description="массив uuid кассовых смен (необязательнок)")
    operating_cash_ids: list[int] | None = PydField(default=None, description="массив id касс (необязательнок)")
    stock_ids: list[int] | None = PydField(default=None, description="массив id мест хранения (складов) (необязательнок)")
    firm_ids: list[int] | None = PydField(default=None, description="массив id предприятий (необязательнок)")
    customer_ids: list[int] | None = PydField(default=None, description="массив id покупателей (необязательнок)")
    sort_orders: list[DocChequeShortSortOrder] | None = PydField(default=None, description="сортировки (необязательнок)")
    is_return: bool | None = PydField(default=None, description="метка чеков возрата (null - все чеки) (необязательнок)")
    sale_status: DocChequeStatusEnum | None = PydField(default=None, description="статус чека (null - все чеки) (необязательнок)")
    limit: int | None = PydField(default=None)
    offset: int | None = PydField(default=None)


class DocChequeShortOrderColumn(str, Enum):
    "перечесление колонок сортировок при получении данных о чеках в коротком формате"
    Default = "Default"
    SessionCode = "SessionCode"
    Code = "Code"
    Amount = "Amount"
    Date = "Date"
    IsReturn = "IsReturn"
    SaleStatus = "SaleStatus"
    StockName = "StockName"
    FirmName = "FirmName"


class DocChequeShortRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocChequeShort] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocChequeShortSortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocChequeShortOrderColumn | None = PydField(default=None, description="перечесление колонок сортировок при получении данных о чеках в коротком формате")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocChequeStatusEnum(str, Enum):
    "статусы чеков продаж розничной торговли"
    Default = "Default"
    Opened = "Opened"
    Paying = "Paying"
    Closed = "Closed"
    Delayed = "Delayed"
    DelayedPayment = "DelayedPayment"
    Canceled = "Canceled"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import AgregateStatusEnum, ColumnSortOrderDirection, Error
from schemas.api.rbac.user import User
from schemas.api.references.item import Item
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_return_reason import RetailReturnReason


DocChequeGetFavoritePeriodRequest: TypeAlias = DocChequeGet
DocChequeGetFavoritePeriodResponse: TypeAlias = DocChequeRegosOffsettedArrayResult
DocChequeGetRequest: TypeAlias = DocChequeGet
DocChequeGetResponse: TypeAlias = DocChequeRegosOffsettedArrayResult
DocChequeGetShortRequest: TypeAlias = DocChequeShortGet
DocChequeGetShortResponse: TypeAlias = DocChequeShortRegosOffsettedArrayResult


_MODEL_NAMES = ['DocCheque', 'DocChequeColumn', 'DocChequeGet', 'DocChequeOperation', 'DocChequeOperationGet', 'DocChequeOperationRegosArrayResult', 'DocChequeRegosOffsettedArrayResult', 'DocChequeShort', 'DocChequeShortGet', 'DocChequeShortRegosOffsettedArrayResult', 'DocChequeShortSortOrder']


__all__ = [
    'DocCheque',
    'DocChequeColumn',
    'DocChequeColumns',
    'DocChequeGet',
    'DocChequeOperation',
    'DocChequeOperationGet',
    'DocChequeOperationRegosArrayResult',
    'DocChequeRegosOffsettedArrayResult',
    'DocChequeShort',
    'DocChequeShortGet',
    'DocChequeShortOrderColumn',
    'DocChequeShortRegosOffsettedArrayResult',
    'DocChequeShortSortOrder',
    'DocChequeStatusEnum',
    'DocChequeGetRequest',
    'DocChequeGetResponse',
    'DocChequeGetShortRequest',
    'DocChequeGetShortResponse',
    'DocChequeGetFavoritePeriodRequest',
    'DocChequeGetFavoritePeriodResponse'
]
