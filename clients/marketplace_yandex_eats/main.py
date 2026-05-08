from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs

import httpx
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

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
from schemas.api.docs.order_delivery import (
    DocOrderDeliveryAddFullRequest,
    DocOrderDeliveryGetRequest,
    DocOrderDeliveryOperationGetRequest,
    DocOrderDeliverySetStatusRequest,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.api.references.item import (
    ItemGetExtImageSize,
    ItemGetExtRequest,
    ItemGetRequest,
)
from schemas.api.references.item_group import ItemGroupGetRequest


logger = setup_logger("yandexeats")


class YandexEatsError(Exception):
    def __init__(self, code: int, description: str, *, status_code: int = 400) -> None:
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)
        self.status_code = int(status_code)


def _json(payload: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder(_drop_none(payload)))


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _error(code: int, description: str) -> Dict[str, Any]:
    return {"code": int(code), "description": str(description)}


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
    if value is None:
        return default
    return str(value)


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


def _sha1(value: str) -> str:
    return hashlib.sha1((value or "").encode("utf-8")).hexdigest()


def _is_pcs(unit_type: Any) -> bool:
    if isinstance(unit_type, str):
        return unit_type.strip().lower() == "pcs"
    return _to_int(unit_type) == 2


def _body(envelope: Dict[str, Any]) -> Dict[str, Any]:
    body = envelope.get("body")
    if isinstance(body, dict):
        return body
    raw = envelope.get("raw_body") or b""
    text = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw or body or "")
    parsed = parse_qs(text, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()} if parsed else {}


def _lookup(data: Dict[str, Any], *names: str) -> Any:
    lower = {str(k).lower(): v for k, v in data.items()}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    return None


def _connected_integration_id(envelope: Dict[str, Any]) -> str:
    for key in ("connected_integration_id", "connectedIntegrationId"):
        value = envelope.get(key)
        if value:
            return str(value or "").strip()
    for key, value in (envelope.get("headers") or {}).items():
        if str(key).lower() == "connected-integration-id":
            return str(value or "").strip()
    return ""


def _authorization(envelope: Dict[str, Any]) -> str:
    for key, value in (envelope.get("headers") or {}).items():
        if str(key).lower() == "authorization":
            return str(value or "")
    return ""


def _path(envelope: Dict[str, Any]) -> str:
    external_path = str(envelope.get("external_path") or "").strip("/")
    if not external_path:
        raw = str(envelope.get("path") or "")
        external_path = raw.split("/external/", 1)[1] if "/external/" in raw else ""
    normalized = external_path.strip("/")
    ci = _connected_integration_id(envelope)
    if ci and normalized.lower().startswith(f"{ci.lower()}/"):
        normalized = normalized[len(ci) + 1 :]
    if normalized.lower().startswith("yandexeats/"):
        normalized = normalized[len("yandexeats/") :]
    return normalized.strip("/").lower()


