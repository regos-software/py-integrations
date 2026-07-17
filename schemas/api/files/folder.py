"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CommonFolderAdd(RegosModel):
    "Модель запроса добавления папки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование папки")
    parent_id: int | None = PydField(default=None, description="Родительская папка. По умолчанию используется root (id = 1)")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="personal или public")


class CommonFolderDelete(RegosModel):
    "Модель запроса удаления папки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID папки")


class CommonFolderEdit(RegosModel):
    "Модель запроса редактирования папки."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID папки")
    name: str | None = PydField(default=None, description="Новое имя папки")
    parent_id: int | None = PydField(default=None, description="Новый родитель")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Новый уровень доступа")


class CommonFolderGet(RegosModel):
    "Модель запроса получения папок."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID папок")
    parent_id: int | None = PydField(default=None, description="Фильтр по родительской папке")
    user_id: int | None = PydField(default=None, description="Фильтр по владельцу")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Фильтр по уровню доступа")
    search: str | None = PydField(default=None, description="Поиск по имени папки")
    limit: int | None = PydField(default=None, description="Лимит")
    offset: int | None = PydField(default=None, description="Смещение")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировка")


class CommonFolderRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CommonFolder] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, CommonFileAccessLevelEnum, CommonFolder, Error, InsertResult, UpdateResult


FolderAddRequest: TypeAlias = CommonFolderAdd
FolderAddResponse: TypeAlias = InsertResult
FolderDeleteRequest: TypeAlias = CommonFolderDelete
FolderDeleteResponse: TypeAlias = UpdateResult
FolderEditRequest: TypeAlias = CommonFolderEdit
FolderEditResponse: TypeAlias = UpdateResult
FolderGetRequest: TypeAlias = CommonFolderGet
FolderGetResponse: TypeAlias = CommonFolderRegosOffsettedArrayResult


_MODEL_NAMES = ['CommonFolderAdd', 'CommonFolderDelete', 'CommonFolderEdit', 'CommonFolderGet', 'CommonFolderRegosOffsettedArrayResult']


__all__ = [
    'CommonFolderAdd',
    'CommonFolderDelete',
    'CommonFolderEdit',
    'CommonFolderGet',
    'CommonFolderRegosOffsettedArrayResult',
    'FolderGetRequest',
    'FolderGetResponse',
    'FolderAddRequest',
    'FolderAddResponse',
    'FolderEditRequest',
    'FolderEditResponse',
    'FolderDeleteRequest',
    'FolderDeleteResponse'
]
