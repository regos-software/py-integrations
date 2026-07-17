"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WorkSchedule(RegosModel):
    "Модель, описывающая график рабочего времени"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID графика")
    name: str | None = PydField(default=None, description="Наименование графика")
    schedule_type: WorkScheduleTypeEnum | None = PydField(default=None, description="Тип графика: Weekly, Shift")
    is_account_default: bool | None = PydField(default=None, description="Признак default-графика аккаунта")
    check_in_early_sec: int | None = PydField(default=None, description="Допустимый ранний check-in (сек.)")
    check_in_late_sec: int | None = PydField(default=None, description="Допустимое опоздание на check-in (сек.)")
    active: bool | None = PydField(default=None, description="Активность графика")
    deleted: bool | None = PydField(default=None, description="Признак удаления")
    created_user_id: int | None = PydField(default=None, description="ID пользователя, создавшего график")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения (Unix time, сек.)")


class WorkScheduleAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название графика")
    schedule_type: WorkScheduleTypeEnum | None = PydField(default=None, description="Тип графика: Weekly или Shift")
    is_account_default: bool | None = PydField(default=None, description="Сделать график default для аккаунта")
    check_in_early_sec: int | None = PydField(default=None, description="Допустимый ранний check-in, сек")
    check_in_late_sec: int | None = PydField(default=None, description="Допустимое опоздание check-in, сек")
    active: bool | None = PydField(default=None, description="Признак активного графика")


class WorkScheduleDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID графика")


