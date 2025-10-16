# services/brand.py
from __future__ import annotations

from typing import List, Tuple
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse, ArrayResult
from schemas.api.references.brand import (
    Brand,
    BrandGetRequest,
    BrandAddRequest,
    BrandEditRequest,
    BrandDeleteRequest,
)

logger = setup_logger("references.Brand")


class BrandService:
    PATH_GET = "Brand/Get"
    PATH_ADD = "Brand/Add"
    PATH_EDIT = "Brand/Edit"
    PATH_DELETE = "Brand/Delete"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам) ----------
    async def get(self, req: BrandGetRequest) -> APIBaseResponse[List[Brand]]:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse[List[Brand]])

    async def add(self, req: BrandAddRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse[ArrayResult])

    async def edit(self, req: BrandEditRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse[ArrayResult])

    async def delete(self, req: BrandDeleteRequest) -> APIBaseResponse[ArrayResult]:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse[ArrayResult])
