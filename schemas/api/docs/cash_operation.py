"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class CashAmountDetailsGet(RegosModel):
    "Получение деталей по кассе"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Конечная дата в формате Unix time в секундах")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")


class CashOperation(RegosModel):
    "Модель, описывающая операцию кассового журнала (запись в кассовом журнале)"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID операции кассового журнала")
    date: int | None = PydField(default=None, description="Время создания операции в формате Unix time в секундах")
    type: CashOperationType | None = PydField(default=None, description="Тип операции кассового журнала")
    payment_type_id: int | None = PydField(default=None, description="ID формы оплаты")
    payment_type_name: str | None = PydField(default=None, description="Наименоавние формы оплаты")
    session_uuid: str | None = PydField(default=None, description="UUID кассовой смены")
    document_uuid: str | None = PydField(default=None, description="UUID чека")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    value: _Decimal | None = PydField(default=None, description="Значение операции")
    description: str | None = PydField(default=None, description="Комментарий к операции")
    user_id: int | None = PydField(default=None, description="ID пользователя, который добавил операцию")
    user_full_name: str | None = PydField(default=None, description="ФИО пользователя, который добавил операцию")
    last_update: int | None = PydField(default=None, description="Время последнего изменения записи в формате Unix time в секундах")


class CashOperationGet(RegosModel):
    "Модель для получения операций кассового журанала"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="Начальная дата в формате Unix time в секундах")
    end_date: int | None = PydField(default=None, description="Конечная дата в формате Unix time в секундах")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов выборки")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class CashOperationRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[CashOperation] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class CashOperationType(RegosModel):
    "Тип кассовой операции"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="id")
    name: str | None = PydField(default=None, description="наименование")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import CashAmountDetailsRegosObjectResult, Error


CashOperationGetAmountDetailsRequest: TypeAlias = CashAmountDetailsGet
CashOperationGetAmountDetailsResponse: TypeAlias = CashAmountDetailsRegosObjectResult
CashOperationGetRequest: TypeAlias = CashOperationGet
CashOperationGetResponse: TypeAlias = CashOperationRegosOffsettedArrayResult


_MODEL_NAMES = ['CashAmountDetailsGet', 'CashOperation', 'CashOperationGet', 'CashOperationRegosOffsettedArrayResult', 'CashOperationType']


__all__ = [
    'CashAmountDetailsGet',
    'CashOperation',
    'CashOperationGet',
    'CashOperationRegosOffsettedArrayResult',
    'CashOperationType',
    'CashOperationGetRequest',
    'CashOperationGetResponse',
    'CashOperationGetAmountDetailsRequest',
    'CashOperationGetAmountDetailsResponse'
]
