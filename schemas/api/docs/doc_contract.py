"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocContract(RegosModel):
    "Модель, описывающая договора"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id договора")
    code: str | None = PydField(default=None, description="Код договора")
    name: str | None = PydField(default=None, description="Наименование договора")
    date: int | None = PydField(default=None, description="Дата договора в формате unix time")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения работ по договору в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания выполнения работ по договору в формате unix time в секундах")
    partner: Partner | None = PydField(default=None, description="Контрагент")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    direction: ContractDirection | None = PydField(default=None, description="Направление договора: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    amount: _Decimal | None = PydField(default=None, description="Сумма договора")
    currency: Currency | None = PydField(default=None, description="Валюта договора")
    details: str | None = PydField(default=None, description="Детали договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user: User | None = PydField(default=None, description="Ответственный пользователь")
    active: bool | None = PydField(default=None, description="Действительность: true - Действительный, false - Не действительный")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocContractAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: str | None = PydField(default=None, description="Код договора")
    date: int | None = PydField(default=None, description="Дата договора в формате unix time в секундах")
    direction: ContractDirection | None = PydField(default=None, description="Направление договора: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    name: str | None = PydField(default=None, description="Наименование договора")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    amount: _Decimal | None = PydField(default=None, description="Сумма договора")
    currency_id: int | None = PydField(default=None, description="ID валюты договора")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения работ по договору в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания выполнения работ по договору в формате unix time в секундах")
    details: str | None = PydField(default=None, description="Детали договора")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию подставляется текущий пользователь")
    active: bool | None = PydField(default=None, description="Действительность: true - Действительный, false - Не действительный")


class DocContractColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocContractColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocContractColumns(str, Enum):
    Default = "Default"
    Code = "Code"
    Date = "Date"
    FirmName = "FirmName"
    PartnerName = "PartnerName"
    Dircetion = "Dircetion"
    Amount = "Amount"
    CurrencyName = "CurrencyName"
    StartDate = "StartDate"
    EndDate = "EndDate"


class DocContractDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID договора")


class DocContractDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id договора")


class DocContractEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID договора")
    code: str | None = PydField(default=None, description="Код договора")
    date: int | None = PydField(default=None, description="Дата договора в формате unix time в секундах")
    direction: ContractDirection | None = PydField(default=None, description="Направление договора: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    name: str | None = PydField(default=None, description="Наименование договора")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    amount: _Decimal | None = PydField(default=None, description="Сумма договора")
    currency_id: int | None = PydField(default=None, description="ID валюты договора")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения работ по договору в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания выполнения работ по договору в формате unix time в секундах")
    details: str | None = PydField(default=None, description="Детали договора")
    description: str | None = PydField(default=None, description="Примечание")
    active: bool | None = PydField(default=None, description="Действительность: true - Действительный, false - Не действительный")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию подставляется текущий пользователь")


class DocContractGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    direction: ContractDirection | None = PydField(default=None, description="Направление договора: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов оплаты")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    partner_ids: list[int] | None = PydField(default=None, description="Массив ID контрагентов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    search: str | None = PydField(default=None, description="Строка поиска по полям: code - Код документа, Partner/name - ФИО контрагента, partner_inn - ИНН контрагента, firm_name -\nНаименование предприятия, attached_user_name - ФИО ответственноого пользователя")
    sort_orders: list[DocContractColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    active: bool | None = PydField(default=None, description="Действительность: true - Действительный, false - Не действительный")
    deleted_mark: bool | None = PydField(default=None, description="Пометка на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocContractRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocContract] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocContractShort(RegosModel):
    "Модель, сокращённо описывающая договора"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID договора")
    code: str | None = PydField(default=None, description="Код договора")
    name: str | None = PydField(default=None, description="Наименование договора")
    date: int | None = PydField(default=None, description="Дата договора в формате unix time в секундах")
    start_date: int | None = PydField(default=None, description="Дата начала выполнения работ по договору в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания выполнения работ по договору в формате unix time в секундах")
    partner_id: int | None = PydField(default=None, description="ID контрагента")
    partner_name: str | None = PydField(default=None, description="ФИО контрагента")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    direction: ContractDirection | None = PydField(default=None, description="Направление договора: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    currency_id: int | None = PydField(default=None, description="ID валюты договора")
    amount: _Decimal | None = PydField(default=None, description="Сумма договора")
    details: str | None = PydField(default=None, description="Детали договора")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None)
    active: bool | None = PydField(default=None, description="Действительность: true - Действительный, false - Не действительный")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocContractShortRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocContractShort] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, ContractDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.partner import Partner


ContractDirection: TypeAlias = ContractDirection
DocContractAddRequest: TypeAlias = DocContractAdd
DocContractAddResponse: TypeAlias = InsertResult
DocContractDeleteMarkRequest: TypeAlias = DocContractDeleteMark
DocContractDeleteMarkResponse: TypeAlias = UpdateResult
DocContractDeleteRequest: TypeAlias = DocContractDelete
DocContractDeleteResponse: TypeAlias = UpdateResult
DocContractEditRequest: TypeAlias = DocContractEdit
DocContractEditResponse: TypeAlias = UpdateResult
DocContractGetRequest: TypeAlias = DocContractGet
DocContractGetResponse: TypeAlias = DocContractRegosOffsettedArrayResult
DocContractGetShortRequest: TypeAlias = DocContractGet
DocContractGetShortResponse: TypeAlias = DocContractShortRegosOffsettedArrayResult


_MODEL_NAMES = ['DocContract', 'DocContractAdd', 'DocContractColumn', 'DocContractDelete', 'DocContractDeleteMark', 'DocContractEdit', 'DocContractGet', 'DocContractRegosOffsettedArrayResult', 'DocContractShort', 'DocContractShortRegosOffsettedArrayResult']


__all__ = [
    'DocContract',
    'DocContractAdd',
    'DocContractColumn',
    'DocContractColumns',
    'DocContractDelete',
    'DocContractDeleteMark',
    'DocContractEdit',
    'DocContractGet',
    'DocContractRegosOffsettedArrayResult',
    'DocContractShort',
    'DocContractShortRegosOffsettedArrayResult',
    'DocContractGetRequest',
    'DocContractGetResponse',
    'DocContractGetShortRequest',
    'DocContractGetShortResponse',
    'DocContractAddRequest',
    'DocContractAddResponse',
    'DocContractEditRequest',
    'DocContractEditResponse',
    'DocContractDeleteMarkRequest',
    'DocContractDeleteMarkResponse',
    'DocContractDeleteRequest',
    'DocContractDeleteResponse',
    'ContractDirection'
]
