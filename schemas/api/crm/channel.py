"""Schemas for CRM channel endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema


class QueueModeEnum(str, Enum):
    Pool = "Pool"
    Direct = "Direct"


class RoutingStrategyEnum(str, Enum):
    RoundRobin = "RoundRobin"
    LeastLoaded = "LeastLoaded"
    Manual = "Manual"


class ChannelOperator(BaseSchema):
    """Read model for channel operators."""

    model_config = ConfigDict(extra="ignore")

    channel_id: Optional[int] = PydField(default=None, description="Channel id.")
    user_id: Optional[int] = PydField(default=None, description="Operator user id.")
    sort_order: Optional[int] = PydField(default=None, description="Queue sort order.")
    max_active_leads: Optional[int] = PydField(default=None, description="Operator lead limit.")
    is_active: Optional[bool] = PydField(default=None, description="Operator active flag.")
    joined_date: Optional[int] = PydField(default=None, description="Joined unix time.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")


class ChannelScheduleInterval(BaseSchema):
    """Read model for working schedule interval."""

    model_config = ConfigDict(extra="ignore")

    channel_id: Optional[int] = PydField(default=None, description="Channel id.")
    day_of_week: Optional[int] = PydField(default=None, description="Day of week (1-7).")
    start_minute: Optional[int] = PydField(default=None, description="Start minute (0-1439).")
    end_minute: Optional[int] = PydField(default=None, description="End minute (0-1439).")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")


class Channel(BaseSchema):
    """CRM channel read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Channel id.")
    name: Optional[str] = PydField(default=None, description="Channel name.")
    queue_mode: Optional[QueueModeEnum] = PydField(default=None, description="Queue mode.")
    routing_strategy: Optional[RoutingStrategyEnum] = PydField(default=None, description="Routing strategy.")
    first_response_sec: Optional[int] = PydField(default=None, description="First response SLA in seconds.")
    next_response_sec: Optional[int] = PydField(default=None, description="Next response SLA in seconds.")
    resolve_sec: Optional[int] = PydField(default=None, description="Resolve SLA in seconds.")
    pause_on_waiting_client: Optional[bool] = PydField(default=None, description="Pause SLA when waiting for client.")
    start_message: Optional[str] = PydField(default=None, description="Start message.")
    end_message: Optional[str] = PydField(default=None, description="End message.")
    off_hours_message: Optional[str] = PydField(default=None, description="Off-hours message.")
    rating_enabled: Optional[bool] = PydField(default=None, description="Rating enabled flag.")
    rating_message: Optional[str] = PydField(default=None, description="Rating prompt message.")
    rating_positive_message: Optional[str] = PydField(default=None, description="Positive rating message.")
    rating_negative_message: Optional[str] = PydField(default=None, description="Negative rating message.")
    active: Optional[bool] = PydField(default=None, description="Is active.")
    created_user_id: Optional[int] = PydField(default=None, description="Created user id.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")
    operators: Optional[List[ChannelOperator]] = PydField(default=None, description="Channel operators.")
    intervals: Optional[List[ChannelScheduleInterval]] = PydField(default=None, description="Working intervals.")


class ChannelGetRequest(BaseSchema):
    """Request for Channel/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Channel ids.")
    search: Optional[str] = PydField(default=None, description="Search by channel name.")
    active: Optional[bool] = PydField(default=None, description="Is active.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class ChannelAddRequest(BaseSchema):
    """Request for Channel/Add."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., description="Channel name.")
    queue_mode: QueueModeEnum = PydField(..., description="Queue mode.")
    routing_strategy: RoutingStrategyEnum = PydField(..., description="Routing strategy.")
    first_response_sec: Optional[int] = PydField(default=None, ge=0, description="First response SLA in seconds.")
    next_response_sec: Optional[int] = PydField(default=None, ge=0, description="Next response SLA in seconds.")
    resolve_sec: Optional[int] = PydField(default=None, ge=0, description="Resolve SLA in seconds.")
    pause_on_waiting_client: Optional[bool] = PydField(default=None, description="Pause SLA when waiting for client.")
    start_message: Optional[str] = PydField(default=None, description="Start message.")
    end_message: Optional[str] = PydField(default=None, description="End message.")
    off_hours_message: Optional[str] = PydField(default=None, description="Off-hours message.")
    rating_enabled: Optional[bool] = PydField(default=None, description="Rating enabled flag.")
    rating_message: Optional[str] = PydField(default=None, description="Rating prompt message.")
    rating_positive_message: Optional[str] = PydField(default=None, description="Positive rating message.")
    rating_negative_message: Optional[str] = PydField(default=None, description="Negative rating message.")
    active: Optional[bool] = PydField(default=None, description="Is active.")


