from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.partner import PartnerGetRequest, PartnerGetResponse

logger = setup_logger("references.Partner")


class PartnerService:
    """Сервис работы со справочником контрагентов."""

    PATH_GET = "Partner/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PartnerGetRequest) -> PartnerGetResponse:
        """Возвращает список контрагентов согласно фильтрам запроса."""

        return await self.api.call(self.PATH_GET, req, PartnerGetResponse)
