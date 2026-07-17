"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocMovement(RegosModel):
    "Модель, описывающая документ перемещения"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перемещения")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа")
    stock_sender: Stock | None = PydField(default=None, description="Склад отправитель")
    stock_receiver: Stock | None = PydField(default=None, description="Склад получатель")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи")


class DocMovementAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock_sender_id: int | None = PydField(default=None, description="ID склада отправителя")
    stock_receiver_id: int | None = PydField(default=None, description="ID склада получателя")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя. По умолчанию берётся ID текущего пользователя, выполняющего данный метод")


class DocMovementColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocMovementColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocMovementColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    StockSenderName = "StockSenderName"
    StockReceiverName = "StockReceiverName"
    AttacheUserName = "AttacheUserName"
    Performed = "Performed"
    Blocked = "Blocked"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocMovementDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перемещения")


class DocMovementDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перемещения")


class DocMovementEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перемещения")
    date: int | None = PydField(default=None, description="Дата документа в формате unix time в секундах")
    stock_sender_id: int | None = PydField(default=None, description="ID склада отправителя")
    stock_receiver_id: int | None = PydField(default=None, description="ID склада получателя")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")


class DocMovementGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов перемещения")
    stock_sender_ids: list[int] | None = PydField(default=None, description="Массив ID складов отправителей")
    stock_receiver_ids: list[int] | None = PydField(default=None, description="Массив ID складов получателей")
    firm_sender_ids: list[int] | None = PydField(default=None, description="Массив ID фирм отправителей")
    firm_receiver_ids: list[int] | None = PydField(default=None, description="Массив ID фирм получателей")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    search: str | None = PydField(default=None, description="Поиск про значениям параметров: code - Код документа, Stock/name - Наименование склада, Partner/name - Наименование\nконтрагента, Partner/inn - ИНН контрагента, User/name - ФИО ответственного лица, DocContract/code - Код договора,\nFirm/name - Наименование предприятия, Firm/inn - ИНН предприятия")
    sort_orders: list[DocMovementColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocMovementLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов перемещения")


class DocMovementPerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа перемещения")


class DocMovementRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocMovement] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.stock import Stock


DocMovementAddRequest: TypeAlias = DocMovementAdd
DocMovementAddResponse: TypeAlias = InsertResult
DocMovementDeleteMarkRequest: TypeAlias = DocMovementDeleteMark
DocMovementDeleteMarkResponse: TypeAlias = UpdateResult
DocMovementDeleteRequest: TypeAlias = DocMovementDelete
DocMovementDeleteResponse: TypeAlias = UpdateResult
DocMovementEditRequest: TypeAlias = DocMovementEdit
DocMovementEditResponse: TypeAlias = UpdateResult
DocMovementGetRequest: TypeAlias = DocMovementGet
DocMovementGetResponse: TypeAlias = DocMovementRegosOffsettedArrayResult
DocMovementLockRequest: TypeAlias = DocMovementLockAndUnlock
DocMovementLockResponse: TypeAlias = UpdateResult
DocMovementPerformCancelRequest: TypeAlias = DocMovementPerformAndCancel
DocMovementPerformCancelResponse: TypeAlias = UpdateResult
DocMovementPerformRequest: TypeAlias = DocMovementPerformAndCancel
DocMovementPerformResponse: TypeAlias = UpdateResult
DocMovementUnlockRequest: TypeAlias = DocMovementLockAndUnlock
DocMovementUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocMovement', 'DocMovementAdd', 'DocMovementColumn', 'DocMovementDelete', 'DocMovementDeleteMark', 'DocMovementEdit', 'DocMovementGet', 'DocMovementLockAndUnlock', 'DocMovementPerformAndCancel', 'DocMovementRegosOffsettedArrayResult']


__all__ = [
    'DocMovement',
    'DocMovementAdd',
    'DocMovementColumn',
    'DocMovementColumns',
    'DocMovementDelete',
    'DocMovementDeleteMark',
    'DocMovementEdit',
    'DocMovementGet',
    'DocMovementLockAndUnlock',
    'DocMovementPerformAndCancel',
    'DocMovementRegosOffsettedArrayResult',
    'DocMovementGetRequest',
    'DocMovementGetResponse',
    'DocMovementAddRequest',
    'DocMovementAddResponse',
    'DocMovementEditRequest',
    'DocMovementEditResponse',
    'DocMovementDeleteMarkRequest',
    'DocMovementDeleteMarkResponse',
    'DocMovementDeleteRequest',
    'DocMovementDeleteResponse',
    'DocMovementLockRequest',
    'DocMovementLockResponse',
    'DocMovementUnlockRequest',
    'DocMovementUnlockResponse',
    'DocMovementPerformRequest',
    'DocMovementPerformResponse',
    'DocMovementPerformCancelRequest',
    'DocMovementPerformCancelResponse'
]
