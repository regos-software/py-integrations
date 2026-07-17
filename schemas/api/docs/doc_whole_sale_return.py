"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocWholeSaleReturn(RegosModel):
    "Модель, описывающая документ возврата от контрагента"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата контрагенту")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа оптового возврата")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocWholeSaleReturnAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа возврата контрагенту в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    contract_id: int | None = PydField(default=None, description="ID договора")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию - текущий пользователь")


class DocWholeSaleReturnColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocWholeSaleReturnColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocWholeSaleReturnColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    PartnerName = "PartnerName"
    StockName = "StockName"
    CurrencyName = "CurrencyName"
    ContractName = "ContractName"
    Amount = "Amount"
    VatCalculationType = "VatCalculationType"
    AttacheUserName = "AttacheUserName"
    Blocked = "Blocked"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocWholeSaleReturnDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата от контрагента")


class DocWholeSaleReturnDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата от контрагента")


class DocWholeSaleReturnEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата контрагенту")
    date: int | None = PydField(default=None, description="Дата документа возврата контрагенту в формате unixtime в секундах")
    contract_id: int | None = PydField(default=None, description="Id договора")
    partner_id: int | None = PydField(default=None, description="Id контрагента")
    stock_id: int | None = PydField(default=None, description="Id склада")
    currency_id: int | None = PydField(default=None, description="Id валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="Id ответственного пользователя")


class DocWholeSaleReturnGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов возврата от контрагента")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    sort_orders: list[DocWholeSaleReturnColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Partner/name - Наименование контрагента, Partner/inn - ИНН\nконтрагента, User/name - ФИО ответственного лица, DocContract/code - Код договора, Firm/name - Наименование предприятия,\nFirm/inn - ИНН предприятия")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocWholeSaleReturnLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов возврата от контрагента")


class DocWholeSaleReturnPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа возврата от контрагента")


class DocWholeSaleReturnRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocWholeSaleReturn] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.stock import Stock


DocWholeSaleReturnAddRequest: TypeAlias = DocWholeSaleReturnAdd
DocWholeSaleReturnAddResponse: TypeAlias = InsertResult
DocWholeSaleReturnDeleteMarkRequest: TypeAlias = DocWholeSaleReturnDeleteMark
DocWholeSaleReturnDeleteMarkResponse: TypeAlias = UpdateResult
DocWholeSaleReturnDeleteRequest: TypeAlias = DocWholeSaleReturnDelete
DocWholeSaleReturnDeleteResponse: TypeAlias = UpdateResult
DocWholeSaleReturnEditRequest: TypeAlias = DocWholeSaleReturnEdit
DocWholeSaleReturnEditResponse: TypeAlias = UpdateResult
DocWholeSaleReturnGetRequest: TypeAlias = DocWholeSaleReturnGet
DocWholeSaleReturnGetResponse: TypeAlias = DocWholeSaleReturnRegosOffsettedArrayResult
DocWholeSaleReturnLockRequest: TypeAlias = DocWholeSaleReturnLockAndUnlock
DocWholeSaleReturnLockResponse: TypeAlias = UpdateResult
DocWholeSaleReturnPerformCancelRequest: TypeAlias = DocWholeSaleReturnPerformAndCancel
DocWholeSaleReturnPerformCancelResponse: TypeAlias = UpdateResult
DocWholeSaleReturnPerformRequest: TypeAlias = DocWholeSaleReturnPerformAndCancel
DocWholeSaleReturnPerformResponse: TypeAlias = UpdateResult
DocWholeSaleReturnUnlockRequest: TypeAlias = DocWholeSaleReturnLockAndUnlock
DocWholeSaleReturnUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocWholeSaleReturn', 'DocWholeSaleReturnAdd', 'DocWholeSaleReturnColumn', 'DocWholeSaleReturnDelete', 'DocWholeSaleReturnDeleteMark', 'DocWholeSaleReturnEdit', 'DocWholeSaleReturnGet', 'DocWholeSaleReturnLockAndUnlock', 'DocWholeSaleReturnPerformAndCancel', 'DocWholeSaleReturnRegosOffsettedArrayResult']


__all__ = [
    'DocWholeSaleReturn',
    'DocWholeSaleReturnAdd',
    'DocWholeSaleReturnColumn',
    'DocWholeSaleReturnColumns',
    'DocWholeSaleReturnDelete',
    'DocWholeSaleReturnDeleteMark',
    'DocWholeSaleReturnEdit',
    'DocWholeSaleReturnGet',
    'DocWholeSaleReturnLockAndUnlock',
    'DocWholeSaleReturnPerformAndCancel',
    'DocWholeSaleReturnRegosOffsettedArrayResult',
    'DocWholeSaleReturnGetRequest',
    'DocWholeSaleReturnGetResponse',
    'DocWholeSaleReturnAddRequest',
    'DocWholeSaleReturnAddResponse',
    'DocWholeSaleReturnEditRequest',
    'DocWholeSaleReturnEditResponse',
    'DocWholeSaleReturnDeleteMarkRequest',
    'DocWholeSaleReturnDeleteMarkResponse',
    'DocWholeSaleReturnDeleteRequest',
    'DocWholeSaleReturnDeleteResponse',
    'DocWholeSaleReturnLockRequest',
    'DocWholeSaleReturnLockResponse',
    'DocWholeSaleReturnUnlockRequest',
    'DocWholeSaleReturnUnlockResponse',
    'DocWholeSaleReturnPerformRequest',
    'DocWholeSaleReturnPerformResponse',
    'DocWholeSaleReturnPerformCancelRequest',
    'DocWholeSaleReturnPerformCancelResponse'
]