class ChannelEditRequest(BaseSchema):
    """Request for Channel/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Channel id.")
    name: Optional[str] = PydField(default=None, description="Channel name.")
    queue_mode: Optional[QueueModeEnum] = PydField(default=None, description="Queue mode.")
    routing_strategy: Optional[RoutingStrategyEnum] = PydField(default=None, description="Routing strategy.")
    first_response_sec: Optional[int] = PydField(default=None, ge=0, description="First response SLA in seconds.")
    next_response_sec: Optional[int] = PydField(default=None, ge=0, description="Next response SLA in seconds.")
    resolve_sec: Optional[int] = PydField(default=None, ge=0, description="Resolve SLA in seconds.")
    pause_on_waiting_client: Optional[bool] = PydField(default=None, description="Pause SLA when waiting for client.")
    start_message: Optional[str] = PydField(default=None, description="Start message.")
    end_message: Optional[str] = PydField(default=None, description="End message.")
    off_hours_message: Optional[str] = PydField(default=None, description="Off-hours message.")
    rating_enabled: Optional[bool] = PydField(default=None, description="Rating enabled flag.")
    rating_message: Optional[str] = PydField(default=None, description="Rating prompt message.")
    rating_positive_message: Optional[str] = PydField(default=None, description="Positive rating message.")
    rating_negative_message: Optional[str] = PydField(default=None, description="Negative rating message.")
    active: Optional[bool] = PydField(default=None, description="Is active.")


class ChannelDeleteRequest(BaseSchema):
    """Request for Channel/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Channel id.")


class ChannelSetOperator(BaseSchema):
    """Single operator payload for Channel/SetOperators."""

    model_config = ConfigDict(extra="forbid")

    user_id: int = PydField(..., ge=1, description="Operator user id.")
    sort_order: Optional[int] = PydField(default=None, description="Queue sort order.")
    max_active_leads: Optional[int] = PydField(default=None, ge=0, description="Operator lead limit.")
    is_active: Optional[bool] = PydField(default=None, description="Operator active flag.")


class ChannelSetOperatorsRequest(BaseSchema):
    """Request for Channel/SetOperators."""

    model_config = ConfigDict(extra="forbid")

    channel_id: int = PydField(..., ge=1, description="Channel id.")
    operators: Optional[List[ChannelSetOperator]] = PydField(default=None, description="Operator payload.")


class ChannelSetInterval(BaseSchema):
    """Single schedule payload for Channel/SetIntervals."""

    model_config = ConfigDict(extra="forbid")

    day_of_week: int = PydField(..., ge=1, le=7, description="Day of week (1-7).")
    start_minute: int = PydField(..., ge=0, le=1439, description="Start minute (0-1439).")
    end_minute: int = PydField(..., ge=0, le=1439, description="End minute (0-1439).")

    @model_validator(mode="after")
    def _validate_bounds(self) -> "ChannelSetInterval":
        if self.start_minute == self.end_minute:
            raise ValueError("start_minute and end_minute must be different")
        return self


class ChannelSetIntervalsRequest(BaseSchema):
    """Request for Channel/SetIntervals."""

    model_config = ConfigDict(extra="forbid")

    channel_id: int = PydField(..., ge=1, description="Channel id.")
    intervals: List[ChannelSetInterval] = PydField(..., description="Schedule intervals.")


class ChannelGetResponse(APIBaseResponse[List[Channel]]):
    """Response for Channel/Get."""

    model_config = ConfigDict(extra="ignore")


class ChannelAddResponse(APIBaseResponse[AddResult]):
    """Response for Channel/Add."""

    model_config = ConfigDict(extra="ignore")


class ChannelEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Channel/Edit."""

    model_config = ConfigDict(extra="ignore")


class ChannelDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for Channel/Delete."""

    model_config = ConfigDict(extra="ignore")


class ChannelSetOperatorsResponse(APIBaseResponse[ArrayResult]):
    """Response for Channel/SetOperators."""

    model_config = ConfigDict(extra="ignore")


class ChannelSetIntervalsResponse(APIBaseResponse[ArrayResult]):
    """Response for Channel/SetIntervals."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Channel",
    "ChannelAddRequest",
    "ChannelAddResponse",
    "ChannelDeleteRequest",
    "ChannelDeleteResponse",
    "ChannelGetRequest",
    "ChannelGetResponse",
    "ChannelOperator",
    "ChannelScheduleInterval",
    "ChannelSetInterval",
    "ChannelSetIntervalsRequest",
    "ChannelSetIntervalsResponse",
    "ChannelSetOperator",
    "ChannelSetOperatorsRequest",
    "ChannelSetOperatorsResponse",
    "ChannelEditRequest",
    "ChannelEditResponse",
    "QueueModeEnum",
    "RoutingStrategyEnum",
]
