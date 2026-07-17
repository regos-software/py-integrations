"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ItemImage(RegosModel):
    "Модель, описывающая изображения номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="Id номенклатуры")
    id: int | None = PydField(default=None)
    width: int | None = PydField(default=None)
    height: int | None = PydField(default=None)
    size: int | None = PydField(default=None)
    file: str | None = PydField(default=None)
    url: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class ItemImageDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None)


class ItemImageGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_ids: list[int] | None = PydField(default=None, description="Массив id номенклатуры")
    ids: list[int] | None = PydField(default=None)
    include_data: bool | None = PydField(default=None)
    compress_data: bool | None = PydField(default=None)


class ItemImageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemImage] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


ItemImageDeleteRequest: TypeAlias = ItemImageDelete
ItemImageDeleteResponse: TypeAlias = UpdateResult
ItemImageGetRequest: TypeAlias = ItemImageGet
ItemImageGetResponse: TypeAlias = ItemImageRegosArrayResult
ItemImageSaveResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['ItemImage', 'ItemImageDelete', 'ItemImageGet', 'ItemImageRegosArrayResult']


__all__ = [
    'ItemImage',
    'ItemImageDelete',
    'ItemImageGet',
    'ItemImageRegosArrayResult',
    'ItemImageGetRequest',
    'ItemImageGetResponse',
    'ItemImageSaveResponse',
    'ItemImageDeleteRequest',
    'ItemImageDeleteResponse'
]
