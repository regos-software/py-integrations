"""Schemas for CRM project task endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.references.fields import FieldValue, FieldValueEdit


class ProjectTask(BaseSchema):
    """Project task read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="Task id.")
    title: Optional[str] = PydField(default=None, description="Task title.")
    description: Optional[str] = PydField(default=None, description="Task description.")
    responsible_user_id: Optional[int] = PydField(default=None, ge=1, description="Responsible user id.")
    status_id: Optional[int] = PydField(default=None, ge=1, description="Status id.")
    due_date: Optional[int] = PydField(default=None, description="Due unix time.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")
    fields: Optional[List[FieldValue]] = PydField(default=None, description="Custom fields.")


class ProjectTaskGetRequest(BaseSchema):
    """Request for ProjectTask/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Task ids.")
    responsible_user_ids: Optional[List[int]] = PydField(default=None, description="Responsible user ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    filters: Optional[List[Filter]] = PydField(default=None, description="Additional filters.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class ProjectTaskEditRequest(BaseSchema):
    """Request for ProjectTask/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Task id.")
    fields: Optional[List[FieldValueEdit]] = PydField(default=None, description="Custom field changes.")


class ProjectTaskGetResponse(APIBaseResponse[List[ProjectTask] | Dict[str, Any]]):
    """Response for ProjectTask/Get."""

    model_config = ConfigDict(extra="ignore")


class ProjectTaskEditResponse(APIBaseResponse[ArrayResult | Dict[str, Any]]):
    """Response for ProjectTask/Edit."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ProjectTask",
    "ProjectTaskEditRequest",
    "ProjectTaskEditResponse",
    "ProjectTaskGetRequest",
    "ProjectTaskGetResponse",
]
