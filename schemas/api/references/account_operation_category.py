"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class AccountOperationCategory(RegosModel):
    "Модель, описывающая статьи доходов и расходов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id статьи дохода или расхода")
    parent_id: int | None = PydField(default=None, description="Id родительской статьи дохода или расхода")
    child_count: int | None = PydField(default=None, description="Количество вложенных (дочерних) статей дохода/расхода")
    name: str | None = PydField(default=None, description="Наименование статьи расхода или дохода")
    positive: bool | None = PydField(default=None, description="Вид статьи: true - статья дохода, false - статья расхода")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате Unix time в секундах")


class AccountOperationCategoryAdd(RegosModel):
    "Модель добавления категории операции."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="Id родительской статьи дохода или расхода, если не указан, то 0")
    name: str | None = PydField(default=None, description="Наименование статьи дохода или расхода")
    positive: bool | None = PydField(default=None, description="Вид статьи: true - статья дохода, false - статья расхода")


class AccountOperationCategoryDelete(RegosModel):
    "Модель удаления категории операции."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id статьи дохода или расхода")


class AccountOperationCategoryEdit(RegosModel):
    "Модель изменения категории операции."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id статьи дохода или расхода")
    parent_id: int | None = PydField(default=None, description="Id родительской статьи дохода или расхода")
    name: str | None = PydField(default=None, description="Наименование статьи расхода или дохода")


class AccountOperationCategoryGet(RegosModel):
    "Модель запроса списка категорий операций."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив id статьей доходов и расходов")
    parent_ids: list[int] | None = PydField(default=None, description="массив id родительских групп")
    child_count: int | None = PydField(default=None, description="количество вложенных (дочерних) статей дохода/расхода")
    positive: bool | None = PydField(default=None, description="Вид статьи: true - статья дохода, false - статья расхода")
    sort_orders: list[AccountOperationCategory_SortOrder] | None = PydField(default=None, description="Сортировака выходных параметров")
    search: str | None = PydField(default=None, description="Поиск по: наименованию")
    limit: int | None = PydField(default=None, description="Количество элементов выборки, возвращаемых при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class AccountOperationCategoryRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[AccountOperationCategory] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class AccountOperationCategory_SortOrder(RegosModel):
    "Настройка сортировки категорий операций."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: AccountOperationCategory_SortOrderColumn | None = PydField(default=None, description="Колонка сортировки.")
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="Направление сортировки.")


class AccountOperationCategory_SortOrderColumn(str, Enum):
    "Колонки сортировки категорий операций."
    Default = "Default"
    Id = "Id"
    ParentId = "ParentId"
    ChildCount = "ChildCount"
    Name = "Name"
    Positive = "Positive"
    LastUpdate = "LastUpdate"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error, InsertResult, UpdateResult


AccountOperationCategoryAddRequest: TypeAlias = AccountOperationCategoryAdd
AccountOperationCategoryAddResponse: TypeAlias = InsertResult
AccountOperationCategoryDeleteRequest: TypeAlias = AccountOperationCategoryDelete
AccountOperationCategoryDeleteResponse: TypeAlias = UpdateResult
AccountOperationCategoryEditRequest: TypeAlias = AccountOperationCategoryEdit
AccountOperationCategoryEditResponse: TypeAlias = UpdateResult
AccountOperationCategoryGetRequest: TypeAlias = AccountOperationCategoryGet
AccountOperationCategoryGetResponse: TypeAlias = AccountOperationCategoryRegosOffsettedArrayResult


_MODEL_NAMES = ['AccountOperationCategory', 'AccountOperationCategoryAdd', 'AccountOperationCategoryDelete', 'AccountOperationCategoryEdit', 'AccountOperationCategoryGet', 'AccountOperationCategoryRegosOffsettedArrayResult', 'AccountOperationCategory_SortOrder']


__all__ = [
    'AccountOperationCategory',
    'AccountOperationCategoryAdd',
    'AccountOperationCategoryDelete',
    'AccountOperationCategoryEdit',
    'AccountOperationCategoryGet',
    'AccountOperationCategoryRegosOffsettedArrayResult',
    'AccountOperationCategory_SortOrder',
    'AccountOperationCategory_SortOrderColumn',
    'AccountOperationCategoryGetRequest',
    'AccountOperationCategoryGetResponse',
    'AccountOperationCategoryAddRequest',
    'AccountOperationCategoryAddResponse',
    'AccountOperationCategoryEditRequest',
    'AccountOperationCategoryEditResponse',
    'AccountOperationCategoryDeleteRequest',
    'AccountOperationCategoryDeleteResponse'
]
