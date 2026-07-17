"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocOrderFromPartner(RegosModel):
    "Модель, описывающая документы заказов от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа от контрагента")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    currency: Currency | None = PydField(default=None, description="Валюта")
    stock: Stock | None = PydField(default=None, description="Склад")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа закупки")
    status: DocumentStatus | None = PydField(default=None, description="Статус документа")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    booked: bool | None = PydField(default=None, description="Метка о том, что заказ бронирует номенклатуру")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    description: str | None = PydField(default=None, description="Примечение")


class DocOrderFromPartnerAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа заказа от контрагента в формате unixtime в секундах")
    stock_id: int | None = PydField(default=None, description="ID склада")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    contract_id: int | None = PydField(default=None, description="ID договора")
    booked: bool | None = PydField(default=None, description="Метка о том, что заказ бронирует номенклатуру")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Примечение")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию - текущий пользователь")


class DocOrderFromPartnerColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocOrderFromPartnerColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocOrderFromPartnerColumns(str, Enum):
    Default = "Default"
    Code = "Code"
    Date = "Date"
    ContractName = "ContractName"
    PartnerName = "PartnerName"
    StockName = "StockName"
    FirmName = "FirmName"
    OrderStatusName = "OrderStatusName"
    Amount = "Amount"
    CurrencyName = "CurrencyName"


class DocOrderFromPartnerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа от контрагента")


class DocOrderFromPartnerDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа от контрагента")


class DocOrderFromPartnerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа от контрагента")
    date: int | None = PydField(default=None, description="Дата документа заказа от контрагента в формате unix time в секундах")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    contract_id: int | None = PydField(default=None, description="ID договора")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада. Если значение параметра booked = true, то данныей параметр недопустимо редактировать")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    booked: bool | None = PydField(default=None, description="Статус бронирования заказанной номенклатуры: true - Забронировать заказанную номенклатуру, заказанная номенклатура не\nбудет доступна для отгрузки другому контрагенту; при этом не допускается изменять значение параметра stock_id, false -\nЗаказанная номенклатура не бронируется, её можно будет отгрузить другому контрагенту при необходимости")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Примечание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocOrderFromPartnerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа от контрагента")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    status_ids: list[int] | None = PydField(default=None, description="Массив ID статусов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    blocked: bool | None = PydField(default=None, description="Состояние блокировки для редактирования: true - Заблокирован, false - Разблокировин")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    sort_orders: list[DocOrderFromPartnerColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: code - Код документа, Stock/name - Наименование склада, Partner/name - Наименование контрагента,\nPartner/inn - ИНН контрагента, User/name - ФИО ответственного лица, DocContract/code - Код договора, Firm/name -\nНаименование предприятия, Firm/inn - ИНН предприятия")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocOrderFromPartnerLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа от контрагента")


class DocOrderFromPartnerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocOrderFromPartner] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.docs.document_status import DocumentStatus
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.stock import Stock


DocOrderFromPartnerAddRequest: TypeAlias = DocOrderFromPartnerAdd
DocOrderFromPartnerAddResponse: TypeAlias = InsertResult
DocOrderFromPartnerDeleteMarkRequest: TypeAlias = DocOrderFromPartnerDeleteMark
DocOrderFromPartnerDeleteMarkResponse: TypeAlias = UpdateResult
DocOrderFromPartnerDeleteRequest: TypeAlias = DocOrderFromPartnerDelete
DocOrderFromPartnerDeleteResponse: TypeAlias = UpdateResult
DocOrderFromPartnerEditRequest: TypeAlias = DocOrderFromPartnerEdit
DocOrderFromPartnerEditResponse: TypeAlias = UpdateResult
DocOrderFromPartnerGetRequest: TypeAlias = DocOrderFromPartnerGet
DocOrderFromPartnerGetResponse: TypeAlias = DocOrderFromPartnerRegosOffsettedArrayResult
DocOrderFromPartnerLockRequest: TypeAlias = DocOrderFromPartnerLockAndUnlock
DocOrderFromPartnerLockResponse: TypeAlias = UpdateResult
DocOrderFromPartnerUnlockRequest: TypeAlias = DocOrderFromPartnerLockAndUnlock
DocOrderFromPartnerUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocOrderFromPartner', 'DocOrderFromPartnerAdd', 'DocOrderFromPartnerColumn', 'DocOrderFromPartnerDelete', 'DocOrderFromPartnerDeleteMark', 'DocOrderFromPartnerEdit', 'DocOrderFromPartnerGet', 'DocOrderFromPartnerLockAndUnlock', 'DocOrderFromPartnerRegosOffsettedArrayResult']


__all__ = [
    'DocOrderFromPartner',
    'DocOrderFromPartnerAdd',
    'DocOrderFromPartnerColumn',
    'DocOrderFromPartnerColumns',
    'DocOrderFromPartnerDelete',
    'DocOrderFromPartnerDeleteMark',
    'DocOrderFromPartnerEdit',
    'DocOrderFromPartnerGet',
    'DocOrderFromPartnerLockAndUnlock',
    'DocOrderFromPartnerRegosOffsettedArrayResult',
    'DocOrderFromPartnerGetRequest',
    'DocOrderFromPartnerGetResponse',
    'DocOrderFromPartnerAddRequest',
    'DocOrderFromPartnerAddResponse',
    'DocOrderFromPartnerEditRequest',
    'DocOrderFromPartnerEditResponse',
    'DocOrderFromPartnerDeleteMarkRequest',
    'DocOrderFromPartnerDeleteMarkResponse',
    'DocOrderFromPartnerDeleteRequest',
    'DocOrderFromPartnerDeleteResponse',
    'DocOrderFromPartnerLockRequest',
    'DocOrderFromPartnerLockResponse',
    'DocOrderFromPartnerUnlockRequest',
    'DocOrderFromPartnerUnlockResponse'
]
