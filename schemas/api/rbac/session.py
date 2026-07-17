"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Session(RegosModel):
    "Модель, описывающая существующие активные сессии в системе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: str | None = PydField(default=None, description="Id сессии")
    user: User | None = PydField(default=None, description="Пользователь")
    ip: str | None = PydField(default=None, description="IP адрес устройства")
    device_name: str | None = PydField(default=None, description="Наименование устройства")
    start_time: int | None = PydField(default=None, description="Дата и время начала сессии")
    duration: str | None = PydField(default=None, description="Длительность сессии: _ДД.ЧЧ:ММ:СС_")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class SessionCashOprPaymentAmount(RegosModel):
    "Операции по кассовому журналу"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    opr_sale: _Decimal | None = PydField(default=None, description="продажи")
    opr_return: _Decimal | None = PydField(default=None, description="возвраты")
    opr_cash_in: _Decimal | None = PydField(default=None, description="внесение в кассу")
    opr_cash_out: _Decimal | None = PydField(default=None, description="изъятие из кассы")
    opr_change_out: _Decimal | None = PydField(default=None, description="выдача сдачи")
    opr_change_in: _Decimal | None = PydField(default=None, description="приём сдачи")
    opr_payment_out: _Decimal | None = PydField(default=None, description="платёж из кассы")


class SessionGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[str] | None = PydField(default=None)


class SessionPaymentSale(RegosModel):
    "Платежи"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    amount: _Decimal | None = PydField(default=None, description="сумма")
    payment_type: PaymentType | None = PydField(default=None, description="тип платежа")
    is_return: bool | None = PydField(default=None, description="метка возврата")


class SessionRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Session] | Error | None = PydField(default=None, description="Массив результата.")


class SessionSaleDetails(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    position_counter: int | None = PydField(default=None)
    units_counter: _Decimal | None = PydField(default=None)
    is_return: bool | None = PydField(default=None)


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.rbac.user import User
from schemas.api.references.payment_type import PaymentType


SessionGetRequest: TypeAlias = SessionGet
SessionGetResponse: TypeAlias = SessionRegosArrayResult


_MODEL_NAMES = ['Session', 'SessionCashOprPaymentAmount', 'SessionGet', 'SessionPaymentSale', 'SessionRegosArrayResult', 'SessionSaleDetails']


__all__ = [
    'Session',
    'SessionCashOprPaymentAmount',
    'SessionGet',
    'SessionPaymentSale',
    'SessionRegosArrayResult',
    'SessionSaleDetails',
    'SessionGetRequest',
    'SessionGetResponse'
]
