from __future__ import annotations

from core.logger import setup_logger
from schemas.api.references.currency import CurrencyGetRequest, CurrencyGetResponse

logger = setup_logger("references.Currency")


class CurrencyService:
    """Сервис работы со справочником валют."""

    PATH_GET = "Currency/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: CurrencyGetRequest) -> CurrencyGetResponse:
        """Возвращает перечень валют согласно фильтрам запроса."""

        return await self.api.call(self.PATH_GET, req, CurrencyGetResponse)
