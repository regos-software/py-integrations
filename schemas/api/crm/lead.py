"""Schemas for CRM lead endpoints."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.crm.client import Client
from schemas.api.references.fields import FieldValue, FieldValueAdd, FieldValueEdit


class LeadStatusEnum(str, Enum):
    """Lead status values used by backend business rules."""

    New = "New"
    InProgress = "InProgress"
    WaitingClient = "WaitingClient"
    Converted = "Converted"
    Closed = "Closed"


class LeadConvertTargetEntityTypeEnum(str, Enum):
    Deal = "Deal"


class Lead(BaseSchema):
    """Lead read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Lead id.")
    client_id: Optional[int] = PydField(default=None, description="Client id.")
    client: Optional[Client] = PydField(default=None, description="Client payload.")
    pipeline_id: Optional[int] = PydField(default=None, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(default=None, description="Responsible user id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    title: Optional[str] = PydField(default=None, description="Lead title.")
    description: Optional[str] = PydField(default=None, description="Description.")
    amount: Optional[Decimal] = PydField(default=None, description="Lead amount.")
    start_date: Optional[int] = PydField(default=None, description="Start unix time.")
    end_date: Optional[int] = PydField(default=None, description="End unix time.")
    converted_deal_id: Optional[int] = PydField(default=None, description="Converted deal id.")
    repeat_of_lead_id: Optional[int] = PydField(default=None, description="Repeat source lead id.")
    ticket_id: Optional[int] = PydField(default=None, description="Source ticket id.")
    created_user_id: Optional[int] = PydField(default=None, description="Created user id.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")
    chat_id: Optional[str] = PydField(default=None, description="Related chat UUID.")
    fields: Optional[List[FieldValue]] = PydField(default=None, description="Custom field values.")

    # Compatibility fields that can still appear in old integrations.
    subject: Optional[str] = PydField(default=None, description="Legacy lead subject.")
    source_ticket_id: Optional[int] = PydField(default=None, description="Legacy source ticket id.")
    channel_id: Optional[int] = PydField(default=None, description="Legacy channel id.")
    status: Optional[LeadStatusEnum] = PydField(default=None, description="Lead status.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(default=None, description="Legacy client photo URL.")
    rating: Optional[int] = PydField(default=None, description="Lead rating.")
    rating_comment: Optional[str] = PydField(default=None, description="Lead rating comment.")


class LeadGetRequest(BaseSchema):
    """Request for Lead/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Lead ids.")
    client_ids: Optional[List[int]] = PydField(default=None, description="Client ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    responsible_user_ids: Optional[List[int]] = PydField(default=None, description="Responsible ids.")
    stage_ids: Optional[List[int]] = PydField(default=None, description="Stage ids.")
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    filters: Optional[List[Filter]] = PydField(default=None, description="Additional filters.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")

    # Legacy filters kept for compatibility.
    channel_ids: Optional[List[int]] = PydField(default=None, description="Legacy channel ids.")
    statuses: Optional[List[LeadStatusEnum]] = PydField(default=None, description="Legacy statuses.")
    sla_breached: Optional[bool] = PydField(default=None, description="Legacy SLA flag.")


class LeadAddRequest(BaseSchema):
    """Request for Lead/Add."""

    model_config = ConfigDict(extra="forbid")

    client_id: Optional[int] = PydField(default=None, ge=1, description="Client id.")
    ticket_id: Optional[int] = PydField(default=None, ge=1, description="Source ticket id.")
    chat_id: Optional[str] = PydField(default=None, description="Existing chat UUID.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(default=None, ge=1, description="Responsible user id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    title: Optional[str] = PydField(default=None, description="Lead title.")
    description: Optional[str] = PydField(default=None, description="Lead description.")
    amount: Optional[Decimal] = PydField(default=None, description="Lead amount.")
    fields: Optional[List[FieldValueAdd]] = PydField(default=None, description="Custom field values.")

    # Legacy fields mapped by service.
    source_ticket_id: Optional[int] = PydField(default=None, ge=1, description="Legacy source ticket id.")
    subject: Optional[str] = PydField(default=None, description="Legacy lead subject.")
    channel_id: Optional[int] = PydField(default=None, ge=1, description="Legacy channel id.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(default=None, description="Legacy client photo URL.")


class LeadEditRequest(BaseSchema):
    """Request for Lead/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    title: Optional[str] = PydField(default=None, description="Lead title.")
    description: Optional[str] = PydField(default=None, description="Lead description.")
    amount: Optional[Decimal] = PydField(default=None, description="Lead amount.")
    fields: Optional[List[FieldValueEdit]] = PydField(default=None, description="Custom field changes.")

    # Legacy fields mapped by service.
    subject: Optional[str] = PydField(default=None, description="Legacy lead subject.")
    channel_id: Optional[int] = PydField(default=None, ge=1, description="Legacy channel id.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Legacy pipeline id.")
    external_id: Optional[str] = PydField(default=None, description="Legacy external id.")
    client_name: Optional[str] = PydField(default=None, description="Legacy client name.")
    client_phone: Optional[str] = PydField(default=None, description="Legacy client phone.")
    client_photo_url: Optional[str] = PydField(default=None, description="Legacy client photo URL.")


class LeadDeleteRequest(BaseSchema):
    """Request for Lead/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")


class LeadSetStageRequest(BaseSchema):
    """Request for Lead/SetStage."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    stage_id: int = PydField(..., ge=1, description="Stage id.")
    comment: Optional[str] = PydField(default=None, description="Comment.")


class LeadSetResponsibleRequest(BaseSchema):
    """Request for Lead/SetResponsible."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    responsible_user_id: int = PydField(..., ge=1, description="Responsible user id.")


class LeadSetParticipantsRequest(BaseSchema):
    """Request for Lead/SetParticipants."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    replace_mode: Optional[bool] = PydField(default=None, description="Replace mode.")


class LeadSetRatingRequest(BaseSchema):
    """Request for Lead/SetRating."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    rating: int = PydField(..., ge=1, description="Rating.")
    rating_comment: Optional[str] = PydField(default=None, description="Rating comment.")


class LeadCloseRequest(BaseSchema):
    """Request for Lead/Close."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Terminal stage id.")


class LeadConvertRequest(BaseSchema):
    """Request for Lead/Convert."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Lead id.")
    target_entity_type: LeadConvertTargetEntityTypeEnum = PydField(..., description="Target entity type.")
    deal_type_id: Optional[int] = PydField(default=None, ge=1, description="Deal type id.")
    deal_title: str = PydField(..., description="Deal title.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Deal pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Deal stage id.")
    responsible_user_id: Optional[int] = PydField(default=None, ge=1, description="Deal responsible user id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Deal participant user ids.")
    amount: Optional[Decimal] = PydField(default=None, description="Deal amount.")
    currency_id: Optional[int] = PydField(default=None, ge=1, description="Deal currency id.")
    fields: Optional[List[FieldValueAdd]] = PydField(default=None, description="Deal custom field values.")


class LeadGetResponse(APIBaseResponse[List[Lead]]):
    """Response for Lead/Get."""

    model_config = ConfigDict(extra="ignore")


class LeadAddResponse(APIBaseResponse[AddResult]):
    """Response for Lead/Add."""

    model_config = ConfigDict(extra="ignore")


class LeadEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/Edit."""

    model_config = ConfigDict(extra="ignore")


class LeadDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/Delete."""

    model_config = ConfigDict(extra="ignore")


class LeadSetStageResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/SetStage."""

    model_config = ConfigDict(extra="ignore")


class LeadSetResponsibleResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/SetResponsible."""

    model_config = ConfigDict(extra="ignore")


class LeadSetParticipantsResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/SetParticipants."""

    model_config = ConfigDict(extra="ignore")


class LeadSetRatingResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/SetRating."""

    model_config = ConfigDict(extra="ignore")


class LeadCloseResponse(APIBaseResponse[ArrayResult]):
    """Response for Lead/Close."""

    model_config = ConfigDict(extra="ignore")


class LeadConvertResponse(APIBaseResponse[AddResult]):
    """Response for Lead/Convert."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Lead",
    "LeadAddRequest",
    "LeadAddResponse",
    "LeadCloseRequest",
    "LeadCloseResponse",
    "LeadConvertRequest",
    "LeadConvertResponse",
    "LeadConvertTargetEntityTypeEnum",
    "LeadDeleteRequest",
    "LeadDeleteResponse",
    "LeadEditRequest",
    "LeadEditResponse",
    "LeadGetRequest",
    "LeadGetResponse",
    "LeadSetParticipantsRequest",
    "LeadSetParticipantsResponse",
    "LeadSetRatingRequest",
    "LeadSetRatingResponse",
    "LeadSetResponsibleRequest",
    "LeadSetResponsibleResponse",
    "LeadSetStageRequest",
    "LeadSetStageResponse",
    "LeadStatusEnum",
]
