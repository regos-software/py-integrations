# services/retail_customer.py
from __future__ import annotations

from typing import List, Tuple
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.retail_customer import (
    RetailCustomer,
    RetailCustomerGetRequest,
    RetailCustomerAddRequest,
    RetailCustomerEditRequest,
    RetailCustomerDeleteMarkRequest,
    RetailCustomerDeleteRequest,
)

logger = setup_logger("references.RetailCustomer")


class RetailCustomerService:
    PATH_GET         = "RetailCustomer/Get"
    PATH_ADD         = "RetailCustomer/Add"
    PATH_EDIT        = "RetailCustomer/Edit"
    PATH_DELETE_MARK = "RetailCustomer/DeleteMark"
    PATH_DELETE      = "RetailCustomer/Delete"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам) ----------

    async def get_raw(self, req: RetailCustomerGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def add_raw(self, req: RetailCustomerAddRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit_raw(self, req: RetailCustomerEditRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_mark_raw(self, req: RetailCustomerDeleteMarkRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE_MARK, req, APIBaseResponse)

    async def delete_raw(self, req: RetailCustomerDeleteRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)

    # ---------- Тонкие удобные методы ----------

    async def get(self, req: RetailCustomerGetRequest) -> List[RetailCustomer]:
        """
        Возвращает список покупателей. Бросает RuntimeError при ok=False
        и TypeError при неверном формате result.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("GET ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False (result={getattr(resp, 'result', None)!r})")
        if not isinstance(resp.result, list):
            logger.error("GET unexpected result format: %r", resp.result)
            raise TypeError("Ожидался список покупателей в result")
        return TypeAdapter(List[RetailCustomer]).validate_python(resp.result)

    async def get_page(self, req: RetailCustomerGetRequest) -> Tuple[List[RetailCustomer], int, int]:
        """
        Возвращает (items, next_offset, total). Бросает RuntimeError/TypeError при ошибках.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("GET ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False (result={getattr(resp, 'result', None)!r})")
        if not isinstance(resp.result, list):
            logger.error("GET unexpected result format: %r", resp.result)
            raise TypeError("Ожидался список покупателей в result")

        items = TypeAdapter(List[RetailCustomer]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def add(self, req: RetailCustomerAddRequest) -> int:
        """
        Создаёт покупателя. Возвращает ID. Бросает RuntimeError при ok=False
        и TypeError при неожиданном формате result.
        """
        resp = await self.add_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("ADD ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_ADD}: ok=False (result={getattr(resp, 'result', None)!r})")
        if isinstance(resp.result, int):
            return resp.result
        if isinstance(resp.result, dict) and isinstance(resp.result.get("id"), int):
            return resp.result["id"]
        logger.error("ADD unexpected result format: %r", resp.result)
        raise TypeError("Ожидался int или {'id': int} в result")

    async def edit(self, req: RetailCustomerEditRequest) -> None:
        """
        Редактирует покупателя. Успех — отсутствие исключения.
        """
        resp = await self.edit_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("EDIT ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_EDIT}: ok=False (result={getattr(resp, 'result', None)!r})")

    async def delete_mark(self, req: RetailCustomerDeleteMarkRequest) -> None:
        """
        Тогглит флаг deleted_mark. Успех — отсутствие исключения.
        """
        resp = await self.delete_mark_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("DELETE_MARK ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_DELETE_MARK}: ok=False (result={getattr(resp, 'result', None)!r})")

    async def delete(self, req: RetailCustomerDeleteRequest) -> None:
        """
        Полное удаление (возможно только при deleted_mark=true).
        Успех — отсутствие исключения.
        """
        resp = await self.delete_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("DELETE ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_DELETE}: ok=False (result={getattr(resp, 'result', None)!r})")
