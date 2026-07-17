"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Storage(RegosModel):
    "##### Модель хранилища"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    capacity: int | None = PydField(default=None, description="Общий объем хранилища в байтах")
    used: int | None = PydField(default=None, description="Занятое место в байтах")
    free: int | None = PydField(default=None, description="Свободное место в байтах")
    entities: list[StorageEntity] | None = PydField(default=None, description="Занятое место в разрезе сущностей")


class StorageCleanup(RegosModel):
    "Модель запуска очистки хранилища."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Необязательный. Начальная дата в unix time (включительно)")
    end_date: int | None = PydField(default=None, description="Необязательный. Конечная дата в unix time (включительно)")
    entities: list[StorageEntityEnum] | None = PydField(default=None, description="Необязательный. Сущности для очистки: chat, report, item, payment_type, contract, retail_customer_document, other")


class StorageEntity(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    entity: StorageEntityEnum | None = PydField(default=None, description="Сущность: chat, report, item, payment_type, contract, retail_customer_document, other.")
    used: int | None = PydField(default=None, description="Занятое место по сущности (байт).")


class StorageEntityEnum(str, Enum):
    "Занятое место по конкретной сущности."
    chat = "chat"
    report = "report"
    item = "item"
    payment_type = "payment_type"
    contract = "contract"
    print_form = "print_form"
    retail_customer_document = "retail_customer_document"
    other = "other"


class StorageGet(RegosModel):
    "Модель запроса данных по хранилищу."
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    pass


class StorageRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: Storage | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BooleanRegosObjectResult, Error


StorageCleanupRequest: TypeAlias = StorageCleanup
StorageCleanupResponse: TypeAlias = BooleanRegosObjectResult
StorageGetRequest: TypeAlias = StorageGet
StorageGetResponse: TypeAlias = StorageRegosObjectResult


_MODEL_NAMES = ['Storage', 'StorageCleanup', 'StorageEntity', 'StorageGet', 'StorageRegosObjectResult']


__all__ = [
    'Storage',
    'StorageCleanup',
    'StorageEntity',
    'StorageEntityEnum',
    'StorageGet',
    'StorageRegosObjectResult',
    'StorageGetRequest',
    'StorageGetResponse',
    'StorageCleanupRequest',
    'StorageCleanupResponse'
]
