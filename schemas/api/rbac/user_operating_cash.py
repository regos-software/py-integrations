"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class UserOperatingCash(RegosModel):
    "Модель, описывающая кассу пользователя"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id кассы пользователя")
    user: User | None = PydField(default=None, description="Пользователь")
    operating_cash: OperatingCash | None = PydField(default=None, description="Касса")


class UserOperatingCashGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="id пользователя")
    user_id: int | None = PydField(default=None)
    operating_cash_id: int | None = PydField(default=None, description="id кассы")
    price_type_ids: list[int] | None = PydField(default=None)
    stock_ids: list[int] | None = PydField(default=None)
    is_virtual: bool | None = PydField(default=None, description="Метка о том, что касса виртуальная")
    sort_orders: list[UserOperatingCash_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: user_first_name - , middle_name - , last_name - , main_phone - , phones -")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class UserOperatingCashRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[UserOperatingCash] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class UserOperatingCashRemove(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id записи в таблице о связке кассы с пользователем")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    user_id: int | None = PydField(default=None, description="ID пользователя")


class UserOperatingCashSet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")


class UserOperatingCash_SortOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: UserOperatingCash_SortOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class UserOperatingCash_SortOrderColumn(str, Enum):
    Default = "Default"
    Id = "Id"
    OperatingCashId = "OperatingCashId"
    UserFullName = "UserFullName"
    UserMainPhone = "UserMainPhone"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.operating_cash import OperatingCash


UserOperatingCashGetRequest: TypeAlias = UserOperatingCashGet
UserOperatingCashGetResponse: TypeAlias = UserOperatingCashRegosOffsettedArrayResult
UserOperatingCashRemoveRequest: TypeAlias = UserOperatingCashRemove
UserOperatingCashRemoveResponse: TypeAlias = UpdateResult
UserOperatingCashSetRequest: TypeAlias = UserOperatingCashSet
UserOperatingCashSetResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['UserOperatingCash', 'UserOperatingCashGet', 'UserOperatingCashRegosOffsettedArrayResult', 'UserOperatingCashRemove', 'UserOperatingCashSet', 'UserOperatingCash_SortOrder']


__all__ = [
    'UserOperatingCash',
    'UserOperatingCashGet',
    'UserOperatingCashRegosOffsettedArrayResult',
    'UserOperatingCashRemove',
    'UserOperatingCashSet',
    'UserOperatingCash_SortOrder',
    'UserOperatingCash_SortOrderColumn',
    'UserOperatingCashGetRequest',
    'UserOperatingCashGetResponse',
    'UserOperatingCashSetRequest',
    'UserOperatingCashSetResponse',
    'UserOperatingCashRemoveRequest',
    'UserOperatingCashRemoveResponse'
]
