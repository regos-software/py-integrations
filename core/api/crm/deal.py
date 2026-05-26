"""CRM deal service."""

from __future__ import annotations

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
        payload = req.model_dump(exclude_none=True)
        ticket_id = payload.get("ticket_id") or payload.get("source_ticket_id")

        sanitized = {
            "source_lead_id": payload.get("source_lead_id"),
            "ticket_id": ticket_id,
            "source_deal_id": payload.get("source_deal_id"),
            "client_id": payload.get("client_id"),
            "task_id": payload.get("task_id"),
            "chat_id": payload.get("chat_id"),
            "lead_id": payload.get("lead_id"),
            "deal_type_id": payload.get("deal_type_id"),
            "pipeline_id": payload.get("pipeline_id"),
            "stage_id": payload.get("stage_id"),
            "title": payload.get("title"),
            "description": payload.get("description"),
            "amount": payload.get("amount"),
            "currency_id": payload.get("currency_id"),
            "responsible_user_id": payload.get("responsible_user_id"),
            "participant_user_ids": payload.get("participant_user_ids"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_ADD, sanitized, DealAddResponse)

    async def edit(self, req: DealEditRequest) -> DealEditResponse:
        payload = req.model_dump(exclude_none=True)
        stage_id = payload.get("stage_id")
        sanitized = {
            "id": payload.get("id"),
            "task_id": payload.get("task_id"),
            "deal_type_id": payload.get("deal_type_id"),
            "pipeline_id": payload.get("pipeline_id"),
            "title": payload.get("title"),
            "description": payload.get("description"),
            "amount": payload.get("amount"),
            "currency_id": payload.get("currency_id"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        response: DealEditResponse | None = None
        if len(sanitized) > 1:
            response = await self.api.call(self.PATH_EDIT, sanitized, DealEditResponse)
            if not getattr(response, "ok", False) or stage_id is None:
                return response

        if stage_id is not None:
            return await self.set_stage(
                DealSetStageRequest(id=int(payload["id"]), stage_id=int(stage_id))
            )

        if response is not None:
            return response
        return await self.api.call(self.PATH_EDIT, sanitized, DealEditResponse)

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
