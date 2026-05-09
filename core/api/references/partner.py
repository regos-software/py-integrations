from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.partner import (
    PartnerAddRequest,
    PartnerAddResponse,
    PartnerGetRequest,
    PartnerGetResponse,
)

logger = setup_logger("references.Partner")


class PartnerService:
    """Service for Partner endpoints."""

    PATH_GET = "Partner/Get"
    PATH_ADD = "Partner/Add"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PartnerGetRequest) -> PartnerGetResponse:
        return await self.api.call(self.PATH_GET, req, PartnerGetResponse)

    async def add(self, req: PartnerAddRequest) -> PartnerAddResponse:
        return await self.api.call(self.PATH_ADD, req, PartnerAddResponse)
