"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Channel(RegosModel):
    "Модели Channel"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID канала")
    name: str | None = PydField(default=None, description="Название канала")
    queue_mode: QueueModeEnum | None = PydField(default=None, description="Режим очереди обработки обращений")
    routing_strategy: RoutingStrategyEnum | None = PydField(default=None, description="Стратегия распределения обращений")
    first_response_sec: int | None = PydField(default=None, description="SLA первого ответа (сек.)")
    next_response_sec: int | None = PydField(default=None, description="SLA следующего ответа (сек.)")
    resolve_sec: int | None = PydField(default=None, description="SLA полного решения (сек.)")
    pause_on_waiting_client: bool | None = PydField(default=None, description="Пауза SLA в статусе ожидания клиента")
    start_message: str | None = PydField(default=None, description="Приветственное сообщение канала")
    end_message: str | None = PydField(default=None, description="Сообщение завершения диалога")
    off_hours_message: str | None = PydField(default=None, description="Сообщение вне рабочего времени")
    rating_enabled: bool | None = PydField(default=None, description="Признак включенной оценки диалога")
    rating_message: str | None = PydField(default=None, description="Текст запроса оценки")
    rating_positive_message: str | None = PydField(default=None, description="Текст при положительной оценке")
    rating_negative_message: str | None = PydField(default=None, description="Текст при отрицательной оценке")
    active: bool | None = PydField(default=None, description="Признак активности канала")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего канал")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")
    operators: list[ChannelOperator] | None = PydField(default=None, description="Список операторов канала")
    intervals: list[ChannelScheduleInterval] | None = PydField(default=None, description="Рабочие интервалы канала; пустой список означает режим 24/7")


class ChannelAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название канала")
    queue_mode: QueueModeEnum | None = PydField(default=None, description="Режим очереди: Pool, Direct")
    routing_strategy: RoutingStrategyEnum | None = PydField(default=None, description="Стратегия маршрутизации: RoundRobin, LeastLoaded, Manual")
    first_response_sec: int | None = PydField(default=None, description="SLA первого ответа (сек.)")
    next_response_sec: int | None = PydField(default=None, description="SLA следующего ответа (сек.)")
    resolve_sec: int | None = PydField(default=None, description="SLA решения (сек.)")
    pause_on_waiting_client: bool | None = PydField(default=None, description="Пауза SLA в статусе ожидания клиента")
    start_message: str | None = PydField(default=None, description="Приветственное сообщение")
    end_message: str | None = PydField(default=None, description="Сообщение завершения")
    off_hours_message: str | None = PydField(default=None, description="Сообщение вне рабочего времени")
    rating_enabled: bool | None = PydField(default=None, description="Включение оценки диалога")
    rating_message: str | None = PydField(default=None, description="Текст запроса оценки")
    rating_positive_message: str | None = PydField(default=None, description="Текст при позитивной оценке")
    rating_negative_message: str | None = PydField(default=None, description="Текст при негативной оценке")
    active: bool | None = PydField(default=None, description="Признак активности канала")


class ChannelDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID канала")


class ChannelEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID канала")
    name: str | None = PydField(default=None, description="Новое название")
    queue_mode: QueueModeEnum | None = PydField(default=None, description="Pool, Direct")
    routing_strategy: RoutingStrategyEnum | None = PydField(default=None, description="RoundRobin, LeastLoaded, Manual")
    first_response_sec: int | None = PydField(default=None, description="SLA первого ответа (сек.)")
    next_response_sec: int | None = PydField(default=None, description="SLA следующего ответа (сек.)")
    resolve_sec: int | None = PydField(default=None, description="SLA решения (сек.)")
    pause_on_waiting_client: bool | None = PydField(default=None, description="Пауза SLA в статусе ожидания клиента")
    start_message: str | None = PydField(default=None, description="Приветственное сообщение (\"\" -> NULL)")
    end_message: str | None = PydField(default=None, description="Сообщение завершения (\"\" -> NULL)")
    off_hours_message: str | None = PydField(default=None, description="Сообщение вне рабочего времени (\"\" -> NULL)")
    rating_enabled: bool | None = PydField(default=None, description="Включение оценки диалога")
    rating_message: str | None = PydField(default=None, description="Текст запроса оценки (\"\" -> NULL)")
    rating_positive_message: str | None = PydField(default=None, description="Текст при позитивной оценке (\"\" -> NULL)")
    rating_negative_message: str | None = PydField(default=None, description="Текст при негативной оценке (\"\" -> NULL)")
    active: bool | None = PydField(default=None, description="Признак активности канала")


class ChannelGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Фильтр по ID каналов")
    search: str | None = PydField(default=None, description="Поиск по названию канала")
    active: bool | None = PydField(default=None, description="Фильтр по признаку активности")
    limit: int | None = PydField(default=None, description="Лимит выборки, при <= 0 используется 100, максимум 1000")
    offset: int | None = PydField(default=None, description="Смещение выборки, при < 0 используется 0")


class ChannelOperator(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    channel_id: int | None = PydField(default=None)
    user_id: int | None = PydField(default=None)
    sort_order: int | None = PydField(default=None)
    max_active_leads: int | None = PydField(default=None)
    is_active: bool | None = PydField(default=None)
    joined_date: int | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class ChannelRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Channel] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ChannelScheduleInterval(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    channel_id: int | None = PydField(default=None)
    day_of_week: int | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    cross_day: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class ChannelSetInterval(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    day_of_week: int | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    cross_day: bool | None = PydField(default=None)


class ChannelSetIntervals(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    channel_id: int | None = PydField(default=None, description="ID канала")
    intervals: list[ChannelSetInterval] | None = PydField(default=None, description="Новый список интервалов графика; пустой массив очищает график и означает режим 24/7")


class ChannelSetOperator(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None)
    sort_order: int | None = PydField(default=None)
    max_active_leads: int | None = PydField(default=None)
    is_active: bool | None = PydField(default=None)


class ChannelSetOperators(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    channel_id: int | None = PydField(default=None, description="ID канала")
    operators: list[ChannelSetOperator] | None = PydField(default=None, description="Новый список операторов; при пустом массиве все операторы канала удаляются")


class QueueModeEnum(str, Enum):
    Default = "Default"
    Pool = "Pool"
    Direct = "Direct"


class RoutingStrategyEnum(str, Enum):
    Default = "Default"
    RoundRobin = "RoundRobin"
    LeastLoaded = "LeastLoaded"
    Manual = "Manual"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


ChannelAddRequest: TypeAlias = ChannelAdd
ChannelAddResponse: TypeAlias = InsertResult
ChannelDeleteRequest: TypeAlias = ChannelDelete
ChannelDeleteResponse: TypeAlias = UpdateResult
ChannelEditRequest: TypeAlias = ChannelEdit
ChannelEditResponse: TypeAlias = UpdateResult
ChannelGetRequest: TypeAlias = ChannelGet
ChannelGetResponse: TypeAlias = ChannelRegosOffsettedArrayResult
ChannelSetIntervalsRequest: TypeAlias = ChannelSetIntervals
ChannelSetIntervalsResponse: TypeAlias = UpdateResult
ChannelSetOperatorsRequest: TypeAlias = ChannelSetOperators
ChannelSetOperatorsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['Channel', 'ChannelAdd', 'ChannelDelete', 'ChannelEdit', 'ChannelGet', 'ChannelOperator', 'ChannelRegosOffsettedArrayResult', 'ChannelScheduleInterval', 'ChannelSetInterval', 'ChannelSetIntervals', 'ChannelSetOperator', 'ChannelSetOperators']


__all__ = [
    'Channel',
    'ChannelAdd',
    'ChannelDelete',
    'ChannelEdit',
    'ChannelGet',
    'ChannelOperator',
    'ChannelRegosOffsettedArrayResult',
    'ChannelScheduleInterval',
    'ChannelSetInterval',
    'ChannelSetIntervals',
    'ChannelSetOperator',
    'ChannelSetOperators',
    'QueueModeEnum',
    'RoutingStrategyEnum',
    'ChannelGetRequest',
    'ChannelGetResponse',
    'ChannelAddRequest',
    'ChannelAddResponse',
    'ChannelEditRequest',
    'ChannelEditResponse',
    'ChannelDeleteRequest',
    'ChannelDeleteResponse',
    'ChannelSetOperatorsRequest',
    'ChannelSetOperatorsResponse',
    'ChannelSetIntervalsRequest',
    'ChannelSetIntervalsResponse'
]
