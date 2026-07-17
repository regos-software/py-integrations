"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocProduction(RegosModel):
    "Модель, описывающая документ производства"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа производства")
    type: DocTechMapType | None = PydField(default=None, description="Тип документа производства: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    date: int | None = PydField(default=None, description="Дата документа производства")
    code: str | None = PydField(default=None, description="Код документа производства")
    stock: Stock | None = PydField(default=None, description="Склад")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user: User | None = PydField(default=None, description="Ответственный пользователь")
    blocked: bool | None = PydField(default=None, description="Статус блокировки документа производства для редактирования: true - Заблокирован для редактирования, false - Разблокирован для редактирования")
    current_user_blocked: bool | None = PydField(default=None, description="Статус блокировки документа производства текущим пользователем: true - Заблокирован для редактирования текущим\nпользователем, false - Не заблокирован для редактирования текущим пользователем")
    performed: bool | None = PydField(default=None, description="Статус проведения документа производства: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Статус пометки на удаление:true - Помечен на удаление, false - Не помечен на удаление")
    last_update: int | None = PydField(default=None, description="Время последнего изменения в формате Unix time")


class DocProductionRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocProduction] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class DocProduction_Add(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: DocTechMapType | None = PydField(default=None, description="Тип документа производства: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    date: int | None = PydField(default=None, description="Дата документа производства в формате unix time")
    stock_id: int | None = PydField(default=None, description="ID склада")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умалчанию - текущий пользователь")


class DocProduction_Column(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocProduction_Columns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocProduction_Columns(str, Enum):
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


class DocProduction_Edit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа производства")
    date: int | None = PydField(default=None, description="Дата документа производства в формате unix time")
    stock_id: int | None = PydField(default=None, description="ID склада")
    description: str | None = PydField(default=None, description="Примечание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocProduction_Get(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов производства")
    type: DocTechMapType | None = PydField(default=None, description="Тип документа производства: <Assemblable | 1> - Сборка, <Disassemblable | 2> - Разборка")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа производства")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    blocked: bool | None = PydField(default=None, description="Статус блокировки документа производства для редактирования: true - Заблокирован для редактирования, false - Разблокирован для редактирования")
    performed: bool | None = PydField(default=None, description="Статус проведения документа производства: true - Проведён, false - Не проведён")
    deleted_mark: bool | None = PydField(default=None, description="Статус пометки на удаление документа производства: true - Проведён, false - Не проведён")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, User/name - ФИО ответственного лица, Stock/name - Наименование\nсклада, Firm/name - Наименование предприятия, Firm/inn - ИНН предприятия")
    sort_orders: list[DocProduction_Column] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.docs.doc_tech_map import DocTechMapType
from schemas.api.rbac.user import User
from schemas.api.references.stock import Stock


DocProductionAddRequest: TypeAlias = DocProduction_Add
DocProductionAddResponse: TypeAlias = InsertResult
DocProductionDeleteRequest: TypeAlias = Base_ID
DocProductionDeleteResponse: TypeAlias = UpdateResult
DocProductionEditRequest: TypeAlias = DocProduction_Edit
DocProductionEditResponse: TypeAlias = UpdateResult
DocProductionGetRequest: TypeAlias = DocProduction_Get
DocProductionGetResponse: TypeAlias = DocProductionRegosOffsettedArrayResult
DocProductionLockRequest: TypeAlias = Base_ID
DocProductionLockResponse: TypeAlias = UpdateResult
DocProductionPerformCancelRequest: TypeAlias = Base_ID
DocProductionPerformCancelResponse: TypeAlias = UpdateResult
DocProductionPerformRequest: TypeAlias = Base_ID
DocProductionPerformResponse: TypeAlias = UpdateResult
DocProductionUnlockRequest: TypeAlias = Base_ID
DocProductionUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocProduction', 'DocProductionRegosOffsettedArrayResult', 'DocProduction_Add', 'DocProduction_Column', 'DocProduction_Edit', 'DocProduction_Get']


__all__ = [
    'DocProduction',
    'DocProductionRegosOffsettedArrayResult',
    'DocProduction_Add',
    'DocProduction_Column',
    'DocProduction_Columns',
    'DocProduction_Edit',
    'DocProduction_Get',
    'DocProductionGetRequest',
    'DocProductionGetResponse',
    'DocProductionAddRequest',
    'DocProductionAddResponse',
    'DocProductionEditRequest',
    'DocProductionEditResponse',
    'DocProductionDeleteRequest',
    'DocProductionDeleteResponse',
    'DocProductionLockRequest',
    'DocProductionLockResponse',
    'DocProductionUnlockRequest',
    'DocProductionUnlockResponse',
    'DocProductionPerformRequest',
    'DocProductionPerformResponse',
    'DocProductionPerformCancelRequest',
    'DocProductionPerformCancelResponse'
]
