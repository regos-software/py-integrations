"""CRM client service."""

from schemas.api.crm.client import (
    ClientAddRequest,
    ClientAddResponse,
    ClientDeleteRequest,
    ClientDeleteResponse,
    ClientEditRequest,
    ClientEditResponse,
    ClientGetRequest,
    ClientGetResponse,
    ClientMergeRequest,
    ClientMergeResponse,
    ClientSetResponsibleRequest,
    ClientSetResponsibleResponse,
)


class ClientService:
    PATH_GET = "Client/Get"
    PATH_ADD = "Client/Add"
    PATH_EDIT = "Client/Edit"
    PATH_DELETE = "Client/Delete"
    PATH_SET_RESPONSIBLE = "Client/SetResponsible"
    PATH_MERGE = "Client/Merge"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ClientGetRequest) -> ClientGetResponse:
        return await self.api.call(self.PATH_GET, req, ClientGetResponse)

    async def add(self, req: ClientAddRequest) -> ClientAddResponse:
        return await self.api.call(self.PATH_ADD, req, ClientAddResponse)

    async def edit(self, req: ClientEditRequest) -> ClientEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ClientEditResponse)

    async def delete(self, req: ClientDeleteRequest) -> ClientDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, ClientDeleteResponse)

    async def set_responsible(
        self, req: ClientSetResponsibleRequest
    ) -> ClientSetResponsibleResponse:
        return await self.api.call(
            self.PATH_SET_RESPONSIBLE,
            req,
            ClientSetResponsibleResponse,
        )

    async def merge(self, req: ClientMergeRequest) -> ClientMergeResponse:
        return await self.api.call(self.PATH_MERGE, req, ClientMergeResponse)
