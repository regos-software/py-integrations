"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CommonFileDelete(RegosModel):
    "Запрос на удаление файла."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID файла")


class CommonFileEdit(RegosModel):
    "Запрос на изменение файла."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID файла")
    name: str | None = PydField(default=None, description="Новое имя файла")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Новый уровень доступа")
    folder_id: int | None = PydField(default=None, description="Новая папка файла")
    width: int | None = PydField(default=None, description="Ширина визуального файла в пикселях")
    height: int | None = PydField(default=None, description="Высота визуального файла в пикселях")
    duration_ms: int | None = PydField(default=None, description="Длительность audio/video файла в миллисекундах")


class CommonFileGet(RegosModel):
    "Запрос на получение списка файлов с фильтрами и пагинацией."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID файлов")
    user_id: int | None = PydField(default=None, description="Фильтр по владельцу")
    folder_id: int | None = PydField(default=None, description="Фильтр по папке")
    access_level: CommonFileAccessLevelEnum | None = PydField(default=None, description="Фильтр по уровню доступа")
    search: str | None = PydField(default=None, description="Поиск по имени файла")
    limit: int | None = PydField(default=None, description="Лимит")
    offset: int | None = PydField(default=None, description="Смещение")
    sort_orders: list[BaseSortColumn] | None = PydField(default=None, description="Сортировка")


class CommonFileRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CommonFile] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BaseSortColumn, CommonFile, CommonFileAccessLevelEnum, Error, InsertResult, UpdateResult


FileAddResponse: TypeAlias = InsertResult
FileDeleteRequest: TypeAlias = CommonFileDelete
FileDeleteResponse: TypeAlias = UpdateResult
FileEditRequest: TypeAlias = CommonFileEdit
FileEditResponse: TypeAlias = UpdateResult
FileGetRequest: TypeAlias = CommonFileGet
FileGetResponse: TypeAlias = CommonFileRegosOffsettedArrayResult


_MODEL_NAMES = ['CommonFileDelete', 'CommonFileEdit', 'CommonFileGet', 'CommonFileRegosOffsettedArrayResult']


__all__ = [
    'CommonFileDelete',
    'CommonFileEdit',
    'CommonFileGet',
    'CommonFileRegosOffsettedArrayResult',
    'FileGetRequest',
    'FileGetResponse',
    'FileAddResponse',
    'FileEditRequest',
    'FileEditResponse',
    'FileDeleteRequest',
    'FileDeleteResponse'
]
