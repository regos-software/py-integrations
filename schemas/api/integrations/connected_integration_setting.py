"""Schemas for connected integration settings."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, RootModel, model_validator

from schemas.api.base import BaseSchema


class ConnectedIntegrationSetting(BaseSchema):
    """Read model for an integration setting."""

    model_config = ConfigDict(extra="ignore")

    key: Optional[str] = PydField(default=None, description="Setting key.")
    value: Optional[str] = PydField(default=None, description="Setting value.")
    last_update: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Last update timestamp (unix time).",
    )


class ConnectedIntegrationSettingRequest(BaseSchema):
    """Request for ConnectedIntegrationSetting/Get."""

    model_config = ConfigDict(extra="forbid")

    integration_key: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Legacy integration key.",
    )
    connected_integration_id: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Connected integration ID.",
    )
    firm_id: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Firm ID filter.",
    )

    @model_validator(mode="after")
    def _ensure_scope(self) -> "ConnectedIntegrationSettingRequest":
        has_integration_key = bool((self.integration_key or "").strip())
        has_connected_id = bool((self.connected_integration_id or "").strip())
        if not (has_integration_key or has_connected_id):
            raise ValueError(
                "One of integration_key or connected_integration_id must be provided"
            )
        return self


class ConnectedIntegrationSettingEditItem(BaseSchema):
    """Single item for ConnectedIntegrationSetting/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = PydField(default=None, ge=1, description="Setting ID.")
    key: Optional[str] = PydField(default=None, description="Setting key.")
    value: Optional[str] = PydField(default=None, description="New setting value.")
    integration_key: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Legacy integration key.",
    )
    connected_integration_id: Optional[str] = PydField(
        default=None,
        min_length=1,
        description="Connected integration ID.",
    )
    firm_id: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Firm ID filter.",
    )

    @model_validator(mode="after")
    def _ensure_scope(self) -> "ConnectedIntegrationSettingEditItem":
        has_integration_key = bool((self.integration_key or "").strip())
        has_connected_id = bool((self.connected_integration_id or "").strip())
        if not (has_integration_key or has_connected_id):
            raise ValueError(
                "One of integration_key or connected_integration_id must be provided"
            )
        return self


class ConnectedIntegrationSettingEditRequest(
    RootModel[List[ConnectedIntegrationSettingEditItem]]
):
    """Batch edit request (root=list)."""


__all__ = [
    "ConnectedIntegrationSetting",
    "ConnectedIntegrationSettingEditItem",
    "ConnectedIntegrationSettingEditRequest",
    "ConnectedIntegrationSettingRequest",
]
