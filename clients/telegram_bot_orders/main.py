import asyncio
import hashlib
import importlib
import json
import time
import uuid
from datetime import datetime, time as dt_time
from decimal import Decimal
from io import BytesIO
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from aiogram.types import Update as TelegramUpdate

from clients.base import ClientBase
from clients.telegram_bot_orders.texts import TelegramBotOrdersTexts as Texts
from clients.telegram_polling import telegram_polling_manager
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_ops,
    redis_error_contains,
    redis_expire_if_due,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import (
    IntegrationErrorModel,
    IntegrationErrorResponse,
    IntegrationSuccessResponse,
)
from schemas.integration.telegram_integration_base import IntegrationTelegramBase
from schemas.api.common.sort_orders import SortDirection, SortOrder
from schemas.api.docs.order_delivery import (
    DocOrderDelivery,
    DocOrderDeliveryAddFullRequest,
    DocOrderDeliveryAddRequest,
    DocOrderDeliveryGetRequest,
    DocOrderDeliveryOperation,
    Location,
)
from schemas.api.references.item import ItemExt, ItemGetExtImageSize, ItemGetExtRequest
from schemas.api.references.delivery_type import DeliveryType, DeliveryTypeGetRequest
from schemas.api.references.item_group import ItemGroup, ItemGroupGetRequest
from schemas.api.references.retail_card import RetailCardGetRequest
from schemas.api.references.fields import FieldValueAdd, FieldValueEdit
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.references.retail_customer import (
    RetailCustomerAddRequest,
    RetailCustomerEditRequest,
    RetailCustomerGetRequest,
)

try:
    qrcode = importlib.import_module("qrcode")
except Exception:  # pragma: no cover - optional dependency
    qrcode = None

