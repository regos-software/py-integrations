"""Schemas for chat quick replies."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import APIBaseResponse, AddResult, ArrayResult, BaseSchema


class QuickReply(BaseSchema):
    """Quick reply read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="Quick reply id.")
    text: Optional[str] = PydField(default=None, description="Quick reply text.")
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Last update unix time."
    )


class QuickReplyGetRequest(BaseSchema):
    """Request for QuickReply/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Quick reply ids.")
    search: Optional[str] = PydField(default=None, description="Text search.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class QuickReplyAddRequest(BaseSchema):
    """Request for QuickReply/Add."""

    model_config = ConfigDict(extra="forbid")

    text: str = PydField(..., min_length=1, max_length=200, description="Reply text.")

    @field_validator("text", mode="before")
    @classmethod
    def _normalize_text(cls, value: str) -> str:
        return str(value or "").strip()


class QuickReplyDeleteRequest(BaseSchema):
    """Request for QuickReply/Delete."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Quick reply id.")


class QuickReplyGetResponse(APIBaseResponse[List[QuickReply]]):
    """Response for QuickReply/Get."""

    model_config = ConfigDict(extra="ignore")


class QuickReplyAddResponse(APIBaseResponse[AddResult]):
    """Response for QuickReply/Add."""

    model_config = ConfigDict(extra="ignore")


class QuickReplyDeleteResponse(APIBaseResponse[ArrayResult]):
    """Response for QuickReply/Delete."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "QuickReply",
    "QuickReplyAddRequest",
    "QuickReplyAddResponse",
    "QuickReplyDeleteRequest",
    "QuickReplyDeleteResponse",
    "QuickReplyGetRequest",
    "QuickReplyGetResponse",
]
