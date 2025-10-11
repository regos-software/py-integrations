# services/item.py
from __future__ import annotations

import functools
import warnings
from typing import Iterable, List, Optional, Tuple

from pydantic import TypeAdapter, ValidationError

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.item import (
    Item,
    ItemExt,
    ItemGetExtRequest,
    ItemGetRequest,
    ItemSearchRequest,
)

logger = setup_logger("refrences.Item")


# ---------- helper: deprecation decorator (BC-маркер) ----------
def deprecated(reason: str):
    """
    Помечает метод устаревшим.
    - добавляет атрибуты: __deprecated__=True, __deprecated_reason__=<reason>
    - при вызове генерирует DeprecationWarning
    """

    def _wrap(func):
        @functools.wraps(func)
        async def _inner(*args, **kwargs):
            warnings.warn(
                f"{func.__qualname__} is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=2,
            )
            return await func(*args, **kwargs)

        _inner.__deprecated__ = True  # <- BC: явный атрибут
        _inner.__deprecated_reason__ = reason
        return _inner

    return _wrap


class ItemService:
    PATH_SEARCH = "Item/Search"
    PATH_GET = "Item/Get"
    PATH_GET_EXT = "Item/GetExt"

    def __init__(self, api):
        self.api = api

    # ---------- RAW слой (1:1 к эндпоинтам) ----------
    async def search_raw(self, req: ItemSearchRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_SEARCH, req, APIBaseResponse)

    async def get_raw(self, req: ItemGetRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def get_ext_raw(self, req: ItemGetExtRequest) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET_EXT, req, APIBaseResponse)

    # ---------- Тонкие методы (рекомендуемый «стандарт») ----------
    async def search_ids(self, req: ItemSearchRequest) -> List[int]:
        """
        Строгий вариант поиска: возвращает список ID или бросает исключение.
        - ok=False -> RuntimeError
        - result не list -> TypeError
        - элементы приводим к int (мягкая попытка BC)
        """
        resp = await self.search_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Search ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_SEARCH}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Search unexpected result format: %r", resp.result)
            raise TypeError("Item/Search: ожидался list в result")

        # в идеале это строгая проверка...
        try:
            return TypeAdapter(List[int]).validate_python(resp.result)
        except ValidationError:
            # ...но для обратной совместимости попробуем мягко привести элементы к int
            out: List[int] = []
            for v in resp.result:
                try:
                    out.append(int(v))
                except Exception:
                    pass
            if not out and resp.result:
                # если совсем не удалось — считаем это ошибкой формата
                raise TypeError("Item/Search: элементы result не приводятся к int")
            return out

    async def get_items(self, req: ItemGetRequest) -> List[Item]:
        """
        Строгий вариант получения списка Item: возвращает список или бросает исключение.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Get unexpected result format: %r", resp.result)
            raise TypeError("Item/Get: ожидался list в result")

        return TypeAdapter(List[Item]).validate_python(resp.result)

    async def get_page(self, req: ItemGetRequest) -> Tuple[List[Item], int, int]:
        """
        Возвращает (items, next_offset, total).
        Бросает исключение при ok=False/невалидном формате.
        """
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/Get ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/Get unexpected result format: %r", resp.result)
            raise TypeError("Item/Get: ожидался list в result")

        items = TypeAdapter(List[Item]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def get_ext_items(self, req: ItemGetExtRequest) -> List[ItemExt]:
        """
        Строгий вариант расширенной выдачи.
        """
        resp = await self.get_ext_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/GetExt ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET_EXT}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/GetExt unexpected result format: %r", resp.result)
            raise TypeError("Item/GetExt: ожидался list в result")

        return TypeAdapter(List[ItemExt]).validate_python(resp.result)

    async def get_ext_page(
        self, req: ItemGetExtRequest
    ) -> Tuple[List[ItemExt], int, int]:
        """
        Возвращает (items_ext, next_offset, total) для расширенной выдачи.
        """
        resp = await self.get_ext_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("Item/GetExt ok=False: %r", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET_EXT}: ok=False")

        if not isinstance(resp.result, list):
            logger.error("Item/GetExt unexpected result format: %r", resp.result)
            raise TypeError("Item/GetExt: ожидался list в result")

        items_ext = TypeAdapter(List[ItemExt]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items_ext)
        return items_ext, next_offset, total

    # ---------- Backward compatibility (устаревшие методы) ----------
    # Оставлены имена и поведение, добавлена пометка @deprecated и мягкая обработка ошибок.
    @deprecated("use search_ids() or search_raw() instead")
    async def search(self, req: ItemSearchRequest) -> List[int]:
        try:
            return await self.search_ids(req)
        except Exception:
            logger.exception("Item/Search (deprecated) failed")
            return []

    @deprecated("use get_items()/get_page() or get_raw() instead")
    async def get(self, req: ItemGetRequest) -> List[Item]:
        try:
            items = await self.get_items(req)
            logger.debug("Item/Get (deprecated) -> %d items", len(items))
            return items
        except Exception:
            logger.exception("Item/Get (deprecated) failed")
            return []

    @deprecated("use get_items() in chunks yourself, or iterate with get_page()")
    async def get_by_ids(self, ids: Iterable[int], chunk_size: int = 50) -> List[Item]:
        ids_list = list(ids)
        if not ids_list:
            return []
        out: List[Item] = []
        for i in range(0, len(ids_list), chunk_size):
            part = ids_list[i : i + chunk_size]
            try:
                out.extend(await self.get_items(ItemGetRequest(ids=part)))
            except Exception:
                logger.exception(
                    "Item/Get (deprecated get_by_ids) failed for chunk %r", part
                )
        return out

    @deprecated("use get_ext_items()/get_ext_page() or get_ext_raw() instead")
    async def get_ext(self, req: ItemGetExtRequest) -> List[ItemExt]:
        try:
            items_ext = await self.get_ext_items(req)
            logger.debug("Item/GetExt (deprecated) -> %d rows", len(items_ext))
            return items_ext
        except Exception:
            logger.exception("Item/GetExt (deprecated) failed")
            return []

    @deprecated("prefer search_ids()+get_items() or direct get_page()")
    async def search_and_get(self, query: str) -> List[Item]:
        try:
            ids = await self.search_ids(
                ItemSearchRequest(barcode=query, code=query, articul=query, name=query)
            )
            if not ids:
                return []
            # старое поведение: ограничить до 100
            ids = ids[:100]
            return await self.get_by_ids(ids)
        except Exception:
            logger.exception("Item search_and_get (deprecated) failed")
            return []

    @deprecated("prefer get_ext_items()/get_ext_page() with search=<query>")
    async def search_and_get_ext(
        self,
        query: str,
        *,
        stock_id: Optional[int] = None,
        price_type_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[ItemExt]:
        try:
            req = ItemGetExtRequest(
                search=query,
                stock_id=stock_id,
                price_type_id=price_type_id,
                limit=limit,
                offset=0,
            )
            return await self.get_ext_items(req)
        except Exception:
            logger.exception("Item search_and_get_ext (deprecated) failed")
            return []
