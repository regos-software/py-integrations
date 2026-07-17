"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocReturnsToPartner(RegosModel):
    "Модель, описывающая документы возврата контрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа возврата контрагенту")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа возврата")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user: User | None = PydField(default=None, description="Ответственное пользователь")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocReturnsToPartnerAdd(RegosModel):
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


class DocReturnsToPartnerColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocReturnsToPartnerColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocReturnsToPartnerColumns(str, Enum):
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


class DocReturnsToPartnerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата контрагенту")


class DocReturnsToPartnerDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа возврата контрагенту")


class DocReturnsToPartnerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа возврата контрагенту")
    date: int | None = PydField(default=None, description="Дата документа возврата контрагенту в формате unix time в секундах")
    contract_id: int | None = PydField(default=None, description="ID договора")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocReturnsToPartnerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов возврата контрагенту")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    search: str | None = PydField(default=None, description="Поиск по значению параметров: code - Код документа, Partner/name - Наименование контрагента, Partner/inn - ИНН\nконтрагента, User/name - ФИО ответственного лица, DocContract/code - Код договора, Stock/name - Наименование склада,\nFirm/name - Наименование предприятия, Firm/inn - ИНН предприятия")
    sort_orders: list[DocReturnsToPartnerColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocReturnsToPartnerLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов возврата контрагенту")


class DocReturnsToPartnerPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа возврата контрагенту")


class DocReturnsToPartnerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocReturnsToPartner] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.stock import Stock


DocReturnsToPartnerAddRequest: TypeAlias = DocReturnsToPartnerAdd
DocReturnsToPartnerAddResponse: TypeAlias = InsertResult
DocReturnsToPartnerDeleteMarkRequest: TypeAlias = DocReturnsToPartnerDeleteMark
DocReturnsToPartnerDeleteMarkResponse: TypeAlias = UpdateResult
DocReturnsToPartnerDeleteRequest: TypeAlias = DocReturnsToPartnerDelete
DocReturnsToPartnerDeleteResponse: TypeAlias = UpdateResult
DocReturnsToPartnerEditRequest: TypeAlias = DocReturnsToPartnerEdit
DocReturnsToPartnerEditResponse: TypeAlias = UpdateResult
DocReturnsToPartnerGetRequest: TypeAlias = DocReturnsToPartnerGet
DocReturnsToPartnerGetResponse: TypeAlias = DocReturnsToPartnerRegosOffsettedArrayResult
DocReturnsToPartnerLockRequest: TypeAlias = DocReturnsToPartnerLockAndUnlock
DocReturnsToPartnerLockResponse: TypeAlias = UpdateResult
DocReturnsToPartnerPerformCancelRequest: TypeAlias = DocReturnsToPartnerPerformAndCancel
DocReturnsToPartnerPerformCancelResponse: TypeAlias = UpdateResult
DocReturnsToPartnerPerformRequest: TypeAlias = DocReturnsToPartnerPerformAndCancel
DocReturnsToPartnerPerformResponse: TypeAlias = UpdateResult
DocReturnsToPartnerUnlockRequest: TypeAlias = DocReturnsToPartnerLockAndUnlock
DocReturnsToPartnerUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocReturnsToPartner', 'DocReturnsToPartnerAdd', 'DocReturnsToPartnerColumn', 'DocReturnsToPartnerDelete', 'DocReturnsToPartnerDeleteMark', 'DocReturnsToPartnerEdit', 'DocReturnsToPartnerGet', 'DocReturnsToPartnerLockAndUnlock', 'DocReturnsToPartnerPerformAndCancel', 'DocReturnsToPartnerRegosOffsettedArrayResult']


__all__ = [
    'DocReturnsToPartner',
    'DocReturnsToPartnerAdd',
    'DocReturnsToPartnerColumn',
    'DocReturnsToPartnerColumns',
    'DocReturnsToPartnerDelete',
    'DocReturnsToPartnerDeleteMark',
    'DocReturnsToPartnerEdit',
    'DocReturnsToPartnerGet',
    'DocReturnsToPartnerLockAndUnlock',
    'DocReturnsToPartnerPerformAndCancel',
    'DocReturnsToPartnerRegosOffsettedArrayResult',
    'DocReturnsToPartnerGetRequest',
    'DocReturnsToPartnerGetResponse',
    'DocReturnsToPartnerAddRequest',
    'DocReturnsToPartnerAddResponse',
    'DocReturnsToPartnerEditRequest',
    'DocReturnsToPartnerEditResponse',
    'DocReturnsToPartnerDeleteMarkRequest',
    'DocReturnsToPartnerDeleteMarkResponse',
    'DocReturnsToPartnerDeleteRequest',
    'DocReturnsToPartnerDeleteResponse',
    'DocReturnsToPartnerLockRequest',
    'DocReturnsToPartnerLockResponse',
    'DocReturnsToPartnerUnlockRequest',
    'DocReturnsToPartnerUnlockResponse',
    'DocReturnsToPartnerPerformRequest',
    'DocReturnsToPartnerPerformResponse',
    'DocReturnsToPartnerPerformCancelRequest',
    'DocReturnsToPartnerPerformCancelResponse'
]
