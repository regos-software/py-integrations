"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WorkAttendanceBreakEnd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    comment: str | None = PydField(default=None, description="Комментарий к завершению перерыва")


class WorkAttendanceBreakStart(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    break_type: WorkBreakTypeEnum | None = PydField(default=None, description="Тип перерыва: Lunch, Short, Other")
    comment: str | None = PydField(default=None, description="Комментарий к перерыву")


class WorkAttendanceCheckIn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    comment: str | None = PydField(default=None, description="Комментарий к check-in")


class WorkAttendanceCheckOut(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    comment: str | None = PydField(default=None, description="Комментарий к check-out")


class WorkAttendanceCurrentSession(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя (по умолчанию текущий)")


class WorkAttendanceStatus(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID пользователя (по умолчанию текущий)")


class WorkAvailabilityStatusEnum(str, Enum):
    Default = "Default"
    Offline = "Offline"
    InShiftNotCheckedIn = "InShiftNotCheckedIn"
    Available = "Available"
    OnBreak = "OnBreak"
    OutOfShift = "OutOfShift"


class WorkBreakTypeEnum(str, Enum):
    Default = "Default"
    Lunch = "Lunch"
    Short = "Short"
    Other = "Other"


class WorkSession(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    user_id: int | None = PydField(default=None)
    schedule_id: int | None = PydField(default=None)
    planned_shift_start: int | None = PydField(default=None)
    planned_shift_end: int | None = PydField(default=None)
    check_in_date: int | None = PydField(default=None)
    check_out_date: int | None = PydField(default=None)
    check_in_source: WorkSessionSourceEnum | None = PydField(default=None)
    check_out_source: WorkSessionSourceEnum | None = PydField(default=None)
    check_in_comment: str | None = PydField(default=None)
    check_out_comment: str | None = PydField(default=None)
    worked_sec: int | None = PydField(default=None)
    deleted: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkSessionRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: WorkSession | Error | None = PydField(default=None, description="Объект результата.")


class WorkSessionSourceEnum(str, Enum):
    Default = "Default"
    User = "User"
    Manager = "Manager"


class WorkUserAvailability(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    user_id: int | None = PydField(default=None)
    status: WorkAvailabilityStatusEnum | None = PydField(default=None)
    is_in_shift: bool | None = PydField(default=None)
    is_checked_in: bool | None = PydField(default=None)
    is_on_break: bool | None = PydField(default=None)
    active_session_id: int | None = PydField(default=None)
    active_break_id: int | None = PydField(default=None)
    next_shift_start_date: int | None = PydField(default=None)
    next_shift_end_date: int | None = PydField(default=None)
    last_update: int | None = PydField(default=None)


class WorkUserAvailabilityRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: WorkUserAvailability | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, InsertResult, UpdateResult


WorkAttendanceBreakEndRequest: TypeAlias = WorkAttendanceBreakEnd
WorkAttendanceBreakEndResponse: TypeAlias = UpdateResult
WorkAttendanceBreakStartRequest: TypeAlias = WorkAttendanceBreakStart
WorkAttendanceBreakStartResponse: TypeAlias = InsertResult
WorkAttendanceCheckInRequest: TypeAlias = WorkAttendanceCheckIn
WorkAttendanceCheckInResponse: TypeAlias = InsertResult
WorkAttendanceCheckOutRequest: TypeAlias = WorkAttendanceCheckOut
WorkAttendanceCheckOutResponse: TypeAlias = UpdateResult
WorkAttendanceCurrentSessionRequest: TypeAlias = WorkAttendanceCurrentSession
WorkAttendanceCurrentSessionResponse: TypeAlias = WorkSessionRegosObjectResult
WorkAttendanceStatusRequest: TypeAlias = WorkAttendanceStatus
WorkAttendanceStatusResponse: TypeAlias = WorkUserAvailabilityRegosObjectResult


_MODEL_NAMES = ['WorkAttendanceBreakEnd', 'WorkAttendanceBreakStart', 'WorkAttendanceCheckIn', 'WorkAttendanceCheckOut', 'WorkAttendanceCurrentSession', 'WorkAttendanceStatus', 'WorkSession', 'WorkSessionRegosObjectResult', 'WorkUserAvailability', 'WorkUserAvailabilityRegosObjectResult']


__all__ = [
    'WorkAttendanceBreakEnd',
    'WorkAttendanceBreakStart',
    'WorkAttendanceCheckIn',
    'WorkAttendanceCheckOut',
    'WorkAttendanceCurrentSession',
    'WorkAttendanceStatus',
    'WorkAvailabilityStatusEnum',
    'WorkBreakTypeEnum',
    'WorkSession',
    'WorkSessionRegosObjectResult',
    'WorkSessionSourceEnum',
    'WorkUserAvailability',
    'WorkUserAvailabilityRegosObjectResult',
    'WorkAttendanceStatusRequest',
    'WorkAttendanceStatusResponse',
    'WorkAttendanceCheckInRequest',
    'WorkAttendanceCheckInResponse',
    'WorkAttendanceCheckOutRequest',
    'WorkAttendanceCheckOutResponse',
    'WorkAttendanceBreakStartRequest',
    'WorkAttendanceBreakStartResponse',
    'WorkAttendanceBreakEndRequest',
    'WorkAttendanceBreakEndResponse',
    'WorkAttendanceCurrentSessionRequest',
    'WorkAttendanceCurrentSessionResponse'
]
