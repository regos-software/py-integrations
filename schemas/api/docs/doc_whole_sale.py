"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocWholeSale(RegosModel):
    "Модель, описывающая документ отгрузки контрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа отгрузки контрагенту")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа отгрузки контрагенту")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    seller: User | None = PydField(default=None, description="Продавец")
    price_type: PriceType | None = PydField(default=None, description="Вид цены")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа: true - Заблокирован, false - Разблокирован")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем: true - Заблокирован текущим пользователем, false - Заблокирован другим пользователем")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Метка пометка на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocWholeSaleAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа отгрузки контрагенту в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="Id контрагента")
    stock_id: int | None = PydField(default=None, description="Id склада")
    currency_id: int | None = PydField(default=None, description="Id валюты")
    contract_id: int | None = PydField(default=None, description="Id договора")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="Id ответственного пользователя")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")
    seller_id: int | None = PydField(default=None, description="ID продавца")


class DocWholeSaleColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocWholeSaleColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocWholeSaleColumns(str, Enum):
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
    PriceTypeName = "PriceTypeName"
    Blocked = "Blocked"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocWholeSaleDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа отгрузки контрагенту")


class DocWholeSaleDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа отгрузки контрагенту")


class DocWholeSaleEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа отгрузки контрагенту")
    date: int | None = PydField(default=None, description="Дата документа отгрузки контрагенту в формате unix time в секундах")
    contract_id: int | None = PydField(default=None, description="ID договора")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    stock_id: int | None = PydField(default=None, description="ID склада")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    seller_id: int | None = PydField(default=None, description="ID продавца")
    price_type_id: int | None = PydField(default=None, description="ID вида цены")


class DocWholeSaleGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов отгрузки контрагенту")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="??? ??????? ???")
    sort_orders: list[DocWholeSaleColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="?????? ?????? ?? ??????????")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocWholeSaleLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id документов отгрузки контрагенту")


class DocWholeSalePerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа отгрузки контрагенту")


class DocWholeSaleRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocWholeSale] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock


DocWholeSaleAddRequest: TypeAlias = DocWholeSaleAdd
DocWholeSaleAddResponse: TypeAlias = InsertResult
DocWholeSaleDeleteMarkRequest: TypeAlias = DocWholeSaleDeleteMark
DocWholeSaleDeleteMarkResponse: TypeAlias = UpdateResult
DocWholeSaleDeleteRequest: TypeAlias = DocWholeSaleDelete
DocWholeSaleDeleteResponse: TypeAlias = UpdateResult
DocWholeSaleEditRequest: TypeAlias = DocWholeSaleEdit
DocWholeSaleEditResponse: TypeAlias = UpdateResult
DocWholeSaleGetRequest: TypeAlias = DocWholeSaleGet
DocWholeSaleGetResponse: TypeAlias = DocWholeSaleRegosOffsettedArrayResult
DocWholeSaleLockRequest: TypeAlias = DocWholeSaleLockAndUnlock
DocWholeSaleLockResponse: TypeAlias = UpdateResult
DocWholeSalePerformCancelRequest: TypeAlias = DocWholeSalePerformAndCancel
DocWholeSalePerformCancelResponse: TypeAlias = UpdateResult
DocWholeSalePerformRequest: TypeAlias = DocWholeSalePerformAndCancel
DocWholeSalePerformResponse: TypeAlias = UpdateResult
DocWholeSaleUnlockRequest: TypeAlias = DocWholeSaleLockAndUnlock
DocWholeSaleUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocWholeSale', 'DocWholeSaleAdd', 'DocWholeSaleColumn', 'DocWholeSaleDelete', 'DocWholeSaleDeleteMark', 'DocWholeSaleEdit', 'DocWholeSaleGet', 'DocWholeSaleLockAndUnlock', 'DocWholeSalePerformAndCancel', 'DocWholeSaleRegosOffsettedArrayResult']


__all__ = [
    'DocWholeSale',
    'DocWholeSaleAdd',
    'DocWholeSaleColumn',
    'DocWholeSaleColumns',
    'DocWholeSaleDelete',
    'DocWholeSaleDeleteMark',
    'DocWholeSaleEdit',
    'DocWholeSaleGet',
    'DocWholeSaleLockAndUnlock',
    'DocWholeSalePerformAndCancel',
    'DocWholeSaleRegosOffsettedArrayResult',
    'DocWholeSaleGetRequest',
    'DocWholeSaleGetResponse',
    'DocWholeSaleAddRequest',
    'DocWholeSaleAddResponse',
    'DocWholeSaleEditRequest',
    'DocWholeSaleEditResponse',
    'DocWholeSaleDeleteMarkRequest',
    'DocWholeSaleDeleteMarkResponse',
    'DocWholeSaleDeleteRequest',
    'DocWholeSaleDeleteResponse',
    'DocWholeSaleLockRequest',
    'DocWholeSaleLockResponse',
    'DocWholeSaleUnlockRequest',
    'DocWholeSaleUnlockResponse',
    'DocWholeSalePerformRequest',
    'DocWholeSalePerformResponse',
    'DocWholeSalePerformCancelRequest',
    'DocWholeSalePerformCancelResponse'
]
