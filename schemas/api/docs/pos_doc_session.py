"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class PosDocSession(RegosModel):
    "Смена"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="идентификатор")
    code: str | None = PydField(default=None, description="код")
    operating_cash_id: int | None = PydField(default=None, description="привязка к кассе")
    start_date: int | None = PydField(default=None, description="время открытия")
    start_user: User | None = PydField(default=None, description="кассир открывщий")
    start_amount: _Decimal | None = PydField(default=None, description="начальная сумма на кассе при открытии")
    close_date: int | None = PydField(default=None, description="время закрытия")
    close_user: User | None = PydField(default=None, description="кассир закрывщий смену")
    closed: bool | None = PydField(default=None, description="флаг закрытости смены")
    close_amount: _Decimal | None = PydField(default=None, description="конечная сумма на кассе при закрытии")
    last_update: int | None = PydField(default=None, description="дата последнего изменения строки на базе")


class PosDocSessionArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[PosDocSession] | Error | None = PydField(default=None, description="Объект результата.")


class PosDocSessionClose(RegosModel):
    "модель закрытия смены"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    session_uuid: str | None = PydField(default=None, description="uuid смены")


class PosDocSessionGet(RegosModel):
    "модель получения смены"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="uuid смены")
    code: str | None = PydField(default=None, description="Код смены")
    operating_cash_ids: list[int] | None = PydField(default=None, description="Массив Id касс, к которым привязаны смены")
    start_user: int | None = PydField(default=None, description="id пользователя, открывшего смену")
    close_user: int | None = PydField(default=None, description="id пользователя, закрывшего смену")
    closed: bool | None = PydField(default=None, description="Метка о том, что смена закрыта")
    start_date1: int | None = PydField(default=None, description="Начало периода даты открытия смены в формате unixtime в секундах")
    start_date2: int | None = PydField(default=None, description="Окончание периода даты открытия смены в формате unixtime в секундах")
    close_date1: int | None = PydField(default=None, description="Начало периода даты закрытия смены в формате unixtime в секундах")
    close_date2: int | None = PydField(default=None, description="Окончание периода даты закрытия смены в формате unixtime в секундах")


class PosDocSessionRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: PosDocSession | Error | None = PydField(default=None, description="Объект результата.")


class PosDocSessionReport(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    session: PosDocSession | None = PydField(default=None, description="Смена")
    sale_counters: list[PosDocSessionSaleCounter] | None = PydField(default=None)
    sale_details: list[SessionSaleDetails] | None = PydField(default=None)
    payment_sale: list[SessionPaymentSale] | None = PydField(default=None)
    cash_total: SessionCashOprPaymentAmount | None = PydField(default=None, description="Операции по кассовому журналу")


class PosDocSessionReportRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: PosDocSessionReport | Error | None = PydField(default=None, description="Объект результата.")


class PosDocSessionSaleCounter(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    sale_counter: int | None = PydField(default=None)
    sale_status: int | None = PydField(default=None)
    is_return: bool | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, Insert_uuid_Result
from schemas.api.rbac.session import SessionCashOprPaymentAmount, SessionPaymentSale, SessionSaleDetails
from schemas.api.rbac.user import User


PosDocSessionCloseRequest: TypeAlias = PosDocSessionClose
PosDocSessionCloseResponse: TypeAlias = Insert_uuid_Result
PosDocSessionGetCurrentResponse: TypeAlias = PosDocSessionRegosObjectResult
PosDocSessionGetRequest: TypeAlias = PosDocSessionGet
PosDocSessionGetResponse: TypeAlias = PosDocSessionArrayRegosObjectResult
PosDocSessionOpenResponse: TypeAlias = Insert_uuid_Result
PosDocSessionXReportResponse: TypeAlias = PosDocSessionReportRegosObjectResult


_MODEL_NAMES = ['PosDocSession', 'PosDocSessionArrayRegosObjectResult', 'PosDocSessionClose', 'PosDocSessionGet', 'PosDocSessionRegosObjectResult', 'PosDocSessionReport', 'PosDocSessionReportRegosObjectResult', 'PosDocSessionSaleCounter']


__all__ = [
    'PosDocSession',
    'PosDocSessionArrayRegosObjectResult',
    'PosDocSessionClose',
    'PosDocSessionGet',
    'PosDocSessionRegosObjectResult',
    'PosDocSessionReport',
    'PosDocSessionReportRegosObjectResult',
    'PosDocSessionSaleCounter',
    'PosDocSessionGetRequest',
    'PosDocSessionGetResponse',
    'PosDocSessionGetCurrentResponse',
    'PosDocSessionOpenResponse',
    'PosDocSessionCloseRequest',
    'PosDocSessionCloseResponse',
    'PosDocSessionXReportResponse'
]
