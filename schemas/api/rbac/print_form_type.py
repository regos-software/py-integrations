"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PrintFormType(RegosModel):
    "Модель, описывающая связи форм на печать с типами документов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id связи типа документа и формы на печать")
    type: DocumentType | None = PydField(default=None, description="Тип документа")
    printform: DocPrintForm | None = PydField(default=None, description="Форма на печать")
    version: int | None = PydField(default=None, description="Версия связанной печатной формы (1 или 2)")


class PrintFormTypeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id связей типа документа и формы печати")
    type_ids: list[int] | None = PydField(default=None, description="Массив id типов документов")
    printform_ids: list[int] | None = PydField(default=None, description="Массив id форм на печать документов")
    version: int | None = PydField(default=None, description="Версия связанной печатной формы (1 или 2). По умолчанию 1")


class PrintFormTypeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PrintFormType] | Error | None = PydField(default=None, description="Массив результата.")


class PrintFormTypeRemove(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id связи между формой на печать и типом документа")


class PrintFormTypeSet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type_id: int | None = PydField(default=None, description="ID типа документа")
    printform_id: int | None = PydField(default=None, description="ID формы на печать")
    version: int | None = PydField(default=None, description="Версия формы (1 или 2). По умолчанию 1")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.docs.document_type import DocumentType
from schemas.api.rbac.doc_print_form import DocPrintForm


PrintFormTypeGetRequest: TypeAlias = PrintFormTypeGet
PrintFormTypeGetResponse: TypeAlias = PrintFormTypeRegosArrayResult
PrintFormTypeRemoveRequest: TypeAlias = PrintFormTypeRemove
PrintFormTypeRemoveResponse: TypeAlias = UpdateResult
PrintFormTypeSetRequest: TypeAlias = PrintFormTypeSet
PrintFormTypeSetResponse: TypeAlias = InsertResult


_MODEL_NAMES = ['PrintFormType', 'PrintFormTypeGet', 'PrintFormTypeRegosArrayResult', 'PrintFormTypeRemove', 'PrintFormTypeSet']


__all__ = [
    'PrintFormType',
    'PrintFormTypeGet',
    'PrintFormTypeRegosArrayResult',
    'PrintFormTypeRemove',
    'PrintFormTypeSet',
    'PrintFormTypeGetRequest',
    'PrintFormTypeGetResponse',
    'PrintFormTypeSetRequest',
    'PrintFormTypeSetResponse',
    'PrintFormTypeRemoveRequest',
    'PrintFormTypeRemoveResponse'
]
