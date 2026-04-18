"""Schemas for chat messages."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema


class ChatMessageTypeEnum(str, Enum):
    Regular = "Regular"
    System = "System"
    Private = "Private"


class ChatMessage(BaseSchema):
    """Chat message read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = PydField(default=None, description="Message UUID.")
    chat_id: Optional[str] = PydField(default=None, description="Chat UUID.")
    reply_id: Optional[str] = PydField(
        default=None, description="Reply-to message UUID."
    )
    replay_text: Optional[str] = PydField(
        default=None, description="Reply-to message text snapshot."
    )
    author_entity_type: Optional[str] = PydField(
        default=None, description="Author entity type."
    )
    author_entity_id: Optional[int] = PydField(
        default=None, description="Author entity id."
    )
    author_role: Optional[str] = PydField(
        default=None, description="Author role in chat."
    )
    author_entity_name: Optional[str] = PydField(
        default=None, description="Author display name."
    )
    author_entity_photo: Optional[str] = PydField(
        default=None, description="Author photo URL."
    )
    message_type: Optional[ChatMessageTypeEnum] = PydField(
        default=None, description="Message type."
    )
    text: Optional[str] = PydField(default=None, description="Message text.")
    file_ids: Optional[List[int]] = PydField(
        default=None, description="Attached file ids."
    )
    action_code: Optional[str] = PydField(default=None, description="System action.")
    action_payload: Optional[str] = PydField(
        default=None, description="System action payload."
    )
    event_id: Optional[str] = PydField(default=None, description="Event id.")
    external_message_id: Optional[str] = PydField(
        default=None, description="External message id."
    )
    edited: Optional[bool] = PydField(default=None, description="Edited flag.")
    read: Optional[bool] = PydField(default=None, description="Read flag.")
    deleted: Optional[bool] = PydField(default=None, description="Deleted flag.")
    created_date: Optional[int] = PydField(
        default=None, description="Created unix time."
    )
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )


class ChatMessageGetRequest(BaseSchema):
    """Request for ChatMessage/Get."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    ids: Optional[List[str]] = PydField(default=None, description="Message UUIDs.")
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")
    include_staff_private: Optional[bool] = PydField(
        default=None, description="Include private messages for staff."
    )


class ChatMessageAddRequest(BaseSchema):
    """Request for ChatMessage/Add."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    reply_id: Optional[str] = PydField(
        default=None, description="Reply-to message UUID."
    )
    replay_text: Optional[str] = PydField(
        default=None, description="Reply-to message text snapshot."
    )
    author_entity_type: Optional[str] = PydField(
        default=None, description="Optional explicit author entity type."
    )
    author_entity_id: Optional[int] = PydField(
        default=None, description="Optional explicit author entity id."
    )
    message_type: Optional[ChatMessageTypeEnum] = PydField(
        default=None, description="Regular or Private."
    )
    text: Optional[str] = PydField(default=None, description="Message text.")
    file_ids: Optional[List[int]] = PydField(default=None, description="File ids.")
    event_id: Optional[str] = PydField(default=None, description="Event id.")
    external_message_id: Optional[str] = PydField(
        default=None, description="External message id."
    )


class ChatMessageAddResult(BaseSchema):
    """Result payload for ChatMessage/Add."""

    model_config = ConfigDict(extra="ignore")

    new_uuid: Optional[str] = PydField(default=None, description="Message UUID.")


class ChatMessageAddResponse(APIBaseResponse[ChatMessageAddResult]):
    """Response for ChatMessage/Add."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageAddFileRequest(BaseSchema):
    """Request for ChatMessage/AddFile in JSON/base64 mode."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    name: str = PydField(..., description="File display name.")
    extension: str = PydField(..., description="File extension without dot.")
    data: str = PydField(..., description="Base64 file payload.")


class ChatMessageAddFileResult(BaseSchema):
    """Result payload for ChatMessage/AddFile."""

    model_config = ConfigDict(extra="ignore")

    file_id: Optional[int] = PydField(default=None, description="Created file id.")


class ChatMessageAddFileResponse(APIBaseResponse[ChatMessageAddFileResult]):
    """Response for ChatMessage/AddFile."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageMarkSentRequest(BaseSchema):
    """Request for ChatMessage/MarkSent."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Message UUID.")
    external_message_id: str = PydField(..., description="External message id.")


class ChatMessageMarkSentResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/MarkSent."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageMarkReadRequest(BaseSchema):
    """Request for ChatMessage/MarkRead."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")


class ChatMessageMarkReadResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/MarkRead."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageGetResponse(APIBaseResponse[List[ChatMessage]]):
    """Response for ChatMessage/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ChatMessage",
    "ChatMessageAddFileRequest",
    "ChatMessageAddFileResponse",
    "ChatMessageAddRequest",
    "ChatMessageAddResponse",
    "ChatMessageGetRequest",
    "ChatMessageGetResponse",
    "ChatMessageMarkReadRequest",
    "ChatMessageMarkReadResponse",
    "ChatMessageMarkSentRequest",
    "ChatMessageMarkSentResponse",
    "ChatMessageTypeEnum",
]
