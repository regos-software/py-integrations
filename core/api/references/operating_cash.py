from typing import List

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.references.operating_cash import (
    OperatingCash,
    OperatingCashGetRequest,
)

logger = setup_logger("references.OperatingCash")


class OperatingCashService:
    PATH_GET = "OperatingCash/Get"

    def __init__(self, api):
        self.api = api

    async def get(
        self, req: OperatingCashGetRequest
    ) -> APIBaseResponse[List[OperatingCash]]:
        resp = await self.api.call(
            self.PATH_GET,
            req,
            APIBaseResponse[List[OperatingCash]],
        )
        return resp
