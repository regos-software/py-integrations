"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ReportPrepared(RegosModel):
    "> Раздел устарел. Поддерживается до 10.04.2027"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user: User | None = PydField(default=None, description="Пользователь, для которого подготовлен отчет")
    request_uuid: str | None = PydField(default=None, description="Uuid запроса отчета")
    file_url: str | None = PydField(default=None, description="URL файла подготовленного отчёта в CDN")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    warnings: str | None = PydField(default=None, description="Информация об ошибках при выполнении отчета")
    parameters: str | None = PydField(default=None, description="Json-строка с параметрами запроса для формирования отчёта")
    report: Report | None = PydField(default=None, description="Вид отчета")
    data: str | None = PydField(default=None, description="Данные отчета - BitArray архива gzip, внутри которого файла json с данными сформированного отчета")
    saved: bool | None = PydField(default=None, description="Метка о том, что отчет не удаляется автоматически")
    date: int | None = PydField(default=None, description="Дата подготовки отчета в формате unixtime в секундах")


class ReportPreparedArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ReportPrepared] | Error | None = PydField(default=None, description="Объект результата.")


class ReportPreparedGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    report_ids: list[int] | None = PydField(default=None, description="Массив id отчётов")
    request_uuid: str | None = PydField(default=None, description="UUID запроса отчёта")
    user_ids: list[int] | None = PydField(default=None, description="Массив id пользователей, для которых подготовлен отчёт")
    include_data: bool | None = PydField(default=None, description="Метка включения бинарных данных отчёта в ответ")


class ReportPreparedRemove(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    request_uuid: str | None = PydField(default=None, description="UUID запроса на отчет")


class ReportPreparedSave(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    request_uuid: str | None = PydField(default=None)
    save: bool | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.reports.report import Report


ReportPreparedGetRequest: TypeAlias = ReportPreparedGet
ReportPreparedGetResponse: TypeAlias = ReportPreparedArrayRegosObjectResult
ReportPreparedRemoveRequest: TypeAlias = ReportPreparedRemove
ReportPreparedRemoveResponse: TypeAlias = UpdateResult
ReportPreparedSaveRequest: TypeAlias = ReportPreparedSave
ReportPreparedSaveResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['ReportPrepared', 'ReportPreparedArrayRegosObjectResult', 'ReportPreparedGet', 'ReportPreparedRemove', 'ReportPreparedSave']


__all__ = [
    'ReportPrepared',
    'ReportPreparedArrayRegosObjectResult',
    'ReportPreparedGet',
    'ReportPreparedRemove',
    'ReportPreparedSave',
    'ReportPreparedGetRequest',
    'ReportPreparedGetResponse',
    'ReportPreparedSaveRequest',
    'ReportPreparedSaveResponse',
    'ReportPreparedRemoveRequest',
    'ReportPreparedRemoveResponse'
]
