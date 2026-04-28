"""Schemas for files."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders


class FileAccessLevelEnum(str, Enum):
    system = "system"
    personal = "personal"
    public = "public"


class Folder(BaseSchema):
    """Folder read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="Folder id.")
    name: Optional[str] = PydField(default=None, description="Folder name.")
    parent_id: Optional[int] = PydField(default=None, description="Parent folder id.")
    user_id: Optional[int] = PydField(default=None, description="Owner user id.")
    access_level: Optional[FileAccessLevelEnum] = PydField(
        default=None, description="Access level."
    )
    date: Optional[int] = PydField(default=None, description="Created unix time.")
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )
    deleted: Optional[bool] = PydField(default=None, description="Deleted flag.")


class File(BaseSchema):
    """File read model."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, description="File id.")
    name: Optional[str] = PydField(default=None, description="File name.")
    size: Optional[int] = PydField(default=None, description="File size in bytes.")
    extension: Optional[str] = PydField(default=None, description="File extension.")
    mime_type: Optional[str] = PydField(default=None, description="MIME type.")
    date: Optional[int] = PydField(default=None, description="Created unix time.")
    user_id: Optional[int] = PydField(default=None, description="Owner user id.")
    access_level: Optional[FileAccessLevelEnum] = PydField(
        default=None, description="Access level."
    )
    hash: Optional[str] = PydField(default=None, description="SHA-256 hash.")
    folder: Optional[Folder] = PydField(default=None, description="Folder model.")
    folder_id: Optional[int] = PydField(default=None, description="Legacy folder id.")
    url: Optional[str] = PydField(default=None, description="File URL.")
    last_update: Optional[int] = PydField(
        default=None, description="Last update unix time."
    )


class FileGetRequest(BaseSchema):
    """Request for File/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="File ids.")
    user_id: Optional[int] = PydField(default=None, description="Owner user id.")
    folder_id: Optional[int] = PydField(default=None, description="Folder id.")
    access_level: Optional[FileAccessLevelEnum] = PydField(
        default=None, description="Access level."
    )
    search: Optional[str] = PydField(default=None, description="Name search.")
    sort_orders: Optional[SortOrders] = PydField(default=None, description="Sorting.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class FileGetResponse(APIBaseResponse[List[File]]):
    """Response for File/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "File",
    "FileAccessLevelEnum",
    "FileGetRequest",
    "FileGetResponse",
    "Folder",
]
