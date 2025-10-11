from typing import List, Optional

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, APIErrorResult
from schemas.api.docs.wholesale import (
    DocWholeSaleGetRequest,
    DocWholeSale,
    DocWholeSaleGetResponse,
)

logger = setup_logger("docs.WholeSale")


class DocWholeSaleService:
    PATH_GET = "DocWholeSale/Get"

    def __init__(self, api):
        self.api = api

    async def get_raw(self, req: DocWholeSaleGetRequest) -> DocWholeSaleGetResponse:
        """ """
        return await self.api.call(self.PATH_GET, req, DocWholeSaleGetResponse)

    async def get_by_id(self, id_: int) -> Optional[DocWholeSale]:
        """
        Получить один документ по ID. Возвращает None, если не найден.
        """
        resp = await self.get_raw(DocWholeSaleGetRequest(ids=[id_]))
        return resp.result[0] if len(resp.result) >= 1 else None
