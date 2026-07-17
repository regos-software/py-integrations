"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocEnumerator(RegosModel):
    "Модель, описывающая нумератор документов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id нумератора документов")
    table_name: str | None = PydField(default=None, description="Наименование типа документа")
    mask: str | None = PydField(default=None, description="Маска")
    counter: int | None = PydField(default=None, description="Начало отсчёта")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocEnumeratorEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id нумератора документов")
    mask: str | None = PydField(default=None, description="Маска нумератора документов")


class DocEnumeratorGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id нумераторов документов")
    table_ids: list[int] | None = PydField(default=None, description="Массив id документов")


class DocEnumeratorRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocEnumerator] | Error | None = PydField(default=None, description="Массив результата.")


class DocEnumeratorReset(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id нумератора документов")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult


DocumentEnumeratorEditRequest: TypeAlias = DocEnumeratorEdit
DocumentEnumeratorEditResponse: TypeAlias = UpdateResult
DocumentEnumeratorGetRequest: TypeAlias = DocEnumeratorGet
DocumentEnumeratorGetResponse: TypeAlias = DocEnumeratorRegosArrayResult
DocumentEnumeratorResetRequest: TypeAlias = DocEnumeratorReset
DocumentEnumeratorResetResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['DocEnumerator', 'DocEnumeratorEdit', 'DocEnumeratorGet', 'DocEnumeratorRegosArrayResult', 'DocEnumeratorReset']


__all__ = [
    'DocEnumerator',
    'DocEnumeratorEdit',
    'DocEnumeratorGet',
    'DocEnumeratorRegosArrayResult',
    'DocEnumeratorReset',
    'DocumentEnumeratorGetRequest',
    'DocumentEnumeratorGetResponse',
    'DocumentEnumeratorEditRequest',
    'DocumentEnumeratorEditResponse',
    'DocumentEnumeratorResetRequest',
    'DocumentEnumeratorResetResponse'
]
