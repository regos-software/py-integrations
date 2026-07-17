"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocumentType(RegosModel):
    "Модель, описывающая типы документов в системе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id типа документа")
    name: str | None = PydField(default=None, description="Наименование типа документа")
    name_var: str | None = PydField(default=None, description="Ключ перевода наименования типа документа")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocumentTypeArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocumentType] | Error | None = PydField(default=None, description="Объект результата.")


class DocumentTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id типов документов")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


DocumentTypeGetRequest: TypeAlias = DocumentTypeGet
DocumentTypeGetResponse: TypeAlias = DocumentTypeArrayRegosObjectResult


_MODEL_NAMES = ['DocumentType', 'DocumentTypeArrayRegosObjectResult', 'DocumentTypeGet']


__all__ = [
    'DocumentType',
    'DocumentTypeArrayRegosObjectResult',
    'DocumentTypeGet',
    'DocumentTypeGetRequest',
    'DocumentTypeGetResponse'
]
