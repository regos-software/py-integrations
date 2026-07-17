"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocOrderToPartner(RegosModel):
    "Модель, описывающая документ заказа контрагенту"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа заказа контрагенту")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    contract: DocContractShort | None = PydField(default=None, description="Документ договора")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    currency: Currency | None = PydField(default=None, description="Валюта")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    amount: _Decimal | None = PydField(default=None, description="Сумма документа закупки")
    status: DocumentStatus | None = PydField(default=None, description="Статус документа")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    description: str | None = PydField(default=None, description="Примечение")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocOrderToPartnerAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа заказа контрагенту в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    contract_id: int | None = PydField(default=None, description="ID договора")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечение")


class DocOrderToPartnerColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocOrderToPartnerColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocOrderToPartnerColumns(str, Enum):
    Default = "Default"
    Code = "Code"
    Date = "Date"
    ContractName = "ContractName"
    PartnerName = "PartnerName"
    OrderStatusName = "OrderStatusName"
    Amount = "Amount"
    CurrencyName = "CurrencyName"


class DocOrderToPartnerDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа заказа контрагенту")


class DocOrderToPartnerDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа контрагенту")


class DocOrderToPartnerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа контрагенту")
    date: int | None = PydField(default=None, description="Дата документа заказа контрагенту в формате unixtime в секундах")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    contract_id: int | None = PydField(default=None, description="ID договора")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    currency_id: int | None = PydField(default=None, description="ID валюты")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    exchange_rate: _Decimal | None = PydField(default=None, description="Курс валюты")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    description: str | None = PydField(default=None, description="Примечание")


class DocOrderToPartnerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа от контрагента")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    status_ids: list[int] | None = PydField(default=None, description="Массив ID статусов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    blocked: bool | None = PydField(default=None, description="Состояние блокировки для редактирования: true - Заблокирован, false - Разблокировин")
    deleted_mark: bool | None = PydField(default=None, description="Состояние пометки на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    vat_calculation_type: VatCalculationTypeEnum | None = PydField(default=None, description="Расчет НДС: <No | 1> - Не начислять, <Exclude | 2> - В сумме, <Include | 3> - Сверху")
    sort_orders: list[DocOrderToPartnerColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: code - Код документа, Partner/name - Наименование контрагента, Partner/inn - ИНН контрагента,\nUser/name - ФИО ответственного лица, DocContract/code - Код договора")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocOrderToPartnerLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа контрагенту")


class DocOrderToPartnerRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocOrderToPartner] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult, VatCalculationTypeEnum
from schemas.api.docs.doc_contract import DocContractShort
from schemas.api.docs.document_status import DocumentStatus
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.partner import Partner


DocOrderToPartnerAddRequest: TypeAlias = DocOrderToPartnerAdd
DocOrderToPartnerAddResponse: TypeAlias = InsertResult
DocOrderToPartnerDeleteMarkRequest: TypeAlias = DocOrderToPartnerDeleteMark
DocOrderToPartnerDeleteMarkResponse: TypeAlias = UpdateResult
DocOrderToPartnerDeleteRequest: TypeAlias = DocOrderToPartnerDelete
DocOrderToPartnerDeleteResponse: TypeAlias = UpdateResult
DocOrderToPartnerEditRequest: TypeAlias = DocOrderToPartnerEdit
DocOrderToPartnerEditResponse: TypeAlias = UpdateResult
DocOrderToPartnerGetRequest: TypeAlias = DocOrderToPartnerGet
DocOrderToPartnerGetResponse: TypeAlias = DocOrderToPartnerRegosOffsettedArrayResult
DocOrderToPartnerLockRequest: TypeAlias = DocOrderToPartnerLockAndUnlock
DocOrderToPartnerLockResponse: TypeAlias = UpdateResult
DocOrderToPartnerUnlockRequest: TypeAlias = DocOrderToPartnerLockAndUnlock
DocOrderToPartnerUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocOrderToPartner', 'DocOrderToPartnerAdd', 'DocOrderToPartnerColumn', 'DocOrderToPartnerDelete', 'DocOrderToPartnerDeleteMark', 'DocOrderToPartnerEdit', 'DocOrderToPartnerGet', 'DocOrderToPartnerLockAndUnlock', 'DocOrderToPartnerRegosOffsettedArrayResult']


__all__ = [
    'DocOrderToPartner',
    'DocOrderToPartnerAdd',
    'DocOrderToPartnerColumn',
    'DocOrderToPartnerColumns',
    'DocOrderToPartnerDelete',
    'DocOrderToPartnerDeleteMark',
    'DocOrderToPartnerEdit',
    'DocOrderToPartnerGet',
    'DocOrderToPartnerLockAndUnlock',
    'DocOrderToPartnerRegosOffsettedArrayResult',
    'DocOrderToPartnerGetRequest',
    'DocOrderToPartnerGetResponse',
    'DocOrderToPartnerAddRequest',
    'DocOrderToPartnerAddResponse',
    'DocOrderToPartnerEditRequest',
    'DocOrderToPartnerEditResponse',
    'DocOrderToPartnerDeleteMarkRequest',
    'DocOrderToPartnerDeleteMarkResponse',
    'DocOrderToPartnerDeleteRequest',
    'DocOrderToPartnerDeleteResponse',
    'DocOrderToPartnerLockRequest',
    'DocOrderToPartnerLockResponse',
    'DocOrderToPartnerUnlockRequest',
    'DocOrderToPartnerUnlockResponse'
]
