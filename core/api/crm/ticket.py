"""REGOS API service for Ticket."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from core.api.service import RegosAPIService
from schemas.api import models


class TicketService(RegosAPIService):
    PATH_GET = "Ticket/Get"
    PATH_ADD = "Ticket/Add"
    PATH_EDIT = "Ticket/Edit"
    PATH_SET_RESPONSIBLE = "Ticket/SetResponsible"
    PATH_SET_PARTICIPANTS = "Ticket/SetParticipants"
    PATH_SET_STATUS = "Ticket/SetStatus"
    PATH_SET_RATING = "Ticket/SetRating"
    PATH_SET_CLIENT_SENTIMENT = "Ticket/SetClientSentiment"
    PATH_CLOSE = "Ticket/Close"
    PATH_DELETE = "Ticket/Delete"
    REQUEST_MODELS = {
        'add': models.TicketAdd,
        'close': models.TicketClose,
        'delete': models.TicketDelete,
        'edit': models.TicketEdit,
        'get': models.TicketGet,
        'set_client_sentiment': models.TicketSetClientSentiment,
        'set_participants': models.TicketSetParticipants,
        'set_rating': models.TicketSetRating,
        'set_responsible': models.TicketSetResponsible,
        'set_status': models.TicketSetStatus,
    }

    async def get(self, req: models.TicketGet | dict[str, Any]) -> models.TicketRegosOffsettedArrayResult:
        """POST Ticket/Get."""
        return await self._call(self.PATH_GET, req, models.TicketRegosOffsettedArrayResult)

    async def add(self, req: models.TicketAdd | dict[str, Any]) -> models.InsertResult:
        """POST Ticket/Add."""
        return await self._call(self.PATH_ADD, req, models.InsertResult)

    async def edit(self, req: models.TicketEdit | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/Edit."""
        return await self._call(self.PATH_EDIT, req, models.UpdateResult)

    async def set_responsible(self, req: models.TicketSetResponsible | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/SetResponsible."""
        return await self._call(self.PATH_SET_RESPONSIBLE, req, models.UpdateResult)

    async def set_participants(self, req: models.TicketSetParticipants | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/SetParticipants."""
        return await self._call(self.PATH_SET_PARTICIPANTS, req, models.UpdateResult)

    async def set_status(self, req: models.TicketSetStatus | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/SetStatus."""
        return await self._call(self.PATH_SET_STATUS, req, models.UpdateResult)

    async def set_rating(self, req: models.TicketSetRating | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/SetRating."""
        return await self._call(self.PATH_SET_RATING, req, models.UpdateResult)

    async def set_client_sentiment(self, req: models.TicketSetClientSentiment | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/SetClientSentiment."""
        return await self._call(self.PATH_SET_CLIENT_SENTIMENT, req, models.UpdateResult)

    async def close(self, req: models.TicketClose | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/Close."""
        return await self._call(self.PATH_CLOSE, req, models.UpdateResult)

    async def delete(self, req: models.TicketDelete | dict[str, Any]) -> models.UpdateResult:
        """POST Ticket/Delete."""
        return await self._call(self.PATH_DELETE, req, models.UpdateResult)

__all__ = ['TicketService']
