"""Schemas for ConnectedIntegration endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditItem,
)
from schemas.api.rbac.user import User


class ConnectedIntegrationOwnerEnum(str, Enum):
    Global = "Global"
    Firm = "Firm"


class ConnectedIntegrationHandlerEnum(str, Enum):
    Default = "Default"
    MarketPlace = "MarketPlace"
    EPS = "EPS"
    EDO = "EDO"
    SMS = "SMS"
    TG_BOT = "TG_BOT"
    Custom = "Custom"


class IntegrationSchedule(BaseSchema):
    """Model describing connected integration schedule."""

    model_config = ConfigDict(extra="ignore")

    scheduler_uuid: Optional[str] = PydField(default=None, description="Scheduler UUID.")
    period_type: Optional[str] = PydField(default=None, description="Schedule period type.")
    period_value: Optional[int] = PydField(default=None, ge=0, description="Schedule period value.")
    last_execute: Optional[str] = PydField(default=None, description="Last execution datetime.")


class ConnectedIntegration(BaseSchema):
    """Connected integration read model."""

    model_config = ConfigDict(extra="ignore")

    key: Optional[str] = PydField(default=None, description="Integration key.")
    is_public: Optional[bool] = PydField(default=None, description="Public integration flag.")
    user_id: Optional[int] = PydField(default=None, ge=1, description="Creator user id.")
    user: Optional[User] = PydField(default=None, description="Creator user payload.")
    connected_integration_id: Optional[str] = PydField(
        default=None,
        description="Connected integration id.",
    )
    alias: Optional[str] = PydField(default=None, description="Connected integration alias.")
    owner: Optional[ConnectedIntegrationOwnerEnum] = PydField(
        default=None,
        description="Integration owner mode.",
    )
    handler: Optional[ConnectedIntegrationHandlerEnum] = PydField(
        default=None,
        description="Integration handler type.",
    )
    scheduled: Optional[bool] = PydField(default=None, description="Scheduled mode flag.")
    schedule: Optional[IntegrationSchedule] = PydField(
        default=None,
        description="Schedule payload.",
    )
    check_enabled: Optional[bool] = PydField(
        default=None,
        description="Check method availability flag.",
    )
    is_active: Optional[bool] = PydField(default=None, description="Integration active flag.")
    name: Optional[str] = PydField(default=None, description="Integration display name.")
    description: Optional[str] = PydField(default=None, description="Integration description.")
    endpoint: Optional[str] = PydField(default=None, description="Integration endpoint.")
    webhooks: Optional[List[str]] = PydField(default=None, description="Connected webhooks.")
    image_url: Optional[str] = PydField(default=None, description="Integration logo URL.")
    docs_url: Optional[str] = PydField(default=None, description="Integration docs URL.")
    version: Optional[str] = PydField(default=None, description="Integration version.")


class ConnectedIntegrationGetRequest(BaseSchema):
    """Request for ConnectedIntegration/Get."""

    model_config = ConfigDict(extra="forbid")

    keys: Optional[List[str]] = PydField(default=None, description="Integration keys.")
    connected_integration_ids: Optional[List[str]] = PydField(
        default=None,
        description="Connected integration ids.",
    )
    include_schedule: Optional[bool] = PydField(
        default=None,
        description="Include schedule payload.",
    )
    is_public: Optional[bool] = PydField(default=None, description="Public integration filter.")
    user_id: Optional[int] = PydField(default=None, ge=1, description="Creator user id filter.")
    include_name: Optional[bool] = PydField(
        default=None,
        description="Include name/description fields.",
    )
    handler: Optional[ConnectedIntegrationHandlerEnum] = PydField(
        default=None,
        description="Integration handler filter.",
    )


class ConnectedIntegrationEditRequest(BaseSchema):
    """Request for ConnectedIntegration/Edit."""

    model_config = ConfigDict(extra="forbid")

    integration_key: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Legacy integration key.",
    )
    connected_integration_id: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Connected integration id.",
    )
    is_active: Optional[bool] = PydField(default=None, description="Active state.")
    alias: Optional[str] = PydField(default=None, description="Connected integration alias.")
    settings: Optional[List[ConnectedIntegrationSettingEditItem]] = PydField(
        default=None,
        description="Connected integration settings updates.",
    )
    schedule: Optional[IntegrationSchedule] = PydField(default=None, description="Schedule settings.")
    webhooks: Optional[List[str]] = PydField(default=None, description="Connected webhooks list.")

    @model_validator(mode="after")
    def _ensure_scope(self) -> "ConnectedIntegrationEditRequest":
        has_integration_key = bool((self.integration_key or "").strip())
        has_connected_id = bool((self.connected_integration_id or "").strip())
        if not (has_integration_key or has_connected_id):
            raise ValueError(
                "One of integration_key or connected_integration_id must be provided"
            )
        return self


class ConnectedIntegrationGetResponse(
    APIBaseResponse[List[ConnectedIntegration] | dict[str, Any]]
):
    """Response for ConnectedIntegration/Get."""

    model_config = ConfigDict(extra="ignore")


class ConnectedIntegrationEditResponse(APIBaseResponse[Any]):
    """Response for ConnectedIntegration/Edit."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ConnectedIntegration",
    "ConnectedIntegrationEditRequest",
    "ConnectedIntegrationEditResponse",
    "ConnectedIntegrationGetRequest",
    "ConnectedIntegrationGetResponse",
    "ConnectedIntegrationHandlerEnum",
    "ConnectedIntegrationOwnerEnum",
    "IntegrationSchedule",
]
