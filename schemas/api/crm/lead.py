"""Schemas for CRM leads."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.crm.client import Client
from schemas.api.references.fields import FieldValue, FieldValueAdd, FieldValueEdit


class LeadStatusEnum(str, Enum):
    """Legacy lead statuses kept for backward compatibility in integrations."""

    New = "New"
    InProgress = "InProgress"
    WaitingClient = "WaitingClient"
    Converted = "Converted"
    Closed = "Closed"


class LeadSetStatusEnum(str, Enum):
    """Legacy Lead/SetStatus statuses (endpoint is deprecated)."""

    New = "New"
    InProgress = "InProgress"
    WaitingClient = "WaitingClient"
    Closed = "Closed"


class Lead(BaseSchema):
    """Lead read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Lead id.")
    client_id: Optional[int] = PydField(default=None, description="Client id.")
    client: Optional[Client] = PydField(default=None, description="Client payload.")
    pipeline_id: Optional[int] = PydField(default=None, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(
        default=None, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    subject: Optional[str] = PydField(default=None, description="Subject.")
    description: Optional[str] = PydField(default=None, description="Description.")
    start_date: Optional[int] = PydField(default=None, description="Start unix time.")
    end_date: Optional[int] = PydField(default=None, description="End unix time.")
    converted_deal_id: Optional[int] = PydField(
        default=None, description="Converted deal id."
    )
    repeat_of_lead_id: Optional[int] = PydField(
        default=None, description="Repeat source lead id."
    )
    source_ticket_id: Optional[int] = PydField(
        default=None, description="Source ticket id."
    )
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

    # Legacy fields kept to avoid breaking old integrations during migration.
    channel_id: Optional[int] = PydField(default=None, description="Legacy channel id.")
    status: Optional[LeadStatusEnum] = PydField(default=None, description="Legacy status.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(
        default=None, description="Legacy client photo URL."
    )


class LeadGetRequest(BaseSchema):
    """Request for Lead/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Lead ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    responsible_user_ids: Optional[List[int]] = PydField(
        default=None, description="Responsible ids."
    )
    stage_ids: Optional[List[int]] = PydField(default=None, description="Stage ids.")
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    filters: Optional[List[Filter]] = PydField(
        default=None, description="Additional filters."
    )
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")

    # Legacy filters kept for transition.
    channel_ids: Optional[List[int]] = PydField(default=None, description="Legacy channel ids.")
    statuses: Optional[List[LeadStatusEnum]] = PydField(
        default=None, description="Legacy statuses."
    )
    sla_breached: Optional[bool] = PydField(default=None, description="Legacy SLA flag.")


class LeadAddRequest(BaseSchema):
    """Request for Lead/Add."""

    model_config = ConfigDict(extra="forbid")

    client_id: Optional[int] = PydField(default=None, ge=1, description="Client id.")
    source_ticket_id: Optional[int] = PydField(
        default=None, ge=1, description="Source ticket id."
    )
    chat_id: Optional[str] = PydField(default=None, description="Existing chat UUID.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(
        default=None, ge=1, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    subject: Optional[str] = PydField(default=None, description="Lead subject.")
    description: Optional[str] = PydField(default=None, description="Lead description.")
    fields: Optional[List[FieldValueAdd]] = PydField(
        default=None, description="Custom field values."
    )

    # Legacy fields kept for transition (will be sanitized by service).
    channel_id: Optional[int] = PydField(default=None, ge=1, description="Legacy channel id.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(
        default=None, description="Legacy client photo URL."
    )


class LeadEditRequest(BaseSchema):
    """Request for Lead/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    subject: Optional[str] = PydField(default=None, description="Lead subject.")
    description: Optional[str] = PydField(default=None, description="Lead description.")
    fields: Optional[List[FieldValueEdit]] = PydField(
        default=None, description="Custom field changes."
    )

    # Legacy fields kept for transition (will be sanitized by service).
    channel_id: Optional[int] = PydField(default=None, ge=1, description="Legacy channel id.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Legacy pipeline id.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(
        default=None, description="Legacy client photo URL."
    )


class LeadGetResponse(APIBaseResponse[List[Lead]]):
    """Response for Lead/Get."""

    model_config = ConfigDict(extra="ignore")


class LeadAddResponse(APIBaseResponse[AddResult]):
    """Response for Lead/Add."""

    model_config = ConfigDict(extra="ignore")


class LeadEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/Edit."""

    model_config = ConfigDict(extra="ignore")


class LeadSetStatusRequest(BaseSchema):
    """Legacy request for Lead/SetStatus (deprecated endpoint)."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    status: LeadSetStatusEnum = PydField(..., description="Legacy lead status.")


class LeadSetStatusResponse(APIBaseResponse[ArrayResult]):
    """Legacy response for Lead/SetStatus."""

    model_config = ConfigDict(extra="ignore")


class LeadSetResponsibleRequest(BaseSchema):
    """Request for Lead/SetResponsible."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    responsible_user_id: int = PydField(..., ge=1, description="Responsible user id.")


class LeadSetResponsibleResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/SetResponsible."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Lead",
    "LeadAddRequest",
    "LeadAddResponse",
    "LeadEditRequest",
    "LeadEditResponse",
    "LeadGetRequest",
    "LeadGetResponse",
    "LeadSetResponsibleRequest",
    "LeadSetResponsibleResponse",
    "LeadSetStatusEnum",
    "LeadSetStatusRequest",
    "LeadSetStatusResponse",
    "LeadStatusEnum",
]
