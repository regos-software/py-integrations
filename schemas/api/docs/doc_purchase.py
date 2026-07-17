"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocPurchase(RegosModel):
    "Модель, описывающая документ поступления от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа поступления от контрагента")
    date: int | None = PydField(default=None, description="Дата документа в формате unixtime в секундах")
    code: str | None = PydField(default=None, description="Код документа поступления от контрагента")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа поступления от контрагента")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    additional_expenses_amount: _Decimal | None = PydField(default=None, description="Сумма дополнительных расходов документа (считается только по проведённым документам и в валюте документа)")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    price_type: PriceType | None = PydField(default=None, description="Вид цены документа")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Флаг показываеющий, что документ заблокирован текущим пользователем. Null если документ не блокирован")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class DocPurchaseAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа поступления от контрагента в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    contract_id: int | None = PydField(default=None, description="ID договора")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    fields: list[FieldValueAdd] | None = PydField(default=None, description="Массив значений дополнительных полей")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    price_type_id: int | None = PydField(default=None, description="iD типа цены")


class DocPurchaseColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocPurchaseSortOrderColumnsEnum | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocPurchaseEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа поступления от контрагента")
    date: int | None = PydField(default=None, description="Дата документа поступления от контрагента в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    contract_id: int | None = PydField(default=None, description="ID договора")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    price_type_id: int | None = PydField(default=None, description="ID типа цены")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")


class DocPurchaseGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов поступлений от контрагентов")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    search: str | None = PydField(default=None, description="Строка поиска по полям: cade - Код документа поступления от контрагента, Partner/name - Наименование контрагента,\nPartner/inn - ИНН контрагента, User/name - ФИО пользователя, Contract/code - Код договора, Firm/name - Наименование\nпредприятия, Firm/inn - ИНН предприятия, - , -")
    sort_orders: list[DocPurchaseColumn] | None = PydField(default=None, description="Сортировка выходных параметров")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocPurchaseRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocPurchase] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocPurchaseSortOrderColumnsEnum(str, Enum):
    default = "default"
    id = "id"
    date = "date"
    code = "code"
    partner_name = "partner.name"
    stock_name = "stock.name"
    currency_name = "currency.name"
    contract_name = "contract.name"
    amount = "amount"
    vat_calculation_type = "vat_calculation_type"
    attached_user_name = "attached_user.name"
    price_type_name = "price_type.name"
    blocked = "blocked"
    performed = "performed"
    deleted_mark = "deleted_mark"
    last_update = "last_update"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseLockAndUnlock, Base_ID, ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.common.filter import Filter
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.partner import Partner
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock


DocPurchaseAddRequest: TypeAlias = DocPurchaseAdd
DocPurchaseAddResponse: TypeAlias = InsertResult
DocPurchaseDeleteMarkRequest: TypeAlias = Base_ID
DocPurchaseDeleteMarkResponse: TypeAlias = UpdateResult
DocPurchaseDeleteRequest: TypeAlias = Base_ID
DocPurchaseDeleteResponse: TypeAlias = UpdateResult
DocPurchaseEditRequest: TypeAlias = DocPurchaseEdit
DocPurchaseEditResponse: TypeAlias = UpdateResult
DocPurchaseGetRequest: TypeAlias = DocPurchaseGet
DocPurchaseGetResponse: TypeAlias = DocPurchaseRegosOffsettedArrayResult
DocPurchaseLockRequest: TypeAlias = BaseLockAndUnlock
DocPurchaseLockResponse: TypeAlias = UpdateResult
DocPurchasePerformCancelRequest: TypeAlias = Base_ID
DocPurchasePerformCancelResponse: TypeAlias = UpdateResult
DocPurchasePerformRequest: TypeAlias = Base_ID
DocPurchasePerformResponse: TypeAlias = UpdateResult
DocPurchaseUnlockRequest: TypeAlias = BaseLockAndUnlock
DocPurchaseUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocPurchase', 'DocPurchaseAdd', 'DocPurchaseColumn', 'DocPurchaseEdit', 'DocPurchaseGet', 'DocPurchaseRegosOffsettedArrayResult']


__all__ = [
    'DocPurchase',
    'DocPurchaseAdd',
    'DocPurchaseColumn',
    'DocPurchaseEdit',
    'DocPurchaseGet',
    'DocPurchaseRegosOffsettedArrayResult',
    'DocPurchaseSortOrderColumnsEnum',
    'DocPurchaseGetRequest',
    'DocPurchaseGetResponse',
    'DocPurchaseAddRequest',
    'DocPurchaseAddResponse',
    'DocPurchaseEditRequest',
    'DocPurchaseEditResponse',
    'DocPurchaseDeleteMarkRequest',
    'DocPurchaseDeleteMarkResponse',
    'DocPurchaseDeleteRequest',
    'DocPurchaseDeleteResponse',
    'DocPurchaseLockRequest',
    'DocPurchaseLockResponse',
    'DocPurchaseUnlockRequest',
    'DocPurchaseUnlockResponse',
    'DocPurchasePerformRequest',
    'DocPurchasePerformResponse',
    'DocPurchasePerformCancelRequest',
    'DocPurchasePerformCancelResponse'
]
