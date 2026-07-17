"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class DocCashSession(RegosModel):
    "Модель, описывающая кассовые смены"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    uuid: str | None = PydField(default=None, description="UUID кассовой смены")
    code: str | None = PydField(default=None, description="Код кассовой смены")
    operating_cash_id: int | None = PydField(default=None, description="ID кассы")
    start_date: int | None = PydField(default=None, description="Дата открытия смены в формате unix time в секундах")
    start_user: User | None = PydField(default=None, description="Пользователь, открывший смену")
    start_amount: _Decimal | None = PydField(default=None, description="Сумма в кассе на открытие")
    close_date: int | None = PydField(default=None, description="Дата закрытия смены в формате unix time в секундах")
    close_user: User | None = PydField(default=None, description="Пользователь, закрывший смену")
    closed: bool | None = PydField(default=None, description="Метка о том, что смена закрыта")
    close_amount: _Decimal | None = PydField(default=None, description="Сумма в кассе на закрытие")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class DocCashSessionColumn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: DocCashSessionColumns | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class DocCashSessionColumns(str, Enum):
    Default = "Default"
    Uuid = "Uuid"
    Code = "Code"
    OperatingCashId = "OperatingCashId"
    StartDate = "StartDate"
    StartUserName = "StartUserName"
    StartAmount = "StartAmount"
    CloseDate = "CloseDate"
    CloseUserName = "CloseUserName"
    Closed = "Closed"
    CloseAmount = "CloseAmount"
    LastUpdate = "LastUpdate"


class DocCashSessionGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    uuids: list[str] | None = PydField(default=None, description="Массив UUID смен")
    operating_cash_ids: list[int] | None = PydField(default=None, description="Массив ID касс, к которым привязаны смены")
    start_date: int | None = PydField(default=None, description="Дата начала периода в формате unix time в секундах")
    end_date: int | None = PydField(default=None, description="Дата окончания периода в формате unix time в секундах")
    is_agregated: bool | None = PydField(default=None, description="Статус агрегации кассовых операций: true - Агрегированы, false - Не агрегированы, null - Возвращаются все смены (с аггрегированными и не аггрегированными операциями)")
    is_close: bool | None = PydField(default=None, description="Статус смены: true - Закрыта, false - Не закрыта, null - Возвращаются все смены (открытые и закрытые)")
    open_user_id: int | None = PydField(default=None, description="ID пользователя, открывшего смену")
    close_user_id: int | None = PydField(default=None, description="ID пользователя, закрывшего смену")
    sort_orders: list[DocCashSessionColumn] | None = PydField(default=None, description="Сортировака выходных параметров")
    limit: int | None = PydField(default=None, description="Лимит возвращаемых данных при запросе. Значение по умолчанию 10000. Максимальное значение 10000")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class DocCashSessionRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[DocCashSession] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import ColumnSortOrderDirection, Error
from schemas.api.rbac.user import User


DocCashSessionGetRequest: TypeAlias = DocCashSessionGet
DocCashSessionGetResponse: TypeAlias = DocCashSessionRegosOffsettedArrayResult


_MODEL_NAMES = ['DocCashSession', 'DocCashSessionColumn', 'DocCashSessionGet', 'DocCashSessionRegosOffsettedArrayResult']


__all__ = [
    'DocCashSession',
    'DocCashSessionColumn',
    'DocCashSessionColumns',
    'DocCashSessionGet',
    'DocCashSessionRegosOffsettedArrayResult',
    'DocCashSessionGetRequest',
    'DocCashSessionGetResponse'
]
