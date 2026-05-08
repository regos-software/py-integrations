from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi.encoders import jsonable_encoder

from clients.base import ClientBase
from config.settings import settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_acquire_lock,
    redis_delete_keys,
    redis_get_json,
    redis_make_key,
    redis_release_lock,
    redis_set_json,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest
from schemas.api.references.item import (
    ItemGetCurrentQuantityRequest,
    ItemGetExtImageSize,
    ItemGetExtRequest,
)
from schemas.api.references.stock import StockGetRequest


logger = setup_logger("marketplace_toserver")


class MarketplaceToServerError(Exception):
    def __init__(self, code: int, description: str) -> None:
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(Decimal(text))
    except Exception:
        return default


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return default


def _text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _nested(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return default
    return current


class MarketplaceToServerIntegration(ClientBase):
    integration_key = "marketplace_toserver"
    redis_prefix = "mp:ts"

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None
        self._settings: Optional[Dict[str, str]] = None

    def _ci(self) -> str:
        return str(self.connected_integration_id or "").strip()

    def _redis_key(self, *parts: Any) -> str:
        return redis_make_key(self.redis_prefix, self._ci(), *parts)

    def _active_cache_key(self) -> str:
        return self._redis_key("a")

    def _settings_cache_key(self) -> str:
        return self._redis_key("s")

    def _settings_lock_key(self) -> str:
        return self._redis_key("sl")

    def _run_lock_key(self) -> str:
        return self._redis_key("rl")

    async def check(self) -> Dict[str, Any]:
        await self._ensure_active()
        settings_map = await self._load_settings()
        endpoint = _text(settings_map.get("ENDPOINT")).strip()
        if not endpoint:
            raise MarketplaceToServerError(111350, "ENDPOINT is not set")

        async with httpx.AsyncClient(timeout=settings.marketplace_external_timeout) as client:
            response = await client.post(
                endpoint,
                json=[],
                auth=self._basic_auth(settings_map),
            )
        if response.status_code == 400:
            return {"status": "reachable_bad_request"}
        response.raise_for_status()
        return {"status": "ok"}

    async def update_settings(self, settings: Optional[dict] = None, **kwargs: Any) -> Dict[str, Any]:
        ci = str(
            kwargs.get("connected_integration_id")
            or kwargs.get("connectedIntegrationId")
            or ""
        ).strip()
        if ci:
            self.connected_integration_id = ci
        if not self._ci():
            return {"status": "error", "error": "connected_integration_id is required"}
        self._settings = None
        await redis_delete_keys(self._active_cache_key(), self._settings_cache_key())
        return {"status": "settings updated"}

    async def do_work(self) -> Dict[str, Any]:
        await self._ensure_active()
        lock_token = await redis_acquire_lock(self._run_lock_key(), settings.marketplace_toserver_lock_ttl)
        if not lock_token:
            return {"status": "skipped", "reason": "already_running"}
        try:
            settings_map = await self._load_settings()
            if str(settings_map.get("UNLOAD_ENABLED", "1")).strip() == "0":
                return {"status": "skipped", "reason": "unload_disabled"}

            endpoint = _text(settings_map.get("ENDPOINT")).strip()
            if not endpoint:
                raise MarketplaceToServerError(111350, "ENDPOINT is not set")

            firm_id = _to_int(settings_map.get("FIRM"), -1)
            price_type_id = _to_int(settings_map.get("PRICE_TYPE"), -1)
            stock_ids = self._parse_ids(settings_map.get("STOCK_ID") or settings_map.get("STOCK_IDS"))

            stocks = await self._get_stocks(firm_id=firm_id, stock_ids=stock_ids)
            if not stocks:
                raise MarketplaceToServerError(111422, f"{self.integration_key} stocks is not specified")
            if not stock_ids:
                stock_ids = sorted({_to_int(stock.get("id")) for stock in stocks if _to_int(stock.get("id")) > 0})
            if not stock_ids:
                raise MarketplaceToServerError(111422, f"{self.integration_key} stock_ids is not specified")

            sent_items = 0
            offset = 0
            total = 0
            image_size = self._image_size(settings_map.get("IMAGE_SIZE"))
            async with httpx.AsyncClient(timeout=settings.marketplace_external_timeout) as client:
                await self._preflight(client, endpoint, settings_map)
                while True:
                    item_ext_rows, next_offset, response_total = await self._item_ext_page(
                        price_type_id=price_type_id,
                        image_size=image_size,
                        offset=offset,
                    )
                    if not item_ext_rows:
                        break

                    item_ids = [_to_int(_nested(row, "item.id")) for row in item_ext_rows]
                    item_ids = [item_id for item_id in item_ids if item_id > 0]
                    qty_rows = await self._current_quantities(item_ids=item_ids, stock_ids=stock_ids)
                    payload = self._build_payload(item_ext_rows, qty_rows, stocks)
                    if payload:
                        post_response = await client.post(
                            endpoint,
                            json=jsonable_encoder(payload),
                            auth=self._basic_auth(settings_map),
                        )
                        post_response.raise_for_status()
                        sent_items += len(payload)

                    total = _to_int(response_total, total)
                    if next_offset == 0 or next_offset == offset or (total > 0 and next_offset >= total):
                        break
                    offset = next_offset

            return {
                "status": "ok",
                "items_sent": sent_items,
                "finished_at": int(time.time()),
            }
        finally:
            await redis_release_lock(self._run_lock_key(), lock_token)

    async def do_task(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def run(self, **_: Any) -> Dict[str, Any]:
        return await self.do_work()

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok"}

    async def _ensure_active(self) -> str:
        ci = self._ci()
        if not ci:
            raise MarketplaceToServerError(100, "connected-integration-id не получен")
        cached = await redis_get_json(self._active_cache_key())
        if isinstance(cached, dict):
            if not bool(cached.get("active")):
                raise MarketplaceToServerError(111350, "inactive")
            return str(cached.get("key") or self.integration_key)

        async with RegosAPI(ci) as api:
            response = await api.integrations.connected_integration.get(
                ConnectedIntegrationGetRequest(
                    connected_integration_ids=[ci],
                    include_schedule=False,
                    include_name=False,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        row = rows[0] if rows else None
        if row is None:
            raise MarketplaceToServerError(111350, "not found")
        if not bool(getattr(row, "is_active", False)):
            await redis_set_json(
                self._active_cache_key(),
                {"active": False, "key": self.integration_key},
                settings.marketplace_cache_ttl,
            )
            raise MarketplaceToServerError(111350, "inactive")
        key = str(getattr(row, "key", "") or "").strip()
        if key and key != self.integration_key:
            logger.warning("Unexpected integration key for toserver: ci=%s key=%s", ci, key)
        integration_key = key or self.integration_key
        await redis_set_json(
            self._active_cache_key(),
            {"active": True, "key": integration_key},
            settings.marketplace_cache_ttl,
        )
        return integration_key

    async def _load_settings(self) -> Dict[str, str]:
        if self._settings is not None:
            return self._settings
        cached = await redis_get_json(self._settings_cache_key())
        if isinstance(cached, dict):
            self._settings = {str(key): str(value or "") for key, value in cached.items() if str(key)}
            return self._settings

        lock_token = await redis_acquire_lock(
            self._settings_lock_key(),
            settings.marketplace_lock_ttl,
            wait_timeout_sec=settings.marketplace_lock_wait_timeout,
        )
        if not lock_token:
            raise MarketplaceToServerError(111350, "settings cache lock timeout")
        try:
            cached = await redis_get_json(self._settings_cache_key())
            if isinstance(cached, dict):
                self._settings = {str(key): str(value or "") for key, value in cached.items() if str(key)}
                return self._settings

            await self._ensure_active()
            async with RegosAPI(self._ci()) as api:
                response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(connected_integration_id=self._ci())
                )
            if not response.ok or not isinstance(response.result, list):
                raise MarketplaceToServerError(111350, "settings not found")
            self._settings = {
                str(getattr(row, "key", "") or ""): str(getattr(row, "value", "") or "")
                for row in response.result
                if str(getattr(row, "key", "") or "")
            }
            await redis_set_json(self._settings_cache_key(), self._settings, settings.marketplace_cache_ttl)
            return self._settings
        finally:
            await redis_release_lock(self._settings_lock_key(), lock_token)

    async def _get_stocks(self, *, firm_id: int, stock_ids: List[int]) -> List[Dict[str, Any]]:
        async with RegosAPI(self._ci()) as api:
            response = await api.references.stock.get(
                StockGetRequest(
                    firm_ids=[firm_id] if firm_id > 0 else None,
                    ids=stock_ids or None,
                    offset=0,
                    limit=250,
                )
            )
        if not response.ok:
            raise MarketplaceToServerError(111321, "REGOS stocks request rejected")
        return [
            row.model_dump(mode="json", by_alias=True)
            for row in (response.result or [])
        ]

    async def _item_ext_page(
        self,
        *,
        price_type_id: int,
        image_size: Optional[ItemGetExtImageSize],
        offset: int,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        async with RegosAPI(self._ci()) as api:
            response = await api.references.item.get_ext(
                ItemGetExtRequest(
                    price_type_id=price_type_id if price_type_id > 0 else None,
                    offset=offset,
                    limit=settings.marketplace_unload_page_size,
                    deleted_mark=False,
                    image_size=image_size,
                    zero_price=False,
                )
            )
        if not response.ok:
            raise MarketplaceToServerError(111321, "REGOS item ext request rejected")
        return (
            [
                row.model_dump(mode="json", by_alias=True)
                for row in (response.result or [])
            ],
            _to_int(response.next_offset),
            _to_int(response.total),
        )

    async def _current_quantities(self, *, item_ids: List[int], stock_ids: List[int]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        async with RegosAPI(self._ci()) as api:
            for start in range(0, len(item_ids), 250):
                chunk_ids = item_ids[start : start + 250]
                if not chunk_ids:
                    continue
                response = await api.references.item.get_current_quantity(
                    ItemGetCurrentQuantityRequest(item_ids=chunk_ids, stock_ids=stock_ids)
                )
                if not response.ok:
                    raise MarketplaceToServerError(111321, "REGOS item quantity request rejected")
                result.extend(
                    row.model_dump(mode="json", by_alias=True)
                    for row in (response.result or [])
                )
        return result

    async def _preflight(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        settings_map: Dict[str, str],
    ) -> None:
        response = await client.post(endpoint, json=[], auth=self._basic_auth(settings_map))
        if response.status_code == 400:
            return
        response.raise_for_status()

    @staticmethod
    def _basic_auth(settings_map: Dict[str, str]) -> Optional[Tuple[str, str]]:
        if _to_int(settings_map.get("AUTHORIZATION_REQUIRED")) != 1:
            return None
        return _text(settings_map.get("USER_LOGIN")), _text(settings_map.get("USER_PASSWORD"))

    @staticmethod
    def _image_size(value: Any) -> Optional[ItemGetExtImageSize]:
        text = str(value or "").strip().lower()
        if text in {"1", "large"}:
            return ItemGetExtImageSize.Large
        if text in {"2", "medium"}:
            return ItemGetExtImageSize.Medium
        if text in {"3", "small"}:
            return ItemGetExtImageSize.Small
        return None

    @staticmethod
    def _parse_ids(raw: Any) -> List[int]:
        result = []
        for part in str(raw or "").split(","):
            value = _to_int(part)
            if value > 0:
                result.append(value)
        return sorted(set(result))

    @staticmethod
    def _build_payload(
        item_ext_rows: List[Dict[str, Any]],
        qty_rows: List[Dict[str, Any]],
        stocks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        stock_template = {
            _to_int(stock.get("id")): {"stock_id": _to_int(stock.get("id")), "value": Decimal("0")}
            for stock in stocks
            if _to_int(stock.get("id")) > 0
        }
        qty_by_item: Dict[int, Dict[int, Decimal]] = {}
        for row in qty_rows:
            item_id = _to_int(row.get("item_id"))
            stock_id = _to_int(row.get("stock_id"))
            if item_id <= 0 or stock_id <= 0:
                continue
            qty_by_item.setdefault(item_id, {})
            qty_by_item[item_id][stock_id] = qty_by_item[item_id].get(stock_id, Decimal("0")) + _to_decimal(row.get("quantity"))

        result = []
        for ext in item_ext_rows:
            item = ext.get("item") if isinstance(ext, dict) else None
            if not isinstance(item, dict):
                continue
            item_id = _to_int(item.get("id"))
            quantities = {stock_id: dict(row) for stock_id, row in stock_template.items()}
            for stock_id, quantity in qty_by_item.get(item_id, {}).items():
                if stock_id in quantities:
                    quantities[stock_id]["value"] = quantities[stock_id].get("value", Decimal("0")) + quantity

            result.append(
                {
                    "id": item_id,
                    "code": _to_int(item.get("code")),
                    "name": _text(item.get("name")),
                    "articul": _text(item.get("articul")),
                    "icps": _text(item.get("icps")),
                    "package_code": _text(item.get("package_code")),
                    "base_barcode": _text(item.get("base_barcode")),
                    "price": _to_decimal(ext.get("price")),
                    "image_url": _text(ext.get("image_url")),
                    "quantity": list(quantities.values()),
                }
            )
        return result
