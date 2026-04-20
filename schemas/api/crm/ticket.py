"""Schemas for CRM ticket endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.crm.client import Client
from schemas.api.references.fields import FieldValue, FieldValueAdd, FieldValueEdit


class TicketDirectionEnum(str, Enum):
    Inbound = "Inbound"
    Outbound = "Outbound"


class TicketStatusEnum(str, Enum):
    Open = "Open"
    Closed = "Closed"


class Ticket(BaseSchema):
    """CRM ticket read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Ticket id.")
    client_id: Optional[int] = PydField(default=None, description="Client id.")
    client: Optional[Client] = PydField(default=None, description="Client payload.")
    channel_id: Optional[int] = PydField(default=None, description="Channel id.")
    direction: Optional[TicketDirectionEnum] = PydField(default=None, description="Ticket direction.")
    external_dialog_id: Optional[str] = PydField(default=None, description="External dialog id.")
    subject: Optional[str] = PydField(default=None, description="Subject.")
    description: Optional[str] = PydField(default=None, description="Description.")
    responsible_user_id: Optional[int] = PydField(default=None, description="Responsible user id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    status: Optional[TicketStatusEnum] = PydField(default=None, description="Status.")
    first_response_date: Optional[int] = PydField(default=None, description="First response unix time.")
    first_response_due_date: Optional[int] = PydField(default=None, description="First response due unix time.")
    resolve_due_date: Optional[int] = PydField(default=None, description="Resolve due unix time.")
    sla_breached: Optional[bool] = PydField(default=None, description="SLA breached.")
    sla_breached_date: Optional[int] = PydField(default=None, description="SLA breached unix time.")
    resolved_date: Optional[int] = PydField(default=None, description="Resolved unix time.")
    rating: Optional[int] = PydField(default=None, description="Rating.")
    rating_comment: Optional[str] = PydField(default=None, description="Rating comment.")
    chat_id: Optional[str] = PydField(default=None, description="Related chat UUID.")
    fields: Optional[List[FieldValue]] = PydField(default=None, description="Custom fields.")
    created_user_id: Optional[int] = PydField(default=None, description="Created user id.")
    created_date: Optional[int] = PydField(default=None, description="Created unix time.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")


class TicketGetRequest(BaseSchema):
    """Request for Ticket/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Ticket ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    client_ids: Optional[List[int]] = PydField(default=None, description="Client ids.")
    channel_ids: Optional[List[int]] = PydField(default=None, description="Channel ids.")
    responsible_user_ids: Optional[List[int]] = PydField(default=None, description="Responsible user ids.")
    statuses: Optional[List[TicketStatusEnum]] = PydField(default=None, description="Ticket statuses.")
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    filters: Optional[List[Filter]] = PydField(default=None, description="Additional filters.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class TicketAddRequest(BaseSchema):
    """Request for Ticket/Add."""

    model_config = ConfigDict(extra="forbid")

    client_id: int = PydField(..., ge=1, description="Client id.")
    channel_id: int = PydField(..., ge=1, description="Channel id.")
    direction: Optional[TicketDirectionEnum] = PydField(default=None, description="Ticket direction.")
    external_dialog_id: Optional[str] = PydField(default=None, description="External dialog id.")
    subject: Optional[str] = PydField(default=None, description="Subject.")
    description: Optional[str] = PydField(default=None, description="Description.")
    responsible_user_id: Optional[int] = PydField(default=None, ge=1, description="Responsible user id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    fields: Optional[List[FieldValueAdd]] = PydField(default=None, description="Custom field values.")


class TicketEditRequest(BaseSchema):
    """Request for Ticket/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Ticket id.")
    direction: Optional[TicketDirectionEnum] = PydField(default=None, description="Ticket direction.")
    subject: Optional[str] = PydField(default=None, description="Subject.")
    description: Optional[str] = PydField(default=None, description="Description.")
    fields: Optional[List[FieldValueEdit]] = PydField(default=None, description="Custom field changes.")


class TicketDeleteRequest(BaseSchema):
    """Request for Ticket/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Ticket id.")


class TicketSetResponsibleRequest(BaseSchema):
    """Request for Ticket/SetResponsible."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Ticket id.")
    responsible_user_id: int = PydField(..., ge=1, description="Responsible user id.")


class TicketSetParticipantsRequest(BaseSchema):
    """Request for Ticket/SetParticipants."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Ticket id.")
    participant_user_ids: Optional[List[int]] = PydField(default=None, description="Participant user ids.")
    replace_mode: Optional[bool] = PydField(default=None, description="Replace mode.")


class TicketCloseRequest(BaseSchema):
    """Request for Ticket/Close."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Ticket id.")
    resolved_date: Optional[int] = PydField(default=None, description="Resolved unix time.")


class TicketGetResponse(APIBaseResponse[List[Ticket]]):
    """Response for Ticket/Get."""

    model_config = ConfigDict(extra="ignore")


class TicketAddResponse(APIBaseResponse[AddResult]):
    """Response for Ticket/Add."""

    model_config = ConfigDict(extra="ignore")


class TicketEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Ticket/Edit."""

    model_config = ConfigDict(extra="ignore")


class TicketDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for Ticket/Delete."""

    model_config = ConfigDict(extra="ignore")


class TicketSetResponsibleResponse(APIBaseResponse[ArrayResult]):
    """Response for Ticket/SetResponsible."""

    model_config = ConfigDict(extra="ignore")


class TicketSetParticipantsResponse(APIBaseResponse[ArrayResult]):
    """Response for Ticket/SetParticipants."""

    model_config = ConfigDict(extra="ignore")


class TicketCloseResponse(APIBaseResponse[ArrayResult]):
    """Response for Ticket/Close."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Ticket",
    "TicketAddRequest",
    "TicketAddResponse",
    "TicketCloseRequest",
    "TicketCloseResponse",
    "TicketDeleteRequest",
    "TicketDeleteResponse",
    "TicketDirectionEnum",
    "TicketEditRequest",
    "TicketEditResponse",
    "TicketGetRequest",
    "TicketGetResponse",
    "TicketSetParticipantsRequest",
    "TicketSetParticipantsResponse",
    "TicketSetResponsibleRequest",
    "TicketSetResponsibleResponse",
    "TicketStatusEnum",
]
