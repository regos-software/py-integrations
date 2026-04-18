"""Schemas for CRM clients."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema
from schemas.api.common.filters import Filter
from schemas.api.references.fields import FieldValue, FieldValueAdd, FieldValueEdit


class Client(BaseSchema):
    """CRM client model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Client id.")
    external_id: Optional[str] = PydField(default=None, description="External client id.")
    telegram_id: Optional[str] = PydField(default=None, description="Telegram id.")
    whatsapp_id: Optional[str] = PydField(default=None, description="WhatsApp id.")
    instagram_id: Optional[str] = PydField(default=None, description="Instagram id.")
    facebook_id: Optional[str] = PydField(default=None, description="Facebook id.")
    vk_id: Optional[str] = PydField(default=None, description="VK id.")
    name: Optional[str] = PydField(default=None, description="Client name.")
    phone: Optional[str] = PydField(default=None, description="Client phone.")
    email: Optional[str] = PydField(default=None, description="Client email.")
    photo_url: Optional[str] = PydField(default=None, description="Avatar URL.")
    description: Optional[str] = PydField(default=None, description="Description.")
    responsible_user_id: Optional[int] = PydField(
        default=None, description="Responsible user id."
    )
    deleted: Optional[bool] = PydField(default=None, description="Deleted flag.")
    created_user_id: Optional[int] = PydField(
        default=None, description="Created user id."
    )
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )
    fields: Optional[List[FieldValue]] = PydField(
        default=None, description="Custom fields."
    )


class ClientGetRequest(BaseSchema):
    """Request for Client/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Client ids.")
    phones: Optional[List[str]] = PydField(default=None, description="Client phones.")
    external_ids: Optional[List[str]] = PydField(
        default=None, description="External ids."
    )
    telegram_ids: Optional[List[str]] = PydField(
        default=None, description="Telegram ids."
    )
    whatsapp_ids: Optional[List[str]] = PydField(
        default=None, description="WhatsApp ids."
    )
    instagram_ids: Optional[List[str]] = PydField(
        default=None, description="Instagram ids."
    )
    facebook_ids: Optional[List[str]] = PydField(
        default=None, description="Facebook ids."
    )
    vk_ids: Optional[List[str]] = PydField(default=None, description="VK ids.")
    emails: Optional[List[str]] = PydField(default=None, description="Client emails.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    responsible_user_ids: Optional[List[int]] = PydField(
        default=None, description="Responsible user ids."
    )
    filters: Optional[List[Filter]] = PydField(
        default=None, description="Additional filters."
    )
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class ClientAddRequest(BaseSchema):
    """Request for Client/Add."""

    model_config = ConfigDict(extra="forbid")

    external_id: Optional[str] = PydField(default=None, description="External client id.")
    telegram_id: Optional[str] = PydField(default=None, description="Telegram id.")
    whatsapp_id: Optional[str] = PydField(default=None, description="WhatsApp id.")
    instagram_id: Optional[str] = PydField(default=None, description="Instagram id.")
    facebook_id: Optional[str] = PydField(default=None, description="Facebook id.")
    vk_id: Optional[str] = PydField(default=None, description="VK id.")
    name: Optional[str] = PydField(default=None, description="Client name.")
    phone: Optional[str] = PydField(default=None, description="Client phone.")
    email: Optional[str] = PydField(default=None, description="Client email.")
    photo_url: Optional[str] = PydField(default=None, description="Avatar URL.")
    description: Optional[str] = PydField(default=None, description="Description.")
    responsible_user_id: Optional[int] = PydField(
        default=None, ge=1, description="Responsible user id."
    )
    fields: Optional[List[FieldValueAdd]] = PydField(
        default=None, description="Custom field values."
    )

    @model_validator(mode="after")
    def _validate_identifiers(self) -> "ClientAddRequest":
        identifiers = (
            self.external_id,
            self.telegram_id,
            self.whatsapp_id,
            self.instagram_id,
            self.facebook_id,
            self.vk_id,
            self.phone,
            self.email,
        )
        if any(str(value or "").strip() for value in identifiers):
            return self
        raise ValueError(
            "At least one identifier is required: external_id/telegram_id/"
            "whatsapp_id/instagram_id/facebook_id/vk_id/phone/email"
        )


class ClientEditRequest(BaseSchema):
    """Request for Client/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Client id.")
    external_id: Optional[str] = PydField(default=None, description="External client id.")
    telegram_id: Optional[str] = PydField(default=None, description="Telegram id.")
    whatsapp_id: Optional[str] = PydField(default=None, description="WhatsApp id.")
    instagram_id: Optional[str] = PydField(default=None, description="Instagram id.")
    facebook_id: Optional[str] = PydField(default=None, description="Facebook id.")
    vk_id: Optional[str] = PydField(default=None, description="VK id.")
    name: Optional[str] = PydField(default=None, description="Client name.")
    phone: Optional[str] = PydField(default=None, description="Client phone.")
    email: Optional[str] = PydField(default=None, description="Client email.")
    photo_url: Optional[str] = PydField(default=None, description="Avatar URL.")
    description: Optional[str] = PydField(default=None, description="Description.")
    responsible_user_id: Optional[int] = PydField(
        default=None, ge=1, description="Responsible user id."
    )
    fields: Optional[List[FieldValueEdit]] = PydField(
        default=None, description="Custom field changes."
    )


class ClientDeleteRequest(BaseSchema):
    """Request for Client/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Client id.")


class ClientSetResponsibleRequest(BaseSchema):
    """Request for Client/SetResponsible."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Client id.")
    responsible_user_id: int = PydField(..., ge=1, description="Responsible user id.")


class ClientMergeRequest(BaseSchema):
    """Request for Client/Merge."""

    model_config = ConfigDict(extra="forbid")

    source_client_id: int = PydField(..., ge=1, description="Source client id.")
    target_client_id: int = PydField(..., ge=1, description="Target client id.")
    comment: Optional[str] = PydField(default=None, description="Merge comment.")


class ClientGetResponse(APIBaseResponse[List[Client]]):
    """Response for Client/Get."""

    model_config = ConfigDict(extra="ignore")


class ClientAddResponse(APIBaseResponse[AddResult]):
    """Response for Client/Add."""

    model_config = ConfigDict(extra="ignore")


class ClientEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Client/Edit."""

    model_config = ConfigDict(extra="ignore")


class ClientDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for Client/Delete."""

    model_config = ConfigDict(extra="ignore")


class ClientSetResponsibleResponse(APIBaseResponse[ArrayResult]):
    """Response for Client/SetResponsible."""

    model_config = ConfigDict(extra="ignore")


class ClientMergeResponse(APIBaseResponse[ArrayResult]):
    """Response for Client/Merge."""

    model_config = ConfigDict(extra="ignore")

__all__ = [
    "Client",
    "ClientAddRequest",
    "ClientAddResponse",
    "ClientDeleteRequest",
    "ClientDeleteResponse",
    "ClientEditRequest",
    "ClientEditResponse",
    "ClientGetRequest",
    "ClientGetResponse",
    "ClientMergeRequest",
    "ClientMergeResponse",
    "ClientSetResponsibleRequest",
    "ClientSetResponsibleResponse",
]
