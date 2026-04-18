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
    LeadSetResponsibleRequest,
    LeadSetResponsibleResponse,
    LeadSetStatusRequest,
    LeadSetStatusResponse,
)


class LeadService:
    PATH_GET = "Lead/Get"
    PATH_ADD = "Lead/Add"
    PATH_EDIT = "Lead/Edit"
    PATH_SET_RESPONSIBLE = "Lead/SetResponsible"
    PATH_SET_STATUS = "Lead/SetStatus"

    def __init__(self, api):
        self.api = api

    async def get(self, req: LeadGetRequest) -> LeadGetResponse:
        payload = req.model_dump(exclude_none=True)
        allowed_keys = {
            "ids",
            "search",
            "responsible_user_ids",
            "stage_ids",
            "from_date",
            "to_date",
            "filters",
            "limit",
            "offset",
        }
        sanitized = {key: value for key, value in payload.items() if key in allowed_keys}
        return await self.api.call(self.PATH_GET, sanitized, LeadGetResponse)

    async def add(self, req: LeadAddRequest) -> LeadAddResponse:
        payload = req.model_dump(exclude_none=True)
        allowed_keys = {
            "client_id",
            "source_ticket_id",
            "chat_id",
            "pipeline_id",
            "stage_id",
            "responsible_user_id",
            "participant_user_ids",
            "subject",
            "description",
            "fields",
        }
        sanitized = {key: value for key, value in payload.items() if key in allowed_keys}
        return await self.api.call(self.PATH_ADD, sanitized, LeadAddResponse)

    async def edit(self, req: LeadEditRequest) -> LeadEditResponse:
        payload = req.model_dump(exclude_none=True)
        allowed_keys = {
            "id",
            "stage_id",
            "subject",
            "description",
            "fields",
        }
        sanitized = {key: value for key, value in payload.items() if key in allowed_keys}
        return await self.api.call(self.PATH_EDIT, sanitized, LeadEditResponse)

    async def set_responsible(
        self, req: LeadSetResponsibleRequest
    ) -> LeadSetResponsibleResponse:
        return await self.api.call(
            self.PATH_SET_RESPONSIBLE, req, LeadSetResponsibleResponse
        )

    async def set_status(self, req: LeadSetStatusRequest) -> LeadSetStatusResponse:
        return await self.api.call(self.PATH_SET_STATUS, req, LeadSetStatusResponse)

    async def get_by_id(self, lead_id: int) -> Optional[Lead]:
        response = await self.get(LeadGetRequest(ids=[lead_id], limit=1, offset=0))
        if not response.result:
            return None
        return response.result[0]
