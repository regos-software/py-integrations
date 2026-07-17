from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import AliasChoices, ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema


class ScheduleTaskStatus(str, Enum):
    Default = "Default"
    New = "New"
    Processing = "Processing"
    Finished = "Finished"
    Error = "Error"
    Canceled = "Canceled"
    NotFinished = "NotFinished"


class SchedulePeriodType(str, Enum):
    Default = "Default"
    None_ = "None"
    Minute = "Minute"
    Hour = "Hour"
    Day = "Day"
    Week = "Week"
    Month = "Month"
    Year = "Year"


def _blank_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return value


def _string_or_none(value: Any) -> Optional[str]:
    value = _blank_to_none(value)
    if value is None:
        return None
    return str(value)


def _int_or_zero(value: Any) -> int:
    value = _blank_to_none(value)
    if value is None:
        return 0
    return int(value)


def _int_or_one(value: Any) -> int:
    value = _blank_to_none(value)
    if value is None:
        return 1
    return int(value)


def _enum_or_default(value: Any, default: Enum) -> Any:
    value = _blank_to_none(value)
    return default if value is None else value


class SchedulerAPIErrorResult(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    error: int = PydField(..., description="Scheduler error code.")
    description: str = PydField(..., description="Scheduler error description.")


T = TypeVar("T")


class SchedulerAPIResponse(BaseSchema, Generic[T]):
    model_config = ConfigDict(extra="ignore")

    ok: bool = PydField(..., description="Success flag.")
    result: Optional[T] = PydField(default=None, description="Response payload.")


class ScheduleIdRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = PydField(
        ...,
        min_length=1,
        validation_alias=AliasChoices("id", "Id"),
        description="Schedule UUID.",
    )

    @field_validator("id", mode="before")
    @classmethod
    def _strip_id(cls, value: Any) -> str:
        text = _string_or_none(value)
        if not text:
            raise ValueError("id is required")
        return text


class ScheduleTaskIdRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    uuid: str = PydField(
        ...,
        min_length=1,
        validation_alias=AliasChoices("uuid", "Uuid", "UUID"),
        description="Task UUID.",
    )

    @field_validator("uuid", mode="before")
    @classmethod
    def _strip_uuid(cls, value: Any) -> str:
        text = _string_or_none(value)
        if not text:
            raise ValueError("uuid is required")
        return text


class ScheduleTaskSetStatusRequest(ScheduleTaskIdRequest):
    status: ScheduleTaskStatus = PydField(..., description="Task status.")

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value: Any) -> Any:
        return _blank_to_none(value)


class ScheduleAddRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    handler_id: int = PydField(default=1, ge=1, description="Scheduler handler id.")
    start_date: Optional[datetime] = PydField(default=None, description="Schedule start datetime.")
    end_date: Optional[datetime] = PydField(default=None, description="Schedule end datetime.")
    period_type: SchedulePeriodType = PydField(
        default=SchedulePeriodType.Default,
        description="Schedule period type.",
    )
    period_value: int = PydField(default=0, ge=0, description="Schedule period value.")
    api_login: Optional[str] = PydField(default=None, description="API login.")
    data: Optional[str] = PydField(default=None, description="Scheduler payload data.")
    connected_integration_id: Optional[str] = PydField(
        default=None,
        description="Connected integration id.",
    )
    run_immediately: bool = PydField(default=False, description="Run task immediately.")

    @field_validator("period_type", mode="before")
    @classmethod
    def _normalize_period_type(cls, value: Any) -> Any:
        return _enum_or_default(value, SchedulePeriodType.Default)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _normalize_datetime(cls, value: Any) -> Any:
        return _blank_to_none(value)

    @field_validator("api_login", "data", "connected_integration_id", mode="before")
    @classmethod
    def _normalize_text(cls, value: Any) -> Optional[str]:
        return _string_or_none(value)

    @field_validator("period_value", mode="before")
    @classmethod
    def _normalize_int(cls, value: Any) -> int:
        return _int_or_zero(value)

    @field_validator("handler_id", mode="before")
    @classmethod
    def _normalize_handler_id(cls, value: Any) -> int:
        return _int_or_one(value)


