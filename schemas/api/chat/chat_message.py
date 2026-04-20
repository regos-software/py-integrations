"""Schemas for chat message endpoints."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator, model_validator

from schemas.api.base import APIBaseResponse, ArrayResult, BaseSchema
from schemas.api.chat.chat import ChatEntityTypeEnum


class ChatMessageTypeEnum(str, Enum):
    Regular = "Regular"
    System = "System"
    Private = "Private"


class ChatMessage(BaseSchema):
    """Chat message read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = PydField(default=None, description="Message UUID.")
    chat_id: Optional[str] = PydField(default=None, description="Chat UUID.")
    reply_id: Optional[str] = PydField(default=None, description="Reply-to message UUID.")
    replay_text: Optional[str] = PydField(default=None, description="Reply-to message text snapshot.")
    author_entity_type: Optional[ChatEntityTypeEnum] = PydField(default=None, description="Author entity type.")
    author_entity_id: Optional[int] = PydField(default=None, description="Author entity id.")
    author_role: Optional[str] = PydField(default=None, description="Author role in chat.")
    author_entity_name: Optional[str] = PydField(default=None, description="Author display name.")
    author_entity_photo: Optional[str] = PydField(default=None, description="Author photo URL.")
    message_type: Optional[ChatMessageTypeEnum] = PydField(default=None, description="Message type.")
    text: Optional[str] = PydField(default=None, description="Message text.")
    file_ids: Optional[List[int]] = PydField(default=None, description="Attached file ids.")
    action_code: Optional[str] = PydField(default=None, description="System action code.")
    action_payload: Optional[str] = PydField(default=None, description="System action payload JSON.")
    event_id: Optional[str] = PydField(default=None, description="Event id.")
    external_message_id: Optional[str] = PydField(default=None, description="External message id.")
    edited: Optional[bool] = PydField(default=None, description="Edited flag.")
    read: Optional[bool] = PydField(default=None, description="Read flag for current user.")
    created_date: Optional[int] = PydField(default=None, description="Created unix time.")
    last_update: Optional[int] = PydField(default=None, description="Last update unix time.")

    # Compatibility flag that can still appear in old payloads.
    deleted: Optional[bool] = PydField(default=None, description="Legacy deleted flag.")


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
        default=None,
        description="Include private/staff messages where allowed.",
    )


class ChatMessageAddRequest(BaseSchema):
    """Request for ChatMessage/Add."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    reply_id: Optional[str] = PydField(default=None, description="Reply-to message UUID.")
    replay_text: Optional[str] = PydField(default=None, description="Reply-to message text snapshot.")
    author_entity_type: Optional[ChatEntityTypeEnum] = PydField(
        default=None,
        description="Optional explicit author entity type.",
    )
    author_entity_id: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Optional explicit author entity id.",
    )
    message_type: Optional[ChatMessageTypeEnum] = PydField(default=None, description="Message type.")
    text: Optional[str] = PydField(default=None, description="Message text.")
    file_ids: Optional[List[int]] = PydField(default=None, description="Attached file ids.")
    event_id: Optional[str] = PydField(default=None, description="Legacy event id (ignored by server).")
    external_message_id: Optional[str] = PydField(default=None, description="External message id.")

    @model_validator(mode="after")
    def _validate_payload(self) -> "ChatMessageAddRequest":
        if (self.author_entity_type is None) != (self.author_entity_id is None):
            raise ValueError("author_entity_type and author_entity_id must be provided together")

        has_text = bool(str(self.text or "").strip())
        has_files = bool(self.file_ids)
        if not has_text and not has_files:
            raise ValueError("At least one of text or file_ids is required")
        return self


class ChatMessageDeleteRequest(BaseSchema):
    """Request for ChatMessage/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Message UUID.")


class ChatMessageEditRequest(BaseSchema):
    """Request for ChatMessage/Edit."""

    model_config = ConfigDict(extra="forbid")

    id: str = PydField(..., description="Message UUID.")
    text: Optional[str] = PydField(default=None, description="Message text.")
    file_ids: Optional[List[int]] = PydField(default=None, description="Attached file ids.")

    @model_validator(mode="after")
    def _validate_payload(self) -> "ChatMessageEditRequest":
        if self.text is None and self.file_ids is None:
            raise ValueError("At least one of text or file_ids must be provided")
        return self


