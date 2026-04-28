"""CRM client service."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

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

    @staticmethod
    def _first_non_empty(values: Iterable[Any]) -> str | None:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return None

    @staticmethod
    def _merge_text_lists(*collections: List[str] | None) -> List[str] | None:
        merged: list[str] = []
        seen: set[str] = set()
        for collection in collections:
            for value in collection or []:
                text = str(value or "").strip()
                if not text or text in seen:
                    continue
                seen.add(text)
                merged.append(text)
        return merged or None

    def _normalize_external_id(self, payload: Dict[str, Any]) -> None:
        external_id = self._first_non_empty([payload.get("external_id")])
        if external_id:
            payload["external_id"] = external_id
            return

        legacy_external = self._first_non_empty(
            [
                payload.get("telegram_id"),
                payload.get("whatsapp_id"),
                payload.get("instagram_id"),
                payload.get("facebook_id"),
                payload.get("vk_id"),
            ]
        )
        if legacy_external:
            payload["external_id"] = legacy_external

    async def get(self, req: ClientGetRequest) -> ClientGetResponse:
        payload = req.model_dump(exclude_none=True)
        external_ids = self._merge_text_lists(
            payload.get("external_ids"),
            payload.get("telegram_ids"),
            payload.get("whatsapp_ids"),
            payload.get("instagram_ids"),
            payload.get("facebook_ids"),
            payload.get("vk_ids"),
        )

        sanitized = {
            "ids": payload.get("ids"),
            "phones": payload.get("phones"),
            "external_ids": external_ids,
            "emails": payload.get("emails"),
            "search": payload.get("search"),
            "responsible_user_ids": payload.get("responsible_user_ids"),
            "filters": payload.get("filters"),
            "limit": payload.get("limit"),
            "offset": payload.get("offset"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_GET, sanitized, ClientGetResponse)

    async def add(self, req: ClientAddRequest) -> ClientAddResponse:
        payload = req.model_dump(exclude_none=True)
        self._normalize_external_id(payload)

        sanitized = {
            "external_id": payload.get("external_id"),
            "name": payload.get("name"),
            "phone": payload.get("phone"),
            "email": payload.get("email"),
            "photo_url": payload.get("photo_url"),
            "description": payload.get("description"),
            "responsible_user_id": payload.get("responsible_user_id"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_ADD, sanitized, ClientAddResponse)

    async def edit(self, req: ClientEditRequest) -> ClientEditResponse:
        payload = req.model_dump(exclude_none=True)
        self._normalize_external_id(payload)

        sanitized = {
            "id": payload.get("id"),
            "external_id": payload.get("external_id"),
            "name": payload.get("name"),
            "phone": payload.get("phone"),
            "email": payload.get("email"),
            "photo_url": payload.get("photo_url"),
            "description": payload.get("description"),
            "responsible_user_id": payload.get("responsible_user_id"),
            "fields": payload.get("fields"),
        }
        sanitized = {key: value for key, value in sanitized.items() if value is not None}
        return await self.api.call(self.PATH_EDIT, sanitized, ClientEditResponse)

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
