"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocumentStatus(RegosModel):
    "Модель, описывающая статусы документов в системе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id статуса")
    document_type_id: int | None = PydField(default=None, description="Id типа документа, к которому относится статус")
    name: str | None = PydField(default=None, description="Наименование статуса")
    name_var: str | None = PydField(default=None, description="Ключ перевода наименования статуса")
    order: int | None = PydField(default=None, description="Порядок статуса")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocumentStatusGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    document_type_id: int | None = PydField(default=None, description="Id типа документа, к которому относится статус")
    ids: list[int] | None = PydField(default=None, description="Массив id статусов")


class DocumentStatusRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocumentStatus] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


DocumentStatusGetRequest: TypeAlias = DocumentStatusGet
DocumentStatusGetResponse: TypeAlias = DocumentStatusRegosArrayResult


_MODEL_NAMES = ['DocumentStatus', 'DocumentStatusGet', 'DocumentStatusRegosArrayResult']


__all__ = [
    'DocumentStatus',
    'DocumentStatusGet',
    'DocumentStatusRegosArrayResult',
    'DocumentStatusGetRequest',
    'DocumentStatusGetResponse'
]