class WorkScheduleEdit(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID графика")
    name: str | None = PydField(default=None, description="Название графика")
    schedule_type: WorkScheduleTypeEnum | None = PydField(default=None, description="Тип графика: Weekly или Shift")
    check_in_early_sec: int | None = PydField(default=None, description="Допустимый ранний check-in, сек")
    check_in_late_sec: int | None = PydField(default=None, description="Допустимое опоздание check-in, сек")
    active: bool | None = PydField(default=None, description="Признак активного графика")


class WorkScheduleException(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    date: str | None = PydField(default=None)
    is_working_day: bool | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    comment: str | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkScheduleExceptionRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WorkScheduleException] | Error | None = PydField(default=None, description="Массив результата.")


class WorkScheduleExceptionSet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: str | None = PydField(default=None)
    is_working_day: bool | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    comment: str | None = PydField(default=None)


class WorkScheduleGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив ID графиков")
    search: str | None = PydField(default=None, description="Поиск по названию")
    active: bool | None = PydField(default=None, description="Фильтр по активности")
    limit: int | None = PydField(default=None, description="Лимит выборки")
    offset: int | None = PydField(default=None, description="Смещение выборки")


class WorkScheduleGetExceptions(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schedule_id: int | None = PydField(default=None, description="ID графика")


class WorkScheduleGetIntervals(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schedule_id: int | None = PydField(default=None, description="ID графика")


class WorkScheduleInterval(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    schedule_id: int | None = PydField(default=None)
    day_of_week: int | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    cross_day: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkScheduleIntervalRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WorkScheduleInterval] | Error | None = PydField(default=None, description="Массив результата.")


class WorkScheduleIntervalSet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    day_of_week: int | None = PydField(default=None)
    start_minute: int | None = PydField(default=None)
    end_minute: int | None = PydField(default=None)
    cross_day: bool | None = PydField(default=None)


class WorkScheduleRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WorkSchedule] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class WorkScheduleSetDefault(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID графика, который станет default")


class WorkScheduleSetExceptions(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schedule_id: int | None = PydField(default=None, description="ID графика")
    exceptions: list[WorkScheduleExceptionSet] | None = PydField(default=None, description="Новый список исключений")


class WorkScheduleSetIntervals(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schedule_id: int | None = PydField(default=None, description="ID графика")
    intervals: list[WorkScheduleIntervalSet] | None = PydField(default=None, description="Новый список интервалов")


class WorkScheduleTypeEnum(str, Enum):
    Default = "Default"
    Weekly = "Weekly"
    Shift = "Shift"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


WorkScheduleAddRequest: TypeAlias = WorkScheduleAdd
WorkScheduleAddResponse: TypeAlias = InsertResult
WorkScheduleDeleteRequest: TypeAlias = WorkScheduleDelete
WorkScheduleDeleteResponse: TypeAlias = UpdateResult
WorkScheduleEditRequest: TypeAlias = WorkScheduleEdit
WorkScheduleEditResponse: TypeAlias = UpdateResult
WorkScheduleGetExceptionsRequest: TypeAlias = WorkScheduleGetExceptions
WorkScheduleGetExceptionsResponse: TypeAlias = WorkScheduleExceptionRegosArrayResult
WorkScheduleGetIntervalsRequest: TypeAlias = WorkScheduleGetIntervals
WorkScheduleGetIntervalsResponse: TypeAlias = WorkScheduleIntervalRegosArrayResult
WorkScheduleGetRequest: TypeAlias = WorkScheduleGet
WorkScheduleGetResponse: TypeAlias = WorkScheduleRegosOffsettedArrayResult
WorkScheduleSetDefaultRequest: TypeAlias = WorkScheduleSetDefault
WorkScheduleSetDefaultResponse: TypeAlias = UpdateResult
WorkScheduleSetExceptionsRequest: TypeAlias = WorkScheduleSetExceptions
WorkScheduleSetExceptionsResponse: TypeAlias = UpdateResult
WorkScheduleSetIntervalsRequest: TypeAlias = WorkScheduleSetIntervals
WorkScheduleSetIntervalsResponse: TypeAlias = UpdateResult


_MODEL_NAMES = ['WorkSchedule', 'WorkScheduleAdd', 'WorkScheduleDelete', 'WorkScheduleEdit', 'WorkScheduleException', 'WorkScheduleExceptionRegosArrayResult', 'WorkScheduleExceptionSet', 'WorkScheduleGet', 'WorkScheduleGetExceptions', 'WorkScheduleGetIntervals', 'WorkScheduleInterval', 'WorkScheduleIntervalRegosArrayResult', 'WorkScheduleIntervalSet', 'WorkScheduleRegosOffsettedArrayResult', 'WorkScheduleSetDefault', 'WorkScheduleSetExceptions', 'WorkScheduleSetIntervals']


__all__ = [
    'WorkSchedule',
    'WorkScheduleAdd',
    'WorkScheduleDelete',
    'WorkScheduleEdit',
    'WorkScheduleException',
    'WorkScheduleExceptionRegosArrayResult',
    'WorkScheduleExceptionSet',
    'WorkScheduleGet',
    'WorkScheduleGetExceptions',
    'WorkScheduleGetIntervals',
    'WorkScheduleInterval',
    'WorkScheduleIntervalRegosArrayResult',
    'WorkScheduleIntervalSet',
    'WorkScheduleRegosOffsettedArrayResult',
    'WorkScheduleSetDefault',
    'WorkScheduleSetExceptions',
    'WorkScheduleSetIntervals',
    'WorkScheduleTypeEnum',
    'WorkScheduleGetRequest',
    'WorkScheduleGetResponse',
    'WorkScheduleGetIntervalsRequest',
    'WorkScheduleGetIntervalsResponse',
    'WorkScheduleGetExceptionsRequest',
    'WorkScheduleGetExceptionsResponse',
    'WorkScheduleAddRequest',
    'WorkScheduleAddResponse',
    'WorkScheduleEditRequest',
    'WorkScheduleEditResponse',
    'WorkScheduleDeleteRequest',
    'WorkScheduleDeleteResponse',
    'WorkScheduleSetDefaultRequest',
    'WorkScheduleSetDefaultResponse',
    'WorkScheduleSetIntervalsRequest',
    'WorkScheduleSetIntervalsResponse',
    'WorkScheduleSetExceptionsRequest',
    'WorkScheduleSetExceptionsResponse'
]
