"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DealType(RegosModel):
    "Модели DealType"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID типа сделки")
    name: str | None = PydField(default=None, description="Название типа сделки")
    description: str | None = PydField(default=None, description="Описание типа сделки")
    active: bool | None = PydField(default=None, description="Признак активности")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class DealTypeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название типа сделки, максимум 200 символов")
    description: str | None = PydField(default=None, description="Описание типа сделки")
    active: bool | None = PydField(default=None, description="Признак активности")


class DealTypeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID типа сделки")


class DealTypeEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID типа сделки")
    name: str | None = PydField(default=None, description="Новое название, максимум 200 символов")
    description: str | None = PydField(default=None, description="Новое описание (\"\" -> NULL)")
    active: bool | None = PydField(default=None, description="Признак активности")


class DealTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID типов сделок")
    search: str | None = PydField(default=None, description="Поиск по названию типа сделки")
    active: bool | None = PydField(default=None, description="Фильтр по признаку активности")
    limit: int | None = PydField(default=None, description="Лимит выборки, при <= 0 используется системный максимум")
    offset: int | None = PydField(default=None, description="Смещение выборки, при < 0 используется 0")


class DealTypeRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DealType] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


DealTypeAddRequest: TypeAlias = DealTypeAdd
DealTypeAddResponse: TypeAlias = InsertResult
DealTypeDeleteRequest: TypeAlias = DealTypeDelete
DealTypeDeleteResponse: TypeAlias = UpdateResult
DealTypeEditRequest: TypeAlias = DealTypeEdit
DealTypeEditResponse: TypeAlias = UpdateResult
DealTypeGetRequest: TypeAlias = DealTypeGet
DealTypeGetResponse: TypeAlias = DealTypeRegosOffsettedArrayResult


_MODEL_NAMES = ['DealType', 'DealTypeAdd', 'DealTypeDelete', 'DealTypeEdit', 'DealTypeGet', 'DealTypeRegosOffsettedArrayResult']


__all__ = [
    'DealType',
    'DealTypeAdd',
    'DealTypeDelete',
    'DealTypeEdit',
    'DealTypeGet',
    'DealTypeRegosOffsettedArrayResult',
    'DealTypeGetRequest',
    'DealTypeGetResponse',
    'DealTypeAddRequest',
    'DealTypeAddResponse',
    'DealTypeEditRequest',
    'DealTypeEditResponse',
    'DealTypeDeleteRequest',
    'DealTypeDeleteResponse'
]
