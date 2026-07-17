"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CashServer(RegosModel):
    "Модель, описывающая сервера касс"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id сервера касс")
    name: str | None = PydField(default=None, description="Наименование сервера касс")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    last_sync: int | None = PydField(default=None, description="Дата последней синхронизации в формате unixtime в секундах")
    sync_status: CashServers_SyncStatus | None = PydField(default=None, description="Статус синхронизации: <Waiting | 1> (Ожидает\"), <Started | 2> (Начата\"), <Finished | 3> (Закончина\"), <Error | 4> (Ошибка)")
    active: bool | None = PydField(default=None, description="Метка об активности сервера касс")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unixtime в секундах")


class CashServerAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование сервера касс")
    firm_id: int | None = PydField(default=None, description="Id фирмы, к которой относится сервер касс")
    active: bool | None = PydField(default=None, description="Метка об активности сервера касс")


class CashServerArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CashServer] | Error | None = PydField(default=None, description="Объект результата.")


class CashServerEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="id сервера касс")
    name: str | None = PydField(default=None, description="Наименование сервера касс")
    active: bool | None = PydField(default=None, description="Метка об активности сервера касс")


class CashServerGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id серверов касс")
    firm_ids: list[int] | None = PydField(default=None, description="Массив id фирм")
    search: str | None = PydField(default=None, description="строка поиска по: name (наименование)")


class CashServerOnlyId(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id сервера касс")


class CashServers_SyncStatus(str, Enum):
    Default = "Default"
    Waiting = "Waiting"
    Started = "Started"
    Finished = "Finished"
    Error = "Error"


class EndSyncDatetime(RegosModel):
    "модель для возрата даты начала и окончания синхронизации"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    end_date: int | None = PydField(default=None, description="дата и время завершения синхронизации")
    row_affected: int | None = PydField(default=None)
    start_date: int | None = PydField(default=None, description="дата и время начала синхронизации")


class EndSyncDatetimeRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: EndSyncDatetime | Error | None = PydField(default=None, description="Объект результата.")


class StartSyncDatetime(RegosModel):
    "модель для возврата даты начала синхронизации"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    row_affected: int | None = PydField(default=None)
    start_date: int | None = PydField(default=None, description="дата и время начала синхронизации")


class StartSyncDatetimeRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: StartSyncDatetime | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult
from schemas.api.references.firm import Firm


CashServerAddRequest: TypeAlias = CashServerAdd
CashServerAddResponse: TypeAlias = InsertResult
CashServerBeginSyncRequest: TypeAlias = CashServerOnlyId
CashServerBeginSyncResponse: TypeAlias = StartSyncDatetimeRegosObjectResult
CashServerDeleteRequest: TypeAlias = CashServerOnlyId
CashServerDeleteResponse: TypeAlias = UpdateResult
CashServerEditRequest: TypeAlias = CashServerEdit
CashServerEditResponse: TypeAlias = UpdateResult
CashServerEndSyncRequest: TypeAlias = CashServerOnlyId
CashServerEndSyncResponse: TypeAlias = EndSyncDatetimeRegosObjectResult
CashServerGetRequest: TypeAlias = CashServerGet
CashServerGetResponse: TypeAlias = CashServerArrayRegosObjectResult


_MODEL_NAMES = ['CashServer', 'CashServerAdd', 'CashServerArrayRegosObjectResult', 'CashServerEdit', 'CashServerGet', 'CashServerOnlyId', 'EndSyncDatetime', 'EndSyncDatetimeRegosObjectResult', 'StartSyncDatetime', 'StartSyncDatetimeRegosObjectResult']


__all__ = [
    'CashServer',
    'CashServerAdd',
    'CashServerArrayRegosObjectResult',
    'CashServerEdit',
    'CashServerGet',
    'CashServerOnlyId',
    'CashServers_SyncStatus',
    'EndSyncDatetime',
    'EndSyncDatetimeRegosObjectResult',
    'StartSyncDatetime',
    'StartSyncDatetimeRegosObjectResult',
    'CashServerGetRequest',
    'CashServerGetResponse',
    'CashServerAddRequest',
    'CashServerAddResponse',
    'CashServerEditRequest',
    'CashServerEditResponse',
    'CashServerDeleteRequest',
    'CashServerDeleteResponse',
    'CashServerBeginSyncRequest',
    'CashServerBeginSyncResponse',
    'CashServerEndSyncRequest',
    'CashServerEndSyncResponse'
]
