from __future__ import annotations

from typing import Optional

from core.logger import setup_logger
from schemas.api.references.firm import Firm, FirmGetRequest, FirmGetResponse

logger = setup_logger("references.Firm")


class FirmService:
    """Service for Firm endpoints."""

    PATH_GET = "Firm/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: FirmGetRequest) -> FirmGetResponse:
        return await self.api.call(self.PATH_GET, req, FirmGetResponse)

    async def get_by_id(self, id_: int) -> Optional[Firm]:
        resp = await self.get(FirmGetRequest(ids=[id_], limit=1))
        result = resp.result or []
        return result[0] if result else None
