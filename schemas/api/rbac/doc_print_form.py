"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocPrintForm(RegosModel):
    "Модель, описывающая формы на печать документов"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id формы печати")
    name: str | None = PydField(default=None, description="Наименование формы печати. Не более 150 символов")
    data: str | None = PydField(default=None, description="Данные формы: для version=1 — base64 шаблона, для version=2 — URL файла")
    version: int | None = PydField(default=None, description="Версия хранения данных формы: 1 — старым способом (в будущем будет убрано), 2 — через CDN")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocPrintFormDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id формы печати")


class DocPrintFormGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="массив id форм печати")
    include_data: bool | None = PydField(default=None, description="Метка о включении в ответ данных формы печати: false - не включать, true - включать. По умолчанию false")
    version: int | None = PydField(default=None, description="Версия режима ответа (1 или 2). По умолчанию 1. При version=2 для форм с version=2 поле data возвращается как URL файла и include_data игнорируется")


class DocPrintFormPrepare(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    print_form_type_id: int | None = PydField(default=None, description="Id связи печатной формы с типом документа")
    data: Any = PydField(default=None, description="Объект с данными для подготовки печатной формы. Состав объекта зависит от типа документа, указанного в print_form_type_id")
    version: int | None = PydField(default=None, description="Версия формата ответа: 1 или 2. По умолчанию 1")


class DocPrintFormPreparedFile(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    file_name: str | None = PydField(default=None)
    data: str | None = PydField(default=None)
    version: int | None = PydField(default=None)


class DocPrintFormPreparedFileRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: DocPrintFormPreparedFile | Error | None = PydField(default=None, description="Объект результата.")


class DocPrintFormRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocPrintForm] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


DocPrintFormAddResponse: TypeAlias = InsertResult
DocPrintFormDeleteRequest: TypeAlias = DocPrintFormDelete
DocPrintFormDeleteResponse: TypeAlias = UpdateResult
DocPrintFormEditResponse: TypeAlias = UpdateResult
DocPrintFormGetRequest: TypeAlias = DocPrintFormGet
DocPrintFormGetResponse: TypeAlias = DocPrintFormRegosArrayResult
DocPrintFormPrepareRequest: TypeAlias = DocPrintFormPrepare
DocPrintFormPrepareResponse: TypeAlias = DocPrintFormPreparedFileRegosObjectResult


_MODEL_NAMES = ['DocPrintForm', 'DocPrintFormDelete', 'DocPrintFormGet', 'DocPrintFormPrepare', 'DocPrintFormPreparedFile', 'DocPrintFormPreparedFileRegosObjectResult', 'DocPrintFormRegosArrayResult']


__all__ = [
    'DocPrintForm',
    'DocPrintFormDelete',
    'DocPrintFormGet',
    'DocPrintFormPrepare',
    'DocPrintFormPreparedFile',
    'DocPrintFormPreparedFileRegosObjectResult',
    'DocPrintFormRegosArrayResult',
    'DocPrintFormGetRequest',
    'DocPrintFormGetResponse',
    'DocPrintFormPrepareRequest',
    'DocPrintFormPrepareResponse',
    'DocPrintFormAddResponse',
    'DocPrintFormEditResponse',
    'DocPrintFormDeleteRequest',
    'DocPrintFormDeleteResponse'
]
