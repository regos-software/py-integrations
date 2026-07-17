"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PersonalDocType(RegosModel):
    "Модель, описывающая тип персонального документа"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id персонального документа")
    name: str | None = PydField(default=None, description="Наименование персонального документа")
    mask: str | None = PydField(default=None, description="Маска персонального документа")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class PersonalDocTypeAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование типа персонального документа")
    mask: str | None = PydField(default=None, description="Маска типа персонального документа")


class PersonalDocTypeArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PersonalDocType] | Error | None = PydField(default=None, description="Объект результата.")


class PersonalDocTypeDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id типа персонального документа")


class PersonalDocTypeEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID типа персональног документа")
    name: str | None = PydField(default=None, description="Наименование типа персональног документа")
    mask: str | None = PydField(default=None, description="Маска типа персонального документа")


class PersonalDocTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id типов персональных документов")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


PersonalDocTypeAddRequest: TypeAlias = PersonalDocTypeAdd
PersonalDocTypeAddResponse: TypeAlias = InsertResult
PersonalDocTypeDeleteRequest: TypeAlias = PersonalDocTypeDelete
PersonalDocTypeDeleteResponse: TypeAlias = UpdateResult
PersonalDocTypeEditRequest: TypeAlias = PersonalDocTypeEdit
PersonalDocTypeEditResponse: TypeAlias = UpdateResult
PersonalDocTypeGetRequest: TypeAlias = PersonalDocTypeGet
PersonalDocTypeGetResponse: TypeAlias = PersonalDocTypeArrayRegosObjectResult


_MODEL_NAMES = ['PersonalDocType', 'PersonalDocTypeAdd', 'PersonalDocTypeArrayRegosObjectResult', 'PersonalDocTypeDelete', 'PersonalDocTypeEdit', 'PersonalDocTypeGet']


__all__ = [
    'PersonalDocType',
    'PersonalDocTypeAdd',
    'PersonalDocTypeArrayRegosObjectResult',
    'PersonalDocTypeDelete',
    'PersonalDocTypeEdit',
    'PersonalDocTypeGet',
    'PersonalDocTypeGetRequest',
    'PersonalDocTypeGetResponse',
    'PersonalDocTypeAddRequest',
    'PersonalDocTypeAddResponse',
    'PersonalDocTypeEditRequest',
    'PersonalDocTypeEditResponse',
    'PersonalDocTypeDeleteRequest',
    'PersonalDocTypeDeleteResponse'
]