class ChatMessageSearchRequest(BaseSchema):
    """Request for ChatMessage/Search."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    query: str = PydField(..., description="Search query.")
    from_date: Optional[int] = PydField(default=None, description="From unix time.")
    to_date: Optional[int] = PydField(default=None, description="To unix time.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")
    include_staff_private: Optional[bool] = PydField(
        default=None,
        description="Include private/staff messages where allowed.",
    )


class ChatMessageWritingRequest(BaseSchema):
    """Request for ChatMessage/Writing."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    author_entity_type: Optional[ChatEntityTypeEnum] = PydField(
        default=None,
        description="Author entity type.",
    )
    author_entity_id: Optional[int] = PydField(default=None, ge=1, description="Author entity id.")

    @model_validator(mode="after")
    def _validate_pair(self) -> "ChatMessageWritingRequest":
        if (self.author_entity_type is None) != (self.author_entity_id is None):
            raise ValueError("author_entity_type and author_entity_id must be provided together")
        return self


class ChatMessageSuggestRequest(BaseSchema):
    """Request for ChatMessage/Suggest."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")
    author_entity_type: ChatEntityTypeEnum = PydField(..., description="Suggestion author entity type.")
    author_entity_id: int = PydField(..., ge=1, description="Suggestion author entity id.")
    suggestions: List[str] = PydField(..., description="Quick reply suggestions.")
    source_message_id: Optional[str] = PydField(default=None, description="Source message UUID.")

    @field_validator("suggestions", mode="before")
    @classmethod
    def _normalize_suggestions(cls, value: object) -> List[str]:
        raw = list(value or []) if isinstance(value, list) else []
        normalized: list[str] = []
        seen: set[str] = set()
        for item in raw:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            if len(text) > 200:
                raise ValueError("Each suggestion must be 200 characters or less")
            seen.add(text)
            normalized.append(text)
        if not (1 <= len(normalized) <= 5):
            raise ValueError("suggestions must contain from 1 to 5 unique non-empty values")
        return normalized

    @model_validator(mode="after")
    def _validate_author(self) -> "ChatMessageSuggestRequest":
        if self.author_entity_type != ChatEntityTypeEnum.ChatBot:
            raise ValueError("author_entity_type must be ChatBot for suggest")
        return self


class ChatMessageAddResult(BaseSchema):
    """Result payload for ChatMessage/Add."""

    model_config = ConfigDict(extra="ignore")

    new_uuid: Optional[str] = PydField(default=None, description="Created message UUID.")


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


class ChatMessageMarkReadRequest(BaseSchema):
    """Request for ChatMessage/MarkRead."""

    model_config = ConfigDict(extra="forbid")

    chat_id: str = PydField(..., description="Chat UUID.")


class ChatMessageGetResponse(APIBaseResponse[List[ChatMessage]]):
    """Response for ChatMessage/Get."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageSearchResponse(APIBaseResponse[List[ChatMessage]]):
    """Response for ChatMessage/Search."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/Delete."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageEditResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/Edit."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageMarkSentResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/MarkSent."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageMarkReadResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/MarkRead."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageWritingResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/Writing."""

    model_config = ConfigDict(extra="ignore")


class ChatMessageSuggestResponse(APIBaseResponse[ArrayResult]):
    """Response for ChatMessage/Suggest."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "ChatMessage",
    "ChatMessageAddFileRequest",
    "ChatMessageAddFileResponse",
    "ChatMessageAddRequest",
    "ChatMessageAddResponse",
    "ChatMessageDeleteRequest",
    "ChatMessageDeleteResponse",
    "ChatMessageEditRequest",
    "ChatMessageEditResponse",
    "ChatMessageGetRequest",
    "ChatMessageGetResponse",
    "ChatMessageMarkReadRequest",
    "ChatMessageMarkReadResponse",
    "ChatMessageMarkSentRequest",
    "ChatMessageMarkSentResponse",
    "ChatMessageSearchRequest",
    "ChatMessageSearchResponse",
    "ChatMessageSuggestRequest",
    "ChatMessageSuggestResponse",
    "ChatMessageTypeEnum",
    "ChatMessageWritingRequest",
    "ChatMessageWritingResponse",
]
