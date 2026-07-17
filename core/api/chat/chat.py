"""REGOS API service for Chat."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class ChatService(RegosAPIService):
    PATH_GET = "Chat/Get"
    PATH_ADD = "Chat/Add"
    PATH_EDIT = "Chat/Edit"
    PATH_SET_PARTICIPANTS = "Chat/SetParticipants"
    PATH_REMOVE_PARTICIPANTS = "Chat/RemoveParticipants"
    PATH_LEAVE = "Chat/Leave"
    PATH_JOIN = "Chat/Join"
    PATH_ADD_PARTICIPANT = "Chat/AddParticipant"
    PATH_ADD_BOT = "Chat/AddBot"
    PATH_GET_UNREAD_COUNT = "Chat/GetUnreadCount"
    PATH_GET_UNREAD_COUNTS = "Chat/GetUnreadCounts"
    PATH_GET_USER_PRESENCE = "Chat/GetUserPresence"
    PATH_SET_MUTED = "Chat/SetMuted"
    PATH_SET_ARCHIVED = "Chat/SetArchived"
    PATH_SET_PINNED = "Chat/SetPinned"
    PATH_GET_AVAILABLE_REACTIONS = "Chat/GetAvailableReactions"
    PATH_SET_AVAILABLE_REACTIONS = "Chat/SetAvailableReactions"
    REQUEST_MODELS = {
        'add': models.ChatAdd,
        'add_bot': models.ChatAddBot,
        'add_participant': models.ChatAddParticipant,
        'edit': models.ChatEdit,
        'get': models.ChatGet,
        'get_available_reactions': models.ChatGetAvailableReactions,
        'get_unread_counts': models.ChatUnreadCountsGet,
        'get_user_presence': models.ChatUserPresenceGet,
        'join': models.ChatJoin,
        'leave': models.ChatLeave,
        'remove_participants': models.ChatRemoveParticipants,
        'set_archived': models.ChatSetArchived,
        'set_available_reactions': models.ChatSetAvailableReactions,
        'set_muted': models.ChatSetMuted,
        'set_participants': models.ChatSetParticipants,
        'set_pinned': models.ChatSetPinned,
    }

    async def get(self, req: models.ChatGet | dict[str, Any]) -> models.ChatRegosOffsettedArrayResult:
        """POST Chat/Get."""
        return await self._call(self.PATH_GET, req, models.ChatRegosOffsettedArrayResult)

    async def add(self, req: models.ChatAdd | dict[str, Any]) -> models.Insert_uuid_Result:
        """POST Chat/Add."""
        return await self._call(self.PATH_ADD, req, models.Insert_uuid_Result)

    async def edit(self, req: models.ChatEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def set_participants(self, req: models.ChatSetParticipants | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/SetParticipants."""
        return await self._call(self.PATH_SET_PARTICIPANTS, req, models.UpdateResult)

    async def remove_participants(self, req: models.ChatRemoveParticipants | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/RemoveParticipants."""
        return await self._call(self.PATH_REMOVE_PARTICIPANTS, req, models.UpdateResult)

    async def leave(self, req: models.ChatLeave | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/Leave."""
        return await self._call(self.PATH_LEAVE, req, models.UpdateResult)

    async def join(self, req: models.ChatJoin | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/Join."""
        return await self._call(self.PATH_JOIN, req, models.UpdateResult)

    async def add_participant(self, req: models.ChatAddParticipant | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/AddParticipant."""
        return await self._call(self.PATH_ADD_PARTICIPANT, req, models.UpdateResult)

    async def add_bot(self, req: models.ChatAddBot | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/AddBot."""
        return await self._call(self.PATH_ADD_BOT, req, models.UpdateResult)

    async def get_unread_count(self, body: dict[str, Any] | None = None) -> models.ChatUnreadCountRegosObjectResult:
        """POST Chat/GetUnreadCount."""
        return await self._call(self.PATH_GET_UNREAD_COUNT, body or {}, models.ChatUnreadCountRegosObjectResult)

    async def get_unread_counts(self, req: models.ChatUnreadCountsGet | dict[str, Any]) -> models.ChatUnreadCountByKeyRegosArrayResult:
        """POST Chat/GetUnreadCounts."""
        return await self._call(self.PATH_GET_UNREAD_COUNTS, req, models.ChatUnreadCountByKeyRegosArrayResult)

    async def get_user_presence(self, req: models.ChatUserPresenceGet | dict[str, Any]) -> models.ChatUserPresenceRegosArrayResult:
        """POST Chat/GetUserPresence."""
        return await self._call(self.PATH_GET_USER_PRESENCE, req, models.ChatUserPresenceRegosArrayResult)

    async def set_muted(self, req: models.ChatSetMuted | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/SetMuted."""
        return await self._call(self.PATH_SET_MUTED, req, models.UpdateResult)

    async def set_archived(self, req: models.ChatSetArchived | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/SetArchived."""
        return await self._call(self.PATH_SET_ARCHIVED, req, models.UpdateResult)

    async def set_pinned(self, req: models.ChatSetPinned | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/SetPinned."""
        return await self._call(self.PATH_SET_PINNED, req, models.UpdateResult)

    async def get_available_reactions(self, req: models.ChatGetAvailableReactions | dict[str, Any]) -> models.ChatAvailableReactionRegosArrayResult:
        """POST Chat/GetAvailableReactions."""
        return await self._call(self.PATH_GET_AVAILABLE_REACTIONS, req, models.ChatAvailableReactionRegosArrayResult)

    async def set_available_reactions(self, req: models.ChatSetAvailableReactions | dict[str, Any]) -> models.UpdateResult:
        """POST Chat/SetAvailableReactions."""
        return await self._call(self.PATH_SET_AVAILABLE_REACTIONS, req, models.UpdateResult)

__all__ = ['ChatService']
