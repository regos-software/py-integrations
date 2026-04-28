"""CRM lead service."""

from __future__ import annotations

from typing import Any, Optional

from schemas.api.crm.lead import (
    Lead,
    LeadAddRequest,
    LeadAddResponse,
    LeadCloseRequest,
    LeadCloseResponse,
    LeadConvertRequest,
    LeadConvertResponse,
    LeadDeleteRequest,
    LeadDeleteResponse,
    LeadEditRequest,
    LeadEditResponse,
    LeadGetRequest,
    LeadGetResponse,
    LeadSetParticipantsRequest,
    LeadSetParticipantsResponse,
    LeadSetRatingRequest,
    LeadSetRatingResponse,
    LeadSetResponsibleRequest,
    LeadSetResponsibleResponse,
    LeadSetStageRequest,
    LeadSetStageResponse,
)


class LeadService:
    PATH_GET = "Lead/Get"
    PATH_ADD = "Lead/Add"
    PATH_EDIT = "Lead/Edit"
    PATH_DELETE = "Lead/Delete"
    PATH_SET_STAGE = "Lead/SetStage"
    PATH_SET_RESPONSIBLE = "Lead/SetResponsible"
    PATH_SET_PARTICIPANTS = "Lead/SetParticipants"
    PATH_SET_RATING = "Lead/SetRating"
    PATH_CLOSE = "Lead/Close"
    PATH_CONVERT = "Lead/Convert"

    def __init__(self, api):
        self.api = api

    @staticmethod
    def _first_non_empty(*values: Any) -> str | None:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return None

    async def get(self, req: LeadGetRequest) -> LeadGetResponse:
        payload = req.model_dump(exclude_none=True)
        sanitized = {
            "ids": payload.get("ids"),
            "client_ids": payload.get("client_ids"),
            "search": payload.get("search"),
            "responsible_user_ids": payload.get("responsible_user_ids"),
            "stage_ids": payload.get("stage_ids"),
            "from_date": payload.get("from_date"),
            "to_date": payload.get("to_date"),
            "filters": payload.get("filters"),
            "limit": payload.get("limit"),
            "offset": payload.get("offset"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_GET, sanitized, LeadGetResponse)

    async def add(self, req: LeadAddRequest) -> LeadAddResponse:
        payload = req.model_dump(exclude_none=True)
        ticket_id = payload.get("ticket_id") or payload.get("source_ticket_id")
        title = self._first_non_empty(payload.get("title"), payload.get("subject"))

        sanitized = {
            "client_id": payload.get("client_id"),
            "ticket_id": ticket_id,
            "chat_id": payload.get("chat_id"),
            "pipeline_id": payload.get("pipeline_id"),
            "stage_id": payload.get("stage_id"),
            "responsible_user_id": payload.get("responsible_user_id"),
            "participant_user_ids": payload.get("participant_user_ids"),
            "title": title,
            "description": payload.get("description"),
            "amount": payload.get("amount"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_ADD, sanitized, LeadAddResponse)

    async def edit(self, req: LeadEditRequest) -> LeadEditResponse:
        payload = req.model_dump(exclude_none=True)
        title = self._first_non_empty(payload.get("title"), payload.get("subject"))

        sanitized = {
            "id": payload.get("id"),
            "stage_id": payload.get("stage_id"),
            "title": title,
            "description": payload.get("description"),
            "amount": payload.get("amount"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_EDIT, sanitized, LeadEditResponse)

    async def delete(self, req: LeadDeleteRequest) -> LeadDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, LeadDeleteResponse)

    async def set_stage(self, req: LeadSetStageRequest) -> LeadSetStageResponse:
        return await self.api.call(self.PATH_SET_STAGE, req, LeadSetStageResponse)

    async def set_responsible(
        self, req: LeadSetResponsibleRequest
    ) -> LeadSetResponsibleResponse:
        return await self.api.call(
            self.PATH_SET_RESPONSIBLE,
            req,
            LeadSetResponsibleResponse,
        )

    async def set_participants(
        self, req: LeadSetParticipantsRequest
    ) -> LeadSetParticipantsResponse:
        return await self.api.call(
            self.PATH_SET_PARTICIPANTS,
            req,
            LeadSetParticipantsResponse,
        )

    async def set_rating(self, req: LeadSetRatingRequest) -> LeadSetRatingResponse:
        return await self.api.call(self.PATH_SET_RATING, req, LeadSetRatingResponse)

    async def close(self, req: LeadCloseRequest) -> LeadCloseResponse:
        return await self.api.call(self.PATH_CLOSE, req, LeadCloseResponse)

    async def convert(self, req: LeadConvertRequest) -> LeadConvertResponse:
        return await self.api.call(self.PATH_CONVERT, req, LeadConvertResponse)

    async def get_by_id(self, lead_id: int) -> Optional[Lead]:
        response = await self.get(LeadGetRequest(ids=[lead_id], limit=1, offset=0))
        if not response.result:
            return None
        return response.result[0]