logger = setup_logger("telegram_bot_orders")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_STREAM_WORKER_TASKS: Dict[str, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_GROUP_READY: Set[str] = set()
_STREAM_CLAIM_TS: Dict[str, int] = {}
_SETTINGS_LOCAL_CACHE: Dict[str, Tuple[int, Dict[str, str]]] = {}
_WEBHOOK_LOCAL_CACHE: Dict[str, int] = {}
_BOT_RUNTIME_CACHE: Dict[str, Tuple[str, Any]] = {}
_BOT_RUNTIME_LOCK = asyncio.Lock()

_ENQUEUE_DEDUPE_LUA = """
local ok = redis.call('set', KEYS[1], '1', 'EX', ARGV[1], 'NX')
if not ok then
  return 0
end
redis.call('xadd', KEYS[2], 'MAXLEN', '~', ARGV[2], '*', unpack(ARGV, 5))
if ARGV[4] == '1' then
  redis.call('expire', KEYS[2], ARGV[3])
end
return 1
"""


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


class TelegramOrdersSettings(Enum):
    BOT_TOKEN = "BOT_TOKEN"
    PRICE_TYPE_ID = "PRICE_TYPE_ID"
    STOCK_ID = "STOCK_ID"
    STOCK_ID_QUANTITY = "STOCK_ID_QUANTITY"
    SHOW_ZERO_QUANTITY = "SHOW_ZERO_QUANTITY"
    SHOW_WITHOUT_IMAGES = "SHOW_WITHOUT_IMAGES"
    SHOW_ITEMS_WITHOUT_PRICE = "SHOW_ITEMS_WITHOUT_PRICE"
    SHOW_ITEM_STOCK = "SHOW_ITEM_STOCK"
    ORDER_SOURCE_ID = "ORDER_SOURCE_ID"
    MIN_ORDER_AMOUNT = "MIN_ORDER_AMOUNT"
    WORK_TIME_ENABLED = "WORK_TIME_ENABLED"
    WORK_TIME_START = "WORK_TIME_START"
    WORK_TIME_END = "WORK_TIME_END"
    CUSTOMER_GROUP_ID = "CUSTOMER_GROUP_ID"
    WELCOME_MESSAGE = "WELCOME_MESSAGE"
    DELIVERY_TYPE_REQUIRED = "DELIVERY_TYPE_REQUIRED"
    ADDRESS_REQUIRED = "ADDRESS_REQUIRED"
    ITEM_GROUP_IDS = "ITEM_GROUP_IDS"
    CATALOG_PAGE_SIZE = "CATALOG_PAGE_SIZE"
    ORDERS_DISABLED = "ORDERS_DISABLED"
    ORDER_STATE_TTL = "ORDER_STATE_TTL"


class TelegramBotOrdersConfig:
    SETTINGS_TTL = max(int(app_settings.redis_cache_ttl or 0), 60)
    SETTINGS_STALE_TTL = max(SETTINGS_TTL * 10, 10 * 60)
    SETTINGS_LOCAL_TTL = min(30, max(5, SETTINGS_TTL // 4))
    SETTINGS_LOCAL_MAX = 10000
    SETTINGS_LOCK_TTL = 10
    SETTINGS_LOCK_WAIT_SECONDS = 2.0
    CART_TTL = 86400
    CATALOG_TTL = 60
    GROUPS_TTL = 300
    DELIVERY_TYPES_TTL = 300
    CATALOG_PAGE_SIZE = 5
    ORDERS_PAGE_SIZE = 5
    ORDER_STATE_TTL = 86400
    INTEGRATION_KEY = "telegram_bot_orders"
    WEBHOOK_BASE_URL = (
        f"{(app_settings.proxy_integration_url or app_settings.integration_url).rstrip('/')}/external"
    )
    WEBHOOK_REFRESH_TTL = max(int(app_settings.telegram_webhook_refresh_ttl or 0), 60)
    WEBHOOK_LOCAL_TTL = min(300, WEBHOOK_REFRESH_TTL)
    WEBHOOK_LOCK_TTL = 30
    REDIS_PREFIX = "tbo"
    STREAM_GROUP = "tbow"
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = max(int(app_settings.telegram_orders_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(app_settings.telegram_orders_stream_batch_size or 0), 1)
    STREAM_WORKERS_PER_STREAM = max(int(app_settings.telegram_orders_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = 3
    DEDUPE_TTL_SEC = 24 * 60 * 60
    SEND_CONCURRENCY = max(int(app_settings.telegram_orders_send_concurrency or 0), 1)


def _extract_chat_id(payload: dict) -> Optional[str]:
    for key in ("message", "edited_message", "callback_query"):
        block = payload.get(key)
        if isinstance(block, dict):
            chat = block.get("chat")
            if isinstance(chat, dict) and "id" in chat:
                return str(chat["id"])
            if key == "callback_query":
                msg = block.get("message")
                if isinstance(msg, dict):
                    chat = msg.get("chat")
                    if isinstance(chat, dict) and "id" in chat:
                        return str(chat["id"])
    return None


class TelegramBotOrdersIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False
        self._telegram_field_supported: Optional[bool] = None
        self._owns_bot_session = True
        self._bot_token_fingerprint = ""

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_bot_session:
            await self._close_bot_session()

    async def _close_bot_session(self) -> None:
        if self.bot and getattr(self.bot, "session", None):
            try:
                await self.bot.session.close()
            except Exception as error:
                logger.warning("Failed to close bot session: %s", error)
        self.bot = None
        self.dispatcher = None
        self.handlers_registered = False

    def _error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _redis_enabled() -> bool:
        return bool(app_settings.redis_enabled and redis_ops)

    @classmethod
    def _require_redis(cls) -> None:
        if not cls._redis_enabled():
            raise RuntimeError("Redis is required for telegram_bot_orders")

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        if not tokens:
            return TelegramBotOrdersConfig.REDIS_PREFIX
        return f"{TelegramBotOrdersConfig.REDIS_PREFIX}:{':'.join(tokens)}"

    @staticmethod
    def _token_fingerprint(token: str) -> str:
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _kind_code(kind: str) -> str:
        return {
            "telegram_update": "u",
            "send_messages": "s",
            "webhook": "w",
        }.get(kind, "x")

    def _settings_cache_key(self) -> str:
        return self._redis_key("st", self.connected_integration_id)

    def _settings_stale_cache_key(self) -> str:
        return self._redis_key("st", self.connected_integration_id, "s")

    def _settings_fetch_lock_key(self) -> str:
        return self._redis_key("stl", self.connected_integration_id)

    @classmethod
    def _updates_stream_key(cls) -> str:
        return cls._redis_key("s", "u")

    @classmethod
    def _jobs_stream_key(cls) -> str:
        return cls._redis_key("s", "j")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._redis_key("s", "dlq")

    @classmethod
    def _stream_key_for_kind(cls, kind: str) -> str:
        if kind == "telegram_update":
            return cls._updates_stream_key()
        return cls._jobs_stream_key()

    @classmethod
    def _dedupe_key(cls, connected_integration_id: str, kind: str, event_id: str) -> str:
        event_hash = hashlib.sha256(str(event_id or "").encode("utf-8")).hexdigest()[:20]
        return cls._redis_key("d", cls._kind_code(kind), connected_integration_id, event_hash)

    @classmethod
    def _retry_dedupe_key(
        cls,
        connected_integration_id: str,
        kind: str,
        event_id: str,
        attempt: int,
    ) -> str:
        event_hash = hashlib.sha256(str(event_id or "").encode("utf-8")).hexdigest()[:20]
        return cls._redis_key(
            "r",
            cls._kind_code(kind),
            connected_integration_id,
            event_hash,
            str(max(int(attempt), 1)),
        )

    @classmethod
    def _worker_task_key(cls, stream_key: str, worker_index: int = 0) -> str:
        return f"{str(stream_key or '').strip()}:{int(worker_index)}"

    @classmethod
    def _resolve_stream_ttl(cls) -> int:
        return redis_ttl_seconds(TelegramBotOrdersConfig.STREAM_TTL_SEC)

    @classmethod
    async def _redis_delete(cls, *keys: str) -> None:
        cls._require_redis()
        valid = [str(key).strip() for key in keys if str(key or "").strip()]
        if valid:
            await redis_ops.delete(*valid)

    @classmethod
    async def _touch_stream_ttl(cls, stream_key: str, *, force: bool = False) -> None:
        cls._require_redis()
        await redis_expire_if_due(
            stream_key,
            cls._resolve_stream_ttl(),
            _STREAM_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str, *, force: bool = False) -> None:
        cls._require_redis()
        if not force and stream_key in _STREAM_GROUP_READY:
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            TelegramBotOrdersConfig.STREAM_GROUP,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        _STREAM_GROUP_READY.add(stream_key)

    @classmethod
    def _serialize_stream_fields(cls, fields: Dict[str, Any]) -> Dict[str, str]:
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = _json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)
        return serialized

    @classmethod
    async def _enqueue_stream(cls, stream_key: str, fields: Dict[str, Any]) -> None:
        cls._require_redis()
        await redis_stream_add_with_ttl(
            stream_key,
            cls._serialize_stream_fields(fields),
            maxlen=TelegramBotOrdersConfig.STREAM_MAXLEN,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )

    @classmethod
    async def _enqueue_stream_deduped(
        cls,
        *,
        stream_key: str,
        dedupe_key: str,
        fields: Dict[str, Any],
    ) -> bool:
        cls._require_redis()
        now_ts = _now_ts()
        stream_ttl = cls._resolve_stream_ttl()
        should_touch = (
            now_ts - int(_STREAM_TTL_TOUCH_TS.get(stream_key) or 0)
            >= min(3600, max(10, stream_ttl // 4))
        )
        field_args: List[str] = []
        for key, value in cls._serialize_stream_fields(fields).items():
            field_args.extend([key, value])
        result = await redis_ops.eval(
            _ENQUEUE_DEDUPE_LUA,
            2,
            dedupe_key,
            stream_key,
            str(TelegramBotOrdersConfig.DEDUPE_TTL_SEC),
            str(TelegramBotOrdersConfig.STREAM_MAXLEN),
            str(stream_ttl),
            "1" if should_touch else "0",
            *field_args,
        )
        if should_touch and int(result or 0) == 1:
            _STREAM_TTL_TOUCH_TS[stream_key] = now_ts
        return int(result or 0) == 1

    @classmethod
    async def _enqueue_event(
        cls,
        connected_integration_id: str,
        *,
        kind: str,
        payload: Any,
        action: Optional[str] = None,
        event_id: Optional[str] = None,
        attempt: int = 0,
        last_error: Optional[str] = None,
    ) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        if kind not in {"telegram_update", "send_messages", "webhook"}:
            raise ValueError(f"Unsupported stream kind: {kind}")
        await cls._ensure_stream_workers(ensure_groups=False)
        stream_key = cls._stream_key_for_kind(kind)
        fields = {
            "connected_integration_id": ci,
            "kind": kind,
            "payload": payload,
            "action": action or "",
            "event_id": event_id or "",
            "attempt": str(max(int(attempt), 0)),
            "last_error": last_error or "",
            "enqueued_at": str(_now_ts()),
        }
        if event_id:
            attempt_value = max(int(attempt or 0), 0)
            dedupe_key = (
                cls._dedupe_key(ci, kind, event_id)
                if attempt_value <= 0
                else cls._retry_dedupe_key(ci, kind, event_id, attempt_value)
            )
            return await cls._enqueue_stream_deduped(
                stream_key=stream_key,
                dedupe_key=dedupe_key,
                fields=fields,
            )
        await cls._enqueue_stream(stream_key, fields)
        return True

    @classmethod
    def _stream_worker_specs(cls) -> List[Tuple[str, int]]:
        return [
            (stream_key, index)
            for stream_key in (cls._updates_stream_key(), cls._jobs_stream_key())
            for index in range(TelegramBotOrdersConfig.STREAM_WORKERS_PER_STREAM)
        ]

    @classmethod
    def _stream_workers_ready(cls) -> bool:
        for stream_key, index in cls._stream_worker_specs():
            task = _STREAM_WORKER_TASKS.get(cls._worker_task_key(stream_key, index))
            if not task or task.done():
                return False
        return True

    @classmethod
    async def _close_bot_runtime_cache(cls, connected_integration_id: Optional[str] = None) -> int:
        ci = str(connected_integration_id or "").strip()
        async with _BOT_RUNTIME_LOCK:
            if ci:
                entries = [(_BOT_RUNTIME_CACHE.pop(ci, None))]
            else:
                entries = list(_BOT_RUNTIME_CACHE.values())
                _BOT_RUNTIME_CACHE.clear()
        closed = 0
        for entry in entries:
            if not entry:
                continue
            _, runtime = entry
            if isinstance(runtime, TelegramBotOrdersIntegration):
                await runtime._close_bot_session()
                closed += 1
        return closed

    @classmethod
    async def _ensure_stream_workers(cls, *, ensure_groups: bool = True) -> None:
        cls._require_redis()
        if not ensure_groups and cls._stream_workers_ready():
            return
        for stream_key, index in cls._stream_worker_specs():
            if ensure_groups:
                await cls._ensure_consumer_group(stream_key)
            task_key = cls._worker_task_key(stream_key, index)
            async with _STREAM_WORKER_LOCK:
                task = _STREAM_WORKER_TASKS.get(task_key)
                if task and not task.done():
                    continue
                _STREAM_WORKER_TASKS[task_key] = asyncio.create_task(
                    cls._stream_worker_loop(stream_key, index),
                    name=f"tbo_stream_{stream_key.rsplit(':', 1)[-1]}_{index}",
                )

    @classmethod
    async def shutdown_all(cls) -> None:
        async with _STREAM_WORKER_LOCK:
            tasks = list(_STREAM_WORKER_TASKS.values())
            _STREAM_WORKER_TASKS.clear()
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping Telegram orders stream worker")
        await cls._close_bot_runtime_cache()

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        cls._require_redis()
        await cls._ensure_stream_workers()
        return {"streams": 2, "workers": len(_STREAM_WORKER_TASKS)}

    @classmethod
    def _decode_stream_payload(cls, raw: Any) -> Any:
        if isinstance(raw, (dict, list)):
            return raw
        try:
            return _json_loads(str(raw or ""))
        except Exception:
            return {}

    @classmethod
    def _stream_entry_attempt(cls, fields: Dict[str, Any]) -> int:
        try:
            return max(int(str(fields.get("attempt") or "0").strip()), 0)
        except Exception:
            return 0

    @staticmethod
    def _is_error_result(result: Any) -> bool:
        if isinstance(result, IntegrationErrorResponse):
            return True
        if isinstance(result, dict):
            if result.get("ok") is False:
                return True
            payload = result.get("result")
            return isinstance(payload, dict) and "error" in payload
        return False

    @staticmethod
    def _result_error_text(result: Any) -> str:
        if isinstance(result, IntegrationErrorResponse):
            return str(result.result.description)
        if isinstance(result, dict):
            payload = result.get("result")
            if isinstance(payload, dict):
                return str(payload.get("description") or payload)
            return str(result)
        return str(result)

    @classmethod
    async def _ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_ops.xack(stream_key, TelegramBotOrdersConfig.STREAM_GROUP, entry_id)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                TelegramBotOrdersConfig.STREAM_GROUP,
                consumer,
                min_idle_time=TelegramBotOrdersConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=TelegramBotOrdersConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            logger.warning("Telegram orders stream xautoclaim failed: stream=%s error=%s", stream_key, error)
            return []

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @classmethod
    async def _stream_worker_loop(cls, stream_key: str, worker_index: int) -> None:
        task_key = cls._worker_task_key(stream_key, worker_index)
        consumer = f"{_INSTANCE_ID}:{stream_key.rsplit(':', 1)[-1]}:{worker_index}"
        logger.info("Telegram orders stream worker started: stream=%s", stream_key)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._touch_stream_ttl(stream_key)
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= TelegramBotOrdersConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        for entry_id, fields in await cls._process_claimed_entries(stream_key, consumer):
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=entry_id,
                                fields=fields,
                            )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=TelegramBotOrdersConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=TelegramBotOrdersConfig.STREAM_BATCH_SIZE,
                            block=TelegramBotOrdersConfig.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(stream_key, force=True)
                            continue
                        raise

                    for _, entries in records or []:
                        for entry_id, fields in entries or []:
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=str(entry_id),
                                fields=fields if isinstance(fields, dict) else {},
                            )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception("Telegram orders stream worker error: stream=%s error=%s", stream_key, error)
                    await asyncio.sleep(2)
        finally:
            async with _STREAM_WORKER_LOCK:
                current = _STREAM_WORKER_TASKS.get(task_key)
                if current is asyncio.current_task():
                    _STREAM_WORKER_TASKS.pop(task_key, None)

    @classmethod
    async def _process_stream_entry(
        cls,
        *,
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        ci = str(fields.get("connected_integration_id") or "").strip()
        kind = str(fields.get("kind") or "").strip()
        action = str(fields.get("action") or "").strip() or None
        event_id = str(fields.get("event_id") or "").strip()
        payload = cls._decode_stream_payload(fields.get("payload"))
        if not ci or kind not in {"telegram_update", "send_messages", "webhook"}:
            logger.warning("Telegram orders stream entry has invalid payload: entry_id=%s fields=%s", entry_id, fields)
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        attempt = cls._stream_entry_attempt(fields)
        worker = cls()
        worker.connected_integration_id = ci
        chat_lock_key = ""
        chat_lock_token: Optional[str] = None
        try:
            if kind == "telegram_update":
                if not isinstance(payload, dict):
                    raise ValueError("Telegram update payload must be an object")
                chat_id = _extract_chat_id(payload)
                if chat_id:
                    chat_lock_key = cls._redis_key("cl", ci, chat_id)
                    chat_lock_token = await cls._acquire_redis_lock(
                        chat_lock_key,
                        30,
                        wait_seconds=10.0,
                    )
                    if not chat_lock_token:
                        raise TimeoutError(f"Timed out waiting for Telegram orders chat lock {ci}:{chat_id}")
                result = await worker._process_telegram_update(payload)
            elif kind == "send_messages":
                messages = payload.get("messages") if isinstance(payload, dict) else payload
                if not isinstance(messages, list):
                    raise ValueError("send_messages payload must contain messages list")
                result = await worker._send_messages_now(messages)
            else:
                webhook_data = payload if isinstance(payload, dict) else {}
                result = await worker._process_webhook(action=action, data=webhook_data)

            if cls._is_error_result(result):
                raise RuntimeError(cls._result_error_text(result))

            logger.debug(
                "Telegram orders stream job processed: ci=%s kind=%s entry_id=%s status=%s",
                ci,
                kind,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            next_attempt = attempt + 1
            if next_attempt >= TelegramBotOrdersConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(_now_ts())
                dlq_payload["error"] = str(error)
                await cls._enqueue_stream(cls._dlq_stream_key(), dlq_payload)
                if event_id:
                    await cls._redis_delete(cls._dedupe_key(ci, kind, event_id))
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "Telegram orders stream job moved to DLQ: ci=%s kind=%s entry_id=%s error=%s",
                    ci,
                    kind,
                    entry_id,
                    error,
                )
                return
            await cls._enqueue_event(
                ci,
                kind=kind,
                payload=payload,
                action=action,
                event_id=event_id,
                attempt=next_attempt,
                last_error=str(error),
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "Telegram orders stream job requeued: ci=%s kind=%s entry_id=%s attempt=%s error=%s",
                ci,
                kind,
                entry_id,
                next_attempt,
                error,
            )
        finally:
            if chat_lock_key and chat_lock_token:
                await cls._release_redis_lock(chat_lock_key, chat_lock_token)
            await worker.__aexit__(None, None, None)

    @staticmethod
    async def _acquire_redis_lock(
        key: str,
        ttl_sec: int,
        *,
        wait_seconds: float = 0.0,
    ) -> Optional[str]:
        TelegramBotOrdersIntegration._require_redis()
        token = uuid.uuid4().hex
        deadline = asyncio.get_running_loop().time() + max(float(wait_seconds or 0.0), 0.0)
        while True:
            ok = await redis_ops.set(key, token, ex=max(int(ttl_sec), 1), nx=True)
            if ok:
                return token
            if asyncio.get_running_loop().time() >= deadline:
                return None
            await asyncio.sleep(0.05)

    @staticmethod
    async def _release_redis_lock(key: str, token: Optional[str]) -> None:
        if not (TelegramBotOrdersIntegration._redis_enabled() and token):
            return
        script = (
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end"
        )
        try:
            await redis_ops.eval(script, 1, key, token)
        except Exception as error:
            logger.warning("Failed to release Redis lock %s: %s", key, error)

    @classmethod
    def _read_local_settings_cache(cls, cache_key: str) -> Optional[Dict[str, str]]:
        entry = _SETTINGS_LOCAL_CACHE.get(cache_key)
        if not entry:
            return None
        expires_at, settings_map = entry
        if expires_at <= _now_ts():
            _SETTINGS_LOCAL_CACHE.pop(cache_key, None)
            return None
        return dict(settings_map)

    @classmethod
    def _write_local_settings_cache(cls, cache_key: str, settings_map: Dict[str, str]) -> None:
        now_ts = _now_ts()
        if len(_SETTINGS_LOCAL_CACHE) >= TelegramBotOrdersConfig.SETTINGS_LOCAL_MAX:
            for key, (expires_at, _) in list(_SETTINGS_LOCAL_CACHE.items()):
                if expires_at <= now_ts:
                    _SETTINGS_LOCAL_CACHE.pop(key, None)
            while len(_SETTINGS_LOCAL_CACHE) >= TelegramBotOrdersConfig.SETTINGS_LOCAL_MAX:
                _SETTINGS_LOCAL_CACHE.pop(next(iter(_SETTINGS_LOCAL_CACHE)), None)
        _SETTINGS_LOCAL_CACHE[cache_key] = (
            now_ts + TelegramBotOrdersConfig.SETTINGS_LOCAL_TTL,
            dict(settings_map),
        )

    @staticmethod
    def _normalize_settings_map(raw: Dict[str, Any]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in (raw or {}).items():
            normalized_key = str(key or "").strip().lower()
            if normalized_key:
                normalized[normalized_key] = str(value or "").strip()
        return normalized

    async def _fetch_settings(self, cache_key: str) -> Dict[str, str]:
        self._require_redis()
        local = self._read_local_settings_cache(cache_key)
        if local is not None:
            return local
        try:
            cached = await redis_ops.get(cache_key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                cached_map = self._normalize_settings_map(_json_loads(cached))
                self._write_local_settings_cache(cache_key, cached_map)
                return cached_map
        except Exception as error:
            logger.warning(Texts.log_redis_error(error))

        lock_token = await self._acquire_redis_lock(
            self._settings_fetch_lock_key(),
            TelegramBotOrdersConfig.SETTINGS_LOCK_TTL,
            wait_seconds=TelegramBotOrdersConfig.SETTINGS_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            stale = await self._read_settings_stale_cache()
            if stale is not None:
                return stale
            raise TimeoutError(
                f"Timed out waiting for Telegram orders settings refresh for ID {self.connected_integration_id}"
            )

        try:
            cached = await redis_ops.get(cache_key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                cached_map = self._normalize_settings_map(_json_loads(cached))
                self._write_local_settings_cache(cache_key, cached_map)
                return cached_map

            async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
                settings_response = (
                    await api.integrations.connected_integration_setting.get(
                        ConnectedIntegrationSettingRequest(
                            connected_integration_id=self.connected_integration_id,
                        )
                    )
                ).result

            settings_map = self._normalize_settings_map(
                {item.key: item.value for item in (settings_response or [])}
            )
            payload = _json_dumps(settings_map)
            self._write_local_settings_cache(cache_key, settings_map)
            self._write_local_settings_cache(self._settings_stale_cache_key(), settings_map)
            async with redis_ops.pipeline(transaction=True) as pipe:
                await pipe.setex(cache_key, TelegramBotOrdersConfig.SETTINGS_TTL, payload)
                await pipe.setex(
                    self._settings_stale_cache_key(),
                    TelegramBotOrdersConfig.SETTINGS_STALE_TTL,
                    payload,
                )
                await pipe.execute()
            return settings_map
        except Exception:
            stale = await self._read_settings_stale_cache()
            if stale is not None:
                return stale
            raise
        finally:
            await self._release_redis_lock(self._settings_fetch_lock_key(), lock_token)

    async def _read_settings_stale_cache(self) -> Optional[Dict[str, str]]:
        key = self._settings_stale_cache_key()
        local = self._read_local_settings_cache(key)
        if local is not None:
            return local
        try:
            cached = await redis_ops.get(key)
            if not cached:
                return None
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            settings_map = self._normalize_settings_map(_json_loads(cached))
            self._write_local_settings_cache(key, settings_map)
            return settings_map
        except Exception:
            return None

    async def _clear_settings_cache(self) -> None:
        self._require_redis()
        keys = [self._settings_cache_key(), self._settings_stale_cache_key()]
        for key in keys:
            _SETTINGS_LOCAL_CACHE.pop(key, None)
        await redis_ops.delete(*keys)

    async def _write_settings_cache(self, settings_map: Dict[str, str]) -> None:
        self._require_redis()
        normalized = self._normalize_settings_map(settings_map)
        payload = _json_dumps(normalized)
        self._write_local_settings_cache(self._settings_cache_key(), normalized)
        self._write_local_settings_cache(self._settings_stale_cache_key(), normalized)
        async with redis_ops.pipeline(transaction=True) as pipe:
            await pipe.setex(self._settings_cache_key(), TelegramBotOrdersConfig.SETTINGS_TTL, payload)
            await pipe.setex(
                self._settings_stale_cache_key(),
                TelegramBotOrdersConfig.SETTINGS_STALE_TTL,
                payload,
            )
            await pipe.execute()

    async def _get_settings_map(self) -> Dict[str, str]:
        return await self._fetch_settings(self._settings_cache_key())

    async def _initialize_bot(self) -> None:
        if self.bot:
            return
        ci = str(self.connected_integration_id or "").strip()
        if not ci:
            raise ValueError(Texts.ERROR_CONNECTED_ID_MISSING)
        settings_map = await self._get_settings_map()
        bot_token = settings_map.get(TelegramOrdersSettings.BOT_TOKEN.value.lower())
        if not bot_token:
            raise ValueError(Texts.ERROR_BOT_TOKEN_MISSING)
        token_fingerprint = self._token_fingerprint(bot_token)
        async with _BOT_RUNTIME_LOCK:
            cached = _BOT_RUNTIME_CACHE.get(ci)
            if cached and cached[0] == token_fingerprint:
                runtime = cached[1]
                self.bot = runtime.bot
                self.dispatcher = runtime.dispatcher
                self.handlers_registered = runtime.handlers_registered
                self._bot_token_fingerprint = token_fingerprint
                self._owns_bot_session = False
                return
            if cached:
                _BOT_RUNTIME_CACHE.pop(ci, None)
                await cached[1]._close_bot_session()
            try:
                self.bot = Bot(
                    token=bot_token,
                    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
                )
            except Exception as error:
                logger.error("Failed to initialize Telegram orders bot: %s", error)
                raise
            self._bot_token_fingerprint = token_fingerprint
            await self._setup_handlers()
            self._owns_bot_session = False
            _BOT_RUNTIME_CACHE[ci] = (token_fingerprint, self)

    @staticmethod
    def _parse_bool(value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
        return None

    def _should_show_item_stock(self, settings_map: Dict[str, str]) -> bool:
        value = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.SHOW_ITEM_STOCK.value.lower())
        )
        return True if value is None else bool(value)

    @staticmethod
    def _parse_time(value: Optional[str]) -> Optional[dt_time]:
        if value is None:
            return None
        text = str(value).strip()
        try:
            return datetime.strptime(text, "%H:%M").time()
        except ValueError:
            return None

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(app_settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _polling_key(self) -> str:
        return f"{TelegramBotOrdersConfig.INTEGRATION_KEY}:{self.connected_integration_id or 'unknown'}"

    @staticmethod
    def _resolve_webhook_base_url() -> str:
        base_url = str(
            app_settings.proxy_integration_url or app_settings.integration_url
        ).strip()
        if not base_url:
            base_url = str(app_settings.integration_url).strip()
        return f"{base_url.rstrip('/')}/external"

    def _build_webhook_url(self) -> str:
        return f"{self._resolve_webhook_base_url()}/{self.connected_integration_id}/external/"

    def _webhook_refresh_cache_key(self) -> str:
        return self._redis_key("wh", self.connected_integration_id)

    def _webhook_refresh_lock_key(self) -> str:
        return self._redis_key("whl", self.connected_integration_id)

    async def _touch_webhook_refresh_cache(self) -> None:
        if not self.connected_integration_id:
            return
        self._require_redis()
        _WEBHOOK_LOCAL_CACHE[self._webhook_refresh_cache_key()] = (
            _now_ts() + TelegramBotOrdersConfig.WEBHOOK_LOCAL_TTL
        )
        try:
            await redis_ops.setex(
                self._webhook_refresh_cache_key(),
                TelegramBotOrdersConfig.WEBHOOK_REFRESH_TTL,
                "1",
            )
        except Exception as error:
            logger.warning("Failed to update webhook refresh cache: %s", error)

    async def _clear_webhook_refresh_cache(self) -> None:
        if not self.connected_integration_id:
            return
        self._require_redis()
        _WEBHOOK_LOCAL_CACHE.pop(self._webhook_refresh_cache_key(), None)
        try:
            await redis_ops.delete(self._webhook_refresh_cache_key())
        except Exception as error:
            logger.warning("Failed to clear webhook refresh cache: %s", error)

    async def _ensure_webhook_from_regos(self, *, force: bool = False) -> None:
        if self._is_longpolling_mode() or not self.bot or not self.connected_integration_id:
            return

        cache_key = self._webhook_refresh_cache_key()
        if not force and int(_WEBHOOK_LOCAL_CACHE.get(cache_key) or 0) > _now_ts():
            return
        if not force:
            try:
                if await redis_ops.exists(cache_key):
                    _WEBHOOK_LOCAL_CACHE[cache_key] = (
                        _now_ts() + TelegramBotOrdersConfig.WEBHOOK_LOCAL_TTL
                    )
                    return
            except Exception as error:
                logger.warning("Failed to read webhook refresh cache: %s", error)

        lock_token = await self._acquire_redis_lock(
            self._webhook_refresh_lock_key(),
            TelegramBotOrdersConfig.WEBHOOK_LOCK_TTL,
            wait_seconds=TelegramBotOrdersConfig.SETTINGS_LOCK_WAIT_SECONDS if force else 0.0,
        )
        if not lock_token:
            logger.debug(
                "Skipping Telegram orders webhook refresh for ID %s: another instance is refreshing it",
                self.connected_integration_id,
            )
            return

        webhook_url = self._build_webhook_url()
        try:
            if not force:
                try:
                    if await redis_ops.exists(cache_key):
                        _WEBHOOK_LOCAL_CACHE[cache_key] = (
                            _now_ts() + TelegramBotOrdersConfig.WEBHOOK_LOCAL_TTL
                        )
                        return
                except Exception as error:
                    logger.warning("Failed to re-read webhook refresh cache: %s", error)
            info = await self.bot.get_webhook_info()
            current_url = (getattr(info, "url", "") or "").rstrip("/")
            if current_url != webhook_url.rstrip("/"):
                await self.bot.set_webhook(url=webhook_url)
                logger.info("Webhook url updated from REGOS webhook: %s", webhook_url)
            await self._touch_webhook_refresh_cache()
        except Exception as error:
            logger.warning("Failed to refresh webhook from REGOS webhook: %s", error)
            if force:
                raise
        finally:
            await self._release_redis_lock(self._webhook_refresh_lock_key(), lock_token)

    def _is_work_time(self, settings_map: Dict[str, str]) -> bool:
        enabled = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_ENABLED.value.lower())
        )
        if not enabled:
            return True
        start = self._parse_time(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_START.value.lower())
        )
        end = self._parse_time(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_END.value.lower())
        )
        if not start or not end:
            return True
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    def _main_menu_keyboard(
        self, orders_disabled: bool
    ) -> types.ReplyKeyboardMarkup:
        if orders_disabled:
            return types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text=Texts.BUTTON_MENU_CARDS)]],
                resize_keyboard=True,
            )
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=Texts.BUTTON_MENU_CATALOG),
                    types.KeyboardButton(text=Texts.BUTTON_MENU_CART),
                ],
                [types.KeyboardButton(text=Texts.BUTTON_MENU_ORDER)],
                [types.KeyboardButton(text=Texts.BUTTON_MENU_ORDERS)],
                [types.KeyboardButton(text=Texts.BUTTON_MENU_CARDS)],
            ],
            resize_keyboard=True,
        )

    async def _send_main_menu(
        self, message: types.Message, text: Optional[str] = None
    ) -> None:
        settings_map = await self._get_settings_map()
        orders_disabled = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.ORDERS_DISABLED.value.lower())
        )
        message_text = text or Texts.MAIN_MENU
        await message.answer(
            message_text,
            reply_markup=self._main_menu_keyboard(bool(orders_disabled)),
        )

    def _cart_keyboard(self, labels: List[str]) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        row: List[types.KeyboardButton] = []
        for label in labels:
            row.append(types.KeyboardButton(text=label))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append(
            [
                types.KeyboardButton(text=Texts.BUTTON_CART_CLEAR),
                types.KeyboardButton(text=Texts.BUTTON_MENU_ORDER),
            ]
        )
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    async def _send_cart(self, message: types.Message) -> None:
        cart = await self._get_cart(str(message.chat.id))
        if not cart:
            await self._clear_cart_state(str(message.chat.id))
            await self._send_main_menu(message, Texts.CART_EMPTY)
            return
        labels = [
            Texts.cart_button_label(idx, row["name"])
            for idx, row in enumerate(cart, start=1)
        ]
        item_buttons = [
            {"label": label, "item_id": row["item_id"]}
            for label, row in zip(labels, cart)
        ]
        await self._save_cart_state(
            str(message.chat.id),
            awaiting_remove=False,
            item_ids=[row["item_id"] for row in cart],
            item_buttons=item_buttons,
        )
        await message.answer(
            self._format_cart(cart), reply_markup=self._cart_keyboard(labels)
        )

    async def _handle_text(self, message: types.Message) -> None:
        text = message.text.strip() if message.text else ""
        chat_id = str(message.chat.id)
        if text.startswith("/start"):
            await self._send_welcome(message)
            return
        if text.startswith("/"):
            await self._send_main_menu(message, Texts.MAIN_MENU_USE_BUTTONS)
            return
        settings_map = await self._get_settings_map()
        orders_disabled = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.ORDERS_DISABLED.value.lower())
        )
        if orders_disabled:
            if text == Texts.BUTTON_MENU_CARDS:
                await self._handle_cards(message)
                return
            await self._handle_cards(message)
            return
        orders_state = await self._get_orders_state(chat_id)
        if text == Texts.BUTTON_MENU_MAIN:
            await self._clear_orders_state(chat_id)
            await self._save_catalog_state(
                chat_id,
                None,
                0,
                view="categories",
                group_id=None,
                group_name=None,
                awaiting_search=False,
                awaiting_qty=False,
                qty_item_id=None,
                awaiting_action=None,
                page_item_ids=[],
                page_items=[],
                selected_item_id=None,
                category_map={},
            )
            await self._send_main_menu(message, Texts.MAIN_MENU)
            return
        if text in {Texts.BUTTON_MENU_CATALOG, Texts.BUTTON_CATEGORIES}:
            await self._clear_orders_state(chat_id)
            await self._send_categories(message)
            return
        if text == Texts.BUTTON_MENU_CART:
            await self._clear_orders_state(chat_id)
            await self._send_cart(message)
            return
        if text == Texts.BUTTON_MENU_ORDER:
            await self._clear_orders_state(chat_id)
            await self._handle_order(message)
            return
        if text == Texts.BUTTON_MENU_ORDERS:
            await self._send_orders_list(message)
            return
        if text == Texts.BUTTON_MENU_CARDS:
            await self._clear_orders_state(chat_id)
            await self._handle_cards(message)
            return
        if text == Texts.BUTTON_CART_CLEAR:
            await self._clear_cart(chat_id)
            await self._clear_cart_state(chat_id)
            await self._send_cart(message)
            return
        if (
            text == Texts.BUTTON_ORDER_BACK_TO_LIST
            and orders_state.get("view") == "orders_detail"
        ):
            await self._send_orders_list(message)
            return
        if text == Texts.BUTTON_BACK and orders_state.get("view") == "orders_list":
            await self._send_orders_list(message, prev_page=True)
            return
        if text == Texts.BUTTON_NEXT and orders_state.get("view") == "orders_list":
            await self._send_orders_list(message, next_page=True)
            return
        if text == Texts.BUTTON_BACK:
            await self._send_catalog_page(chat_id, prev_page=True)
            return
        if text == Texts.BUTTON_NEXT:
            await self._send_catalog_page(chat_id, next_page=True)
            return
        if text == Texts.BUTTON_BACK_TO_LIST:
            await self._send_catalog_page(chat_id)
            return
        if text == Texts.BUTTON_BACK_TO_CATALOG:
            await self._send_categories(message)
            return
        if text == Texts.BUTTON_ALL_ITEMS:
            await self._select_category(chat_id, None, Texts.BUTTON_ALL_ITEMS, message)
            return
        if text == Texts.BUTTON_SEARCH:
            await self._send_catalog_search_prompt(chat_id)
            return
        if text == Texts.BUTTON_ADD_ONE:
            state = await self._get_catalog_state(chat_id)
            if state.get("view") == "detail" and state.get("selected_item_id"):
                result = await self._add_item_to_cart(
                    chat_id, state["selected_item_id"], Decimal("1")
                )
                await message.answer(result or Texts.ITEM_NOT_FOUND)
                return
        if text == Texts.BUTTON_ADD_OTHER:
            state = await self._get_catalog_state(chat_id)
            if state.get("view") == "detail" and state.get("selected_item_id"):
                await self._prompt_item_quantity(
                    message, state["selected_item_id"]
                )
                return

        if await self._handle_order_text_input(message):
            return
        if await self._handle_qty_input(message):
            return
        if await self._handle_search_input(message):
            return
        if await self._handle_cart_item_select(message):
            return
        if await self._handle_cart_number_action(message):
            return
        if await self._handle_orders_select(message):
            return

        state = await self._get_catalog_state(chat_id)
        if state.get("view") == "list":
            page_items = state.get("page_items") or []
            for item in page_items:
                if text == item.get("label"):
                    await self._send_catalog_detail(chat_id, item.get("id"))
                    return
        category_map = state.get("category_map") or {}
        if text in category_map:
            await self._select_category(chat_id, category_map[text], text, message)
            return

        if state.get("view") == "categories" and text:
            await message.answer(Texts.CATEGORIES_UNKNOWN)
            await self._send_categories(message)
            return

        await self._send_main_menu(message, Texts.MAIN_MENU)

    async def _send_welcome(self, message: types.Message) -> None:
        settings_map = await self._get_settings_map()
        greeting = settings_map.get(
            TelegramOrdersSettings.WELCOME_MESSAGE.value.lower()
        )
        await self._send_main_menu(message, greeting or Texts.WELCOME)
        customer = await self._find_customer_by_chat(str(message.chat.id))
        if not customer:
            await self._request_phone(message)

    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        await self._initialize_bot()
        await self._setup_handlers()
        if not self.bot:
            return {"status": "connected"}

        logger.info("telegram_update_mode=%r is_longpolling=%s",
                    app_settings.telegram_update_mode, self._is_longpolling_mode())

        if self._is_longpolling_mode():
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self._clear_webhook_refresh_cache()
            await telegram_polling_manager.start(self._polling_key(), self.bot, self.dispatcher)
            logger.info("Webhook deleted (longpolling mode).")
            return {"status": "connected", "mode": "longpolling"}

        await telegram_polling_manager.stop(self._polling_key())

        webhook_url = self._build_webhook_url()
        try:
            await self._ensure_webhook_from_regos(force=True)
            await self._ensure_stream_workers()
            info = await self.bot.get_webhook_info()
            logger.info("Webhook set result url=%r", info.url)
            return {"status": "connected", "mode": "webhook", "webhook_url": info.url}
        except Exception as e:
            logger.exception("Failed to set webhook url=%r error=%s", webhook_url, e)
            raise

    async def disconnect(self, **kwargs) -> Dict[str, Any]:
        await telegram_polling_manager.stop(self._polling_key())
        cached = _BOT_RUNTIME_CACHE.get(str(self.connected_integration_id or "").strip())
        if not self.bot and cached:
            runtime = cached[1]
            self.bot = runtime.bot
            self.dispatcher = runtime.dispatcher
        if not self.bot:
            await self._clear_webhook_refresh_cache()
            await self._close_bot_runtime_cache(self.connected_integration_id)
            return {"status": "disconnected", "message": "Bot not initialized"}
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self._clear_webhook_refresh_cache()
            await self._close_bot_runtime_cache(self.connected_integration_id)
            self.bot = None
            self.dispatcher = None
            self.handlers_registered = False
            logger.info("Webhook removed")
            return {"status": "disconnected"}
        except Exception as error:
            logger.error(f"Disconnection error: {error}")
            return self._error_response(1004, f"Webhook removal failed: {error}").dict()

    async def update_settings(
        self,
        request: Optional[ConnectedIntegrationSettingEditRequest] = None,
        data: Optional[List[Dict]] = None,
        incoming_settings: Optional[List[Dict]] = None,
        **kwargs,
    ) -> IntegrationSuccessResponse:
        await self._clear_settings_cache()
        await self._clear_webhook_refresh_cache()
        await self._close_bot_runtime_cache(self.connected_integration_id)
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, Texts.ERROR_CONNECTED_ID_MISSING).dict()
        queued = await self._enqueue_event(
            self.connected_integration_id,
            kind="webhook",
            action=action,
            payload=data or {},
        )
        return {"status": "accepted", "queued": 1 if queued else 0, "kind": "webhook"}

    async def _process_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        logger.debug(
            "Processing REGOS webhook for orders bot (ID=%s, action=%s)",
            self.connected_integration_id,
            action,
        )
        if self._is_longpolling_mode():
            return {"status": "webhook processed", "mode": "longpolling"}
        await self._initialize_bot()
        await self._ensure_webhook_from_regos()
        return {"status": "webhook processed"}

    async def _setup_handlers(self) -> None:
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        @self.dispatcher.message(lambda message: message.contact is not None)
        async def handle_contact(message: types.Message):
            await self._handle_contact(message)

        @self.dispatcher.message(lambda message: message.location is not None)
        async def handle_location(message: types.Message):
            await self._handle_location(message)

        @self.dispatcher.message(lambda message: message.text is not None)
        async def handle_text(message: types.Message):
            await self._handle_text(message)

        self.handlers_registered = True

    @staticmethod
    def _telegram_update_event_id(payload: Dict[str, Any]) -> str:
        update_id = str(payload.get("update_id") or "").strip()
        if update_id:
            return update_id
        return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()

    async def send_messages(self, messages: List[Dict]) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, Texts.ERROR_CONNECTED_ID_MISSING)
        for msg in messages:
            if not msg.get("recipient") or not msg.get("message"):
                return self._error_response(1001, Texts.ERROR_INVALID_MESSAGE_FORMAT)
        queued = await self._enqueue_event(
            self.connected_integration_id,
            kind="send_messages",
            payload={"messages": messages},
        )
        return {
            "status": "accepted",
            "queued": 1 if queued else 0,
            "kind": "send_messages",
            "messages": len(messages),
        }

    async def _send_messages_now(self, messages: List[Dict]) -> Any:
        await self._initialize_bot()

        semaphore = asyncio.Semaphore(TelegramBotOrdersConfig.SEND_CONCURRENCY)

        async def send_one(msg: Dict) -> Dict:
            chat_id = msg.get("recipient")
            text = msg.get("message")
            if not chat_id or not text:
                return {"status": "error", "error": Texts.ERROR_INVALID_MESSAGE_FORMAT}
            try:
                await self.bot.send_message(chat_id=chat_id, text=text)
                return {"status": "sent", "chat_id": chat_id}
            except Exception as error:
                logger.error(Texts.log_send_message_error(chat_id, error))
                return {"status": "error", "chat_id": chat_id, "error": str(error)}

        async def guarded_send(msg: Dict) -> Dict:
            async with semaphore:
                return await send_one(msg)

        results = await asyncio.gather(*(guarded_send(msg) for msg in messages))

        return {"sent": len([r for r in results if r["status"] == "sent"]), "details": results}

    async def handle_external(self, envelope: Dict) -> Dict:
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._error_response(400, Texts.ERROR_EXPECTED_JSON).dict()
        if not self.connected_integration_id:
            return self._error_response(1000, Texts.ERROR_CONNECTED_ID_MISSING).dict()
        queued = await self._enqueue_event(
            self.connected_integration_id,
            kind="telegram_update",
            payload=payload,
            event_id=self._telegram_update_event_id(payload),
        )
        return {
            "status": "accepted",
            "queued": 1 if queued else 0,
            "kind": "telegram_update",
            "connected_integration_id": self.connected_integration_id,
            "update_id": payload.get("update_id"),
            "duplicate": not queued,
        }

    async def _process_telegram_update(self, payload: Dict) -> Dict:
        await self._initialize_bot()
        await self._setup_handlers()

        chat_id = _extract_chat_id(payload)
        if chat_id:
            logger.info(f"Telegram update from chat_id={chat_id}")

        try:
            telegram_update = TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error(Texts.log_update_invalid(error))
            return self._error_response(400, Texts.ERROR_INVALID_UPDATE).dict()

        try:
            await self.dispatcher.feed_update(self.bot, telegram_update)
        except Exception as error:
            logger.exception(Texts.log_update_processing_error(error))
            return self._error_response(500, Texts.ERROR_PROCESSING.format(error=error)).dict()

        return {
            "status": "processed",
            "connected_integration_id": self.connected_integration_id,
            "chat_id": chat_id,
        }

    async def _request_phone(self, message: types.Message) -> None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text=Texts.BUTTON_SHARE_PHONE, request_contact=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            Texts.REQUEST_PHONE,
            reply_markup=keyboard,
        )

    @staticmethod
    def _command_arg(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return None
        return parts[1].strip() or None

    def _cart_key(self, chat_id: str) -> str:
        return self._redis_key("cart", self.connected_integration_id, chat_id)

    def _cart_state_key(self, chat_id: str) -> str:
        return self._redis_key("cs", self.connected_integration_id, chat_id)

    def _catalog_state_key(self, chat_id: str) -> str:
        return self._redis_key("cat", self.connected_integration_id, chat_id)

    def _order_state_key(self, chat_id: str) -> str:
        return self._redis_key("ord", self.connected_integration_id, chat_id)

    def _customer_phone_key(self, chat_id: str) -> str:
        return self._redis_key("phone", self.connected_integration_id, chat_id)

    def _orders_state_key(self, chat_id: str) -> str:
        return self._redis_key("ords", self.connected_integration_id, chat_id)

    async def _get_cart(self, chat_id: str) -> List[dict]:
        self._require_redis()
        key = self._cart_key(chat_id)
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            return _json_loads(cached)
        return []

    async def _save_cart(self, chat_id: str, cart: List[dict]) -> None:
        self._require_redis()
        key = self._cart_key(chat_id)
        await redis_ops.setex(key, TelegramBotOrdersConfig.CART_TTL, _json_dumps(cart))

    async def _clear_cart(self, chat_id: str) -> None:
        self._require_redis()
        key = self._cart_key(chat_id)
        await redis_ops.delete(key)

    async def _get_cart_state(self, chat_id: str) -> Dict[str, Any]:
        self._require_redis()
        key = self._cart_state_key(chat_id)
        defaults = {"awaiting_remove": False, "item_ids": [], "item_buttons": []}
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            payload = _json_loads(cached)
            defaults.update(payload)
        return defaults

    async def _save_cart_state(self, chat_id: str, **extra: Any) -> None:
        self._require_redis()
        key = self._cart_state_key(chat_id)
        state = await self._get_cart_state(chat_id)
        state.update(extra)
        await redis_ops.setex(key, TelegramBotOrdersConfig.CART_TTL, _json_dumps(state))

    async def _clear_cart_state(self, chat_id: str) -> None:
        self._require_redis()
        key = self._cart_state_key(chat_id)
        await redis_ops.delete(key)

    async def _save_catalog_state(
        self, chat_id: str, search: Optional[str], offset: int, **extra: Any
    ) -> None:
        self._require_redis()
        key = self._catalog_state_key(chat_id)
        state = await self._get_catalog_state(chat_id)
        state.update(
            {
                "search": search,
                "offset": offset,
            }
        )
        state.update(extra)
        await redis_ops.setex(key, TelegramBotOrdersConfig.CATALOG_TTL, _json_dumps(state))

    async def _get_catalog_state(self, chat_id: str) -> Dict[str, Any]:
        self._require_redis()
        key = self._catalog_state_key(chat_id)
        defaults = {
            "search": None,
            "offset": 0,
            "group_id": None,
            "group_name": None,
            "view": "categories",
            "awaiting_search": False,
            "awaiting_qty": False,
            "qty_item_id": None,
            "awaiting_action": None,
            "page_item_ids": [],
            "page_items": [],
            "selected_item_id": None,
            "category_map": {},
        }
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            payload = _json_loads(cached)
            defaults.update(payload)
        return defaults

    async def _get_order_state(self, chat_id: str) -> Dict[str, Any]:
        self._require_redis()
        key = self._order_state_key(chat_id)
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            return _json_loads(cached)
        return {}

    async def _get_customer_phone(self, chat_id: str) -> Optional[str]:
        self._require_redis()
        key = self._customer_phone_key(chat_id)
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            return str(cached)
        return None

    async def _get_orders_state(self, chat_id: str) -> Dict[str, Any]:
        self._require_redis()
        key = self._orders_state_key(chat_id)
        defaults = {
            "offset": 0,
            "view": None,
            "order_buttons": [],
        }
        cached = await redis_ops.get(key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            payload = _json_loads(cached)
            defaults.update(payload)
        return defaults

    async def _get_catalog_page_size(self) -> int:
        settings_map = await self._get_settings_map()
        page_size_value = settings_map.get(
            TelegramOrdersSettings.CATALOG_PAGE_SIZE.value.lower()
        )
        page_size = self._parse_int(page_size_value)
        if page_size and page_size > 0:
            return page_size
        return TelegramBotOrdersConfig.CATALOG_PAGE_SIZE

    async def _get_order_state_ttl(self) -> int:
        settings_map = await self._get_settings_map()
        ttl_value = settings_map.get(
            TelegramOrdersSettings.ORDER_STATE_TTL.value.lower()
        )
        ttl = self._parse_int(ttl_value)
        if ttl and ttl > 0:
            return ttl
        return TelegramBotOrdersConfig.ORDER_STATE_TTL

    async def _save_order_state(self, chat_id: str, state: Dict[str, Any]) -> None:
        self._require_redis()
        key = self._order_state_key(chat_id)
        ttl = await self._get_order_state_ttl()
        await redis_ops.setex(key, ttl, _json_dumps(state))

    async def _save_customer_phone(self, chat_id: str, phone: str) -> None:
        self._require_redis()
        key = self._customer_phone_key(chat_id)
        ttl = await self._get_order_state_ttl()
        await redis_ops.setex(key, ttl, phone)

    async def _save_orders_state(self, chat_id: str, **extra: Any) -> None:
        self._require_redis()
        key = self._orders_state_key(chat_id)
        state = await self._get_orders_state(chat_id)
        state.update(extra)
        ttl = await self._get_order_state_ttl()
        await redis_ops.setex(key, ttl, _json_dumps(state))

    async def _clear_order_state(self, chat_id: str) -> None:
        self._require_redis()
        key = self._order_state_key(chat_id)
        await redis_ops.delete(key)

    async def _clear_customer_phone(self, chat_id: str) -> None:
        self._require_redis()
        key = self._customer_phone_key(chat_id)
        await redis_ops.delete(key)

    async def _clear_orders_state(self, chat_id: str) -> None:
        self._require_redis()
        key = self._orders_state_key(chat_id)
        await redis_ops.delete(key)

    @staticmethod
    def _md_escape(value: Optional[str]) -> str:
        if not value:
            return ""
        text = str(value)
        for ch in ("\\", "*", "_", "`", "[", "]"):
            text = text.replace(ch, f"\\{ch}")
        return text

    @staticmethod
    def _group_digits(value: str) -> str:
        if not value:
            return "0"
        groups: List[str] = []
        while value:
            groups.append(value[-3:])
            value = value[:-3]
        groups.reverse()
        return " ".join(groups) if groups else "0"

    @staticmethod
    def _format_decimal(value: Optional[Decimal]) -> str:
        if value is None:
            return "0"
        try:
            dec = Decimal(str(value))
        except Exception:
            return str(value)
        text = format(dec, "f")
        sign = ""
        if text.startswith("-"):
            sign = "-"
            text = text[1:]
        integer, dot, fraction = text.partition(".")
        if not integer:
            integer = "0"
        if fraction:
            fraction = fraction.rstrip("0")
        grouped = TelegramBotOrdersIntegration._group_digits(integer)
        formatted = f"{sign}{grouped}"
        if fraction:
            formatted = f"{formatted}.{fraction}"
        return formatted or "0"

    def _format_item_line(self, index: int, entry: ItemExt, show_stock: bool) -> str:
        item = entry.item
        name = self._md_escape(item.name or Texts.ITEM_UNNAMED)
        price_value = entry.price
        price_text = (
            self._format_decimal(price_value)
            if price_value is not None
            else Texts.item_price_missing()
        )
        qty = (
            entry.quantity.common
            if entry.quantity and entry.quantity.common is not None
            else None
        )
        qty_line = (
            Texts.item_qty_line(qty)
            if qty is not None and show_stock
            else ""
        )
        return Texts.item_line(index, name, price_text, qty_line)

    def _format_catalog_list(
        self,
        items: List[ItemExt],
        search: Optional[str],
        offset: int,
        group_name: Optional[str],
        page_size: int,
        show_stock: bool,
    ) -> str:
        page = offset // page_size + 1
        lines = [Texts.catalog_title(page)]
        if group_name:
            lines.append(Texts.catalog_category_line(self._md_escape(group_name)))
        if search:
            lines.append(Texts.catalog_search_line(self._md_escape(search)))
        if not items:
            lines.append(Texts.catalog_empty_line())
            return "\n".join(lines)
        for idx, entry in enumerate(items, start=1):
            lines.append(self._format_item_line(idx, entry, show_stock))
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_order_date(ts: Optional[int]) -> str:
        if not ts:
            return "-"
        return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")

    def _format_orders_list(
        self, orders: List[DocOrderDelivery], offset: int
    ) -> str:
        page = offset // TelegramBotOrdersConfig.ORDERS_PAGE_SIZE + 1
        lines = [Texts.orders_title(page)]
        if not orders:
            lines.append(Texts.ORDERS_EMPTY)
            return "\n".join(lines)
        for idx, order in enumerate(orders, start=1):
            code = self._md_escape(order.code or str(order.id))
            date_text = self._format_order_date(order.date)
            amount = order.amount if order.amount is not None else Decimal(0)
            status = order.status.name if order.status else None
            status_text = self._md_escape(status) if status else None
            lines.append(
                Texts.order_line(
                    idx, code, date_text, self._format_decimal(amount), status_text
                )
            )
        lines.append(Texts.ORDERS_HINT)
        return "\n".join(lines)

    def _format_order_detail(self, order: DocOrderDelivery) -> str:
        code = self._md_escape(order.code or str(order.id))
        lines = [Texts.order_detail_title(code)]
        lines.append(Texts.order_detail_date(self._format_order_date(order.date)))
        if order.amount is not None:
            lines.append(
                Texts.order_detail_amount(self._format_decimal(order.amount))
            )
        if order.status and order.status.name:
            lines.append(
                Texts.order_detail_status(self._md_escape(order.status.name))
            )
        if order.address:
            lines.append(Texts.order_detail_address(self._md_escape(order.address)))
        if order.description:
            lines.append(
                Texts.order_detail_description(
                    self._md_escape(order.description)
                )
            )
        if order.delivery_type and order.delivery_type.name:
            lines.append(
                Texts.order_detail_delivery_type(
                    self._md_escape(order.delivery_type.name)
                )
            )
        if order.from_ and order.from_.name:
            lines.append(
                Texts.order_detail_from(self._md_escape(order.from_.name))
            )
        return "\n".join(lines)

    def _format_item_detail(self, entry: ItemExt, show_stock: bool) -> str:
        item = entry.item
        name = self._md_escape(item.name or Texts.ITEM_UNNAMED)
        price_value = entry.price
        qty = (
            entry.quantity.common
            if entry.quantity and entry.quantity.common is not None
            else None
        )
        color = (
            self._md_escape(item.color.name)
            if item.color and item.color.name
            else None
        )
        size = (
            self._md_escape(item.size.name)
            if item.size and item.size.name
            else None
        )
        qty_line = (
            self._format_decimal(qty)
            if qty is not None and show_stock
            else None
        )
        lines = Texts.item_detail_lines(
            name,
            self._format_decimal(price_value)
            if price_value is not None
            else Texts.item_price_missing(),
            qty=qty_line,
            color=color,
            size=size,
            articul=self._md_escape(item.articul) if item.articul else None,
            code=item.code,
            description=self._md_escape(item.description) if item.description else None,
        )
        return "\n\n".join(lines)

    def _categories_keyboard(self, groups: List[ItemGroup]) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        rows.append([types.KeyboardButton(text=Texts.BUTTON_SEARCH)])
        buffer: List[types.KeyboardButton] = []
        for group in groups:
            if not group.name:
                continue
            buffer.append(types.KeyboardButton(text=group.name))
            if len(buffer) == 2:
                rows.append(buffer)
                buffer = []
        if buffer:
            rows.append(buffer)
        rows.append([types.KeyboardButton(text=Texts.BUTTON_ALL_ITEMS)])
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def _catalog_list_keyboard(
        self, items: List[ItemExt], offset: int, has_next: bool
    ) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        for index, entry in enumerate(items, start=1):
            name = entry.item.name or Texts.ITEM_UNNAMED
            label = f"{index}. {name}"
            rows.append([types.KeyboardButton(text=label)])
        rows.append([types.KeyboardButton(text=Texts.BUTTON_SEARCH)])
        nav_row: List[types.KeyboardButton] = []
        if offset > 0:
            nav_row.append(types.KeyboardButton(text=Texts.BUTTON_BACK))
        if has_next:
            nav_row.append(types.KeyboardButton(text=Texts.BUTTON_NEXT))
        if nav_row:
            rows.append(nav_row)
        rows.append(
            [
                types.KeyboardButton(text=Texts.BUTTON_CATEGORIES),
                types.KeyboardButton(text=Texts.BUTTON_CART),
            ]
        )
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def _catalog_detail_keyboard(self) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=Texts.BUTTON_ADD_ONE)],
                [types.KeyboardButton(text=Texts.BUTTON_ADD_OTHER)],
                [types.KeyboardButton(text=Texts.BUTTON_BACK_TO_LIST)],
                [
                    types.KeyboardButton(text=Texts.BUTTON_CART),
                    types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN),
                ],
            ],
            resize_keyboard=True,
        )

    def _catalog_search_keyboard(self) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=Texts.BUTTON_BACK_TO_CATALOG)],
                [types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)],
            ],
            resize_keyboard=True,
        )

    def _cart_numbers_keyboard(self, count: int) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        row: List[types.KeyboardButton] = []
        for i in range(1, count + 1):
            row.append(types.KeyboardButton(text=str(i)))
            if len(row) == 5:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def _quantity_keyboard(self) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        row: List[types.KeyboardButton] = []
        for option in Texts.QTY_OPTIONS:
            row.append(types.KeyboardButton(text=option))
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append([types.KeyboardButton(text=Texts.BUTTON_BACK_TO_ITEM)])
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def _orders_list_keyboard(
        self, orders: List[DocOrderDelivery], offset: int, has_next: bool
    ) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        for index, order in enumerate(orders, start=1):
            code = order.code or str(order.id)
            label = Texts.order_button_label(index, code)
            rows.append([types.KeyboardButton(text=label)])
        nav_row: List[types.KeyboardButton] = []
        if offset > 0:
            nav_row.append(types.KeyboardButton(text=Texts.BUTTON_BACK))
        if has_next:
            nav_row.append(types.KeyboardButton(text=Texts.BUTTON_NEXT))
        if nav_row:
            rows.append(nav_row)
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    def _order_detail_keyboard(self) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=Texts.BUTTON_ORDER_BACK_TO_LIST)],
                [types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)],
            ],
            resize_keyboard=True,
        )

    def _delivery_type_keyboard(
        self, types_list: List[DeliveryType]
    ) -> types.ReplyKeyboardMarkup:
        rows: List[List[types.KeyboardButton]] = []
        for entry in types_list:
            if not entry.name:
                continue
            rows.append([types.KeyboardButton(text=entry.name)])
        rows.append([types.KeyboardButton(text=Texts.BUTTON_MENU_MAIN)])
        return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    async def _send_catalog_search_prompt(self, chat_id: str) -> None:
        await self._save_catalog_state(
            chat_id,
            None,
            0,
            awaiting_search=True,
            awaiting_qty=False,
            qty_item_id=None,
            awaiting_action=None,
            view="search",
        )
        if self.bot:
            await self.bot.send_message(
                chat_id=chat_id,
                text=Texts.CATALOG_SEARCH_PROMPT,
                reply_markup=self._catalog_search_keyboard(),
                parse_mode=ParseMode.MARKDOWN,
            )

    async def _handle_search_input(self, message: types.Message) -> bool:
        chat_id = str(message.chat.id)
        state = await self._get_catalog_state(chat_id)
        if not state.get("awaiting_search"):
            return False
        query = message.text.strip() if message.text else ""
        await self._save_catalog_state(
            chat_id,
            query or None,
            0,
            awaiting_search=False,
            awaiting_qty=False,
            qty_item_id=None,
            view="list",
            awaiting_action=None,
        )
        await self._send_catalog_page(chat_id)
        return True

    async def _handle_qty_input(self, message: types.Message) -> bool:
        chat_id = str(message.chat.id)
        state = await self._get_catalog_state(chat_id)
        if not state.get("awaiting_qty"):
            return False
        text = message.text.strip() if message.text else ""
        item_id = state.get("qty_item_id")
        if text == Texts.BUTTON_BACK_TO_ITEM and item_id:
            await self._send_catalog_detail(chat_id, item_id)
            return True
        qty = self._parse_quantity(text)
        if not qty or not item_id:
            await message.answer(
                Texts.QTY_INVALID, reply_markup=self._quantity_keyboard()
            )
            return True
        result = await self._add_item_to_cart(chat_id, item_id, qty)
        if result == Texts.QTY_INTEGER_ONLY:
            await message.answer(result, reply_markup=self._quantity_keyboard())
            return True
        if result == Texts.ITEM_NOT_FOUND:
            await message.answer(Texts.ITEM_NOT_FOUND)
            await self._send_main_menu(message, Texts.MAIN_MENU)
            return True
        await message.answer(result or Texts.ITEM_NOT_FOUND)
        await self._send_catalog_detail(chat_id, item_id)
        return True

    async def _prompt_cart_remove(self, message: types.Message) -> None:
        chat_id = str(message.chat.id)
        cart = await self._get_cart(chat_id)
        if not cart:
            await self._send_main_menu(message, Texts.CART_EMPTY)
            return
        await self._save_cart_state(
            chat_id,
            awaiting_remove=True,
            item_ids=[row["item_id"] for row in cart],
        )
        await message.answer(
            Texts.CART_SELECT_NUMBER_REMOVE,
            reply_markup=self._cart_numbers_keyboard(len(cart)),
        )

    async def _handle_cart_number_action(self, message: types.Message) -> bool:
        text = message.text.strip() if message.text else ""
        if not text.isdigit():
            return False
        chat_id = str(message.chat.id)
        state = await self._get_cart_state(chat_id)
        if not state.get("awaiting_remove"):
            return False
        index = int(text)
        cart = await self._get_cart(chat_id)
        if index < 1 or index > len(cart):
            await message.answer(
                Texts.CART_NUMBER_INVALID,
                reply_markup=self._cart_numbers_keyboard(len(cart)),
            )
            return True
        item_id = cart[index - 1]["item_id"]
        await self._remove_item_from_cart(chat_id, item_id)
        await self._save_cart_state(chat_id, awaiting_remove=False)
        await message.answer(Texts.CART_ITEM_REMOVED)
        await self._send_cart(message)
        return True

    async def _handle_cart_item_select(self, message: types.Message) -> bool:
        text = message.text.strip() if message.text else ""
        if not text:
            return False
        chat_id = str(message.chat.id)
        state = await self._get_cart_state(chat_id)
        for item in state.get("item_buttons") or []:
            if text == item.get("label"):
                await self._remove_item_from_cart(chat_id, item.get("item_id"))
                await message.answer(Texts.CART_ITEM_REMOVED)
                await self._send_cart(message)
                return True
        return False

    async def _send_catalog_detail(self, chat_id: str, item_id: int) -> None:
        cache_key = self._settings_cache_key()
        settings_map = await self._fetch_settings(cache_key)
        item_ext = await self._fetch_item_ext(item_id, settings_map)

        if not item_ext:
            if self.bot:
                orders_disabled = self._parse_bool(
                    settings_map.get(TelegramOrdersSettings.ORDERS_DISABLED.value.lower())
                )
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=Texts.ITEM_NOT_FOUND,
                    reply_markup=self._main_menu_keyboard(bool(orders_disabled)),
                )
            return

        state = await self._get_catalog_state(chat_id)
        show_stock = self._should_show_item_stock(settings_map)
        text = self._format_item_detail(item_ext, show_stock)

        if self.bot:
            if item_ext.image_url:
                try:
                    # Пытаемся отправить описание в caption (под картинкой)
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=item_ext.image_url,
                        caption=text,
                        reply_markup=self._catalog_detail_keyboard(),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception as error:
                    # Частая причина: слишком длинный caption или проблемы с Markdown
                    logger.warning(Texts.log_send_photo_fail(error))

                    # Фолбэк: фото (короткий caption) + отдельным сообщением полный текст
                    try:
                        title = self._md_escape(item_ext.item.name or Texts.ITEM_UNNAMED)
                        await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=item_ext.image_url,
                            caption=title,
                            parse_mode=ParseMode.MARKDOWN,
                        )
                    except Exception as error2:
                        logger.warning(Texts.log_send_photo_fail(error2))

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=self._catalog_detail_keyboard(),
                        parse_mode=ParseMode.MARKDOWN,
                    )
            else:
                # Картинки нет — отдельным сообщением
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=self._catalog_detail_keyboard(),
                    parse_mode=ParseMode.MARKDOWN,
                )

        await self._save_catalog_state(
            chat_id,
            state.get("search"),
            state.get("offset", 0),
            view="detail",
            selected_item_id=item_id,
            awaiting_qty=False,
            qty_item_id=None,
            awaiting_search=False,
            awaiting_action=None,
        )


    async def _prompt_item_quantity(
        self, message: types.Message, item_id: int
    ) -> None:
        state = await self._get_catalog_state(str(message.chat.id))
        await self._save_catalog_state(
            str(message.chat.id),
            state.get("search"),
            state.get("offset", 0),
            view="qty",
            awaiting_qty=True,
            qty_item_id=item_id,
            awaiting_search=False,
            awaiting_action=None,
        )
        await message.answer(
            Texts.REQUEST_QTY,
            reply_markup=self._quantity_keyboard(),
        )

    async def _send_orders_list(
        self,
        message: types.Message,
        *,
        next_page: bool = False,
        prev_page: bool = False,
    ) -> None:
        chat_id = str(message.chat.id)
        customer = await self._find_customer_by_chat(chat_id)
        if not customer:
            await self._request_phone(message)
            return
        state = await self._get_orders_state(chat_id)
        offset = int(state.get("offset", 0))
        if next_page:
            offset += TelegramBotOrdersConfig.ORDERS_PAGE_SIZE
        if prev_page:
            offset = max(0, offset - TelegramBotOrdersConfig.ORDERS_PAGE_SIZE)
        orders = await self._fetch_orders(customer.id, offset)
        if not orders and offset > 0:
            offset = max(0, offset - TelegramBotOrdersConfig.ORDERS_PAGE_SIZE)
            orders = await self._fetch_orders(customer.id, offset)
        if not orders:
            await self._send_main_menu(message, Texts.ORDERS_EMPTY)
            await self._save_orders_state(
                chat_id,
                offset=0,
                view=None,
                order_buttons=[],
            )
            return
        has_next = len(orders) >= TelegramBotOrdersConfig.ORDERS_PAGE_SIZE
        text = self._format_orders_list(orders, offset)
        keyboard = self._orders_list_keyboard(orders, offset, has_next)
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
        order_buttons = [
            {
                "label": Texts.order_button_label(index, order.code or str(order.id)),
                "order_id": order.id,
            }
            for index, order in enumerate(orders, start=1)
        ]
        await self._save_orders_state(
            chat_id,
            offset=offset,
            view="orders_list",
            order_buttons=order_buttons,
        )

    async def _send_order_detail(
        self, message: types.Message, order_id: int
    ) -> None:
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            order = await api.docs.order_delivery.get_by_id(order_id)
        if not order:
            await message.answer(Texts.ORDER_NOT_FOUND)
            await self._send_orders_list(message)
            return
        text = self._format_order_detail(order)
        await message.answer(
            text,
            reply_markup=self._order_detail_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
        )
        await self._save_orders_state(
            str(message.chat.id),
            view="orders_detail",
        )

    async def _handle_orders_select(self, message: types.Message) -> bool:
        chat_id = str(message.chat.id)
        state = await self._get_orders_state(chat_id)
        if state.get("view") != "orders_list":
            return False
        text = message.text.strip() if message.text else ""
        for entry in state.get("order_buttons") or []:
            if text == entry.get("label"):
                await self._send_order_detail(message, entry.get("order_id"))
                return True
        return False

    async def _fetch_catalog(
        self,
        search: Optional[str],
        offset: int,
        group_id: Optional[int],
        page_size: int,
        settings_map: Optional[Dict[str, str]] = None,
    ) -> List[ItemExt]:
        settings = settings_map or await self._get_settings_map()
        if page_size <= 0:
            page_size = TelegramBotOrdersConfig.CATALOG_PAGE_SIZE
        stock_id = self._parse_int(
            settings.get(TelegramOrdersSettings.STOCK_ID_QUANTITY.value.lower())
        )
        price_type_id = self._parse_int(
            settings.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        allowed_group_ids = self._parse_int_list(
            settings.get(TelegramOrdersSettings.ITEM_GROUP_IDS.value.lower())
        )
        zero_qty = self._parse_bool(
            settings.get(TelegramOrdersSettings.SHOW_ZERO_QUANTITY.value.lower())
        )
        show_without_images = self._parse_bool(
            settings.get(TelegramOrdersSettings.SHOW_WITHOUT_IMAGES.value.lower())
        )
        show_without_price = self._parse_bool(
            settings.get(
                TelegramOrdersSettings.SHOW_ITEMS_WITHOUT_PRICE.value.lower()
            )
        )
        if show_without_images is True:
            has_image = None
        elif show_without_images is False:
            has_image = True
        else:
            has_image = None

        hash_input = json.dumps(
            {
                "search": search,
                "offset": offset,
                "group_id": group_id,
                "allowed_group_ids": allowed_group_ids,
                "stock_id": stock_id,
                "price_type_id": price_type_id,
                "zero_qty": zero_qty,
                "has_image": has_image,
                "show_without_price": bool(show_without_price),
                "limit": page_size,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        key_hash = hashlib.sha1(hash_input.encode("utf-8")).hexdigest()
        cache_key = self._redis_key("cc", self.connected_integration_id, key_hash)
        self._require_redis()
        cached = await redis_ops.get(cache_key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            raw_items = _json_loads(cached)
            return [ItemExt.model_validate(item) for item in raw_items]

        request_group_ids: Optional[List[int]]
        if group_id:
            request_group_ids = [group_id]
        elif allowed_group_ids:
            request_group_ids = allowed_group_ids
        else:
            request_group_ids = None
        req = ItemGetExtRequest(
            stock_id=stock_id,
            price_type_id=price_type_id,
            zero_quantity=zero_qty,
            zero_price=show_without_price,
            has_image=has_image,
            image_size=ItemGetExtImageSize.Large,
            search=search,
            group_ids=request_group_ids,
            limit=page_size,
            offset=offset,
        )
        request_payload = req.model_dump(mode="json", exclude_none=True)
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.item.get_ext(request_payload)
            result = resp.result or []
            if group_id:
                result = [
                    entry
                    for entry in result
                    if entry.item
                    and entry.item.group
                    and entry.item.group.id == group_id
                ]

        cache_payload = [item.model_dump(mode="json") for item in result]
        await redis_ops.setex(
            cache_key,
            TelegramBotOrdersConfig.CATALOG_TTL,
            _json_dumps(cache_payload),
        )
        return result

    async def _fetch_categories(self) -> List[ItemGroup]:
        settings_map = await self._get_settings_map()
        allowed_group_ids = set(
            self._parse_int_list(
                settings_map.get(TelegramOrdersSettings.ITEM_GROUP_IDS.value.lower())
            )
        )
        cache_key = self._redis_key("cg", self.connected_integration_id)
        self._require_redis()
        cached = await redis_ops.get(cache_key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            raw_groups = _json_loads(cached)
            groups = [ItemGroup.model_validate(group) for group in raw_groups]
            if allowed_group_ids:
                groups = [group for group in groups if group.id in allowed_group_ids]
            return groups

        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.item_group.get(ItemGroupGetRequest())
            result = resp.result or []
            groups = [group for group in result if group.name]
            groups.sort(key=lambda group: group.name.lower())
            payload = [group.model_dump(mode="json") for group in groups]
            await redis_ops.setex(
                cache_key,
                TelegramBotOrdersConfig.GROUPS_TTL,
                _json_dumps(payload),
            )
            if allowed_group_ids:
                groups = [group for group in groups if group.id in allowed_group_ids]
            return groups

    async def _fetch_delivery_types(self) -> List[DeliveryType]:
        cache_key = self._redis_key("dt", self.connected_integration_id)
        self._require_redis()
        cached = await redis_ops.get(cache_key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            raw_types = _json_loads(cached)
            return [DeliveryType.model_validate(entry) for entry in raw_types]

        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.delivery_type.get(
                DeliveryTypeGetRequest(limit=10000, offset=0)
            )
            if not resp.ok:
                raise RuntimeError(f"DeliveryType/Get rejected: {resp.result}")
            result = resp.result if isinstance(resp.result, list) else []
            types_list = [entry for entry in result if getattr(entry, "name", None)]
            types_list.sort(key=lambda entry: entry.name.lower())
            payload = [entry.model_dump(mode="json") for entry in types_list]
            await redis_ops.setex(
                cache_key,
                TelegramBotOrdersConfig.DELIVERY_TYPES_TTL,
                _json_dumps(payload),
            )
            return types_list

    async def _fetch_orders(
        self, customer_id: int, offset: int
    ) -> List[DocOrderDelivery]:
        req = DocOrderDeliveryGetRequest(
            customer_ids=[customer_id],
            sort_orders=[SortOrder(column="Date", direction=SortDirection.desc)],
            limit=TelegramBotOrdersConfig.ORDERS_PAGE_SIZE,
            offset=offset,
        )
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.docs.order_delivery.get(req)
            return resp.result or []

    async def _send_categories(self, message: types.Message) -> None:
        chat_id = str(message.chat.id)
        groups = await self._fetch_categories()
        if not groups:
            await self._send_main_menu(message, Texts.CATEGORIES_EMPTY)
            return
        category_map = {group.name: group.id for group in groups if group.name}
        await self._save_catalog_state(
            chat_id,
            None,
            0,
            view="categories",
            group_id=None,
            group_name=None,
            awaiting_search=False,
            awaiting_qty=False,
            qty_item_id=None,
            awaiting_action=None,
            page_item_ids=[],
            page_items=[],
            selected_item_id=None,
            category_map=category_map,
        )
        await message.answer(
            Texts.CATEGORIES_TITLE, reply_markup=self._categories_keyboard(groups)
        )

    async def _select_category(
        self,
        chat_id: str,
        group_id: Optional[int],
        group_name: Optional[str],
        message: types.Message,
    ) -> None:
        await self._save_catalog_state(
            chat_id,
            None,
            0,
            view="list",
            group_id=group_id,
            group_name=group_name,
            awaiting_search=False,
            awaiting_action=None,
        )
        await self._send_catalog_page(chat_id)

    async def _send_catalog_page(
        self,
        chat_id: str,
        *,
        next_page: bool = False,
        prev_page: bool = False,
    ) -> None:
        state = await self._get_catalog_state(chat_id)
        search = state.get("search")
        offset = int(state.get("offset", 0))
        group_id = state.get("group_id")
        page_size = await self._get_catalog_page_size()
        if next_page:
            offset += page_size
        if prev_page:
            offset = max(0, offset - page_size)
        settings_map = await self._get_settings_map()
        show_stock = self._should_show_item_stock(settings_map)
        items = await self._fetch_catalog(
            search=search,
            offset=offset,
            group_id=group_id,
            page_size=page_size,
            settings_map=settings_map,
        )
        if not items and offset > 0:
            offset = max(0, offset - page_size)
            items = await self._fetch_catalog(
                search=search,
                offset=offset,
                group_id=group_id,
                page_size=page_size,
                settings_map=settings_map,
            )

        has_next = len(items) >= page_size
        text = self._format_catalog_list(
            items,
            search,
            offset,
            state.get("group_name"),
            page_size,
            show_stock,
        )
        keyboard = self._catalog_list_keyboard(items, offset, has_next)
        if self.bot:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
        await self._save_catalog_state(
            chat_id,
            search,
            offset,
            view="list",
            awaiting_search=False,
            awaiting_qty=False,
            qty_item_id=None,
            awaiting_action=None,
            page_item_ids=[entry.item.id for entry in items],
            page_items=[
                {
                    "id": entry.item.id,
                    "label": f"{index}. {entry.item.name or Texts.ITEM_UNNAMED}",
                }
                for index, entry in enumerate(items, start=1)
            ],
            selected_item_id=None,
        )

    def _format_item(self, entry: ItemExt) -> str:
        item = entry.item
        name = item.name or Texts.ITEM_UNNAMED
        price = entry.price if entry.price is not None else Decimal(0)
        qty = (
            entry.quantity.common
            if entry.quantity and entry.quantity.common is not None
            else None
        )
        qty_text = (
            Texts.item_qty_suffix(self._format_decimal(qty)) if qty is not None else ""
        )
        return (
            f"{name}\n"
            f"{Texts.ITEM_DETAIL_PRICE.format(price=self._format_decimal(price))}"
            f"{qty_text}"
        )

    def _format_cart(self, cart: List[dict]) -> str:
        total = Decimal("0")
        lines = [Texts.CART_TITLE, ""]
        for idx, row in enumerate(cart, start=1):
            price = Decimal(str(row["price"]))
            qty = Decimal(str(row["qty"]))
            line_total = price * qty
            total += line_total
            lines.append(Texts.cart_item_header(idx, row["name"]))
            lines.append(
                Texts.cart_item_details(
                    self._format_decimal(qty),
                    self._format_decimal(price),
                    self._format_decimal(line_total),
                )
            )
            lines.append("")
            lines.append(Texts.CART_SEPARATOR)
            lines.append("")
        while lines and lines[-1] == "":
            lines.pop()
        if lines and lines[-1] == Texts.CART_SEPARATOR:
            lines.pop()
        lines.append("")
        lines.append(Texts.cart_total(self._format_decimal(total)))
        lines.append("")
        lines.append(Texts.CART_HINT)
        return "\n".join(lines)

    async def _handle_add_to_cart(self, message: types.Message) -> None:
        if not message.text:
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(Texts.ADD_USAGE)
            return
        try:
            item_id = int(parts[1])
        except ValueError:
            await message.answer(Texts.INVALID_ID)
            return
        qty = Decimal("1")
        if len(parts) > 2:
            try:
                qty = Decimal(parts[2])
            except Exception:
                await message.answer(Texts.INVALID_QTY)
                return
        if qty <= 0:
            await message.answer(Texts.QTY_GT_ZERO)
            return

        result = await self._add_item_to_cart(str(message.chat.id), item_id, qty)
        if result:
            await message.answer(result)

    async def _handle_remove_from_cart(self, message: types.Message) -> None:
        if not message.text:
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(Texts.REMOVE_USAGE)
            return
        try:
            item_id = int(parts[1])
        except ValueError:
            await message.answer(Texts.INVALID_ID)
            return
        cart = await self._get_cart(str(message.chat.id))
        new_cart = [row for row in cart if row["item_id"] != item_id]
        await self._save_cart(str(message.chat.id), new_cart)
        await message.answer(Texts.REMOVED_FROM_CART)

    async def _remove_item_from_cart(self, chat_id: str, item_id: int) -> None:
        cart = await self._get_cart(chat_id)
        new_cart = [row for row in cart if row["item_id"] != item_id]
        await self._save_cart(chat_id, new_cart)

    async def _handle_order(self, message: types.Message) -> None:
        settings_map = await self._get_settings_map()
        orders_disabled = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.ORDERS_DISABLED.value.lower())
        )
        if orders_disabled:
            await message.answer(Texts.ORDERS_DISABLED)
            await self._handle_cards(message)
            return
        if not self._is_work_time(settings_map):
            await message.answer(Texts.WORK_TIME_OFF)
            await self._send_main_menu(message)
            return

        cart = await self._get_cart(str(message.chat.id))
        if not cart:
            await message.answer(Texts.CART_EMPTY)
            await self._send_main_menu(message)
            return

        min_amount = self._parse_decimal(
            settings_map.get(TelegramOrdersSettings.MIN_ORDER_AMOUNT.value.lower())
        )
        total = sum(
            Decimal(str(row["price"])) * Decimal(str(row["qty"])) for row in cart
        )
        if min_amount and min_amount > 0 and total < min_amount:
            await message.answer(Texts.min_order_amount(self._format_decimal(min_amount)))
            await self._send_main_menu(message)
            return

        customer = await self._find_customer_by_chat(str(message.chat.id))
        if not customer:
            await self._request_phone(message)
            return

        state = await self._get_order_state(str(message.chat.id))
        delivery_required = self._parse_bool(
            settings_map.get(
                TelegramOrdersSettings.DELIVERY_TYPE_REQUIRED.value.lower()
            )
        )
        address_required = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.ADDRESS_REQUIRED.value.lower())
        )
        description_skipped = bool(state.get("description_skipped"))
        if delivery_required and not state.get("delivery_type_id"):
            await self._save_order_state(
                str(message.chat.id),
                {
                    "step": "await_delivery_type",
                    "delivery_type_id": None,
                    "address": state.get("address"),
                    "location": state.get("location"),
                    "description": state.get("description"),
                    "description_skipped": description_skipped,
                },
            )
            await self._request_delivery_type(message)
            return
        if address_required and not state.get("address"):
            await self._save_order_state(
                str(message.chat.id),
                {
                    "step": "await_address",
                    "delivery_type_id": state.get("delivery_type_id"),
                    "address": None,
                    "location": state.get("location"),
                    "description": state.get("description"),
                    "description_skipped": description_skipped,
                },
            )
            await self._request_address(message)
            return
        if not state.get("location"):
            await self._save_order_state(
                str(message.chat.id),
                {
                    "step": "await_location",
                    "location": None,
                    "description": state.get("description"),
                    "delivery_type_id": state.get("delivery_type_id"),
                    "address": state.get("address"),
                    "description_skipped": description_skipped,
                },
            )
            await self._request_location(message)
            return
        if not state.get("description") and not description_skipped:
            await self._save_order_state(
                str(message.chat.id),
                {
                    "step": "await_description",
                    "location": state.get("location"),
                    "description": None,
                    "delivery_type_id": state.get("delivery_type_id"),
                    "address": state.get("address"),
                    "description_skipped": description_skipped,
                },
            )
            await self._request_description(message)
            return

        stock_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.STOCK_ID.value.lower())
        )
        price_type_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        from_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.ORDER_SOURCE_ID.value.lower())
        )

        operations = [
            DocOrderDeliveryOperation(
                item_id=row["item_id"],
                quantity=Decimal(str(row["qty"])),
                price=Decimal(str(row["price"])),
            )
            for row in cart
        ]
        location = state.get("location") or {}
        location_payload = Location(
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        )
        document = DocOrderDeliveryAddRequest(
            date=int(datetime.utcnow().timestamp()),
            stock_id=stock_id,
            customer_id=customer.id,
            from_id=from_id,
            price_type_id=price_type_id,
            amount=total,
            phone=customer.main_phone,
            description=state.get("description"),
            location=location_payload,
            address=state.get("address"),
            delivery_type_id=state.get("delivery_type_id"),
            external_code=f"tg-{message.chat.id}-{int(datetime.utcnow().timestamp())}",
        )
        req = DocOrderDeliveryAddFullRequest(document=document, operations=operations)

        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.docs.order_delivery.add_full(req)
        if not resp.ok:
            await message.answer(Texts.ORDER_CREATE_ERROR)
            await self._send_main_menu(message)
            return

        await self._clear_cart(str(message.chat.id))
        await self._clear_cart_state(str(message.chat.id))
        await self._clear_order_state(str(message.chat.id))
        await message.answer(Texts.ORDER_ACCEPTED)
        await self._send_main_menu(message)

    async def _handle_cards(self, message: types.Message) -> None:
        customer = await self._find_customer_by_chat(str(message.chat.id))
        if not customer:
            await self._request_phone(message)
            return
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.retail_card.get(
                RetailCardGetRequest(customer_ids=[customer.id])
            )
        cards = resp.result or []
        if not cards:
            await message.answer(Texts.NO_CARDS)
            await self._send_main_menu(message)
            return
        for card in cards:
            text = Texts.card_text(
                card.id, card.bonus_amount, bool(card.enabled), card.barcode_value
            )
            image = self._make_qr(card.barcode_value)
            if image and self.bot:
                await self.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=BufferedInputFile(image, filename="card.png"),
                    caption=text,
                )
            else:
                await message.answer(text)
        await self._send_main_menu(message)

    @staticmethod
    def _customer_has_telegram_field(customer) -> bool:
        fields = customer.fields or []
        return any(field.key == "field_telegram_id" for field in fields)

    async def _find_customer_by_chat(self, chat_id: str):
        phone = await self._get_customer_phone(chat_id)
        if phone:
            customer = await self._find_customer_by_phone(phone)
            if not customer:
                await self._clear_customer_phone(chat_id)
            return customer
        if self._telegram_field_supported is False:
            return None
        customer = await self._find_customer_by_telegram_id(chat_id)
        if not customer:
            return None
        return customer

    async def _find_customer_by_telegram_id(self, chat_id: str):
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerGetRequest(
                filters=[
                    Filter(
                        field="field_telegram_id",
                        operator=FilterOperator.Equal,
                        value=str(chat_id),
                    )
                ],
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            if isinstance(resp.result, list):
                self._telegram_field_supported = True
                if not resp.result:
                    return None
                customer = resp.result[0]
                if self._customer_has_telegram_field(customer):
                    matched = False
                    for field in customer.fields or []:
                        if (
                            field.key == "field_telegram_id"
                            and str(field.value) == str(chat_id)
                        ):
                            matched = True
                            break
                    if not matched:
                        return None
                if customer.main_phone:
                    normalized = self._normalize_phone(customer.main_phone)
                    if normalized:
                        await self._save_customer_phone(chat_id, normalized)
                return customer
            if isinstance(resp.result, dict):
                error_code = resp.result.get("error")
                description = str(resp.result.get("description", "")).lower()
                if error_code == 7501 or "field_telegram_id" in description:
                    self._telegram_field_supported = False
                logger.warning(
                    "RetailCustomer.Get by field_telegram_id failed: %s", resp.result
                )
                return None
            if resp.ok is False:
                self._telegram_field_supported = False
            return None

    async def _fetch_item_ext(self, item_id: int, settings_map: Dict[str, str]) -> Optional[ItemExt]:
        stock_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.STOCK_ID_QUANTITY.value.lower())
        )
        price_type_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        cache_key = self._redis_key(
            "it",
            self.connected_integration_id,
            item_id,
            stock_id,
            price_type_id,
        )
        self._require_redis()
        cached = await redis_ops.get(cache_key)
        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode("utf-8")
            return ItemExt.model_validate(_json_loads(cached))
        req = ItemGetExtRequest(
            ids=[item_id],
            stock_id=stock_id,
            price_type_id=price_type_id,
            image_size=ItemGetExtImageSize.Large,
            limit=1,
            offset=0,
        )
        payload = req.model_dump(mode="json", exclude_none=True)
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.item.get_ext(payload)
            item = resp.result[0] if resp.result else None
            if item:
                await redis_ops.setex(
                    cache_key,
                    TelegramBotOrdersConfig.CATALOG_TTL,
                    _json_dumps(item.model_dump(mode="json")),
                )
            return item

    async def _add_item_to_cart(
        self, chat_id: str, item_id: int, qty: Decimal
    ) -> Optional[str]:
        cache_key = self._settings_cache_key()
        settings_map = await self._fetch_settings(cache_key)
        item_ext = await self._fetch_item_ext(item_id, settings_map)
        if not item_ext:
            return Texts.ITEM_NOT_FOUND
        if self._unit_requires_integer(item_ext.item.unit) and self._is_fractional(qty):
            return Texts.QTY_INTEGER_ONLY

        cart = await self._get_cart(chat_id)
        existing = next((x for x in cart if x["item_id"] == item_id), None)
        price = item_ext.price if item_ext.price is not None else Decimal(0)
        name = item_ext.item.name or Texts.ITEM_UNNAMED
        if existing:
            existing["qty"] = str(Decimal(existing["qty"]) + qty)
        else:
            cart.append(
                {"item_id": item_id, "name": name, "price": str(price), "qty": str(qty)}
            )
        await self._save_cart(chat_id, cart)
        return Texts.cart_added(name, qty)

    async def _handle_contact(self, message: types.Message) -> None:
        contact = message.contact
        if not contact or not contact.phone_number:
            await message.answer(
                Texts.PHONE_NOT_RECEIVED
            )
            return
        phone = self._normalize_phone(contact.phone_number)
        if not phone:
            await message.answer(Texts.PHONE_INVALID)
            return

        await self._save_customer_phone(str(message.chat.id), phone)

        customer = await self._find_customer_by_phone(phone)
        if customer:
            if self._customer_has_telegram_field(customer):
                await self._update_customer_telegram_id(customer.id, str(message.chat.id))
            await message.answer(
                Texts.CUSTOMER_FOUND,
                reply_markup=types.ReplyKeyboardRemove(),
            )
            await self._send_main_menu(message)
            return

        created = await self._create_customer_from_contact(
            message,
            phone,
            include_telegram_field=self._telegram_field_supported,
        )
        if created:
            await message.answer(
                Texts.CUSTOMER_CREATED,
                reply_markup=types.ReplyKeyboardRemove(),
            )
            await self._send_main_menu(message)
            return

        await message.answer(
            Texts.CUSTOMER_CREATE_FAILED
        )

    async def _handle_location(self, message: types.Message) -> None:
        location = message.location
        if not location:
            return
        state = await self._get_order_state(str(message.chat.id))
        if not state:
            await message.answer(
                Texts.LOCATION_RECEIVED_NOT_STARTED
            )
            await self._send_main_menu(message)
            return
        state["location"] = {
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        state["step"] = None
        await self._save_order_state(str(message.chat.id), state)
        await self._handle_order(message)

    async def _handle_order_text_input(self, message: types.Message) -> bool:
        if not message.text or message.text.startswith("/"):
            return False
        state = await self._get_order_state(str(message.chat.id))
        step = state.get("step")
        text = message.text.strip()
        if step == "await_delivery_type":
            delivery_type_id = None
            delivery_type_options = state.get("delivery_type_options") or {}
            if text in delivery_type_options:
                delivery_type_id = delivery_type_options[text]
            else:
                try:
                    parsed = int(text)
                    if parsed > 0:
                        delivery_type_id = parsed
                except ValueError:
                    delivery_type_id = None
            if not delivery_type_id:
                await message.answer(
                    Texts.DELIVERY_TYPE_INVALID,
                    reply_markup=self._delivery_type_keyboard(
                        await self._fetch_delivery_types()
                    ),
                )
                return True
            state["delivery_type_id"] = delivery_type_id
            state["delivery_type_options"] = {}
            state["step"] = None
            await self._save_order_state(str(message.chat.id), state)
            await self._handle_order(message)
            return True
        if step == "await_address":
            if not text:
                await message.answer(Texts.ADDRESS_INVALID)
                return True
            state["address"] = text
            state["step"] = None
            await self._save_order_state(str(message.chat.id), state)
            await self._handle_order(message)
            return True
        if step == "await_description":
            if text == Texts.BUTTON_SKIP:
                state["description"] = None
                state["description_skipped"] = True
            else:
                state["description"] = text
                state["description_skipped"] = False
            state["step"] = "ready"
            await self._save_order_state(str(message.chat.id), state)
            await message.answer(
                Texts.DESCRIPTION_ACCEPTED,
                reply_markup=types.ReplyKeyboardRemove(),
            )
            await self._handle_order(message)
            return True
        return False

    async def _find_customer_by_phone(self, phone: str):
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerGetRequest(
                main_phone=phone,
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            customers = resp.result if isinstance(resp.result, list) else []
            if customers:
                customer = customers[0]
                if self._customer_has_telegram_field(customer):
                    self._telegram_field_supported = True
                return customer
            if resp.result is not None and not isinstance(resp.result, list):
                logger.warning("RetailCustomer.Get returned non-list result")
            req = RetailCustomerGetRequest(
                search=phone,
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            customers = resp.result if isinstance(resp.result, list) else []
            if customers:
                customer = customers[0]
                if self._customer_has_telegram_field(customer):
                    self._telegram_field_supported = True
                return customer
            if resp.result is not None and not isinstance(resp.result, list):
                logger.warning("RetailCustomer.Get returned non-list result")
            return None

    async def _update_customer_telegram_id(self, customer_id: int, chat_id: str) -> None:
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerEditRequest(
                id=customer_id,
                fields=[FieldValueEdit(key="field_telegram_id", value=chat_id)],
            )
            try:
                await api.references.retail_customer.edit(req)
            except Exception as error:
                logger.warning(
                    "Не удалось обновить field_telegram_id: %s", error
                )

    async def _create_customer_from_contact(
        self,
        message: types.Message,
        phone: str,
        *,
        include_telegram_field: bool = False,
    ) -> bool:
        cache_key = self._settings_cache_key()
        settings_map = await self._fetch_settings(cache_key)
        group_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.CUSTOMER_GROUP_ID.value.lower())
        )
        if not group_id:
            logger.warning(Texts.log_customer_group_missing())
            return False

        first_name = message.contact.first_name or Texts.CUSTOMER_DEFAULT_FIRST_NAME
        last_name = message.contact.last_name
        full_name = " ".join(
            [x for x in [first_name, last_name] if x]
        ).strip()

        fields = None
        if include_telegram_field:
            fields = [FieldValueAdd(key="field_telegram_id", value=str(message.chat.id))]

        req = RetailCustomerAddRequest(
            group_id=group_id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name or None,
            main_phone=phone,
            fields=fields,
        )
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.retail_customer.add(req)
            return bool(resp.ok)

    async def _request_location(self, message: types.Message) -> None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text=Texts.BUTTON_SEND_LOCATION, request_location=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            Texts.REQUEST_LOCATION,
            reply_markup=keyboard,
        )

    async def _request_description(self, message: types.Message) -> None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=Texts.BUTTON_SKIP)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(Texts.REQUEST_DESCRIPTION, reply_markup=keyboard)

    async def _request_delivery_type(self, message: types.Message) -> None:
        types_list = await self._fetch_delivery_types()
        chat_id = str(message.chat.id)
        state = await self._get_order_state(chat_id)
        if not types_list:
            await message.answer(Texts.DELIVERY_TYPES_EMPTY)
            return
        state["delivery_type_options"] = {
            entry.name: entry.id
            for entry in types_list
            if entry.name and entry.id
        }
        await self._save_order_state(chat_id, state)
        await message.answer(
            Texts.REQUEST_DELIVERY_TYPE,
            reply_markup=self._delivery_type_keyboard(types_list),
        )

    async def _request_address(self, message: types.Message) -> None:
        await message.answer(Texts.REQUEST_ADDRESS)

    @staticmethod
    def _make_qr(value: str) -> Optional[bytes]:
        if not value or qrcode is None:
            return None
        img = qrcode.make(value)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value).strip())
        except Exception:
            return None

    @staticmethod
    def _parse_quantity(value: str) -> Optional[Decimal]:
        if not value:
            return None
        text = value.strip().replace(",", ".")
        try:
            qty = Decimal(text)
        except Exception:
            return None
        return qty if qty > 0 else None

    @staticmethod
    def _is_fractional(qty: Decimal) -> bool:
        return qty != qty.to_integral_value()

    @staticmethod
    def _unit_requires_integer(unit: Optional[Any]) -> bool:
        if not unit or unit.type is None:
            return False
        value = str(unit.type).strip().lower()
        if value in {"pcs", "2"}:
            return True
        if value in {"non_pcs", "1"}:
            return False
        return False

    @staticmethod
    def _parse_int_list(value: Optional[str]) -> List[int]:
        if not value:
            return []
        if isinstance(value, str):
            raw = value.replace(";", ",")
            parts = [part.strip() for part in raw.split(",")]
        else:
            parts = [str(value).strip()]
        ids: List[int] = []
        for part in parts:
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                continue
        return ids

    @staticmethod
    def _normalize_phone(value: str) -> Optional[str]:
        if not value:
            return None
        digits = "".join(ch for ch in value if ch.isdigit())
        return digits or None
