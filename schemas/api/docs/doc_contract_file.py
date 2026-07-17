"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocContractFile(RegosModel):
    "Модель, описывающая прикреплённый файл к договору"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID прикреплённого файла")
    contract_id: int | None = PydField(default=None, description="ID договора")
    file: CommonFile | None = PydField(default=None, description="Файл")


class DocContractFileDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID прикреплённого к договору файла (Это не ID файла, а ID связи)")


class DocContractFileGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID прикреплённых файлов")
    contract_ids: list[int] | None = PydField(default=None, description="Массив ID договоров")
    file_ids: list[int] | None = PydField(default=None, description="Массив ID файлов")
    include_data: bool | None = PydField(default=None, description="Признак включения содержимого файлов в ответ")


class DocContractFileRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocContractFile] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CommonFile, Error, InsertResult, UpdateResult


DocContractFileAddResponse: TypeAlias = InsertResult
DocContractFileDeleteRequest: TypeAlias = DocContractFileDelete
DocContractFileDeleteResponse: TypeAlias = UpdateResult
DocContractFileGetRequest: TypeAlias = DocContractFileGet
DocContractFileGetResponse: TypeAlias = DocContractFileRegosArrayResult


_MODEL_NAMES = ['DocContractFile', 'DocContractFileDelete', 'DocContractFileGet', 'DocContractFileRegosArrayResult']


__all__ = [
    'DocContractFile',
    'DocContractFileDelete',
    'DocContractFileGet',
    'DocContractFileRegosArrayResult',
    'DocContractFileGetRequest',
    'DocContractFileGetResponse',
    'DocContractFileAddResponse',
    'DocContractFileDeleteRequest',
    'DocContractFileDeleteResponse'
]
