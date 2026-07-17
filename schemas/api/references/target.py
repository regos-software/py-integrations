"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Target(RegosModel):
    "Модель, описывающая цели"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID цели")
    name: str | None = PydField(default=None, description="Наименование цели")
    target_type: TargetType | None = PydField(default=None, description="Тип цели")
    owner: TargetOwnerEnum | None = PydField(default=None, description="Владелец цели: <Firm | 1> - Предприятие, <User | 2> - Пользователь")
    period_type: TargetPeriodTypeEnum | None = PydField(default=None, description="Тип периода: <Day | 1> - день, <Week | 2> - неделя, <Month | 3> - месяц")
    period: int | None = PydField(default=None, description="Длительность периода")
    value: _Decimal | None = PydField(default=None, description="Значение цели")
    repeateable: bool | None = PydField(default=None, description="Повторяемость цели: true - повторяемая, false - не повторяемая")
    finished: bool | None = PydField(default=None, description="Завершенность цели: true - завершенная, false - не завершенная")
    firm: Firm | None = PydField(default=None, description="Предприятие")
    stock: Stock | None = PydField(default=None, description="Склад")
    currency: Currency | None = PydField(default=None, description="Валюта цели")
    user: User | None = PydField(default=None, description="Владелец цели")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class TargetAdd(RegosModel):
    "Модель для добавления цели"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Наименование цели. Если не указано то формируется так: Наименование типа ели + ID созданной цели")
    type: TargetTypesEnum | None = PydField(default=None, description="Тип цели: <ReceiptCount | 1> - количество чеков, <UnitCount | 2> - количество единиц, <AverageReceipt |\n3> - средний чек, <SalesAmount | 4> - сумма продаж, <CrmDealWonAmount | 5> - план продаж CRM")
    owner: TargetOwnerEnum | None = PydField(default=None, description="Владелец цели: <Firm | 1> - Предприятие, <User | 2> - Пользователь")
    period_type: TargetPeriodTypeEnum | None = PydField(default=None, description="Тип периода: <Day | 1> - день, <Week | 2> - неделя, <Month | 3> - месяц")
    period: int | None = PydField(default=None, description="Значение периода")
    value: _Decimal | None = PydField(default=None, description="Значение цели")
    repeateable: bool | None = PydField(default=None, description="Повторяемость цели: true - повторяемая, false - не повторяемая")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    stock_id: int | None = PydField(default=None, description="ID Склада")
    currency_id: int | None = PydField(default=None, description="ID валюты цели. Обязателен для цели CrmDealWonAmount")
    user_id: int | None = PydField(default=None, description="ID Пользователя")


class TargetGet(RegosModel):
    "Модель для получения списка целей"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID целей")
    firm_ids: list[int] | None = PydField(default=None, description="Массив ID пердприятий")
    user_ids: list[int] | None = PydField(default=None, description="Массив ID пользователей")
    finished: bool | None = PydField(default=None, description="Завершенность цели: true - завершенная, false - не завершенная")
    owner: TargetOwnerEnum | None = PydField(default=None, description="Владелец цели: <Firm | 1> - Предприятие, <User | 2> - Пользователь")


class TargetHistory(RegosModel):
    "Описание истории цели"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    target: Target | None = PydField(default=None, description="цель")
    data: list[TargetHistoryItem] | None = PydField(default=None, description="массив истории цели")


class TargetHistoryItem(RegosModel):
    "Описание элемента истории цели"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    start_date: int | None = PydField(default=None, description="начало периода в unixtime")
    end_date: int | None = PydField(default=None, description="конец периода в unixtime")
    value: _Decimal | None = PydField(default=None, description="значение цели")
    progress: _Decimal | None = PydField(default=None, description="прогресс цели")
    percent: int | None = PydField(default=None, description="прогресс цели в процентах")


class TargetHistoryRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: TargetHistory | Error | None = PydField(default=None, description="Объект результата.")


class TargetOwnerEnum(str, Enum):
    "Перечиление типов владельцев цели"
    Default = "Default"
    Firm = "Firm"
    User = "User"


class TargetPeriodTypeEnum(str, Enum):
    "Перечисление типов периодов цели"
    Default = "Default"
    Day = "Day"
    Week = "Week"
    Month = "Month"


class TargetRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Target] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Base_ID, Error, InsertResult, UpdateResult
from schemas.api.rbac.user import User
from schemas.api.references.currency import Currency
from schemas.api.references.firm import Firm
from schemas.api.references.stock import Stock
from schemas.api.references.target_type import TargetType, TargetTypesEnum


TargetAddRequest: TypeAlias = TargetAdd
TargetAddResponse: TypeAlias = InsertResult
TargetDeleteRequest: TypeAlias = Base_ID
TargetDeleteResponse: TypeAlias = UpdateResult
TargetFinishRequest: TypeAlias = Base_ID
TargetFinishResponse: TypeAlias = UpdateResult
TargetGetHistoryRequest: TypeAlias = Base_ID
TargetGetHistoryResponse: TypeAlias = TargetHistoryRegosObjectResult
TargetGetRequest: TypeAlias = TargetGet
TargetGetResponse: TypeAlias = TargetRegosArrayResult


_MODEL_NAMES = ['Target', 'TargetAdd', 'TargetGet', 'TargetHistory', 'TargetHistoryItem', 'TargetHistoryRegosObjectResult', 'TargetRegosArrayResult']


__all__ = [
    'Target',
    'TargetAdd',
    'TargetGet',
    'TargetHistory',
    'TargetHistoryItem',
    'TargetHistoryRegosObjectResult',
    'TargetOwnerEnum',
    'TargetPeriodTypeEnum',
    'TargetRegosArrayResult',
    'TargetGetRequest',
    'TargetGetResponse',
    'TargetAddRequest',
    'TargetAddResponse',
    'TargetFinishRequest',
    'TargetFinishResponse',
    'TargetDeleteRequest',
    'TargetDeleteResponse',
    'TargetGetHistoryRequest',
    'TargetGetHistoryResponse'
]
