"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CustomerPersonalDocument(RegosModel):
    "Модель, описывающая персональные документы покупателей"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID персонального документа покупателя")
    personal_doc_type: PersonalDocType | None = PydField(default=None, description="Тип персонального документа")
    file: CommonFile | None = PydField(default=None, description="Файл")
    value: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time")


class CustomerPersonalDocumentDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="Id покупателя")
    personal_doc_type_id: int | None = PydField(default=None, description="Id типа персонального документа")


class CustomerPersonalDocumentGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="ID покупателя")
    personal_doc_type_id: int | None = PydField(default=None, description="ID типа документа")
    include_data: bool | None = PydField(default=None, description="Включать бинарные данные файла в ответ")


class CustomerPersonalDocumentRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CustomerPersonalDocument] | Error | None = PydField(default=None, description="Массив результата.")


class CustomerPersonalDocumentRemoveFile(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    customer_id: int | None = PydField(default=None, description="Id покупателя")
    personal_doc_type_id: int | None = PydField(default=None, description="Id типа персонального документа")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CommonFile, Error, InsertResult, UpdateResult
from schemas.api.references.personal_doc_type import PersonalDocType


CustomerPersonalDocumentAddResponse: TypeAlias = InsertResult
CustomerPersonalDocumentDeleteRequest: TypeAlias = CustomerPersonalDocumentDelete
CustomerPersonalDocumentDeleteResponse: TypeAlias = UpdateResult
CustomerPersonalDocumentEditResponse: TypeAlias = UpdateResult
CustomerPersonalDocumentGetRequest: TypeAlias = CustomerPersonalDocumentGet
CustomerPersonalDocumentGetResponse: TypeAlias = CustomerPersonalDocumentRegosArrayResult
CustomerPersonalDocumentRemoveFileRequest: TypeAlias = CustomerPersonalDocumentRemoveFile
CustomerPersonalDocumentRemoveFileResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['CustomerPersonalDocument', 'CustomerPersonalDocumentDelete', 'CustomerPersonalDocumentGet', 'CustomerPersonalDocumentRegosArrayResult', 'CustomerPersonalDocumentRemoveFile']


__all__ = [
    'CustomerPersonalDocument',
    'CustomerPersonalDocumentDelete',
    'CustomerPersonalDocumentGet',
    'CustomerPersonalDocumentRegosArrayResult',
    'CustomerPersonalDocumentRemoveFile',
    'CustomerPersonalDocumentGetRequest',
    'CustomerPersonalDocumentGetResponse',
    'CustomerPersonalDocumentAddResponse',
    'CustomerPersonalDocumentEditResponse',
    'CustomerPersonalDocumentRemoveFileRequest',
    'CustomerPersonalDocumentRemoveFileResponse',
    'CustomerPersonalDocumentDeleteRequest',
    'CustomerPersonalDocumentDeleteResponse'
]
