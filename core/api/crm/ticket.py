"""CRM ticket service."""

from schemas.api.crm.ticket import (
    TicketAddRequest,
    TicketAddResponse,
    TicketCloseRequest,
    TicketCloseResponse,
    TicketDeleteRequest,
    TicketDeleteResponse,
    TicketEditRequest,
    TicketEditResponse,
    TicketGetRequest,
    TicketGetResponse,
    TicketSetParticipantsRequest,
    TicketSetParticipantsResponse,
    TicketSetResponsibleRequest,
    TicketSetResponsibleResponse,
)


class TicketService:
    PATH_GET = "Ticket/Get"
    PATH_ADD = "Ticket/Add"
    PATH_EDIT = "Ticket/Edit"
    PATH_DELETE = "Ticket/Delete"
    PATH_SET_RESPONSIBLE = "Ticket/SetResponsible"
    PATH_SET_PARTICIPANTS = "Ticket/SetParticipants"
    PATH_CLOSE = "Ticket/Close"

    def __init__(self, api):
        self.api = api

    async def get(self, req: TicketGetRequest) -> TicketGetResponse:
        return await self.api.call(self.PATH_GET, req, TicketGetResponse)

    async def add(self, req: TicketAddRequest) -> TicketAddResponse:
        return await self.api.call(self.PATH_ADD, req, TicketAddResponse)

    async def edit(self, req: TicketEditRequest) -> TicketEditResponse:
        return await self.api.call(self.PATH_EDIT, req, TicketEditResponse)

    async def delete(self, req: TicketDeleteRequest) -> TicketDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, TicketDeleteResponse)

    async def set_responsible(
        self, req: TicketSetResponsibleRequest
    ) -> TicketSetResponsibleResponse:
        return await self.api.call(
            self.PATH_SET_RESPONSIBLE,
            req,
            TicketSetResponsibleResponse,
        )

    async def set_participants(
        self, req: TicketSetParticipantsRequest
    ) -> TicketSetParticipantsResponse:
        return await self.api.call(
            self.PATH_SET_PARTICIPANTS,
            req,
            TicketSetParticipantsResponse,
        )

    async def close(self, req: TicketCloseRequest) -> TicketCloseResponse:
        return await self.api.call(self.PATH_CLOSE, req, TicketCloseResponse)
