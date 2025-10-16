# services/brand.py
from __future__ import annotations

from typing import List, Tuple
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
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
    async def get_raw(self, req: BrandGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def add_raw(self, req: BrandAddRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit_raw(self, req: BrandEditRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_raw(self, req: BrandDeleteRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)

    # ---------- Тонкие методы ----------
    async def get(self, req: BrandGetRequest) -> List[Brand]:
        """
        Возвращает список брендов. Бросает:
        - RuntimeError, если ok=False
        - TypeError, если result не list
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Brand/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")
        if not isinstance(resp.result, list):
            logger.error("Brand/Get unexpected result format: %r", resp.result)
            raise TypeError("Brand/Get: ожидался list в result")
        return TypeAdapter(List[Brand]).validate_python(resp.result)

    async def get_page(self, req: BrandGetRequest) -> Tuple[List[Brand], int, int]:
        """
        Возвращает (items, next_offset, total). Пагинация не скрывается.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Brand/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")
        if not isinstance(resp.result, list):
            logger.error("Brand/Get unexpected result format: %r", resp.result)
            raise TypeError("Brand/Get: ожидался list в result")
        items = TypeAdapter(List[Brand]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def add(self, req: BrandAddRequest) -> int:
        """
        Создаёт бренд. Возвращает ID.
        Бросает RuntimeError при ok=False и TypeError при неожиданном формате result.
        """
        resp = await self.add_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Brand/Add ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_ADD}: ok=False")
        if isinstance(resp.result, int):
            return resp.result
        if isinstance(resp.result, dict) and isinstance(resp.result.get("id"), int):
            return resp.result["id"]
        logger.error("Brand/Add unexpected result format: %r", resp.result)
        raise TypeError("Brand/Add: ожидался int или {'id': int} в result")

    async def edit(self, req: BrandEditRequest) -> None:
        """
        Редактирует бренд. Успех — отсутствие исключения.
        """
        resp = await self.edit_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Brand/Edit ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_EDIT}: ok=False")

    async def delete(self, req: BrandDeleteRequest) -> None:
        """
        Удаляет бренд. Успех — отсутствие исключения.
        """
        resp = await self.delete_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Brand/Delete ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_DELETE}: ok=False")