def _parse_datetime_to_unix(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except Exception:
        return None


def _format_unix(value: Any) -> str:
    ts = _to_int(value)
    dt = datetime.fromtimestamp(ts, timezone.utc) if ts > 0 else datetime.now(timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _order_status_id(order: Dict[str, Any]) -> int:
    direct = _to_int(order.get("status_id"))
    if direct:
        return direct
    status = order.get("status")
    if isinstance(status, dict):
        return _to_int(status.get("id"))
    return _to_int(status)


class YandexEatsIntegration(ClientBase):
    integration_key = "marketplace_yandex_eats"
    redis_prefix = "mp:ye"

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None
        self._integration_key: Optional[str] = None
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

    def _token_lock_key(self) -> str:
        return self._redis_key("tl")

    def _order_lock_key(self, external_order_id: str) -> str:
        return self._redis_key("ol", _sha1(external_order_id)[:16])

    def _order_dedupe_key(self, external_order_id: str) -> str:
        return self._redis_key("od", _sha1(external_order_id)[:16])

    async def handle_external(self, envelope: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        if envelope is None:
            envelope = dict(kwargs)
        elif kwargs:
            envelope = {**envelope, **kwargs}
        ci = _connected_integration_id(envelope)
        if ci:
            self.connected_integration_id = ci
        path = _path(envelope)
        method = str(envelope.get("method") or "GET").upper()

        try:
            if method == "POST" and path in {"v1/security/oauth/token", "security/oauth/token"}:
                return _json({"access_token": await self._issue_token(_body(envelope))})

            valid, auth_error = await self._validate_token(_authorization(envelope))
            if not valid:
                return _json(auth_error, 400 if auth_error["code"] != 500 else 500)

            if method == "GET" and path.startswith("v1/nomenclature/"):
                return await self._handle_nomenclature(path)
            if method == "GET" and path.startswith("nomenclature/"):
                return await self._handle_nomenclature(path)
            if method == "POST" and path in {"v1/order", "order"}:
                return _json(await self._create_order(_body(envelope)))

            order_id, subpath = self._parse_order_path(path)
            if order_id is not None:
                if method == "GET" and subpath == "":
                    return _json(await self._get_order(order_id))
                if method == "GET" and subpath == "status":
                    return _json(await self._get_order_status(order_id))
                if method == "PUT" and subpath == "status":
                    await self._cancel_order(order_id)
                    return Response(status_code=204)
                if method == "PUT" and subpath == "":
                    return _json(_error(400, "Изменение заказа невозможно"), 400)

            return _json(_error(404, "Route not found"), 404)
        except YandexEatsError as error:
            return _json(_error(error.code, error.description), error.status_code)
        except httpx.HTTPStatusError as error:
            logger.warning("YandexEats REGOS HTTP error: %s", error)
            return _json(_error(500, "Внутренняя ошибка сервера"), 500)
        except Exception as error:
            logger.exception("YandexEats external handling failed: %s", error)
            return _json(_error(500, "Внутренняя ошибка сервера"), 500)

    async def check(self) -> Dict[str, Any]:
        await self._load_integration()
        await self._load_settings()
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
        self._integration_key = None
        self._settings = None
        await redis_delete_keys(self._active_cache_key(), self._settings_cache_key())
        return {"status": "settings updated"}

    async def _load_integration(self) -> str:
        if self._integration_key:
            return self._integration_key
        ci = self._ci()
        if not ci:
            raise YandexEatsError(100, "connected-integration-id не получен")
        cached = await redis_get_json(self._active_cache_key())
        if isinstance(cached, dict):
            if not bool(cached.get("active")):
                raise YandexEatsError(113422, "Integration is inactive")
            self._integration_key = str(cached.get("key") or self.integration_key)
            return self._integration_key

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
            raise YandexEatsError(113422, "Интеграция не найдена")
        if not bool(getattr(row, "is_active", False)):
            await redis_set_json(
                self._active_cache_key(),
                {"active": False, "key": self.integration_key},
                settings.marketplace_cache_ttl,
            )
            raise YandexEatsError(113422, "Интеграция не активна")
        self._integration_key = str(getattr(row, "key", "") or self.integration_key)
        await redis_set_json(
            self._active_cache_key(),
            {"active": True, "key": self._integration_key},
            settings.marketplace_cache_ttl,
        )
        return self._integration_key

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
            raise YandexEatsError(113423, "Settings cache lock timeout")
        try:
            cached = await redis_get_json(self._settings_cache_key())
            if isinstance(cached, dict):
                self._settings = {str(key): str(value or "") for key, value in cached.items() if str(key)}
                return self._settings

            await self._load_integration()
            async with RegosAPI(self._ci()) as api:
                response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(connected_integration_id=self._ci())
                )
            if not response.ok or not isinstance(response.result, list):
                raise YandexEatsError(113423, "Integration settings not found")
            self._settings = {
                str(getattr(row, "key", "") or ""): str(getattr(row, "value", "") or "")
                for row in response.result
                if str(getattr(row, "key", "") or "")
            }
            await redis_set_json(self._settings_cache_key(), self._settings, settings.marketplace_cache_ttl)
            return self._settings
        finally:
            await redis_release_lock(self._settings_lock_key(), lock_token)

    async def _edit_setting(self, key: str, value: str, *, lock: bool = True) -> None:
        lock_token = None
        if lock:
            lock_token = await redis_acquire_lock(
                self._token_lock_key(),
                settings.marketplace_lock_ttl,
                wait_timeout_sec=settings.marketplace_lock_wait_timeout,
            )
            if not lock_token:
                raise YandexEatsError(113423, "Settings edit lock timeout")
        try:
            await self._load_integration()
            item = ConnectedIntegrationSettingEditItem(
                key=key,
                value=value,
                connected_integration_id=self._ci(),
            )
            async with RegosAPI(self._ci()) as api:
                response = await api.integrations.connected_integration_setting.edit(
                    ConnectedIntegrationSettingEditRequest([item])
                )
            if not response.ok:
                raise YandexEatsError(113423, "Failed to edit integration settings")
            self._settings = None
            await redis_delete_keys(self._settings_cache_key())
        finally:
            if lock:
                await redis_release_lock(self._token_lock_key(), lock_token)

    async def _issue_token(self, data: Dict[str, Any]) -> str:
        lock_token = await redis_acquire_lock(
            self._token_lock_key(),
            settings.marketplace_lock_ttl,
            wait_timeout_sec=settings.marketplace_lock_wait_timeout,
        )
        if not lock_token:
            raise YandexEatsError(113423, "Token issue lock timeout")
        try:
            settings_map = await self._load_settings()
            if "CLIENT_ID" not in settings_map or "CLIENT_SECRET" not in settings_map:
                raise YandexEatsError(113423, "Integration settings not found or incomplete")
            client_id = _text(_lookup(data, "client_id", "client_Id", "Client_Id", "clientId")).strip()
            client_secret = _text(_lookup(data, "client_secret", "client_Secret", "Client_Secret", "clientSecret")).strip()
            if client_id != settings_map.get("CLIENT_ID") or client_secret != settings_map.get("CLIENT_SECRET"):
                raise YandexEatsError(100, "Invalid client credentials")
            token = uuid.uuid4().hex.lower()
            await self._edit_setting("ACCESS_TOKEN", token, lock=False)
            return token
        finally:
            await redis_release_lock(self._token_lock_key(), lock_token)

    async def _validate_token(self, authorization: str) -> Tuple[bool, Dict[str, Any]]:
        if not authorization:
            return False, _error(400, "Authorization header is missing")
        if not authorization.startswith("Bearer "):
            return False, _error(400, "Invalid token format")
        settings_map = await self._load_settings()
        access_token = settings_map.get("ACCESS_TOKEN")
        if not access_token:
            return False, _error(400, "Settings or AccessToken not found")
        if authorization.split(" ", 1)[1].strip() != access_token:
            return False, _error(400, "Invalid AccessToken")
        return True, {}

    async def _read_order_dedupe(self, external_order_id: str) -> int:
        cached = await redis_get_json(self._order_dedupe_key(external_order_id), local_ttl_sec=0)
        return _to_int(cached.get("order_id")) if isinstance(cached, dict) else 0

    async def _write_order_dedupe(self, external_order_id: str, order_id: int) -> None:
        if order_id > 0:
            await redis_set_json(
                self._order_dedupe_key(external_order_id),
                {"order_id": int(order_id)},
                settings.marketplace_order_dedupe_ttl,
                local_ttl_sec=0,
            )

    async def _handle_nomenclature(self, path: str) -> JSONResponse:
        parts = path.split("/")
        if parts[0] == "v1":
            store_id = _to_int(parts[2]) if len(parts) > 2 else 0
            action = parts[3] if len(parts) > 3 else ""
        else:
            store_id = _to_int(parts[1]) if len(parts) > 1 else 0
            action = parts[2] if len(parts) > 2 else ""
        if action == "composition":
            return _json(await self._composition(store_id))
        if action == "availability":
            return _json(await self._availability(store_id))
        return _json(_error(404, "Route not found"), 404)

    async def _price_type(self) -> int:
        settings_map = await self._load_settings()
        price_type = _to_int(settings_map.get("PRICE_TYPE"))
        if price_type <= 0:
            raise YandexEatsError(113422, f"{await self._load_integration()} PRICE_TYPE not set")
        return price_type

    async def _item_ext_all(self, stock_id: int, price_type_id: int, *, zero_price: bool) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        offset = 0
        total = 0
        async with RegosAPI(self._ci()) as api:
            while True:
                response = await api.references.item.get_ext(
                    ItemGetExtRequest(
                        stock_id=stock_id,
                        price_type_id=price_type_id,
                        offset=offset,
                        limit=10000,
                        has_image=True,
                        image_size=ItemGetExtImageSize.Large,
                        zero_price=zero_price,
                        zero_quantity=True,
                        deleted_mark=False,
                        type="Item",
                    )
                )
                if not response.ok:
                    raise YandexEatsError(111321, "REGOS item ext request rejected")
                chunk = [
                    row.model_dump(mode="json", by_alias=True)
                    for row in (response.result or [])
                ]
                result.extend(chunk)
                next_offset = _to_int(response.next_offset)
                total = _to_int(response.total, total)
                if next_offset == 0 or next_offset == offset or (total > 0 and next_offset >= total):
                    break
                offset = next_offset
        return result

    async def _composition(self, store_id: int) -> Dict[str, Any]:
        if store_id <= 0:
            raise YandexEatsError(400, "Неверный формат storeId")
        price_type = await self._price_type()
        groups, items = await asyncio.gather(
            self._item_groups(),
            self._item_ext_all(store_id, price_type, zero_price=False),
        )
        categories = []
        for group in groups:
            group_id = _to_int(group.get("id"))
            parent_id = _to_int(group.get("parent_id"))
            if group_id > 0:
                categories.append(
                    {
                        "id": str(group_id),
                        "name": _text(group.get("name")),
                        "parentId": str(parent_id) if parent_id > 0 else None,
                        "sortOrder": 1,
                    }
                )
        return {"categories": categories, "items": [x for x in (self._map_catalog_item(i) for i in items) if x]}

    def _map_catalog_item(self, ext: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        item = ext.get("item") if isinstance(ext, dict) else None
        if not isinstance(item, dict):
            return None
        price = _to_decimal(ext.get("price"))
        barcode = _text(item.get("base_barcode")).strip()
        if price <= 0 or not barcode:
            return None
        is_pcs = _is_pcs(_nested(item, "unit.type"))
        image_url = _text(ext.get("image_url")).strip()
        images = [{"url": image_url, "hash": _sha1(image_url)}] if image_url else [{"url": "", "hash": None}]
        return {
            "barcode": {"type": "ean13", "value": barcode, "values": [barcode], "weightEncoding": "none"},
            "categoryId": str(_to_int(_nested(item, "group.id"))),
            "description": {
                "general": _text(item.get("description")),
                "vendorCountry": _text(_nested(item, "country.name")),
                "nutritionalValue": _text(_nested(item, "producer.name")),
            },
            "id": str(_to_int(item.get("id"))),
            "images": images,
            "isCatchWeight": not is_pcs,
            "measure": {"quantum": None if is_pcs else Decimal("0.1"), "unit": "GRM", "value": 1 if is_pcs else 1000},
            "name": _text(item.get("name")),
            "oldPrice": None,
            "price": float(price),
            "sortOrder": 0,
            "vat": _to_int(_nested(item, "vat.value")),
            "serviceCodesUz": {"mxikCodeUz": _text(item.get("icps"))},
            "vendorCode": str(_to_int(item.get("code"))).zfill(6),
        }

    async def _availability(self, store_id: int) -> Dict[str, Any]:
        if store_id <= 0:
            raise YandexEatsError(400, "Неверный формат storeId")
        price_type = await self._price_type()
        items = await self._item_ext_all(store_id, price_type, zero_price=True)
        result = []
        for ext in items:
            item_id = _to_int(_nested(ext, "item.id"))
            if item_id <= 0:
                continue
            result.append({"id": str(item_id), "stock": _to_decimal(_nested(ext, "quantity.allowed"))})
        return {"items": result}

    async def _create_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        eats_id = _text(order.get("eatsId") or order.get("EatsId")).strip()
        if not eats_id:
            raise YandexEatsError(400, "Invalid order payload")

        cached_order_id = await self._read_order_dedupe(eats_id)
        if cached_order_id > 0:
            return {"result": "OK", "orderId": str(cached_order_id)}

        lock_key = self._order_lock_key(eats_id)
        lock_token = await redis_acquire_lock(
            lock_key,
            settings.marketplace_lock_ttl,
            wait_timeout_sec=settings.marketplace_lock_wait_timeout,
        )
        if not lock_token:
            raise YandexEatsError(409, "Order is already being processed", status_code=409)
        try:
            cached_order_id = await self._read_order_dedupe(eats_id)
            if cached_order_id > 0:
                return {"result": "OK", "orderId": str(cached_order_id)}

            existing = await self._order_doc(external_code=eats_id)
            if existing:
                existing_id = _to_int(existing.get("id"))
                await self._write_order_dedupe(eats_id, existing_id)
                return {"result": "OK", "orderId": str(existing_id)}

            result = await self._create_order_unlocked(order)
            await self._write_order_dedupe(eats_id, _to_int(result.get("orderId")))
            return result
        finally:
            await redis_release_lock(lock_key, lock_token)

    async def _create_order_unlocked(self, order: Dict[str, Any]) -> Dict[str, Any]:
        eats_id = _text(order.get("eatsId") or order.get("EatsId")).strip()
        restaurant_id = _to_int(order.get("restaurantId") or order.get("RestaurantId"))
        items = order.get("items") or order.get("Items") or []
        payment_info = order.get("paymentInfo") or order.get("PaymentInfo")
        if not eats_id or restaurant_id <= 0 or not isinstance(items, list) or not items or payment_info is None:
            raise YandexEatsError(400, "Некорректные данные в заказе")
        settings_map = await self._load_settings()
        order_from = _to_int(settings_map.get("ORDER_FROM"))
        delivery_type = _to_int(settings_map.get("ORDER_DELIVERY_TYPE"))
        price_type = _to_int(settings_map.get("PRICE_TYPE"))
        if order_from <= 0 or delivery_type <= 0 or price_type <= 0:
            raise YandexEatsError(113422, "Не установлены необходимые параметры заказа")

        delivery = order.get("deliveryInfo") or order.get("DeliveryInfo") or {}
        address = delivery.get("deliveryAddress") or delivery.get("DeliveryAddress") or {} if isinstance(delivery, dict) else {}
        comment = _text(order.get("comment") or order.get("Comment"))
        client_name = _text(delivery.get("clientName") or delivery.get("ClientName")) if isinstance(delivery, dict) else ""
        document = {
            "price_type_id": price_type,
            "from_id": order_from,
            "delivery_type_id": delivery_type,
            "date": int(time.time()),
            "description": f"{client_name}/{comment}",
            "external_code": eats_id,
            "stock_id": restaurant_id,
        }
        if isinstance(delivery, dict):
            document["phone"] = delivery.get("phoneNumber") or delivery.get("PhoneNumber")
            document["delivery_date"] = _parse_datetime_to_unix(delivery.get("deliveryDate") or delivery.get("DeliveryDate"))
        if isinstance(address, dict):
            document["address"] = address.get("full") or address.get("Full")
            document["location"] = {
                "latitude": _to_decimal(address.get("latitude") or address.get("Latitude")),
                "longitude": _to_decimal(address.get("longitude") or address.get("Longitude")),
            }

        item_ids = sorted({_to_int(item.get("id") or item.get("Id")) for item in items if isinstance(item, dict)})
        item_ids = [item_id for item_id in item_ids if item_id > 0]
        regos_items = await self._item_short_all(item_ids)
        found = {_to_int(item.get("id")) for item in regos_items}
        for item_id in item_ids:
            if item_id not in found:
                raise YandexEatsError(113422, f"Товар с ID {item_id} не найден в списке номенклатуры")

        operations = [
            {
                "item_id": _to_int(item.get("id") or item.get("Id")),
                "quantity": _to_decimal(item.get("quantity") or item.get("Quantity")),
                "price": _to_decimal(item.get("price") or item.get("Price")),
            }
            for item in items
            if isinstance(item, dict) and _to_int(item.get("id") or item.get("Id")) > 0
        ]
        async with RegosAPI(self._ci()) as api:
            response = await api.docs.order_delivery.add_full(
                DocOrderDeliveryAddFullRequest(document=document, operations=operations)
            )
        if not response.ok:
            raise YandexEatsError(113422, "Order creation rejected")
        doc_id = _to_int(getattr(response.result, "new_id", None))
        if doc_id <= 0:
            raise YandexEatsError(113422, "Заказ не создан")
        return {"result": "OK", "orderId": str(doc_id)}

    async def _item_groups(self) -> List[Dict[str, Any]]:
        async with RegosAPI(self._ci()) as api:
            response = await api.references.item_group.get(ItemGroupGetRequest())
        if not response.ok:
            raise YandexEatsError(111321, "REGOS item groups request rejected")
        return [
            row.model_dump(mode="json", by_alias=True)
            for row in (response.result or [])
        ]

    async def _item_short_all(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        if not item_ids:
            return []
        result: List[Dict[str, Any]] = []
        offset = 0
        total = 0
        async with RegosAPI(self._ci()) as api:
            while True:
                response = await api.references.item.get_short(
                    ItemGetRequest(
                        ids=item_ids,
                        offset=offset,
                        limit=250,
                        deleted_mark=False,
                    )
                )
                if not response.ok:
                    raise YandexEatsError(111321, "REGOS item short request rejected")
                chunk = [
                    row.model_dump(mode="json", by_alias=True)
                    for row in (response.result or [])
                ]
                result.extend(chunk)
                next_offset = _to_int(response.next_offset)
                total = _to_int(response.total, total)
                if next_offset == 0 or next_offset == offset or (total > 0 and next_offset >= total):
                    break
                offset = next_offset
        return result

    async def _order_doc(self, *, order_id: Optional[int] = None, external_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        async with RegosAPI(self._ci()) as api:
            response = await api.docs.order_delivery.get(
                DocOrderDeliveryGetRequest(
                    ids=[order_id] if order_id else None,
                    external_code=external_code or None,
                )
            )
        if not response.ok:
            raise YandexEatsError(111321, "REGOS order request rejected")
        rows = [
            row.model_dump(mode="json", by_alias=True)
            for row in (response.result or [])
        ]
        return rows[0] if rows else None

    async def _order_operations(self, order_id: int) -> List[Dict[str, Any]]:
        async with RegosAPI(self._ci()) as api:
            response = await api.docs.order_delivery.get_operations(
                DocOrderDeliveryOperationGetRequest(document_id=order_id)
            )
        if not response.ok:
            raise YandexEatsError(111321, "REGOS order operations request rejected")
        return [
            row.model_dump(mode="json", by_alias=True)
            for row in (response.result or [])
        ]

    async def _get_order(self, order_id: int) -> Dict[str, Any]:
        order = await self._order_doc(order_id=order_id)
        if not order:
            raise YandexEatsError(400, "Заказ не найден")
        operations = await self._order_operations(_to_int(order.get("id")))
        return {
            "discriminator": "yandex",
            "eatsId": _text(order.get("external_code")),
            "restaurantId": str(_to_int(_nested(order, "stock.id"))),
            "items": [
                {
                    "id": str(_to_int(_nested(op, "item.id"))),
                    "name": _text(_nested(op, "item.name")),
                    "quantity": _to_decimal(op.get("quantity")),
                    "price": _to_decimal(op.get("price")),
                }
                for op in operations
            ],
            "comment": _text(order.get("description")),
        }

    async def _cancel_order(self, order_id: int) -> Dict[str, Any]:
        order = await self._order_doc(order_id=order_id)
        if not order:
            raise YandexEatsError(400, "Заказ не найден")
        if _order_status_id(order) != 27:
            async with RegosAPI(self._ci()) as api:
                response = await api.docs.order_delivery.set_status(
                    DocOrderDeliverySetStatusRequest(id=_to_int(order.get("id")), status=27)
                )
            if not response.ok:
                raise YandexEatsError(111321, "REGOS order status update rejected")
        return {"result": "OK"}

    async def _get_order_status(self, order_id: int) -> Dict[str, Any]:
        order = await self._order_doc(order_id=order_id)
        if not order:
            raise YandexEatsError(400, "Заказ не найден")
        status = {
            22: "NEW",
            23: "ACCEPTED_BY_RESTAURANT",
            24: "COOKING",
            25: "COOKING",
            26: "READY",
            28: "READY",
            31: "READY",
            27: "CANCELLED",
        }.get(_order_status_id(order), "ERROR")
        return {"status": status, "comment": None, "updatedAt": _format_unix(order.get("last_update"))}

    @staticmethod
    def _parse_order_path(path: str) -> Tuple[Optional[int], str]:
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "order":
            return _to_int(parts[2]), "/".join(parts[3:])
        if len(parts) >= 2 and parts[0] == "order":
            return _to_int(parts[1]), "/".join(parts[2:])
        return None, ""
