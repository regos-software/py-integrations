"""Schemas for chat endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.common.sort_orders import SortOrders


class ChatEntityTypeEnum(str, Enum):
    User = "User"
    ChatBot = "ChatBot"
    Client = "Client"


class ChatParticipantRoleEnum(str, Enum):
    Staff = "Staff"
    Member = "Member"
    Bot = "Bot"


class ChatLinkedEntityTypeEnum(str, Enum):
    Task = "Task"
    Lead = "Lead"
    Deal = "Deal"
    Ticket = "Ticket"


class ChatParticipant(BaseSchema):
    """Chat participant read model."""

    model_config = ConfigDict(extra="ignore")

    entity_type: Optional[ChatEntityTypeEnum] = PydField(default=None, description="Participant entity type.")
    entity_id: Optional[int] = PydField(default=None, description="Participant entity id.")
    role: Optional[ChatParticipantRoleEnum] = PydField(default=None, description="Participant role.")
    name: Optional[str] = PydField(default=None, description="Participant display name.")
    photo_url: Optional[str] = PydField(default=None, description="Participant photo URL.")
    joined_date: Optional[int] = PydField(default=None, description="Joined unix time.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")


class Chat(BaseSchema):
    """Chat read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = PydField(default=None, description="Chat UUID.")
    name: Optional[str] = PydField(default=None, description="Chat name.")
    logo_url: Optional[str] = PydField(default=None, description="Chat logo URL.")
    last_message_id: Optional[str] = PydField(default=None, description="Last message UUID.")
    last_message_date: Optional[int] = PydField(default=None, description="Last message unix time.")
    last_message_text: Optional[str] = PydField(default=None, description="Last visible message text.")
    created_user_id: Optional[int] = PydField(default=None, description="Created user id.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")
    entity_type: Optional[ChatLinkedEntityTypeEnum] = PydField(default=None, description="Linked entity type.")
    entity_id: Optional[int] = PydField(default=None, description="Linked entity id.")
    unread_count: Optional[int] = PydField(default=None, description="Unread count for current user.")
    participants: Optional[List[ChatParticipant]] = PydField(default=None, description="Chat participants.")


class ChatParticipantAddEdit(BaseSchema):
    """Participant payload for add/edit operations."""

    model_config = ConfigDict(extra="forbid")

    entity_type: ChatEntityTypeEnum = PydField(..., description="Participant entity type.")
    entity_id: int = PydField(..., ge=1, description="Participant entity id.")
    role: ChatParticipantRoleEnum = PydField(..., description="Participant role.")

    @model_validator(mode="after")
    def _validate_allowed_values(self) -> "ChatParticipantAddEdit":
        if self.entity_type == ChatEntityTypeEnum.ChatBot:
            raise ValueError("ChatBot participants must be added via Chat/AddBot")
        if self.role == ChatParticipantRoleEnum.Bot:
            raise ValueError("role=Bot is not allowed in ChatParticipantAddEdit")
        return self


class ChatParticipantRemove(BaseSchema):
    """Participant payload for remove operations."""

    model_config = ConfigDict(extra="forbid")

    entity_type: ChatEntityTypeEnum = PydField(..., description="Participant entity type.")
    entity_id: int = PydField(..., ge=1, description="Participant entity id.")


class ChatGetRequest(BaseSchema):
    """Request for Chat/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[str]] = PydField(default=None, description="Chat UUIDs.")
    participant_entity_type: Optional[ChatEntityTypeEnum] = PydField(
        default=None,
        description="Participant entity type filter.",
    )
    participant_entity_id: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Participant entity id filter.",
    )
    search: Optional[str] = PydField(default=None, description="Chat name search.")
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sort payload.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class ChatAddRequest(BaseSchema):
    """Request for Chat/Add."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = PydField(default=None, description="Chat name.")
    logo_url: Optional[str] = PydField(default=None, description="Chat logo URL.")
    participants: Optional[List[ChatParticipantAddEdit]] = PydField(
        default=None,
        description="Participants payload.",
    )


class ChatEditRequest(BaseSchema):
    """Request for Chat/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Chat UUID.")
    name: Optional[str] = PydField(default=None, description="Chat name.")
    logo_url: Optional[str] = PydField(default=None, description="Chat logo URL.")


class ChatRemoveParticipantsRequest(BaseSchema):
    """Request for Chat/RemoveParticipants."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Chat UUID.")
    participants: List[ChatParticipantRemove] = PydField(..., description="Participants to remove.")


class ChatSetParticipantsRequest(BaseSchema):
    """Request for Chat/SetParticipants."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Chat UUID.")
    participants: List[ChatParticipantAddEdit] = PydField(..., description="Participants to set.")


class ChatAddParticipantRequest(BaseSchema):
    """Request for Chat/AddParticipant."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    participant: ChatParticipantAddEdit = PydField(..., description="Participant payload.")


class ChatAddBotRequest(BaseSchema):
    """Request for Chat/AddBot."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    connected_integration_id: str = PydField(..., description="Connected integration id.")


class ChatAddResult(BaseSchema):
    """Result payload for Chat/Add."""

    model_config = ConfigDict(extra="ignore")

    new_uuid: Optional[str] = PydField(default=None, description="Created chat UUID.")


class ChatGetResponse(APIBaseResponse[List[Chat]]):
    """Response for Chat/Get."""

    model_config = ConfigDict(extra="ignore")


class ChatAddResponse(APIBaseResponse[ChatAddResult]):
    """Response for Chat/Add."""

    model_config = ConfigDict(extra="ignore")


class ChatEditResponse(APIBaseResponse[ArrayResult]):
    """Response for Chat/Edit."""

    model_config = ConfigDict(extra="ignore")


class ChatRemoveParticipantsResponse(APIBaseResponse[ArrayResult]):
    """Response for Chat/RemoveParticipants."""

    model_config = ConfigDict(extra="ignore")


class ChatSetParticipantsResponse(APIBaseResponse[ArrayResult]):
    """Response for Chat/SetParticipants."""

    model_config = ConfigDict(extra="ignore")


class ChatAddParticipantResponse(APIBaseResponse[ArrayResult]):
    """Response for Chat/AddParticipant."""

    model_config = ConfigDict(extra="ignore")


class ChatAddBotResponse(APIBaseResponse[ArrayResult]):
    """Response for Chat/AddBot."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "Chat",
    "ChatAddBotRequest",
    "ChatAddBotResponse",
    "ChatAddParticipantRequest",
    "ChatAddParticipantResponse",
    "ChatAddRequest",
    "ChatAddResponse",
    "ChatEditRequest",
    "ChatEditResponse",
    "ChatEntityTypeEnum",
    "ChatGetRequest",
    "ChatGetResponse",
    "ChatLinkedEntityTypeEnum",
    "ChatParticipant",
    "ChatParticipantAddEdit",
    "ChatParticipantRemove",
    "ChatParticipantRoleEnum",
    "ChatRemoveParticipantsRequest",
    "ChatRemoveParticipantsResponse",
    "ChatSetParticipantsRequest",
    "ChatSetParticipantsResponse",
]
