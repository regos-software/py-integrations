"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocInOut(RegosModel):
    "Модель, описывающая документ списания или занесения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа списания или занесения")
    inout_type: InOutType | None = PydField(default=None, description="Тип документа: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    stock: Stock | None = PydField(default=None, description="Склад")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    auto: bool | None = PydField(default=None, description="Метка, что документ создан автоматически")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocInOutAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock_id: int | None = PydField(default=None, description="ID склада")
    inout_type: InOutType | None = PydField(default=None, description="Тип документа: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocInOutColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocInOutColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocInOutColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Type = "Type"
    Date = "Date"
    Code = "Code"
    StockName = "StockName"
    AttacheUserName = "AttacheUserName"
    Blocked = "Blocked"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocInOutDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа занесения или списания")


class DocInOutDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа занесения или списания")


class DocInOutEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа занесения или списания")
    inout_type: InOutType | None = PydField(default=None, description="Тип документа: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock_id: int | None = PydField(default=None, description="ID склада")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocInOutGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    inout_type: InOutType | None = PydField(default=None, description="Тип документа: <Income | 1> - Входящий, <Outcome | 2> - Исходящий")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unixtime в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unixtime в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов занесения или списания")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID предприятий")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    auto: bool | None = PydField(default=None, description="Метка, что документ создан автоматически")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Firm/name - Наименование предприятия, Firm/inn - ИНН предприятия,\nStock/name - Наименование склада, User/name - ФИО ответственного лица")
    sort_orders: list[DocInOutColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocInOutLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив Id документов занесения или списания")


class DocInOutPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа занесения или списания")


class DocInOutRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocInOut] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class InOutType(str, Enum):
    all = "all"
    income = "income"
    outcome = "outcome"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.stock import Stock


DocInOutAddRequest: TypeAlias = DocInOutAdd
DocInOutAddResponse: TypeAlias = InsertResult
DocInOutDeleteMarkRequest: TypeAlias = DocInOutDeleteMark
DocInOutDeleteMarkResponse: TypeAlias = UpdateResult
DocInOutDeleteRequest: TypeAlias = DocInOutDelete
DocInOutDeleteResponse: TypeAlias = UpdateResult
DocInOutEditRequest: TypeAlias = DocInOutEdit
DocInOutEditResponse: TypeAlias = UpdateResult
DocInOutGetRequest: TypeAlias = DocInOutGet
DocInOutGetResponse: TypeAlias = DocInOutRegosOffsettedArrayResult
DocInOutLockRequest: TypeAlias = DocInOutLockAndUnlock
DocInOutLockResponse: TypeAlias = UpdateResult
DocInOutPerformCancelRequest: TypeAlias = DocInOutPerformAndCancel
DocInOutPerformCancelResponse: TypeAlias = UpdateResult
DocInOutPerformRequest: TypeAlias = DocInOutPerformAndCancel
DocInOutPerformResponse: TypeAlias = UpdateResult
DocInOutUnlockRequest: TypeAlias = DocInOutLockAndUnlock
DocInOutUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocInOut', 'DocInOutAdd', 'DocInOutColumn', 'DocInOutDelete', 'DocInOutDeleteMark', 'DocInOutEdit', 'DocInOutGet', 'DocInOutLockAndUnlock', 'DocInOutPerformAndCancel', 'DocInOutRegosOffsettedArrayResult']


__all__ = [
    'DocInOut',
    'DocInOutAdd',
    'DocInOutColumn',
    'DocInOutColumns',
    'DocInOutDelete',
    'DocInOutDeleteMark',
    'DocInOutEdit',
    'DocInOutGet',
    'DocInOutLockAndUnlock',
    'DocInOutPerformAndCancel',
    'DocInOutRegosOffsettedArrayResult',
    'InOutType',
    'DocInOutGetRequest',
    'DocInOutGetResponse',
    'DocInOutAddRequest',
    'DocInOutAddResponse',
    'DocInOutEditRequest',
    'DocInOutEditResponse',
    'DocInOutDeleteMarkRequest',
    'DocInOutDeleteMarkResponse',
    'DocInOutDeleteRequest',
    'DocInOutDeleteResponse',
    'DocInOutLockRequest',
    'DocInOutLockResponse',
    'DocInOutUnlockRequest',
    'DocInOutUnlockResponse',
    'DocInOutPerformRequest',
    'DocInOutPerformResponse',
    'DocInOutPerformCancelRequest',
    'DocInOutPerformCancelResponse'
]
