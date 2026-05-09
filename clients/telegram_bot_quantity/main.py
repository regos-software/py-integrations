import asyncio
import httpx
import json
import hashlib
import time
import uuid
from enum import Enum
from typing import Any, Optional, Dict, List, Set, Tuple
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, BaseFilter
from aiogram.types import Update as TelegramUpdate
from aiogram.types import BotCommand
from clients.telegram_bot_quantity.services.send_messages import send_messages
from clients.telegram_polling import telegram_polling_manager
from .utils import parse_chat_ids, extract_chat_id
from .handlers.get_quantity import handle_get_quantity
from schemas.integration.telegram_integration_base import IntegrationTelegramBase
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
)
from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from clients.base import ClientBase
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
from config.settings import settings

# Configure logging
logger = setup_logger("telegram_bot_min_quantity")


PENDING_GET_QUANTITY_SEARCH_TTL_SECONDS = 5 * 60
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


# Define constants for Telegram settings
class TelegramSettings(Enum):
    BOT_TOKEN = "BOT_TOKEN"
    CHAT_IDS = "CHAT_IDS"
    STOCK_IDS = "STOCK_IDS"


# Configuration for Telegram bot
class TelegramBotMinQuantityConfig:
    WEBHOOK_REFRESH_TTL = max(int(settings.telegram_webhook_refresh_ttl or 0), 60)
    WEBHOOK_LOCAL_TTL = min(300, WEBHOOK_REFRESH_TTL)
    WEBHOOK_LOCK_TTL = 30
    SETTINGS_TTL = max(int(settings.redis_cache_ttl or 0), 60)
    SETTINGS_STALE_TTL = max(SETTINGS_TTL * 10, 10 * 60)
    SETTINGS_LOCAL_TTL = min(30, max(5, SETTINGS_TTL // 4))
    SETTINGS_LOCAL_MAX = 10000
    SETTINGS_LOCK_TTL = 10
    SETTINGS_LOCK_WAIT_SECONDS = 2.0
    SUBSCRIBER_LOCK_TTL = 15
    BATCH_SIZE = 50  # Number of messages to process in one batch
    RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
    RETRY_WAIT_SECONDS = 2  # Seconds to wait between retries
    INTEGRATION_KEY = "regos_telegram_minquantity"
    SLEEP_BETWEEN_MESSAGES = 0.0  # Delay between sending messages (adjust if needed)
    REDIS_PREFIX = "tbq"
    STREAM_GROUP = "tbqw"
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = max(int(settings.telegram_min_quantity_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(settings.telegram_min_quantity_stream_batch_size or 0), 1)
    STREAM_WORKERS_PER_STREAM = max(int(settings.telegram_min_quantity_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = max(int(settings.telegram_min_quantity_stream_retry_limit or 0), 1)
    DEDUPE_TTL_SEC = 24 * 60 * 60
    SEND_CONCURRENCY = max(int(settings.telegram_min_quantity_send_concurrency or 0), 1)


class TelegramBotMinQuantityIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False  # Track if handlers are registered
        self._owns_bot_session = True
        self._bot_token_fingerprint = ""

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _polling_key(self) -> str:
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:{self.connected_integration_id or 'unknown'}"

    def _polling_key_unknown(self) -> str:
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:unknown"

    @staticmethod
    def _polling_key_for_token(bot_token: str) -> str:
        token_hash = hashlib.sha256(str(bot_token).encode("utf-8")).hexdigest()[:16]
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:token:{token_hash}"

    def _pending_get_quantity_search_key(self, chat_id: str) -> str:
        return self._redis_key("q", self.connected_integration_id, chat_id)

    async def _set_pending_get_quantity_search(self, chat_id: str) -> None:
        self._require_redis()
        key = self._pending_get_quantity_search_key(chat_id)
        await redis_ops.setex(key, PENDING_GET_QUANTITY_SEARCH_TTL_SECONDS, "1")

    async def _clear_pending_get_quantity_search(self, chat_id: str) -> None:
        self._require_redis()
        key = self._pending_get_quantity_search_key(chat_id)
        await redis_ops.delete(key)

    async def _has_pending_get_quantity_search(self, chat_id: str) -> bool:
        self._require_redis()
        key = self._pending_get_quantity_search_key(chat_id)
        return bool(await redis_ops.exists(key))

    async def __aenter__(self):
        return self

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

    def _create_error_response(
        self, error_code: int, description: str
    ) -> IntegrationErrorResponse:
        """Create a standardized error response."""
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=error_code, description=description)
        )

    def _parse_stock_ids(self, settings_map: Dict[str, str]) -> Optional[Set[int]]:
        """
        STOCK_IDS — строка с ID складов через запятую.
        Пустая строка или отсутствие настройки = нет фильтрации (все склады).
        """
        raw = settings_map.get(TelegramSettings.STOCK_IDS.value.lower())
        if raw is None:
            return None

        # Accept either: "1,2,3" or JSON list like "[1, 2, 3]".
        if isinstance(raw, (list, tuple, set)):
            candidates = list(raw)
        else:
            text = str(raw).strip()
            if not text:
                return None

            candidates = None
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        candidates = parsed
                except Exception:
                    candidates = None

            if candidates is None:
                candidates = [
                    p.strip() for p in text.replace(";", ",").split(",") if p.strip()
                ]

        if not candidates:
            return None

        result: Set[int] = set()
        for part in candidates:
            try:
                result.add(int(str(part).strip()))
            except ValueError:
                logger.warning(
                    "Invalid STOCK_IDS value '%s' in settings (ID=%s)",
                    part,
                    self.connected_integration_id,
                )

        return result or None

    @staticmethod
    def _redis_enabled() -> bool:
        return bool(settings.redis_enabled and redis_ops)

    @staticmethod
    def _require_redis() -> None:
        if not TelegramBotMinQuantityIntegration._redis_enabled():
            raise RuntimeError("Redis is required for telegram_bot_min_quantity")

    @classmethod
    def _redis_key(cls, *parts: Any) -> str:
        suffix = ":".join(str(part).strip() for part in parts if str(part or "").strip())
        return f"{TelegramBotMinQuantityConfig.REDIS_PREFIX}:{suffix}"

    @staticmethod
    def _token_fingerprint(bot_token: str) -> str:
        return hashlib.sha256(str(bot_token or "").encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _updates_stream_key(cls) -> str:
        return cls._redis_key("s", "u")

    @classmethod
    def _jobs_stream_key(cls) -> str:
        return cls._redis_key("s", "j")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._redis_key("s", "d")

    @classmethod
    def _kind_code(cls, kind: str) -> str:
        return {
            "telegram_update": "u",
            "send_messages": "s",
            "webhook": "w",
        }.get(str(kind or ""), "x")

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
        return redis_ttl_seconds(TelegramBotMinQuantityConfig.STREAM_TTL_SEC)

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
            TelegramBotMinQuantityConfig.STREAM_GROUP,
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
            maxlen=TelegramBotMinQuantityConfig.STREAM_MAXLEN,
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
            str(TelegramBotMinQuantityConfig.DEDUPE_TTL_SEC),
            str(TelegramBotMinQuantityConfig.STREAM_MAXLEN),
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
        if event_id and kind != "send_messages":
            attempt_value = max(int(attempt or 0), 0)
            dedupe_key = (
                cls._dedupe_key(ci, kind, event_id)
                if attempt_value <= 0
                else cls._retry_dedupe_key(ci, kind, event_id, attempt_value)
            )
            inserted = await cls._enqueue_stream_deduped(
                stream_key=stream_key,
                dedupe_key=dedupe_key,
                fields=fields,
            )
            if not inserted:
                logger.debug(
                    "Telegram min quantity duplicate not enqueued: ci=%s kind=%s event_id=%s",
                    ci,
                    kind,
                    event_id,
                )
            return inserted
        await cls._enqueue_stream(stream_key, fields)
        return True

    @classmethod
    def _stream_worker_specs(cls) -> List[Tuple[str, int]]:
        return [
            (stream_key, index)
            for stream_key in (cls._updates_stream_key(), cls._jobs_stream_key())
            for index in range(TelegramBotMinQuantityConfig.STREAM_WORKERS_PER_STREAM)
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
            if isinstance(runtime, TelegramBotMinQuantityIntegration):
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
                    name=f"tbq_stream_{stream_key.rsplit(':', 1)[-1]}_{index}",
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
                logger.exception("Error while stopping Telegram min quantity stream worker")
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
        await redis_ops.xack(stream_key, TelegramBotMinQuantityConfig.STREAM_GROUP, entry_id)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                TelegramBotMinQuantityConfig.STREAM_GROUP,
                consumer,
                min_idle_time=TelegramBotMinQuantityConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=TelegramBotMinQuantityConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            logger.warning("Telegram min quantity stream xautoclaim failed: stream=%s error=%s", stream_key, error)
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
        logger.info("Telegram min quantity stream worker started: stream=%s", stream_key)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._touch_stream_ttl(stream_key)
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= TelegramBotMinQuantityConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        for entry_id, fields in await cls._process_claimed_entries(stream_key, consumer):
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=entry_id,
                                fields=fields,
                            )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=TelegramBotMinQuantityConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=TelegramBotMinQuantityConfig.STREAM_BATCH_SIZE,
                            block=TelegramBotMinQuantityConfig.STREAM_READ_BLOCK_MS,
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
                    logger.exception("Telegram min quantity stream worker error: stream=%s error=%s", stream_key, error)
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
            logger.warning("Telegram min quantity stream entry has invalid payload: entry_id=%s fields=%s", entry_id, fields)
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
                chat_id = extract_chat_id(payload)
                if chat_id:
                    chat_lock_key = cls._redis_key("cl", ci, chat_id)
                    chat_lock_token = await cls._acquire_redis_lock(
                        chat_lock_key,
                        300,
                        wait_seconds=10.0,
                    )
                    if not chat_lock_token:
                        raise TimeoutError(
                            f"Timed out waiting for Telegram min quantity chat lock {ci}:{chat_id}"
                        )
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
                "Telegram min quantity stream job processed: ci=%s kind=%s entry_id=%s status=%s",
                ci,
                kind,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            next_attempt = attempt + 1
            if next_attempt >= TelegramBotMinQuantityConfig.STREAM_MAX_RETRIES:
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
                    "Telegram min quantity stream job moved to DLQ: ci=%s kind=%s entry_id=%s error=%s",
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
                "Telegram min quantity stream job requeued: ci=%s kind=%s entry_id=%s attempt=%s error=%s",
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
        TelegramBotMinQuantityIntegration._require_redis()
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
        if not (TelegramBotMinQuantityIntegration._redis_enabled() and token):
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
        if len(_SETTINGS_LOCAL_CACHE) >= TelegramBotMinQuantityConfig.SETTINGS_LOCAL_MAX:
            for key, (expires_at, _) in list(_SETTINGS_LOCAL_CACHE.items()):
                if expires_at <= now_ts:
                    _SETTINGS_LOCAL_CACHE.pop(key, None)
            while len(_SETTINGS_LOCAL_CACHE) >= TelegramBotMinQuantityConfig.SETTINGS_LOCAL_MAX:
                _SETTINGS_LOCAL_CACHE.pop(next(iter(_SETTINGS_LOCAL_CACHE)), None)
        _SETTINGS_LOCAL_CACHE[cache_key] = (
            now_ts + TelegramBotMinQuantityConfig.SETTINGS_LOCAL_TTL,
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

    def _settings_cache_key(self) -> str:
        return self._redis_key("cfg", self.connected_integration_id)

    def _settings_stale_cache_key(self) -> str:
        return self._redis_key("cfgs", self.connected_integration_id)

    def _settings_fetch_lock_key(self) -> str:
        return self._redis_key("cfgl", self.connected_integration_id)

    def _subscriber_update_lock_key(self) -> str:
        return self._redis_key("sl", self.connected_integration_id)

    async def _fetch_settings(self, cache_key: Optional[str] = None) -> Dict[str, str]:
        """Retrieve settings from local/Redis cache or API under a Redis lock."""
        self._require_redis()
        cache_key = cache_key or self._settings_cache_key()
        local = self._read_local_settings_cache(cache_key)
        if local is not None:
            return local
        try:
            cached_data = await redis_ops.get(cache_key)
            if cached_data:
                if isinstance(cached_data, (bytes, bytearray)):
                    cached_data = cached_data.decode("utf-8")
                settings_map = self._normalize_settings_map(_json_loads(cached_data))
                self._write_local_settings_cache(cache_key, settings_map)
                return settings_map
        except Exception as error:
            logger.warning("Redis settings read error: %s", error)

        lock_token = await self._acquire_redis_lock(
            self._settings_fetch_lock_key(),
            TelegramBotMinQuantityConfig.SETTINGS_LOCK_TTL,
            wait_seconds=TelegramBotMinQuantityConfig.SETTINGS_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            stale = await self._read_settings_stale_cache()
            if stale is not None:
                return stale
            raise TimeoutError(
                f"Timed out waiting for Telegram min quantity settings refresh for ID {self.connected_integration_id}"
            )

        try:
            cached_data = await redis_ops.get(cache_key)
            if cached_data:
                if isinstance(cached_data, (bytes, bytearray)):
                    cached_data = cached_data.decode("utf-8")
                settings_map = self._normalize_settings_map(_json_loads(cached_data))
                self._write_local_settings_cache(cache_key, settings_map)
                return settings_map

            async with RegosAPI(
                connected_integration_id=self.connected_integration_id
            ) as api:
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
            await self._write_settings_cache(settings_map)
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
            await pipe.setex(
                self._settings_cache_key(),
                TelegramBotMinQuantityConfig.SETTINGS_TTL,
                payload,
            )
            await pipe.setex(
                self._settings_stale_cache_key(),
                TelegramBotMinQuantityConfig.SETTINGS_STALE_TTL,
                payload,
            )
            await pipe.execute()

    async def _get_settings_map(self) -> Dict[str, str]:
        return await self._fetch_settings(self._settings_cache_key())

    async def _add_subscriber(self, chat_id: str) -> None:
        """Add a chat ID to the subscribers list."""
        self._require_redis()
        settings_map = await self._get_settings_map()
        raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
        if chat_id in parse_chat_ids(raw_chat_ids):
            return

        lock_token = await self._acquire_redis_lock(
            self._subscriber_update_lock_key(),
            TelegramBotMinQuantityConfig.SUBSCRIBER_LOCK_TTL,
            wait_seconds=TelegramBotMinQuantityConfig.SETTINGS_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            raise TimeoutError(
                f"Timed out waiting for Telegram min quantity subscriber lock for ID {self.connected_integration_id}"
            )
        try:
            _SETTINGS_LOCAL_CACHE.pop(self._settings_cache_key(), None)
            settings_map = await self._get_settings_map()
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id not in subscribers:
                subscribers.append(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = (
                        await api.integrations.connected_integration_setting.edit(
                            [
                                ConnectedIntegrationSettingEditItem(
                                    key=TelegramSettings.CHAT_IDS.value,
                                    value=json.dumps(subscribers),
                                    connected_integration_id=self.connected_integration_id,
                                )
                            ]
                        )
                    )
                success = getattr(edit_resp, "result", edit_resp)
                if not success:
                    raise RuntimeError("Failed to update settings")
                settings_map[TelegramSettings.CHAT_IDS.value.lower()] = json.dumps(
                    subscribers
                )
                await self._write_settings_cache(settings_map)
                logger.info(
                    f"Added subscriber {chat_id} for ID {self.connected_integration_id}"
                )
        except Exception as error:
            logger.error(f"Error adding subscriber {chat_id}: {error}")
            raise
        finally:
            await self._release_redis_lock(self._subscriber_update_lock_key(), lock_token)

    async def _remove_subscriber(self, chat_id: str) -> None:
        """Remove a chat ID from the subscribers list."""
        self._require_redis()
        settings_map = await self._get_settings_map()
        raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
        if chat_id not in parse_chat_ids(raw_chat_ids):
            return

        lock_token = await self._acquire_redis_lock(
            self._subscriber_update_lock_key(),
            TelegramBotMinQuantityConfig.SUBSCRIBER_LOCK_TTL,
            wait_seconds=TelegramBotMinQuantityConfig.SETTINGS_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            raise TimeoutError(
                f"Timed out waiting for Telegram min quantity subscriber lock for ID {self.connected_integration_id}"
            )
        try:
            _SETTINGS_LOCAL_CACHE.pop(self._settings_cache_key(), None)
            settings_map = await self._get_settings_map()
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id in subscribers:
                subscribers.remove(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = (
                        await api.integrations.connected_integration_setting.edit(
                            [
                                ConnectedIntegrationSettingEditItem(
                                    key=TelegramSettings.CHAT_IDS.value,
                                    value=json.dumps(subscribers),
                                    connected_integration_id=self.connected_integration_id,
                                )
                            ]
                        )
                    )
                success = getattr(edit_resp, "result", edit_resp)
                if not success:
                    raise RuntimeError("Failed to update settings")
                settings_map[TelegramSettings.CHAT_IDS.value.lower()] = json.dumps(
                    subscribers
                )
                await self._write_settings_cache(settings_map)
                logger.info(
                    f"Removed subscriber {chat_id} for ID {self.connected_integration_id}"
                )
        except Exception as error:
            logger.error(f"Error removing subscriber {chat_id}: {error}")
            raise
        finally:
            await self._release_redis_lock(self._subscriber_update_lock_key(), lock_token)

    async def _initialize_bot(self) -> None:
        """Initialize the Telegram bot if not already done."""
        if self.bot:
            return
        ci = str(self.connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        settings_map = await self._get_settings_map()
        bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
        if not bot_token:
            raise ValueError(
                f"Bot token not found for ID {self.connected_integration_id}"
            )
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
            self.bot = Bot(
                token=bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
            )
            self._bot_token_fingerprint = token_fingerprint
            await self._setup_handlers()
            self._owns_bot_session = False
            _BOT_RUNTIME_CACHE[ci] = (token_fingerprint, self)

    async def _set_bot_commands(self) -> None:
        """Publish bot commands so they show up in Telegram UI."""
        if not self.bot:
            return
        await self.bot.set_my_commands(
            commands=[
                BotCommand(
                    command="start",
                    description="Запуск бота",
                ),
                BotCommand(
                    command="get_quantity",
                    description="Минимальные остатки",
                ),
                BotCommand(
                    command="get_quantity_search",
                    description="Остатки по поиску",
                ),
                # BotCommand(
                #     command="stop",
                #     description="Отписаться от уведомлений",
                # ),
            ]
        )

    async def _setup_handlers(self) -> None:
        """Set up command and callback handlers for the bot."""
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        class _PendingGetQuantitySearchFilter(BaseFilter):
            def __init__(self, integration: "TelegramBotMinQuantityIntegration"):
                self._integration = integration

            async def __call__(self, message: types.Message) -> bool:
                try:
                    chat_id = str(message.chat.id)
                except Exception:
                    return False
                if not isinstance(message.text, str):
                    return False
                return await self._integration._has_pending_get_quantity_search(chat_id)

        @self.dispatcher.message(Command("start"))
        async def handle_start_command(message: types.Message):
            """Handle /start command to subscribe to notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._add_subscriber(chat_id)
                await message.answer("Вы активировали бота минимальных остатков!")
                logger.info(
                    f"Client {chat_id} subscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error subscribing. Please try again later.")

        @self.dispatcher.message(Command("get_quantity"))
        async def handle_get_quantity_command(message: types.Message):
            """Handle /get_quantity command to provide quantity information."""
            try:
                settings_map = await self._get_settings_map()
                stock_ids_set = self._parse_stock_ids(settings_map) or set()
                await handle_get_quantity(
                    integration=self,
                    message=message,
                    stock_ids=sorted(stock_ids_set),
                )
            except Exception as error:
                logger.exception("/get_quantity failed: %s", error)
                await message.answer(
                    "Ошибка при формировании отчета. Попробуйте позже."
                )

        @self.dispatcher.message(Command("get_quantity_search", "get_quanity_search"))
        async def handle_get_quantity_search_command(message: types.Message):
            """Ask user for a search string, then generate report filtered by it."""
            chat_id = str(message.chat.id)
            await self._set_pending_get_quantity_search(chat_id)
            await message.answer(
                "Введите название товара по которому нужно "
                "составить отчет по минимальным остаткам."
                "(например makfa. Отчет будет содержать список товаров в названии которых "
                "содержиться слово makfa) (или /cancel для отмены)."
            )

        @self.dispatcher.message(Command("cancel"))
        async def handle_cancel_command(message: types.Message):
            chat_id = str(message.chat.id)
            if await self._has_pending_get_quantity_search(chat_id):
                await self._clear_pending_get_quantity_search(chat_id)
                await message.answer("Отменено.")

        @self.dispatcher.message(_PendingGetQuantitySearchFilter(self))
        async def handle_get_quantity_search_text(message: types.Message):
            """Receive the search string and run the report."""
            chat_id = str(message.chat.id)
            text = (message.text or "").strip()
            if not text or text.startswith("/"):
                await message.answer(
                    "Пожалуйста, отправьте текст для поиска (или /cancel)."
                )
                return

            await self._clear_pending_get_quantity_search(chat_id)
            try:
                settings_map = await self._get_settings_map()
                stock_ids_set = self._parse_stock_ids(settings_map) or set()
                await handle_get_quantity(
                    integration=self,
                    message=message,
                    stock_ids=sorted(stock_ids_set),
                    search=text,
                )
            except Exception as error:
                logger.exception("/get_quantity_search failed: %s", error)
                await message.answer(
                    "Ошибка при формировании отчета. Попробуйте позже."
                )

        # @self.dispatcher.message(Command("stop"))
        # async def handle_stop_command(message: types.Message):
        #     """Handle /stop command to unsubscribe from notifications."""
        #     chat_id = str(message.chat.id)
        #     try:
        #         await self._remove_subscriber(chat_id)
        #         await message.answer("Вы отписались от уведомлений.")
        #         logger.info(
        #             f"Client {chat_id} unsubscribed for ID {self.connected_integration_id}"
        #         )
        #     except Exception:
        #         await message.answer("Error unsubscribing. Please try again later.")

        self.handlers_registered = True

    @staticmethod
    def _resolve_webhook_base_url() -> str:
        base_url = str(
            settings.proxy_integration_url or settings.integration_url
        ).strip()
        if not base_url:
            base_url = str(settings.integration_url).strip()
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
            _now_ts() + TelegramBotMinQuantityConfig.WEBHOOK_LOCAL_TTL
        )
        await redis_ops.setex(
            self._webhook_refresh_cache_key(),
            TelegramBotMinQuantityConfig.WEBHOOK_REFRESH_TTL,
            "1",
        )

    async def _clear_webhook_refresh_cache(self) -> None:
        if not self.connected_integration_id:
            return
        self._require_redis()
        _WEBHOOK_LOCAL_CACHE.pop(self._webhook_refresh_cache_key(), None)
        await redis_ops.delete(self._webhook_refresh_cache_key())

    async def _ensure_webhook_from_regos(self, *, force: bool = False) -> None:
        if self._is_longpolling_mode() or not self.bot or not self.connected_integration_id:
            return

        cache_key = self._webhook_refresh_cache_key()
        if not force and int(_WEBHOOK_LOCAL_CACHE.get(cache_key) or 0) > _now_ts():
            return
        if not force and await redis_ops.exists(cache_key):
            _WEBHOOK_LOCAL_CACHE[cache_key] = (
                _now_ts() + TelegramBotMinQuantityConfig.WEBHOOK_LOCAL_TTL
            )
            return

        lock_token = await self._acquire_redis_lock(
            self._webhook_refresh_lock_key(),
            TelegramBotMinQuantityConfig.WEBHOOK_LOCK_TTL,
            wait_seconds=TelegramBotMinQuantityConfig.SETTINGS_LOCK_WAIT_SECONDS if force else 0.0,
        )
        if not lock_token:
            logger.debug(
                "Skipping Telegram min quantity webhook refresh for ID %s: another instance is refreshing it",
                self.connected_integration_id,
            )
            return

        webhook_url = self._build_webhook_url()
        try:
            if not force and await redis_ops.exists(cache_key):
                _WEBHOOK_LOCAL_CACHE[cache_key] = (
                    _now_ts() + TelegramBotMinQuantityConfig.WEBHOOK_LOCAL_TTL
                )
                return
            info = await self.bot.get_webhook_info()
            current_url = (getattr(info, "url", "") or "").rstrip("/")
            if current_url != webhook_url.rstrip("/"):
                await self.bot.set_webhook(url=webhook_url)
                logger.info("Telegram min quantity webhook url updated: %s", webhook_url)
            await self._touch_webhook_refresh_cache()
        finally:
            await self._release_redis_lock(self._webhook_refresh_lock_key(), lock_token)

    @staticmethod
    def _telegram_update_event_id(payload: Dict[str, Any]) -> str:
        update_id = payload.get("update_id")
        if update_id is not None:
            return f"u:{update_id}"
        raw = _json_dumps(payload)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _process_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None
    ) -> Dict:
        await self._initialize_bot()
        await self._set_bot_commands()
        await self._ensure_webhook_from_regos(force=False)
        return {
            "status": "webhook processed",
            "connected_integration_id": self.connected_integration_id,
            "action": action,
        }

    async def _process_telegram_update(self, payload: Dict[str, Any]) -> Dict:
        await self._initialize_bot()
        await self._setup_handlers()

        chat_id = extract_chat_id(payload)
        if chat_id:
            try:
                await self._add_subscriber(chat_id)
            except Exception as error:
                logger.warning("Failed to add subscriber %s: %s", chat_id, error)

        try:
            telegram_update = TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error("Invalid Telegram min quantity update: %s", error)
            return self._create_error_response(400, "Invalid Telegram update").dict()

        try:
            await self.dispatcher.feed_update(self.bot, telegram_update)
        except Exception as error:
            logger.exception("Error processing Telegram min quantity update: %s", error)
            return self._create_error_response(
                500, "Error processing Telegram update"
            ).dict()

        return {
            "status": "processed",
            "connected_integration_id": self.connected_integration_id,
            "chat_id": chat_id,
        }

    async def _send_messages_now(self, messages: List[Dict]) -> Dict:
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            )

        for message in messages:
            if "message" not in message or not message["message"]:
                return self._create_error_response(
                    1009, f"Message missing text: {message}"
                )
            if "recipient" not in message or not message["recipient"]:
                return self._create_error_response(
                    1010, f"Message missing recipient: {message}"
                )

        try:
            settings_map = await self._get_settings_map()
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
        except Exception as error:
            return self._create_error_response(
                1001, f"Settings retrieval error: {error}"
            )

        await self._initialize_bot()
        await self._setup_handlers()

        results = []
        for i in range(0, len(messages), TelegramBotMinQuantityConfig.BATCH_SIZE):
            batch = messages[i : i + TelegramBotMinQuantityConfig.BATCH_SIZE]
            logger.debug("Sending Telegram min quantity batch %s-%s", i, i + len(batch))
            try:
                result = await send_messages(
                    bot=self.bot,
                    messages=batch,
                    sleep_between=TelegramBotMinQuantityConfig.SLEEP_BETWEEN_MESSAGES,
                    logger=logger,
                    concurrency=TelegramBotMinQuantityConfig.SEND_CONCURRENCY,
                )
                results.append(result)
            except Exception as error:
                logger.error("Error sending Telegram min quantity batch %s: %s", i, error)
                results.append({"error": str(error), "batch_index": i})

        logger.debug("Telegram min quantity message sending completed: batches=%s", len(results))
        return {"sent_batches": len(results), "details": results}

    @retry(
        stop=stop_after_attempt(TelegramBotMinQuantityConfig.RETRY_ATTEMPTS),
        wait=wait_fixed(TelegramBotMinQuantityConfig.RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=lambda retry_state: logger.debug(
            f"Retry attempt: {retry_state.attempt_number}"
        ),
    )
    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Connect to Telegram and set up the webhook or long-polling."""
        logger.info(
            f"Connecting to TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        try:
            await self._ensure_stream_workers()
            settings_map = await self._get_settings_map()
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")

            polling_key_token = self._polling_key_for_token(bot_token)
            await self._initialize_bot()
            await self._set_bot_commands()
            await self._setup_handlers()

            if self._is_longpolling_mode():
                # Ensure we never run multiple getUpdates streams for the same bot token.
                # Also stop any legacy sessions started under connected_integration_id/unknown keys.
                await telegram_polling_manager.stop(self._polling_key_unknown())
                await telegram_polling_manager.stop(self._polling_key())
                await self.bot.delete_webhook(drop_pending_updates=True)
                await telegram_polling_manager.start(
                    polling_key_token, self.bot, self.dispatcher
                )
                logger.info("Webhook deleted (longpolling mode).")
                return {"status": "connected", "mode": "longpolling"}

            await telegram_polling_manager.stop(self._polling_key_unknown())
            await telegram_polling_manager.stop(self._polling_key())
            await telegram_polling_manager.stop(polling_key_token)

            webhook_url = self._build_webhook_url()
            await self.bot.set_webhook(url=webhook_url)
            await self._touch_webhook_refresh_cache()
            logger.info(f"Webhook set: {webhook_url}")
            return {
                "status": "connected",
                "mode": "webhook",
                "webhook_url": webhook_url,
            }
        except (httpx.RequestError, httpx.HTTPStatusError) as error:
            logger.error(f"Connection error: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected connection error: {error}")
            return self._create_error_response(1003, f"Webhook setup failed: {error}")

    async def disconnect(self, **kwargs) -> Dict:
        """Disconnect from Telegram and remove the webhook."""
        logger.info(
            f"Disconnecting from TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        # Best-effort stop for all possible polling keys.
        await telegram_polling_manager.stop(self._polling_key_unknown())
        await telegram_polling_manager.stop(self._polling_key())
        try:
            settings_map = await self._get_settings_map()
            bot_token = (settings_map or {}).get(
                TelegramSettings.BOT_TOKEN.value.lower()
            )
            if bot_token:
                await telegram_polling_manager.stop(
                    self._polling_key_for_token(bot_token)
                )
        except Exception as error:
            logger.debug("Failed to resolve bot token for polling stop: %s", error)
        try:
            if not self.bot:
                await self._initialize_bot()
            if self.bot:
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
            return self._create_error_response(1004, f"Webhook removal failed: {error}")

    async def reconnect(self, **kwargs) -> Dict:
        """Reconnect to Telegram by disconnecting and connecting again."""
        logger.info(
            f"Reconnecting to TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        await self.disconnect()
        return await self.connect()

    async def update_settings(
        self,
        request: Optional[ConnectedIntegrationSettingEditRequest] = None,
        data: Optional[List[Dict]] = None,
        incoming_settings: Optional[List[Dict]] = None,
        **kwargs,
    ) -> IntegrationSuccessResponse:
        """Update integration settings and refresh the connection."""
        logger.info(f"Updating settings (ID: {self.connected_integration_id})")
        await self._clear_settings_cache()
        await self._clear_webhook_refresh_cache()
        await self._close_bot_runtime_cache(self.connected_integration_id)
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict:
        """Process incoming webhook requests from the API."""
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            ).dict()
        await self._enqueue_event(
            str(self.connected_integration_id),
            kind="webhook",
            payload=data or {},
            action=action,
        )
        return {
            "status": "queued",
            "connected_integration_id": self.connected_integration_id,
        }

    async def handle_external(self, envelope: Dict) -> Dict:
        """Handle incoming Telegram updates."""
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._create_error_response(
                400, "Invalid request body: JSON object expected"
            ).dict()
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            ).dict()
        try:
            TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error("Invalid Telegram min quantity update: %s", error)
            return self._create_error_response(400, "Invalid Telegram update").dict()

        event_id = self._telegram_update_event_id(payload)
        queued = await self._enqueue_event(
            str(self.connected_integration_id),
            kind="telegram_update",
            payload=payload,
            event_id=event_id,
        )
        return {
            "status": "queued" if queued else "duplicate",
            "connected_integration_id": self.connected_integration_id,
            "event_id": event_id,
        }

    async def send_messages(self, messages: List[Dict]) -> Dict:
        """Send multiple messages to Telegram in batches."""
        logger.info(f"Starting message send for ID {self.connected_integration_id}")
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            )

        # Validate messages
        for message in messages:
            if "message" not in message or not message["message"]:
                return self._create_error_response(
                    1009, f"Message missing text: {message}"
                )
            if "recipient" not in message or not message["recipient"]:
                return self._create_error_response(
                    1010, f"Message missing recipient: {message}"
                )

        event_id = hashlib.sha256(
            _json_dumps(messages).encode("utf-8")
        ).hexdigest()
        queued = await self._enqueue_event(
            str(self.connected_integration_id),
            kind="send_messages",
            payload={"messages": messages},
            event_id=event_id,
        )
        return {
            "status": "queued" if queued else "duplicate",
            "connected_integration_id": self.connected_integration_id,
            "event_id": event_id,
        }
