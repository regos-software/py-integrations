"""CRM lead service."""

from typing import Optional

from schemas.api.crm.lead import (
    Lead,
    LeadAddRequest,
    LeadAddResponse,
    LeadEditRequest,
    LeadEditResponse,
    LeadGetRequest,
    LeadGetResponse,
    LeadSetStatusRequest,
    LeadSetStatusResponse,
)


class LeadService:
    PATH_GET = "Lead/Get"
    PATH_ADD = "Lead/Add"
    PATH_EDIT = "Lead/Edit"
    PATH_SET_STATUS = "Lead/SetStatus"

    def __init__(self, api):
        self.api = api

    async def get(self, req: LeadGetRequest) -> LeadGetResponse:
        return await self.api.call(self.PATH_GET, req, LeadGetResponse)

    async def add(self, req: LeadAddRequest) -> LeadAddResponse:
        return await self.api.call(self.PATH_ADD, req, LeadAddResponse)

    async def edit(self, req: LeadEditRequest) -> LeadEditResponse:
        return await self.api.call(self.PATH_EDIT, req, LeadEditResponse)

    async def set_status(self, req: LeadSetStatusRequest) -> LeadSetStatusResponse:
        return await self.api.call(self.PATH_SET_STATUS, req, LeadSetStatusResponse)

    async def get_by_id(self, lead_id: int) -> Optional[Lead]:
        response = await self.get(LeadGetRequest(ids=[lead_id], limit=1, offset=0))
        if not response.result:
            return None
        return response.result[0]
