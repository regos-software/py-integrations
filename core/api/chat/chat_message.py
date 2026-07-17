"""REGOS API service for ChatMessage."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChatMessageService(RegosAPIService):
    PATH_GET = "ChatMessage/Get"
    PATH_GET_FILES = "ChatMessage/GetFiles"
    PATH_ADD = "ChatMessage/Add"
    PATH_ADD_FILE = "ChatMessage/AddFile"
    PATH_EDIT = "ChatMessage/Edit"
    PATH_DELETE = "ChatMessage/Delete"
    PATH_MARK_READ = "ChatMessage/MarkRead"
    PATH_MARK_SENT = "ChatMessage/MarkSent"
    PATH_WRITING = "ChatMessage/Writing"
    PATH_SUGGEST = "ChatMessage/Suggest"
    PATH_SEARCH = "ChatMessage/Search"
    PATH_SET_PINNED = "ChatMessage/SetPinned"
    PATH_GET_PINNED = "ChatMessage/GetPinned"
    PATH_GET_AROUND = "ChatMessage/GetAround"
    PATH_SET_REACTION = "ChatMessage/SetReaction"
    PATH_CALLBACK = "ChatMessage/Callback"
    PATH_GET_REACTIONS = "ChatMessage/GetReactions"
    PATH_GET_READ_USERS = "ChatMessage/GetReadUsers"
    REQUEST_MODELS = {
        'add': models.ChatMessageAdd,
        'callback': models.ChatMessageCallback,
        'delete': models.ChatMessageDelete,
        'edit': models.ChatMessageEdit,
        'get': models.ChatMessageGet,
        'get_around': models.ChatMessageGetAround,
        'get_files': models.ChatMessageGetFiles,
        'get_pinned': models.ChatMessageGetPinned,
        'get_reactions': models.ChatMessageGetReactions,
        'get_read_users': models.ChatMessageGetReadUsers,
        'mark_read': models.ChatMessageMarkRead,
        'mark_sent': models.ChatMessageMarkSent,
        'search': models.ChatMessageSearch,
        'set_pinned': models.ChatMessageSetPinned,
        'set_reaction': models.ChatMessageSetReaction,
        'suggest': models.ChatMessageSuggest,
        'writing': models.ChatMessageWriting,
    }

    async def get(self, req: models.ChatMessageGet | dict[str, Any]) -> models.ChatMessageRegosOffsettedArrayResult:
        """POST ChatMessage/Get."""
        return await self._call(self.PATH_GET, req, models.ChatMessageRegosOffsettedArrayResult)

    async def get_files(self, req: models.ChatMessageGetFiles | dict[str, Any]) -> models.ChatMessageFileRegosOffsettedArrayResult:
        """POST ChatMessage/GetFiles."""
        return await self._call(self.PATH_GET_FILES, req, models.ChatMessageFileRegosOffsettedArrayResult)

    async def add(self, req: models.ChatMessageAdd | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST ChatMessage/Add."""
        return await self._call(self.PATH_ADD, req, models.Insert_uuid_Result)

    async def add_file(self, body: dict[str, Any] | None = None) -> models.ChatMessageAddFileResultRegosObjectResult:
        """POST ChatMessage/AddFile."""
        return await self._call(self.PATH_ADD_FILE, body or {}, models.ChatMessageAddFileResultRegosObjectResult)

    async def edit(self, req: models.ChatMessageEdit | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def delete(self, req: models.ChatMessageDelete | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

    async def mark_read(self, req: models.ChatMessageMarkRead | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/MarkRead."""
        return await self._call(self.PATH_MARK_READ, req, models.UpdateResult)

    async def mark_sent(self, req: models.ChatMessageMarkSent | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/MarkSent."""
        return await self._call(self.PATH_MARK_SENT, req, models.UpdateResult)

    async def writing(self, req: models.ChatMessageWriting | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/Writing."""
        return await self._call(self.PATH_WRITING, req, models.UpdateResult)

    async def suggest(self, req: models.ChatMessageSuggest | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/Suggest."""
        return await self._call(self.PATH_SUGGEST, req, models.UpdateResult)

    async def search(self, req: models.ChatMessageSearch | dict[str, Any]) -> models.ChatMessageRegosOffsettedArrayResult:
        """POST ChatMessage/Search."""
        return await self._call(self.PATH_SEARCH, req, models.ChatMessageRegosOffsettedArrayResult)

    async def set_pinned(self, req: models.ChatMessageSetPinned | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/SetPinned."""
        return await self._call(self.PATH_SET_PINNED, req, models.UpdateResult)

    async def get_pinned(self, req: models.ChatMessageGetPinned | dict[str, Any]) -> models.ChatMessageRegosOffsettedArrayResult:
        """POST ChatMessage/GetPinned."""
        return await self._call(self.PATH_GET_PINNED, req, models.ChatMessageRegosOffsettedArrayResult)

    async def get_around(self, req: models.ChatMessageGetAround | dict[str, Any]) -> models.ChatMessageRegosArrayResult:
        """POST ChatMessage/GetAround."""
        return await self._call(self.PATH_GET_AROUND, req, models.ChatMessageRegosArrayResult)

    async def set_reaction(self, req: models.ChatMessageSetReaction | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/SetReaction."""
        return await self._call(self.PATH_SET_REACTION, req, models.UpdateResult)

    async def callback(self, req: models.ChatMessageCallback | dict[str, Any]) -> models.UpdateResult:
        """POST ChatMessage/Callback."""
        return await self._call(self.PATH_CALLBACK, req, models.UpdateResult)

    async def get_reactions(self, req: models.ChatMessageGetReactions | dict[str, Any]) -> models.ChatMessageReactionUserRegosOffsettedArrayResult:
        """POST ChatMessage/GetReactions."""
        return await self._call(self.PATH_GET_REACTIONS, req, models.ChatMessageReactionUserRegosOffsettedArrayResult)

    async def get_read_users(self, req: models.ChatMessageGetReadUsers | dict[str, Any]) -> models.ChatMessageReadUserRegosOffsettedArrayResult:
        """POST ChatMessage/GetReadUsers."""
        return await self._call(self.PATH_GET_READ_USERS, req, models.ChatMessageReadUserRegosOffsettedArrayResult)

__all__ = ['ChatMessageService']
