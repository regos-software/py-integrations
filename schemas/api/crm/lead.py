"""Schemas for CRM leads."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.references.fields import FieldValue, FieldValueAdd


class LeadStatusEnum(str, Enum):
    New = "New"
    InProgress = "InProgress"
    WaitingClient = "WaitingClient"
    Converted = "Converted"
    Closed = "Closed"


class Lead(BaseSchema):
    """Lead read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Lead id.")
    channel_id: Optional[int] = PydField(default=None, description="Channel id.")
    pipeline_id: Optional[int] = PydField(default=None, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, description="Stage id.")
    status: Optional[LeadStatusEnum] = PydField(default=None, description="Status.")
    responsible_user_id: Optional[int] = PydField(
        default=None, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    subject: Optional[str] = PydField(default=None, description="Subject.")
    external_contact_id: Optional[str] = PydField(
        default=None, description="External contact id."
    )
    client_name: Optional[str] = PydField(default=None, description="Client name.")
    client_phone: Optional[str] = PydField(default=None, description="Client phone.")
    client_avatar_url: Optional[str] = PydField(
        default=None, description="Client avatar URL."
    )
    external_chat_id: Optional[str] = PydField(
        default=None, description="External chat id."
    )
    bot_id: Optional[str] = PydField(default=None, description="External bot id.")
    first_response_date: Optional[int] = PydField(
        default=None, description="First response unix time."
    )
    start_date: Optional[int] = PydField(default=None, description="Start unix time.")
    end_date: Optional[int] = PydField(default=None, description="End unix time.")
    close_reason_code: Optional[str] = PydField(
        default=None, description="Close reason code."
    )
    rating: Optional[int] = PydField(default=None, description="Rating.")
    rating_comment: Optional[str] = PydField(
        default=None, description="Rating comment."
    )
    first_response_due_date: Optional[int] = PydField(
        default=None, description="First response SLA unix time."
    )
    resolve_due_date: Optional[int] = PydField(
        default=None, description="Resolve SLA unix time."
    )
    sla_breached: Optional[bool] = PydField(default=None, description="SLA breached.")
    sla_breached_date: Optional[int] = PydField(
        default=None, description="SLA breached unix time."
    )
    converted_deal_id: Optional[int] = PydField(
        default=None, description="Converted deal id."
    )
    repeat_of_lead_id: Optional[int] = PydField(
        default=None, description="Repeat source lead id."
    )
    deleted: Optional[bool] = PydField(default=None, description="Deleted.")
    created_user_id: Optional[int] = PydField(
        default=None, description="Created user id."
    )
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )
    chat_id: Optional[str] = PydField(default=None, description="Related chat UUID.")
    fields: Optional[List[FieldValue]] = PydField(
        default=None, description="Custom field values."
    )


class LeadGetRequest(BaseSchema):
    """Request for Lead/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Lead ids.")
    channel_ids: Optional[List[int]] = PydField(default=None, description="Channel ids.")
    responsible_user_ids: Optional[List[int]] = PydField(
        default=None, description="Responsible ids."
    )
    stage_ids: Optional[List[int]] = PydField(default=None, description="Stage ids.")
    statuses: Optional[List[LeadStatusEnum]] = PydField(
        default=None, description="Lead statuses."
    )
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    sla_breached: Optional[bool] = PydField(default=None, description="SLA breached.")
    filters: Optional[List[Filter]] = PydField(
        default=None, description="Additional filters."
    )
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class LeadAddRequest(BaseSchema):
    """Request for Lead/Add."""

    model_config = ConfigDict(extra="forbid")

    channel_id: int = PydField(..., ge=1, description="Channel id.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(
        default=None, ge=1, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    subject: Optional[str] = PydField(default=None, description="Lead subject.")
    external_contact_id: Optional[str] = PydField(
        default=None, description="External contact id."
    )
    client_name: Optional[str] = PydField(default=None, description="Client name.")
    client_phone: Optional[str] = PydField(default=None, description="Client phone.")
    client_avatar_url: Optional[str] = PydField(
        default=None, description="Client avatar URL."
    )
    external_chat_id: Optional[str] = PydField(
        default=None, description="External chat id."
    )
    bot_id: Optional[str] = PydField(default=None, description="External bot id.")
    fields: Optional[List[FieldValueAdd]] = PydField(
        default=None, description="Custom field values."
    )


class LeadGetResponse(APIBaseResponse[List[Lead]]):
    """Response for Lead/Get."""

    model_config = ConfigDict(extra="ignore")


class LeadAddResponse(APIBaseResponse[AddResult]):
    """Response for Lead/Add."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Lead",
    "LeadAddRequest",
    "LeadAddResponse",
    "LeadGetRequest",
    "LeadGetResponse",
    "LeadStatusEnum",
]
