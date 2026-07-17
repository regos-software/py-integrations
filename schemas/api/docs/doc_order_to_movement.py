"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocOrderToMovement(RegosModel):
    "Модель, описывающая документ заказа на перемещение"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа на перемещение")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    stock_receiver: Stock | None = PydField(default=None, description="Склад получатель")
    status: DocumentStatus | None = PydField(default=None, description="Статус документа")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа текущим пользователем")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocOrderToMovementAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock_receiver_id: int | None = PydField(default=None, description="ID склада получателя")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию - текущий пользователь")


class DocOrderToMovementColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocOrderToMovementColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocOrderToMovementColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    StockReceiverName = "StockReceiverName"
    StatusName = "StatusName"
    AttacheUserName = "AttacheUserName"
    Blocked = "Blocked"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocOrderToMovementDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа на перемещение")


class DocOrderToMovementDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа на перемещение")


class DocOrderToMovementEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа заказа на перемещение")
    date: int | None = PydField(default=None, description="Дата документа в формате unixtime в секундах")
    stock_receiver_id: int | None = PydField(default=None, description="ID склада получателя")
    status_id: int | None = PydField(default=None, description="ID статуса документа")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocOrderToMovementGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа на перемещение")
    status_ids: list[int] | None = PydField(default=None, description="Массив ID статусов")
    stock_receiver_ids: list[int] | None = PydField(default=None, description="Массив ID складов получателей")
    firm_receiver_ids: list[int] | None = PydField(default=None, description="Массив ID фирм получателей")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    sort_orders: list[DocOrderToMovementColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Stock/name - Наименование склада, User/name - ФИО ответственного лица")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocOrderToMovementLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов заказа на перемещение")


class DocOrderToMovementRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocOrderToMovement] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.docs.document_status import DocumentStatus
from schemas.api.rbac.user import User
from schemas.api.references.stock import Stock


DocOrderToMovementAddRequest: TypeAlias = DocOrderToMovementAdd
DocOrderToMovementAddResponse: TypeAlias = InsertResult
DocOrderToMovementDeleteMarkRequest: TypeAlias = DocOrderToMovementDeleteMark
DocOrderToMovementDeleteMarkResponse: TypeAlias = UpdateResult
DocOrderToMovementDeleteRequest: TypeAlias = DocOrderToMovementDelete
DocOrderToMovementDeleteResponse: TypeAlias = UpdateResult
DocOrderToMovementEditRequest: TypeAlias = DocOrderToMovementEdit
DocOrderToMovementEditResponse: TypeAlias = UpdateResult
DocOrderToMovementGetRequest: TypeAlias = DocOrderToMovementGet
DocOrderToMovementGetResponse: TypeAlias = DocOrderToMovementRegosOffsettedArrayResult
DocOrderToMovementLockRequest: TypeAlias = DocOrderToMovementLockAndUnlock
DocOrderToMovementLockResponse: TypeAlias = UpdateResult
DocOrderToMovementUnlockRequest: TypeAlias = DocOrderToMovementLockAndUnlock
DocOrderToMovementUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocOrderToMovement', 'DocOrderToMovementAdd', 'DocOrderToMovementColumn', 'DocOrderToMovementDelete', 'DocOrderToMovementDeleteMark', 'DocOrderToMovementEdit', 'DocOrderToMovementGet', 'DocOrderToMovementLockAndUnlock', 'DocOrderToMovementRegosOffsettedArrayResult']


__all__ = [
    'DocOrderToMovement',
    'DocOrderToMovementAdd',
    'DocOrderToMovementColumn',
    'DocOrderToMovementColumns',
    'DocOrderToMovementDelete',
    'DocOrderToMovementDeleteMark',
    'DocOrderToMovementEdit',
    'DocOrderToMovementGet',
    'DocOrderToMovementLockAndUnlock',
    'DocOrderToMovementRegosOffsettedArrayResult',
    'DocOrderToMovementGetRequest',
    'DocOrderToMovementGetResponse',
    'DocOrderToMovementAddRequest',
    'DocOrderToMovementAddResponse',
    'DocOrderToMovementEditRequest',
    'DocOrderToMovementEditResponse',
    'DocOrderToMovementDeleteMarkRequest',
    'DocOrderToMovementDeleteMarkResponse',
    'DocOrderToMovementDeleteRequest',
    'DocOrderToMovementDeleteResponse',
    'DocOrderToMovementLockRequest',
    'DocOrderToMovementLockResponse',
    'DocOrderToMovementUnlockRequest',
    'DocOrderToMovementUnlockResponse'
]
