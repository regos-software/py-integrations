"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocSetPrice(RegosModel):
    "Модель, описывающая документы установки цен"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа установки цен")
    date: int | None = PydField(default=None, description="Дата документа установки цен в формате unix time в секундах")
    code: str | None = PydField(default=None, description="Код документа установки цен")
    price_type: PriceType | None = PydField(default=None, description="Вид цены")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    blocked: bool | None = PydField(default=None, description="Метка о блокировке документа")
    performed: bool | None = PydField(default=None, description="Метка о проведении документа")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    attached_user: User | None = PydField(default=None, description="Ответственное лицо")
    current_user_blocked: bool | None = PydField(default=None, description="Метка о блокировке текущим пользователем")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocSetPriceAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    price_type_id: int | None = PydField(default=None, description="ID вида цены в документе установки цен")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class DocSetPriceColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocSetPriceColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocSetPriceColumns(str, Enum):
    Default = "Default"
    Id = "Id"
    Date = "Date"
    Code = "Code"
    PriceTypeName = "PriceTypeName"
    Blocked = "Blocked"
    Performed = "Performed"
    DeletedMark = "DeletedMark"
    LastUpdate = "LastUpdate"


class DocSetPriceDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа установки цен")


class DocSetPriceDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа")


class DocSetPriceEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id документа установки цен")
    price_type_id: int | None = PydField(default=None, description="Id вида цены")
    attached_user_id: int | None = PydField(default=None, description="ID ответственного пользователя")
    description: str | None = PydField(default=None, description="Дополнительное описание")


class DocSetPriceGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    ids: list[int] | None = PydField(default=None, description="Массив ID документов установки цен")
    price_type_ids: list[int] | None = PydField(default=None, description="Массив ID видов цен")
    search: str | None = PydField(default=None, description="Строка поиска по полям: - , - , - , - , -")
    attached_user_ids: list[int] | None = PydField(default=None, description="Массив ID ответственных пользователей")
    sort_orders: list[DocSetPriceColumn] | None = PydField(default=None, description="Сортировка выходных параметров")
    performed: bool | None = PydField(default=None, description="Проведён ли документ: true - Проведён, false - Не проведён")
    blocked: bool | None = PydField(default=None, description="Заблокирован ли документ: true - Заблокирован, false - Не заблокирован")
    deleted_mark: bool | None = PydField(default=None, description="Помечен ли документ на удаление: true - Помечен на удаление, false - Не помечен на удаление")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocSetPriceLockAndUnlock(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID документов установки цен")


class DocSetPricePerformAndCancel(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID документа установки цен")


class DocSetPriceRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocSetPrice] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.price_type import PriceType


DocSetPriceAddRequest: TypeAlias = DocSetPriceAdd
DocSetPriceAddResponse: TypeAlias = InsertResult
DocSetPriceDeleteMarkRequest: TypeAlias = DocSetPriceDeleteMark
DocSetPriceDeleteMarkResponse: TypeAlias = UpdateResult
DocSetPriceDeleteRequest: TypeAlias = DocSetPriceDelete
DocSetPriceDeleteResponse: TypeAlias = UpdateResult
DocSetPriceEditRequest: TypeAlias = DocSetPriceEdit
DocSetPriceEditResponse: TypeAlias = UpdateResult
DocSetPriceGetRequest: TypeAlias = DocSetPriceGet
DocSetPriceGetResponse: TypeAlias = DocSetPriceRegosOffsettedArrayResult
DocSetPriceLockRequest: TypeAlias = DocSetPriceLockAndUnlock
DocSetPriceLockResponse: TypeAlias = UpdateResult
DocSetPricePerformCancelRequest: TypeAlias = DocSetPricePerformAndCancel
DocSetPricePerformCancelResponse: TypeAlias = UpdateResult
DocSetPricePerformRequest: TypeAlias = DocSetPricePerformAndCancel
DocSetPricePerformResponse: TypeAlias = UpdateResult
DocSetPriceUnlockRequest: TypeAlias = DocSetPriceLockAndUnlock
DocSetPriceUnlockResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocSetPrice', 'DocSetPriceAdd', 'DocSetPriceColumn', 'DocSetPriceDelete', 'DocSetPriceDeleteMark', 'DocSetPriceEdit', 'DocSetPriceGet', 'DocSetPriceLockAndUnlock', 'DocSetPricePerformAndCancel', 'DocSetPriceRegosOffsettedArrayResult']


__all__ = [
    'DocSetPrice',
    'DocSetPriceAdd',
    'DocSetPriceColumn',
    'DocSetPriceColumns',
    'DocSetPriceDelete',
    'DocSetPriceDeleteMark',
    'DocSetPriceEdit',
    'DocSetPriceGet',
    'DocSetPriceLockAndUnlock',
    'DocSetPricePerformAndCancel',
    'DocSetPriceRegosOffsettedArrayResult',
    'DocSetPriceGetRequest',
    'DocSetPriceGetResponse',
    'DocSetPriceAddRequest',
    'DocSetPriceAddResponse',
    'DocSetPriceEditRequest',
    'DocSetPriceEditResponse',
    'DocSetPriceDeleteMarkRequest',
    'DocSetPriceDeleteMarkResponse',
    'DocSetPriceDeleteRequest',
    'DocSetPriceDeleteResponse',
    'DocSetPriceLockRequest',
    'DocSetPriceLockResponse',
    'DocSetPriceUnlockRequest',
    'DocSetPriceUnlockResponse',
    'DocSetPricePerformRequest',
    'DocSetPricePerformResponse',
    'DocSetPricePerformCancelRequest',
    'DocSetPricePerformCancelResponse'
]
