"""Schemas for custom Field endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, AddResult, BaseSchema


class Field(BaseSchema):
    """Custom field read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="Field id.")
    key: Optional[str] = PydField(default=None, description="Field key.")
    name: Optional[str] = PydField(default=None, description="Field display name.")
    entity_type: Optional[str] = PydField(default=None, description="Entity type.")
    data_type: Optional[str] = PydField(default=None, description="Data type.")
    required: Optional[bool] = PydField(default=None, description="Required flag.")
    is_custom: Optional[bool] = PydField(default=None, description="Custom flag.")


class FieldGetRequest(BaseSchema):
    """Request for Field/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Field ids.")
    entity_type: Optional[str] = PydField(default=None, description="Entity type.")
    keys: Optional[List[str]] = PydField(default=None, description="Field keys.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class FieldAddRequest(BaseSchema):
    """Request for Field/Add."""

    model_config = ConfigDict(extra="forbid")

    key: str = PydField(..., min_length=1, description="Field key.")
    name: str = PydField(..., min_length=1, description="Field display name.")
    entity_type: str = PydField(..., min_length=1, description="Entity type.")
    data_type: str = PydField(..., min_length=1, description="Data type.")
    required: Optional[bool] = PydField(default=None, description="Required flag.")


class FieldGetResponse(APIBaseResponse[List[Field] | Dict[str, Any]]):
    """Response for Field/Get."""

    model_config = ConfigDict(extra="ignore")


class FieldAddResponse(APIBaseResponse[AddResult | Dict[str, Any]]):
    """Response for Field/Add."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Field",
    "FieldAddRequest",
    "FieldAddResponse",
    "FieldGetRequest",
    "FieldGetResponse",
]
