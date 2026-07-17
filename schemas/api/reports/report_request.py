"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ReportRequest(RegosModel):
    "> Раздел устарел. Поддерживается до 03.04.2027. Рекомендуется использовать Report/AddRequest"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="Uuid запроса отчета")
    date: int | None = PydField(default=None, description="Дата запроса на отчет в формате unix time в секундах")
    status: int | None = PydField(default=None, description="статус отчета: 0 - в процессе, 1 - готов, 2 - ошибка")
    report: Report | None = PydField(default=None, description="Отчет")
    user_id: int | None = PydField(default=None, description="Id пользователя который отправил запрос на подготовку отчета")
    description: str | None = PydField(default=None, description="Дополнительное описание")
    warnings: str | None = PydField(default=None, description="Информация об ошибках при выполнении запроса")


class ReportRequestArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ReportRequest] | Error | None = PydField(default=None, description="Объект результата.")


class ReportRequestGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_ids: list[int] | None = PydField(default=None, description="Массив id пользователей, которые отправили запросы")
    statuses: list[int] | None = PydField(default=None, description="Массив статусов запросов")
    request_uuid: str | None = PydField(default=None, description="UUID конкретной заявки на отчёт")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, SingleObjectResult
from schemas.api.reports.report import Report, Report0003Request, Report0005Request, Report0006Request, Report0007Request, Report0009Request, Report0011_Request_Model, Report0016Request, Report0017Request, Report0018Request, Report0020Request, Report0021Request, Report0022Request, Report0023Request, Report0024Request, Report0025_Request, Report0026_Request


ReportRequestGetRequest: TypeAlias = ReportRequestGet
ReportRequestGetResponse: TypeAlias = ReportRequestArrayRegosObjectResult
ReportRequestReport0003Request: TypeAlias = Report0003Request
ReportRequestReport0003Response: TypeAlias = SingleObjectResult
ReportRequestReport0005Request: TypeAlias = Report0005Request
ReportRequestReport0005Response: TypeAlias = SingleObjectResult
ReportRequestReport0006Request: TypeAlias = Report0006Request
ReportRequestReport0006Response: TypeAlias = SingleObjectResult
ReportRequestReport0007Request: TypeAlias = Report0007Request
ReportRequestReport0007Response: TypeAlias = SingleObjectResult
ReportRequestReport0009Request: TypeAlias = Report0009Request
ReportRequestReport0009Response: TypeAlias = SingleObjectResult
ReportRequestReport0011Request: TypeAlias = Report0011_Request_Model
ReportRequestReport0011Response: TypeAlias = SingleObjectResult
ReportRequestReport0016Request: TypeAlias = Report0016Request
ReportRequestReport0016Response: TypeAlias = SingleObjectResult
ReportRequestReport0017Request: TypeAlias = Report0017Request
ReportRequestReport0017Response: TypeAlias = SingleObjectResult
ReportRequestReport0018Request: TypeAlias = Report0018Request
ReportRequestReport0018Response: TypeAlias = SingleObjectResult
ReportRequestReport0020Request: TypeAlias = Report0020Request
ReportRequestReport0020Response: TypeAlias = SingleObjectResult
ReportRequestReport0021Request: TypeAlias = Report0021Request
ReportRequestReport0021Response: TypeAlias = SingleObjectResult
ReportRequestReport0022Request: TypeAlias = Report0022Request
ReportRequestReport0022Response: TypeAlias = SingleObjectResult
ReportRequestReport0023Request: TypeAlias = Report0023Request
ReportRequestReport0023Response: TypeAlias = SingleObjectResult
ReportRequestReport0024Request: TypeAlias = Report0024Request
ReportRequestReport0024Response: TypeAlias = SingleObjectResult
ReportRequestReport0025Request: TypeAlias = Report0025_Request
ReportRequestReport0025Response: TypeAlias = SingleObjectResult
ReportRequestReport0026Request: TypeAlias = Report0026_Request
ReportRequestReport0026Response: TypeAlias = SingleObjectResult


_MODEL_NAMES = ['ReportRequest', 'ReportRequestArrayRegosObjectResult', 'ReportRequestGet']


__all__ = [
    'ReportRequest',
    'ReportRequestArrayRegosObjectResult',
    'ReportRequestGet',
    'ReportRequestGetRequest',
    'ReportRequestGetResponse',
    'ReportRequestReport0003Request',
    'ReportRequestReport0003Response',
    'ReportRequestReport0005Request',
    'ReportRequestReport0005Response',
    'ReportRequestReport0006Request',
    'ReportRequestReport0006Response',
    'ReportRequestReport0007Request',
    'ReportRequestReport0007Response',
    'ReportRequestReport0009Request',
    'ReportRequestReport0009Response',
    'ReportRequestReport0011Request',
    'ReportRequestReport0011Response',
    'ReportRequestReport0016Request',
    'ReportRequestReport0016Response',
    'ReportRequestReport0017Request',
    'ReportRequestReport0017Response',
    'ReportRequestReport0018Request',
    'ReportRequestReport0018Response',
    'ReportRequestReport0020Request',
    'ReportRequestReport0020Response',
    'ReportRequestReport0021Request',
    'ReportRequestReport0021Response',
    'ReportRequestReport0022Request',
    'ReportRequestReport0022Response',
    'ReportRequestReport0023Request',
    'ReportRequestReport0023Response',
    'ReportRequestReport0024Request',
    'ReportRequestReport0024Response',
    'ReportRequestReport0025Request',
    'ReportRequestReport0025Response',
    'ReportRequestReport0026Request',
    'ReportRequestReport0026Response'
]
