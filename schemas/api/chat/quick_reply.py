"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class QuickReply(RegosModel):
    "Общие подсказки быстрых ответов для чатов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Идентификатор подсказки")
    text: str | None = PydField(default=None, description="Текст подсказки")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class QuickReplyAdd(RegosModel):
    "Модель добавления шаблона быстрого ответа."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    text: str | None = PydField(default=None, description="Текст подсказки")


class QuickReplyDelete(RegosModel):
    "Модель удаления шаблона быстрого ответа."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID подсказки")


class QuickReplyGet(RegosModel):
    "Модель фильтров для получения шаблонов быстрых ответов."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID")
    search: str | None = PydField(default=None, description="Поиск по тексту")
    limit: int | None = PydField(default=None, description="Размер страницы")
    offset: int | None = PydField(default=None, description="Смещение")


class QuickReplyRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[QuickReply] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


QuickReplyAddRequest: TypeAlias = QuickReplyAdd
QuickReplyAddResponse: TypeAlias = InsertResult
QuickReplyDeleteRequest: TypeAlias = QuickReplyDelete
QuickReplyDeleteResponse: TypeAlias = UpdateResult
QuickReplyGetRequest: TypeAlias = QuickReplyGet
QuickReplyGetResponse: TypeAlias = QuickReplyRegosOffsettedArrayResult


_MODEL_NAMES = ['QuickReply', 'QuickReplyAdd', 'QuickReplyDelete', 'QuickReplyGet', 'QuickReplyRegosOffsettedArrayResult']


__all__ = [
    'QuickReply',
    'QuickReplyAdd',
    'QuickReplyDelete',
    'QuickReplyGet',
    'QuickReplyRegosOffsettedArrayResult',
    'QuickReplyGetRequest',
    'QuickReplyGetResponse',
    'QuickReplyAddRequest',
    'QuickReplyAddResponse',
    'QuickReplyDeleteRequest',
    'QuickReplyDeleteResponse'
]
