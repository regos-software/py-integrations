"""Schemas for CRM pipelines."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema


class CrmEntityTypeEnum(str, Enum):
    Lead = "Lead"
    Deal = "Deal"


class PipelineStage(BaseSchema):
    """Pipeline stage."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Stage id.")
    pipeline_id: Optional[int] = PydField(default=None, description="Pipeline id.")
    name: Optional[str] = PydField(default=None, description="Stage name.")
    code: Optional[str] = PydField(default=None, description="External stage code.")
    sort_order: Optional[int] = PydField(default=None, description="Sort order.")
    is_start: Optional[bool] = PydField(default=None, description="Is start stage.")
    is_terminal: Optional[bool] = PydField(
        default=None, description="Is terminal stage."
    )
    is_success: Optional[bool] = PydField(
        default=None, description="Is successful stage."
    )
    active: Optional[bool] = PydField(default=None, description="Is active.")
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )


class Pipeline(BaseSchema):
    """CRM pipeline."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Pipeline id.")
    entity_type: Optional[CrmEntityTypeEnum] = PydField(
        default=None, description="Entity type."
    )
    name: Optional[str] = PydField(default=None, description="Pipeline name.")
    is_default: Optional[bool] = PydField(
        default=None, description="Default pipeline."
    )
    access_all: Optional[bool] = PydField(default=None, description="Access for all.")
    access_user_ids: Optional[List[int]] = PydField(
        default=None, description="Allowed user ids."
    )
    access_group_ids: Optional[List[int]] = PydField(
        default=None, description="Allowed group ids."
    )
    active: Optional[bool] = PydField(default=None, description="Is active.")
    deleted: Optional[bool] = PydField(default=None, description="Is deleted.")
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )
    stages: Optional[List[PipelineStage]] = PydField(
        default=None, description="Pipeline stages."
    )


class PipelineGetRequest(BaseSchema):
    """Request for Pipeline/Get."""

    model_config = ConfigDict(extra="forbid")

    entity_type: CrmEntityTypeEnum = PydField(..., description="Lead or Deal.")
    ids: Optional[List[int]] = PydField(default=None, description="Pipeline ids.")
    active: Optional[bool] = PydField(default=None, description="Is active.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class PipelineGetResponse(APIBaseResponse[List[Pipeline]]):
    """Response for Pipeline/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "CrmEntityTypeEnum",
    "Pipeline",
    "PipelineGetRequest",
    "PipelineGetResponse",
    "PipelineStage",
]