class Schedule(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    uuid: Optional[str] = PydField(default=None, description="Schedule UUID.")
    start_date: Optional[datetime | str] = PydField(default=None, description="Schedule start datetime.")
    last_execute: Optional[datetime | str] = PydField(default=None, description="Last execution datetime.")
    end_date: Optional[datetime | str] = PydField(default=None, description="Schedule end datetime.")
    period_type: SchedulePeriodType = PydField(
        default=SchedulePeriodType.Default,
        description="Schedule period type.",
    )
    period_value: int = PydField(default=0, ge=0, description="Schedule period value.")

    @field_validator("period_type", mode="before")
    @classmethod
    def _normalize_period_type(cls, value: Any) -> Any:
        return _enum_or_default(value, SchedulePeriodType.Default)

    @field_validator("uuid", mode="before")
    @classmethod
    def _normalize_uuid(cls, value: Any) -> Optional[str]:
        return _string_or_none(value)

    @field_validator("start_date", "last_execute", "end_date", mode="before")
    @classmethod
    def _normalize_datetime(cls, value: Any) -> Any:
        return _blank_to_none(value)

    @field_validator("period_value", mode="before")
    @classmethod
    def _normalize_int(cls, value: Any) -> int:
        return _int_or_zero(value)


class ScheduleTask(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    uuid: Optional[str] = PydField(default=None, description="Task UUID.")
    schedule_uuid: Optional[str] = PydField(default=None, description="Schedule UUID.")
    status: ScheduleTaskStatus = PydField(
        default=ScheduleTaskStatus.Default,
        description="Task status.",
    )
    start_time: Optional[datetime | str] = PydField(default=None, description="Task start datetime.")
    finish_time: Optional[datetime | str] = PydField(default=None, description="Task finish datetime.")
    api_login: Optional[str] = PydField(default=None, description="API login.")
    data: Optional[str] = PydField(default=None, description="Task payload data.")
    connected_integration_id: Optional[str] = PydField(
        default=None,
        description="Connected integration id.",
    )
    last_status_update: Optional[datetime | str] = PydField(
        default=None,
        description="Last status update datetime.",
    )

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value: Any) -> Any:
        return _enum_or_default(value, ScheduleTaskStatus.Default)

    @field_validator("uuid", "schedule_uuid", "api_login", "data", "connected_integration_id", mode="before")
    @classmethod
    def _normalize_text(cls, value: Any) -> Optional[str]:
        return _string_or_none(value)

    @field_validator("start_time", "finish_time", "last_status_update", mode="before")
    @classmethod
    def _normalize_datetime(cls, value: Any) -> Any:
        return _blank_to_none(value)


class AdapterSchedulerRequest(BaseSchema):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    uuid: Optional[str] = PydField(
        default=None,
        validation_alias=AliasChoices("uuid", "Uuid", "UUID"),
        description="Existing schedule UUID.",
    )
    start_date: Optional[datetime] = PydField(
        default=None,
        validation_alias=AliasChoices("start_date", "Start_date", "StartDate", "startDate"),
        description="Schedule start datetime.",
    )
    end_date: Optional[datetime] = PydField(
        default=None,
        validation_alias=AliasChoices("end_date", "End_date", "EndDate", "endDate"),
        description="Schedule end datetime.",
    )
    period_value: int = PydField(
        default=0,
        ge=0,
        validation_alias=AliasChoices("period_value", "Period_value", "PeriodValue", "periodValue"),
        description="Schedule period value.",
    )
    period_type: SchedulePeriodType = PydField(
        default=SchedulePeriodType.Default,
        validation_alias=AliasChoices("period_type", "Period_type", "PeriodType", "periodType"),
        description="Schedule period type.",
    )
    api_login: Optional[str] = PydField(
        default=None,
        validation_alias=AliasChoices("api_login", "ApiLogin", "Api_Login", "apiLogin"),
        description="API login.",
    )
    data: Optional[str] = PydField(
        default=None,
        validation_alias=AliasChoices("data", "Data"),
        description="Scheduler payload data.",
    )

    @field_validator("period_type", mode="before")
    @classmethod
    def _normalize_period_type(cls, value: Any) -> Any:
        return _enum_or_default(value, SchedulePeriodType.Default)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _normalize_datetime(cls, value: Any) -> Any:
        return _blank_to_none(value)

    @field_validator("uuid", "api_login", "data", mode="before")
    @classmethod
    def _normalize_text(cls, value: Any) -> Optional[str]:
        return _string_or_none(value)

    @field_validator("period_value", mode="before")
    @classmethod
    def _normalize_int(cls, value: Any) -> int:
        return _int_or_zero(value)


class AdapterSchedulerUuidRequest(BaseSchema):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    uuid: str = PydField(
        ...,
        min_length=1,
        validation_alias=AliasChoices("uuid", "Uuid", "UUID"),
        description="Schedule UUID.",
    )

    @field_validator("uuid", mode="before")
    @classmethod
    def _strip_uuid(cls, value: Any) -> str:
        text = _string_or_none(value)
        if not text:
            raise ValueError("uuid is required")
        return text


__all__ = [
    "AdapterSchedulerRequest",
    "AdapterSchedulerUuidRequest",
    "Schedule",
    "ScheduleAddRequest",
    "ScheduleIdRequest",
    "SchedulePeriodType",
    "ScheduleTask",
    "ScheduleTaskIdRequest",
    "ScheduleTaskSetStatusRequest",
    "ScheduleTaskStatus",
    "SchedulerAPIErrorResult",
    "SchedulerAPIResponse",
]
