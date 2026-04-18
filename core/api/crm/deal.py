"""CRM deal service."""

from typing import Optional

from schemas.api.crm.deal import (
    Deal,
    DealAddRequest,
    DealAddResponse,
    DealCloseRequest,
    DealCloseResponse,
    DealDeleteRequest,
    DealDeleteResponse,
    DealEditRequest,
    DealEditResponse,
    DealGetRequest,
    DealGetResponse,
    DealSetParticipantsRequest,
    DealSetParticipantsResponse,
    DealSetResponsibleRequest,
    DealSetResponsibleResponse,
    DealSetStageRequest,
    DealSetStageResponse,
)


class DealService:
    PATH_GET = "Deal/Get"
    PATH_ADD = "Deal/Add"
    PATH_EDIT = "Deal/Edit"
    PATH_DELETE = "Deal/Delete"
    PATH_SET_STAGE = "Deal/SetStage"
    PATH_SET_RESPONSIBLE = "Deal/SetResponsible"
    PATH_SET_PARTICIPANTS = "Deal/SetParticipants"
    PATH_CLOSE = "Deal/Close"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DealGetRequest) -> DealGetResponse:
        return await self.api.call(self.PATH_GET, req, DealGetResponse)

    async def add(self, req: DealAddRequest) -> DealAddResponse:
        return await self.api.call(self.PATH_ADD, req, DealAddResponse)

    async def edit(self, req: DealEditRequest) -> DealEditResponse:
        return await self.api.call(self.PATH_EDIT, req, DealEditResponse)

    async def delete(self, req: DealDeleteRequest) -> DealDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, DealDeleteResponse)

    async def set_stage(self, req: DealSetStageRequest) -> DealSetStageResponse:
        return await self.api.call(self.PATH_SET_STAGE, req, DealSetStageResponse)

    async def set_responsible(
        self, req: DealSetResponsibleRequest
    ) -> DealSetResponsibleResponse:
        return await self.api.call(
            self.PATH_SET_RESPONSIBLE,
            req,
            DealSetResponsibleResponse,
        )

    async def set_participants(
        self, req: DealSetParticipantsRequest
    ) -> DealSetParticipantsResponse:
        return await self.api.call(
            self.PATH_SET_PARTICIPANTS,
            req,
            DealSetParticipantsResponse,
        )

    async def close(self, req: DealCloseRequest) -> DealCloseResponse:
        return await self.api.call(self.PATH_CLOSE, req, DealCloseResponse)

    async def get_by_id(self, deal_id: int) -> Optional[Deal]:
        response = await self.get(DealGetRequest(ids=[deal_id], limit=1, offset=0))
        if not response.result:
            return None
        return response.result[0]
