"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Region(RegosModel):
    "Модель, описывающая регионы"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID региона")
    parent_id: int | None = PydField(default=None, description="ID родительского региона")
    name: str | None = PydField(default=None, description="Наименование региона")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class RegionAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parent_id: int | None = PydField(default=None, description="ID родительского региона. По умолчанию: 0")
    name: str | None = PydField(default=None, description="Наименование Региона")


class RegionDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID региона")


class RegionEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID региона")
    parent_id: int | None = PydField(default=None, description="ID родительского региона")
    name: str | None = PydField(default=None, description="Наименование региона")


class RegionGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID регионов")
    parent_ids: list[int] | None = PydField(default=None, description="Массив ID родительских регионов (в которые вложены запрашиваемые регионы)")


class RegionRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Region] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


RegionAddRequest: TypeAlias = RegionAdd
RegionAddResponse: TypeAlias = InsertResult
RegionDeleteRequest: TypeAlias = RegionDelete
RegionDeleteResponse: TypeAlias = UpdateResult
RegionEditRequest: TypeAlias = RegionEdit
RegionEditResponse: TypeAlias = UpdateResult
RegionGetRequest: TypeAlias = RegionGet
RegionGetResponse: TypeAlias = RegionRegosArrayResult


_MODEL_NAMES = ['Region', 'RegionAdd', 'RegionDelete', 'RegionEdit', 'RegionGet', 'RegionRegosArrayResult']


__all__ = [
    'Region',
    'RegionAdd',
    'RegionDelete',
    'RegionEdit',
    'RegionGet',
    'RegionRegosArrayResult',
    'RegionGetRequest',
    'RegionGetResponse',
    'RegionAddRequest',
    'RegionAddResponse',
    'RegionEditRequest',
    'RegionEditResponse',
    'RegionDeleteRequest',
    'RegionDeleteResponse'
]
