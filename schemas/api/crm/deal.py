"""Schemas for CRM deals."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.crm.client import Client
from schemas.api.references.currency import Currency
from schemas.api.references.fields import FieldValue, FieldValueAdd, FieldValueEdit


class Deal(BaseSchema):
    """Deal read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Deal id.")
    client_id: Optional[int] = PydField(default=None, description="Client id.")
    client: Optional[Client] = PydField(default=None, description="Client payload.")
    lead_id: Optional[int] = PydField(default=None, description="Lead id.")
    source_ticket_id: Optional[int] = PydField(
        default=None, description="Source ticket id."
    )
    source_deal_id: Optional[int] = PydField(default=None, description="Source deal id.")
    deal_type_id: Optional[int] = PydField(default=None, description="Deal type id.")
    pipeline_id: Optional[int] = PydField(default=None, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, description="Stage id.")
    responsible_user_id: Optional[int] = PydField(
        default=None, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    title: Optional[str] = PydField(default=None, description="Deal title.")
    description: Optional[str] = PydField(default=None, description="Description.")
    open_date: Optional[int] = PydField(default=None, description="Open unix time.")
    close_date: Optional[int] = PydField(default=None, description="Close unix time.")
    created_user_id: Optional[int] = PydField(
        default=None, description="Created user id."
    )
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    currency: Optional[Currency] = PydField(default=None, description="Currency payload.")
    chat_id: Optional[str] = PydField(default=None, description="Related chat UUID.")
    fields: Optional[List[FieldValue]] = PydField(
        default=None, description="Custom fields."
    )


class DealGetRequest(BaseSchema):
    """Request for Deal/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Deal ids.")
    lead_ids: Optional[List[int]] = PydField(default=None, description="Lead ids.")
    responsible_user_ids: Optional[List[int]] = PydField(
        default=None, description="Responsible user ids."
    )
    stage_ids: Optional[List[int]] = PydField(default=None, description="Stage ids.")
    currency_id: Optional[int] = PydField(default=None, ge=1, description="Currency id.")
    filters: Optional[List[Filter]] = PydField(
        default=None, description="Additional filters."
    )
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class DealAddRequest(BaseSchema):
    """Request for Deal/Add."""

    model_config = ConfigDict(extra="forbid")

    source_lead_id: Optional[int] = PydField(default=None, ge=1, description="Source lead id.")
    source_ticket_id: Optional[int] = PydField(
        default=None, ge=1, description="Source ticket id."
    )
    source_deal_id: Optional[int] = PydField(default=None, ge=1, description="Source deal id.")
    client_id: Optional[int] = PydField(default=None, ge=1, description="Client id.")
    chat_id: Optional[str] = PydField(default=None, description="Existing chat UUID.")
    lead_id: Optional[int] = PydField(default=None, ge=1, description="Lead id.")
    deal_type_id: Optional[int] = PydField(default=None, ge=1, description="Deal type id.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    title: str = PydField(..., description="Deal title.")
    description: Optional[str] = PydField(default=None, description="Description.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    currency_id: Optional[int] = PydField(default=None, ge=1, description="Currency id.")
    responsible_user_id: Optional[int] = PydField(
        default=None, ge=1, description="Responsible user id."
    )
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    fields: Optional[List[FieldValueAdd]] = PydField(
        default=None, description="Custom field values."
    )


class DealEditRequest(BaseSchema):
    """Request for Deal/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")
    deal_type_id: Optional[int] = PydField(default=None, ge=1, description="Deal type id.")
    pipeline_id: Optional[int] = PydField(default=None, ge=1, description="Pipeline id.")
    stage_id: Optional[int] = PydField(default=None, ge=1, description="Stage id.")
    title: Optional[str] = PydField(default=None, description="Deal title.")
    description: Optional[str] = PydField(default=None, description="Description.")
    amount: Optional[Decimal] = PydField(default=None, description="Amount.")
    currency_id: Optional[int] = PydField(default=None, ge=1, description="Currency id.")
    fields: Optional[List[FieldValueEdit]] = PydField(
        default=None, description="Custom field changes."
    )


class DealDeleteRequest(BaseSchema):
    """Request for Deal/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")


class DealSetStageRequest(BaseSchema):
    """Request for Deal/SetStage."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")
    stage_id: int = PydField(..., ge=1, description="Stage id.")
    comment: Optional[str] = PydField(default=None, description="Comment.")


class DealSetResponsibleRequest(BaseSchema):
    """Request for Deal/SetResponsible."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")
    responsible_user_id: int = PydField(..., ge=1, description="Responsible user id.")


class DealSetParticipantsRequest(BaseSchema):
    """Request for Deal/SetParticipants."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")
    participant_user_ids: Optional[List[int]] = PydField(
        default=None, description="Participant user ids."
    )
    replace_mode: Optional[bool] = PydField(default=None, description="Replace mode.")


class DealCloseRequest(BaseSchema):
    """Request for Deal/Close."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Deal id.")
    stage_id: int = PydField(..., ge=1, description="Terminal stage id.")


class DealGetResponse(APIBaseResponse[List[Deal]]):
    """Response for Deal/Get."""

    model_config = ConfigDict(extra="ignore")


class DealAddResponse(APIBaseResponse[AddResult]):
    """Response for Deal/Add."""

    model_config = ConfigDict(extra="ignore")


class DealEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/Edit."""

    model_config = ConfigDict(extra="ignore")


class DealDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/Delete."""

    model_config = ConfigDict(extra="ignore")


class DealSetStageResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/SetStage."""

    model_config = ConfigDict(extra="ignore")


class DealSetResponsibleResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/SetResponsible."""

    model_config = ConfigDict(extra="ignore")


class DealSetParticipantsResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/SetParticipants."""

    model_config = ConfigDict(extra="ignore")


class DealCloseResponse(APIBaseResponse[ArrayResult]):
    """Response for Deal/Close."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Deal",
    "DealAddRequest",
    "DealAddResponse",
    "DealCloseRequest",
    "DealCloseResponse",
    "DealDeleteRequest",
    "DealDeleteResponse",
    "DealEditRequest",
    "DealEditResponse",
    "DealGetRequest",
    "DealGetResponse",
    "DealSetParticipantsRequest",
    "DealSetParticipantsResponse",
    "DealSetResponsibleRequest",
    "DealSetResponsibleResponse",
    "DealSetStageRequest",
    "DealSetStageResponse",
]
