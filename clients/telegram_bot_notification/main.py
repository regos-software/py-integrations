import asyncio
import httpx
import hashlib
import json
import re
import time
import uuid
from enum import Enum
from typing import Any, Optional, Dict, List, Set, Tuple
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import Update as TelegramUpdate
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from clients.telegram_bot_notification.services.message_formatters import (
    format_cheque_details,
    format_cheque_notification,
    format_session_details,
    format_session_notification,
)
from clients.telegram_polling import telegram_polling_manager
from schemas.api.docs.cash_amount_details import CashAmountDetails, CashAmountDetailsGetRequest
from schemas.api.docs.cheque import DocCheque
from schemas.api.docs.cheque_payment import DocChequePayment, DocChequePaymentGetRequest
from schemas.api.reports.retail_report.count import CountsGetRequest
from schemas.api.reports.retail_report.payment import PaymentGetRequest
from .utils import parse_chat_ids, extract_chat_id
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
from schemas.api.docs.cheque_operation import DocChequeOperation, DocChequeOperationGetRequest
from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_client,
    redis_error_contains,
    redis_expire_if_due,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)
from config.settings import settings

# Configure logging
logger = setup_logger("telegram_bot_notification")

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
    CHEQUE_NOTIFICATION = "CHEQUE_NOTIFICATION"
    STOCK_IDS = "STOCK_IDS"


# Configuration for Telegram bot
class TelegramBotConfig:
    BASE_URL = "https://api.telegram.org"
    WEBHOOK_BASE_URL = (
        f"{(settings.proxy_integration_url or settings.integration_url).rstrip('/')}/external"
    )
    WEBHOOK_REFRESH_TTL = max(int(settings.telegram_webhook_refresh_ttl or 0), 60)
    DEFAULT_TIMEOUT = 10  # HTTP request timeout in seconds
    SETTINGS_TTL = max(int(settings.redis_cache_ttl or 0), 60)  # Cache duration for settings
    SETTINGS_STALE_TTL = max(SETTINGS_TTL * 10, 10 * 60)
    SETTINGS_LOCK_TTL = 10
    SETTINGS_LOCK_WAIT_SECONDS = 2.0
    WEBHOOK_LOCK_TTL = 30
    WEBHOOK_LOCAL_TTL = min(300, WEBHOOK_REFRESH_TTL)
    SUBSCRIBER_LOCK_TTL = 15
    INVALID_TOKEN_TTL = 5 * 60
    MISCONFIG_LOG_TTL = 5 * 60
    BATCH_SIZE = 50  # Number of messages to process in one batch
    RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
    RETRY_WAIT_SECONDS = 2  # Seconds to wait between retries
    INTEGRATION_KEY = "regos_telegram_notifier"
    REDIS_PREFIX = "tbn"
    STREAM_GROUP = "tbnw"
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = max(int(settings.telegram_notification_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(settings.telegram_notification_stream_batch_size or 0), 1)
    STREAM_WORKERS_PER_STREAM = max(int(settings.telegram_notification_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = 3
    DEDUPE_TTL_SEC = 24 * 60 * 60
    SETTINGS_LOCAL_TTL = min(30, max(5, SETTINGS_TTL // 4))
    SETTINGS_LOCAL_MAX = 10000
    SEND_CONCURRENCY = max(int(settings.telegram_notification_send_concurrency or 0), 1)
    CHAT_MIN_INTERVAL_SEC = max(float(settings.telegram_notification_chat_min_interval_sec or 0), 0.0)
    FLOOD_RETRY_ATTEMPTS = max(int(settings.telegram_notification_flood_retry_attempts or 0), 1)
    FLOOD_EXTRA_DELAY_SEC = max(float(settings.telegram_notification_flood_extra_delay_sec or 0), 0.0)
    SEND_LOCK_TTL = 120
    SEND_LOCK_WAIT_SECONDS = 30.0


class TelegramBotNotificationIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        self.http_client: Optional[httpx.AsyncClient] = None
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False
        self._owns_bot_session = True
        self._bot_token_fingerprint = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            try:
                await self.http_client.aclose()
            except Exception as error:
                logger.warning("Failed to close http client: %s", error)
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

    def _cheque_notifications_enabled(self, settings_map: Dict[str, str]) -> bool:
        """
        Возвращает True, если уведомления по чекам включены.
        Отсутствие настройки трактуем как включенные уведомления.
        Отключаем только при 'false' или '0' (регистр/пробелы игнорируются).
        """
        raw = settings_map.get(TelegramSettings.CHEQUE_NOTIFICATION.value.lower())
        if raw is None:
            return True  # настройки нет — включено по умолчанию

        s = str(raw).strip().lower()
        return s not in {"false", "0"}
   
    def _parse_stock_ids(self, settings_map: Dict[str, str]) -> Optional[Set[int]]:
        """
        STOCK_IDS — строка с ID складов через запятую.
        Пустая строка или отсутствие настройки = нет фильтрации (все склады).
        """
        raw = settings_map.get(TelegramSettings.STOCK_IDS.value.lower())
        if raw is None:
            return None

        text = str(raw).strip()
        if not text:
            return None

        result: Set[int] = set()
        for part in text.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                result.add(int(part))
            except ValueError:
                logger.warning(
                    "Invalid STOCK_IDS value '%s' in settings (ID=%s)",
                    part,
                    self.connected_integration_id,
                )

        return result or None

    @staticmethod
    def _subscriber_removal_reason(error: object) -> Optional[str]:
        text = str(error).lower()
        if "bot was blocked by the user" in text:
            return "bot was blocked"
        if "bot was kicked from the group chat" in text:
            return "bot was kicked from the group"
        if "chat not found" in text or "bot is not a member of the chat" in text:
            return "chat is unavailable"
        if "not enough rights to send text messages to the chat" in text:
            return "bot lacks rights"
        if "not enough rights to send messages" in text:
            return "bot lacks rights"
        if "forbidden: user is deactivated" in text:
            return "user is deactivated"
        return None

    @staticmethod
    def _migrate_to_chat_id(error: object) -> Optional[str]:
        migrate_to_chat_id = getattr(error, "migrate_to_chat_id", None)
        if migrate_to_chat_id:
            return str(migrate_to_chat_id)
        match = re.search(
            r"migrated to a supergroup with id\s+(-?\d+)",
            str(error),
            flags=re.IGNORECASE,
        )
        return match.group(1) if match else None

    @staticmethod
    def _is_callback_query_expired_error(error: object) -> bool:
        text = str(error).lower()
        return (
            "query is too old" in text
            or "response timeout expired" in text
            or "query id is invalid" in text
        )

    @staticmethod
    def _is_message_not_modified_error(error: object) -> bool:
        text = str(error).lower()
        return "message is not modified" in text

    @staticmethod
    def _is_parse_entities_error(error: object) -> bool:
        text = str(error or "").lower()
        return (
            "can't parse entities" in text
            or "can't find end of the entity" in text
            or "unsupported start tag" in text
            or "parse entities" in text
        )

    @staticmethod
    def _telegram_retry_after_seconds(error: object) -> Optional[int]:
        if isinstance(error, TelegramRetryAfter):
            return max(int(error.retry_after), 1)
        retry_after = getattr(error, "retry_after", None)
        if retry_after is not None:
            try:
                return max(int(retry_after), 1)
            except Exception:
                pass
        match = re.search(
            r"retry(?:\s+in|\s+after)?\s+(\d+)",
            str(error or ""),
            flags=re.IGNORECASE,
        )
        return max(int(match.group(1)), 1) if match else None

    async def _wait_chat_send_turn(self, chat_id: str) -> None:
        self._require_redis()
        raw = await redis_client.get(self._chat_send_next_key(chat_id))
        if not raw:
            return
        try:
            send_after = float(raw)
        except Exception:
            return
        delay = send_after - time.time()
        if delay > 0:
            await asyncio.sleep(delay)

    async def _mark_chat_send_after(self, chat_id: str, delay_seconds: float) -> None:
        self._require_redis()
        delay = max(float(delay_seconds or 0), 0.0)
        if delay <= 0:
            return
        ttl = max(int(delay) + 60, 60)
        await redis_client.set(
            self._chat_send_next_key(chat_id),
            str(time.time() + delay),
            ex=ttl,
        )

    async def _send_message_once(
        self,
        *,
        chat_id: str,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup],
    ) -> Any:
        try:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup if reply_markup else None,
            )
        except Exception as error:
            if self._is_parse_entities_error(error):
                logger.warning(
                    "Telegram markdown send rejected, retrying as plain text: chat_id=%s error=%s",
                    chat_id,
                    error,
                )
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=None,
                    reply_markup=reply_markup if reply_markup else None,
                )
            raise

    async def _edit_text_markdown_with_plain_fallback(
        self,
        message: Any,
        *,
        text: str,
    ) -> None:
        try:
            await message.edit_text(text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as error:
            if self._is_parse_entities_error(error):
                logger.warning(
                    "Telegram markdown edit rejected, retrying as plain text: %s",
                    error,
                )
                await message.edit_text(text=text, parse_mode=None)
                return
            raise

    async def _send_message_markdown_with_plain_fallback(
        self,
        *,
        chat_id: str,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Any:
        self._require_redis()
        lock_key = self._chat_send_lock_key(chat_id)
        lock_token = await self._acquire_redis_lock(
            lock_key,
            TelegramBotConfig.SEND_LOCK_TTL,
            wait_seconds=TelegramBotConfig.SEND_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            raise TimeoutError(f"Timed out waiting for Telegram send lock: chat_id={chat_id}")
        try:
            last_error: Optional[Exception] = None
            for attempt in range(TelegramBotConfig.FLOOD_RETRY_ATTEMPTS):
                await self._wait_chat_send_turn(chat_id)
                try:
                    result = await self._send_message_once(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                    )
                    await self._mark_chat_send_after(
                        chat_id,
                        TelegramBotConfig.CHAT_MIN_INTERVAL_SEC,
                    )
                    return result
                except Exception as error:
                    retry_after = self._telegram_retry_after_seconds(error)
                    if retry_after is None:
                        raise
                    last_error = error
                    delay = retry_after + TelegramBotConfig.FLOOD_EXTRA_DELAY_SEC
                    await self._mark_chat_send_after(chat_id, delay)
                    logger.warning(
                        "Telegram flood control: chat_id=%s retry_after=%s attempt=%s/%s",
                        chat_id,
                        retry_after,
                        attempt + 1,
                        TelegramBotConfig.FLOOD_RETRY_ATTEMPTS,
                    )
            if last_error:
                raise last_error
            raise RuntimeError(f"Telegram message was not sent: chat_id={chat_id}")
        finally:
            await self._release_redis_lock(lock_key, lock_token)

    async def _answer_callback_query(
        self,
        callback_query: types.CallbackQuery,
        *args,
        **kwargs,
    ) -> bool:
        try:
            await callback_query.answer(*args, **kwargs)
            return True
        except TelegramBadRequest as error:
            if self._is_callback_query_expired_error(error):
                logger.info("Ignoring stale callback query answer: %s", error)
            else:
                logger.warning("Failed to answer callback query: %s", error)
            return False
        except Exception as error:
            logger.warning("Failed to answer callback query: %s", error)
            return False

    async def _cleanup_failed_subscriber(self, chat_id: str, error: object) -> Optional[str]:
        reason = self._subscriber_removal_reason(error)
        if not reason:
            return None
        try:
            await self._remove_subscriber(str(chat_id))
            logger.info("Removed subscriber %s because %s", chat_id, reason)
        except Exception as remove_error:
            logger.warning(
                "Failed to remove subscriber %s: %s", chat_id, remove_error
            )
        return reason

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _polling_key(self) -> str:
        return f"{TelegramBotConfig.INTEGRATION_KEY}:{self.connected_integration_id or 'unknown'}"

    @staticmethod
    def _resolve_webhook_base_url() -> str:
        base_url = str(settings.proxy_integration_url or settings.integration_url).strip()
        if not base_url:
            base_url = str(settings.integration_url).strip()
        return f"{base_url.rstrip('/')}/external"

    def _build_webhook_url(self) -> str:
        return f"{self._resolve_webhook_base_url()}/{self.connected_integration_id}/external/"

    def _webhook_refresh_cache_key(self) -> str:
        return self._redis_key("wh", self.connected_integration_id)

    def _webhook_refresh_lock_key(self) -> str:
        return self._redis_key("whl", self.connected_integration_id)

    def _settings_cache_key(self) -> str:
        return self._redis_key("st", self.connected_integration_id)

    def _settings_stale_cache_key(self) -> str:
        return self._redis_key("st", self.connected_integration_id, "s")

    def _settings_fetch_lock_key(self) -> str:
        return self._redis_key("stl", self.connected_integration_id)

    def _subscriber_update_lock_key(self) -> str:
        return self._redis_key("sub", self.connected_integration_id, "l")

    def _invalid_bot_token_cache_key(self, bot_token: str) -> str:
        return self._redis_key("bt", self.connected_integration_id, self._token_fingerprint(bot_token))

    def _telegram_send_identity(self) -> str:
        return self._bot_token_fingerprint or str(self.connected_integration_id or "").strip()

    def _chat_send_key(self, chat_id: str, suffix: str) -> str:
        chat_hash = hashlib.sha256(str(chat_id or "").encode("utf-8")).hexdigest()[:16]
        return self._redis_key("snd", suffix, self._telegram_send_identity(), chat_hash)

    def _chat_send_lock_key(self, chat_id: str) -> str:
        return self._chat_send_key(chat_id, "l")

    def _chat_send_next_key(self, chat_id: str) -> str:
        return self._chat_send_key(chat_id, "n")

    @staticmethod
    def _redis_enabled() -> bool:
        return bool(settings.redis_enabled and redis_client)

    @classmethod
    def _require_redis(cls) -> None:
        if not cls._redis_enabled():
            raise RuntimeError("Redis is required for telegram_bot_notification")

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        if not tokens:
            return TelegramBotConfig.REDIS_PREFIX
        return f"{TelegramBotConfig.REDIS_PREFIX}:{':'.join(tokens)}"

    @staticmethod
    def _token_fingerprint(token: str) -> str:
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _kind_code(kind: str) -> str:
        return {
            "telegram_update": "u",
            "crm_notification": "n",
            "send_messages": "s",
        }.get(kind, "x")

    @classmethod
    def _updates_stream_key(cls) -> str:
        return cls._redis_key("s", "u")

    @classmethod
    def _notifications_stream_key(cls) -> str:
        return cls._redis_key("s", "n")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._redis_key("s", "dlq")

    @classmethod
    def _stream_key_for_kind(cls, kind: str) -> str:
        if kind == "telegram_update":
            return cls._updates_stream_key()
        return cls._notifications_stream_key()

    @classmethod
    def _worker_task_key(cls, stream_key: str, worker_index: int = 0) -> str:
        return f"{str(stream_key or '').strip()}:{int(worker_index)}"

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
    def _misconfiguration_log_key(
        cls,
        connected_integration_id: str,
        kind: str,
        error_text: str,
    ) -> str:
        error_hash = hashlib.sha256(str(error_text or "").encode("utf-8")).hexdigest()[:16]
        return cls._redis_key("cfg", cls._kind_code(kind), connected_integration_id, error_hash)

    @classmethod
    async def _redis_delete(cls, *keys: str) -> None:
        cls._require_redis()
        valid = [str(key).strip() for key in keys if str(key or "").strip()]
        if valid:
            await redis_client.delete(*valid)

    @classmethod
    async def _redis_set_nx(cls, key: str, value: str, ttl_sec: int) -> bool:
        cls._require_redis()
        inserted = await redis_client.set(key, value, ex=max(int(ttl_sec or 1), 1), nx=True)
        return bool(inserted)

    @classmethod
    def _resolve_stream_ttl(cls) -> int:
        return redis_ttl_seconds(TelegramBotConfig.STREAM_TTL_SEC)

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
            TelegramBotConfig.STREAM_GROUP,
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
        serialized = cls._serialize_stream_fields(fields)
        await redis_stream_add_with_ttl(
            stream_key,
            serialized,
            maxlen=TelegramBotConfig.STREAM_MAXLEN,
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
        serialized = cls._serialize_stream_fields(fields)
        field_args: List[str] = []
        for key, value in serialized.items():
            field_args.extend([key, value])
        result = await redis_client.eval(
            _ENQUEUE_DEDUPE_LUA,
            2,
            dedupe_key,
            stream_key,
            str(TelegramBotConfig.DEDUPE_TTL_SEC),
            str(TelegramBotConfig.STREAM_MAXLEN),
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
        if kind not in {"telegram_update", "crm_notification", "send_messages"}:
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
            if not await cls._enqueue_stream_deduped(
                stream_key=stream_key,
                dedupe_key=dedupe_key,
                fields=fields,
            ):
                logger.info(
                    "Telegram notification duplicate not enqueued: ci=%s kind=%s event_id=%s",
                    ci,
                    kind,
                    event_id,
                )
                return False
            return True

        await cls._enqueue_stream(stream_key, fields)
        return True

    @classmethod
    def _stream_worker_specs(cls) -> List[Tuple[str, int]]:
        return [
            (stream_key, index)
            for stream_key in (cls._updates_stream_key(), cls._notifications_stream_key())
            for index in range(TelegramBotConfig.STREAM_WORKERS_PER_STREAM)
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
            if isinstance(runtime, TelegramBotNotificationIntegration):
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
                    name=f"tbn_stream_{cls._kind_code('telegram_update' if stream_key == cls._updates_stream_key() else 'crm_notification')}_{index}",
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
                logger.exception("Error while stopping Telegram notification stream worker")
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

    @staticmethod
    def _is_non_retryable_configuration_error(error_text: str) -> bool:
        text = str(error_text or "").strip().lower()
        return any(
            marker in text
            for marker in (
                "no bot token in settings",
                "bot token not found",
                "token is invalid",
                "settings retrieval error: token is invalid",
            )
        )

    @classmethod
    async def _log_non_retryable_configuration_skip(
        cls,
        *,
        connected_integration_id: str,
        kind: str,
        entry_id: str,
        error_text: str,
    ) -> None:
        should_log = await cls._redis_set_nx(
            cls._misconfiguration_log_key(connected_integration_id, kind, error_text),
            str(_now_ts()),
            TelegramBotConfig.MISCONFIG_LOG_TTL,
        )
        if should_log:
            logger.warning(
                "Telegram notification stream job skipped due to integration configuration: ci=%s kind=%s entry_id=%s error=%s",
                connected_integration_id,
                kind,
                entry_id,
                error_text,
            )

    @classmethod
    async def _ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_client.xack(stream_key, TelegramBotConfig.STREAM_GROUP, entry_id)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_client.xautoclaim(
                stream_key,
                TelegramBotConfig.STREAM_GROUP,
                consumer,
                min_idle_time=TelegramBotConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=TelegramBotConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            logger.warning("Telegram notification stream xautoclaim failed: stream=%s error=%s", stream_key, error)
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
        logger.info("Telegram notification stream worker started: stream=%s", stream_key)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._touch_stream_ttl(stream_key)
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= TelegramBotConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        for entry_id, fields in await cls._process_claimed_entries(stream_key, consumer):
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                entry_id=entry_id,
                                fields=fields,
                            )

                    try:
                        records = await redis_client.xreadgroup(
                            groupname=TelegramBotConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=TelegramBotConfig.STREAM_BATCH_SIZE,
                            block=TelegramBotConfig.STREAM_READ_BLOCK_MS,
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
                    logger.exception("Telegram notification stream worker error: stream=%s error=%s", stream_key, error)
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
        if not ci or kind not in {"telegram_update", "crm_notification", "send_messages"}:
            logger.warning("Telegram notification stream entry has invalid payload: entry_id=%s fields=%s", entry_id, fields)
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        attempt = cls._stream_entry_attempt(fields)
        worker = cls()
        worker.connected_integration_id = ci
        try:
            if kind == "telegram_update":
                if not isinstance(payload, dict):
                    raise ValueError("Telegram update payload must be an object")
                result = await worker._process_telegram_update(payload)
            elif kind == "crm_notification":
                if not isinstance(payload, dict):
                    raise ValueError("CRM notification payload must be an object")
                result = await worker._process_notification_webhook(action=action, data=payload)
            else:
                messages = payload.get("messages") if isinstance(payload, dict) else payload
                if not isinstance(messages, list):
                    raise ValueError("send_messages payload must contain messages list")
                result = await worker._send_messages_now(messages)

            if cls._is_error_result(result):
                error_text = cls._result_error_text(result)
                if cls._is_non_retryable_configuration_error(error_text):
                    await cls._log_non_retryable_configuration_skip(
                        connected_integration_id=ci,
                        kind=kind,
                        entry_id=entry_id,
                        error_text=error_text,
                    )
                    await cls._ack_stream_entry(stream_key, entry_id)
                    return
                raise RuntimeError(error_text)

            logger.debug(
                "Telegram notification stream job processed: ci=%s kind=%s entry_id=%s status=%s",
                ci,
                kind,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            if cls._is_non_retryable_configuration_error(str(error)):
                await cls._log_non_retryable_configuration_skip(
                    connected_integration_id=ci,
                    kind=kind,
                    entry_id=entry_id,
                    error_text=str(error),
                )
                await cls._ack_stream_entry(stream_key, entry_id)
                return
            next_attempt = attempt + 1
            if next_attempt >= TelegramBotConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(_now_ts())
                dlq_payload["error"] = str(error)
                await cls._enqueue_stream(cls._dlq_stream_key(), dlq_payload)
                if event_id and kind != "send_messages":
                    await cls._redis_delete(cls._dedupe_key(ci, kind, event_id))
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "Telegram notification stream job moved to DLQ: ci=%s kind=%s entry_id=%s error=%s",
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
                "Telegram notification stream job requeued: ci=%s kind=%s entry_id=%s attempt=%s error=%s",
                ci,
                kind,
                entry_id,
                next_attempt,
                error,
            )
        finally:
            await worker.__aexit__(None, None, None)

    @staticmethod
    async def _acquire_redis_lock(
        key: str,
        ttl_sec: int,
        *,
        wait_seconds: float = 0.0,
    ) -> Optional[str]:
        TelegramBotNotificationIntegration._require_redis()
        token = uuid.uuid4().hex
        deadline = asyncio.get_running_loop().time() + max(float(wait_seconds or 0.0), 0.0)
        while True:
            try:
                ok = await redis_client.set(key, token, ex=max(int(ttl_sec), 1), nx=True)
                if ok:
                    return token
            except Exception as error:
                logger.error("Failed to acquire Redis lock %s: %s", key, error)
                raise
            if asyncio.get_running_loop().time() >= deadline:
                return None
            await asyncio.sleep(0.05)

    @staticmethod
    async def _release_redis_lock(key: str, token: Optional[str]) -> None:
        if not (TelegramBotNotificationIntegration._redis_enabled() and token):
            return
        script = (
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end"
        )
        try:
            await redis_client.eval(script, 1, key, token)
        except Exception as error:
            logger.warning("Failed to release Redis lock %s: %s", key, error)

    @staticmethod
    def _normalize_settings_map(raw: Dict) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in (raw or {}).items():
            normalized_key = str(key or "").strip().lower()
            if normalized_key:
                normalized[normalized_key] = str(value or "").strip()
        return normalized

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
        if len(_SETTINGS_LOCAL_CACHE) >= TelegramBotConfig.SETTINGS_LOCAL_MAX:
            for key, (expires_at, _) in list(_SETTINGS_LOCAL_CACHE.items()):
                if expires_at <= now_ts:
                    _SETTINGS_LOCAL_CACHE.pop(key, None)
            while len(_SETTINGS_LOCAL_CACHE) >= TelegramBotConfig.SETTINGS_LOCAL_MAX:
                _SETTINGS_LOCAL_CACHE.pop(next(iter(_SETTINGS_LOCAL_CACHE)), None)
        _SETTINGS_LOCAL_CACHE[cache_key] = (
            now_ts + TelegramBotConfig.SETTINGS_LOCAL_TTL,
            dict(settings_map),
        )

    async def _read_settings_cache(self, cache_key: str) -> Optional[Dict[str, str]]:
        local = self._read_local_settings_cache(cache_key)
        if local is not None:
            return local
        self._require_redis()
        try:
            cached_data = await redis_client.get(cache_key)
            if not cached_data:
                return None
            if isinstance(cached_data, (bytes, bytearray)):
                cached_data = cached_data.decode("utf-8")
            loaded = json.loads(cached_data)
            if isinstance(loaded, dict):
                logger.debug("Retrieved settings from Redis: %s", cache_key)
                normalized = self._normalize_settings_map(loaded)
                self._write_local_settings_cache(cache_key, normalized)
                return normalized
        except Exception as error:
            logger.warning("Redis settings cache read failed for %s: %s", cache_key, error)
        return None

    async def _write_settings_cache(self, cache_key: str, settings_map: Dict[str, str]) -> None:
        self._require_redis()
        normalized = self._normalize_settings_map(settings_map)
        payload = _json_dumps(normalized)
        self._write_local_settings_cache(cache_key, normalized)
        self._write_local_settings_cache(self._settings_stale_cache_key(), normalized)
        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.setex(cache_key, TelegramBotConfig.SETTINGS_TTL, payload)
                await pipe.setex(
                    self._settings_stale_cache_key(),
                    TelegramBotConfig.SETTINGS_STALE_TTL,
                    payload,
                )
                await pipe.execute()
        except Exception as error:
            logger.warning("Failed to cache settings: %s", error)

    async def _clear_settings_cache(self, cache_key: Optional[str] = None) -> None:
        self._require_redis()
        keys = [
            cache_key or self._settings_cache_key(),
            self._settings_stale_cache_key(),
        ]
        for key in keys:
            if key:
                _SETTINGS_LOCAL_CACHE.pop(key, None)
        try:
            await redis_client.delete(*[key for key in keys if key])
        except Exception as error:
            logger.warning("Failed to clear settings cache: %s", error)

    async def _touch_webhook_refresh_cache(self) -> None:
        if not (self._redis_enabled() and self.connected_integration_id):
            return
        _WEBHOOK_LOCAL_CACHE[self._webhook_refresh_cache_key()] = (
            _now_ts() + TelegramBotConfig.WEBHOOK_LOCAL_TTL
        )
        try:
            await redis_client.setex(
                self._webhook_refresh_cache_key(),
                TelegramBotConfig.WEBHOOK_REFRESH_TTL,
                "1",
            )
        except Exception as error:
            logger.warning("Failed to update webhook refresh cache: %s", error)

    async def _clear_webhook_refresh_cache(self) -> None:
        if not (self._redis_enabled() and self.connected_integration_id):
            return
        _WEBHOOK_LOCAL_CACHE.pop(self._webhook_refresh_cache_key(), None)
        try:
            await redis_client.delete(self._webhook_refresh_cache_key())
        except Exception as error:
            logger.warning("Failed to clear webhook refresh cache: %s", error)

    async def _ensure_webhook_from_regos(self, *, force: bool = False) -> None:
        if self._is_longpolling_mode() or not self.bot or not self.connected_integration_id:
            return

        cache_key = self._webhook_refresh_cache_key()
        if not force and int(_WEBHOOK_LOCAL_CACHE.get(cache_key) or 0) > _now_ts():
            return
        if self._redis_enabled() and not force:
            try:
                if await redis_client.exists(cache_key):
                    _WEBHOOK_LOCAL_CACHE[cache_key] = (
                        _now_ts() + TelegramBotConfig.WEBHOOK_LOCAL_TTL
                    )
                    return
            except Exception as error:
                logger.warning("Failed to read webhook refresh cache: %s", error)

        lock_token: Optional[str] = None
        if self._redis_enabled():
            lock_token = await self._acquire_redis_lock(
                self._webhook_refresh_lock_key(),
                TelegramBotConfig.WEBHOOK_LOCK_TTL,
                wait_seconds=TelegramBotConfig.SETTINGS_LOCK_WAIT_SECONDS if force else 0.0,
            )
            if not lock_token:
                logger.debug(
                    "Skipping webhook refresh for ID %s: another instance is refreshing it",
                    self.connected_integration_id,
                )
                return

        try:
            if self._redis_enabled() and not force:
                try:
                    if await redis_client.exists(cache_key):
                        _WEBHOOK_LOCAL_CACHE[cache_key] = (
                            _now_ts() + TelegramBotConfig.WEBHOOK_LOCAL_TTL
                        )
                        return
                except Exception as error:
                    logger.warning("Failed to re-read webhook refresh cache: %s", error)

            webhook_url = self._build_webhook_url()
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
            await self._release_redis_lock(
                self._webhook_refresh_lock_key(),
                lock_token,
            )
    
    async def _fetch_settings_from_api(self) -> Dict[str, str]:
        logger.debug("Fetching settings from API for ID %s", self.connected_integration_id)
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
        return self._normalize_settings_map(
            {
                item.key: item.value
                for item in (settings_response or [])
                if getattr(item, "key", None)
            }
        )

    async def _fetch_settings(self, cache_key: str, *, force_refresh: bool = False) -> Optional[Dict[str, str]]:
        """Retrieve settings from Redis cache or API."""
        if not self.connected_integration_id:
            raise ValueError("No connected_integration_id specified")
        self._require_redis()

        if not force_refresh:
            cached = await self._read_settings_cache(cache_key)
            if cached is not None:
                return cached

        lock_key = self._settings_fetch_lock_key()
        lock_token = await self._acquire_redis_lock(
            lock_key,
            TelegramBotConfig.SETTINGS_LOCK_TTL,
        )

        if lock_token:
            try:
                if not force_refresh:
                    cached = await self._read_settings_cache(cache_key)
                    if cached is not None:
                        return cached
                settings_map = await self._fetch_settings_from_api()
                await self._write_settings_cache(cache_key, settings_map)
                return settings_map
            except Exception as error:
                stale = await self._read_settings_cache(self._settings_stale_cache_key())
                if stale is not None:
                    logger.warning(
                        "Using stale Telegram settings for ID %s after API error: %s",
                        self.connected_integration_id,
                        error,
                    )
                    return stale
                logger.error(
                    "Error fetching settings for ID %s: %s",
                    self.connected_integration_id,
                    error,
                )
                raise
            finally:
                await self._release_redis_lock(lock_key, lock_token)

        deadline = asyncio.get_running_loop().time() + TelegramBotConfig.SETTINGS_LOCK_WAIT_SECONDS
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.05)
            cached = await self._read_settings_cache(cache_key)
            if cached is not None:
                return cached

        stale = await self._read_settings_cache(self._settings_stale_cache_key())
        if stale is not None:
            logger.warning(
                "Using stale Telegram settings for ID %s while another instance refreshes settings",
                self.connected_integration_id,
            )
            return stale

        raise TimeoutError(
            f"Timed out waiting for Telegram settings refresh for ID {self.connected_integration_id}"
        )

    async def _cache_current_settings(self, cache_key: str, settings_map: Dict[str, str]) -> None:
        await self._write_settings_cache(cache_key, self._normalize_settings_map(settings_map))

    async def _mark_invalid_bot_token(self, bot_token: str) -> None:
        if not self._redis_enabled():
            return
        try:
            await redis_client.setex(
                self._invalid_bot_token_cache_key(bot_token),
                TelegramBotConfig.INVALID_TOKEN_TTL,
                "1",
            )
        except Exception as error:
            logger.warning("Failed to cache invalid Telegram bot token marker: %s", error)

    async def _is_invalid_bot_token_cached(self, bot_token: str) -> bool:
        if not self._redis_enabled():
            return False
        try:
            return bool(await redis_client.exists(self._invalid_bot_token_cache_key(bot_token)))
        except Exception as error:
            logger.warning("Failed to read invalid Telegram bot token marker: %s", error)
            return False

    async def _with_subscriber_lock(self) -> Optional[str]:
        lock_token = await self._acquire_redis_lock(
            self._subscriber_update_lock_key(),
            TelegramBotConfig.SUBSCRIBER_LOCK_TTL,
            wait_seconds=TelegramBotConfig.SETTINGS_LOCK_WAIT_SECONDS,
        )
        if not lock_token:
            raise TimeoutError(
                f"Timed out waiting for Telegram subscriber settings lock for ID {self.connected_integration_id}"
            )
        return lock_token

    async def _add_subscriber(self, chat_id: str) -> None:
        """Add a chat ID to the subscribers list."""
        cache_key = self._settings_cache_key()
        lock_token: Optional[str] = None
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            if chat_id in parse_chat_ids(raw_chat_ids):
                return

            lock_token = await self._with_subscriber_lock()
            settings_map = await self._fetch_settings(cache_key, force_refresh=True) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id not in subscribers:
                subscribers.append(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = await api.integrations.connected_integration_setting.edit(
                        [
                            ConnectedIntegrationSettingEditItem(
                                key=TelegramSettings.CHAT_IDS.value,
                                value=_json_dumps(subscribers),
                                connected_integration_id=self.connected_integration_id,
                            )
                        ]
                    )
                success = getattr(edit_resp, "ok", None)
                if success is None:
                    success = bool(getattr(edit_resp, "result", edit_resp))
                if not success:
                    logger.error(
                        "Settings update failed (add): ok=%s result=%s",
                        getattr(edit_resp, "ok", None),
                        getattr(edit_resp, "result", None),
                    )
                    raise RuntimeError("Failed to update settings")
                settings_map[TelegramSettings.CHAT_IDS.value.lower()] = _json_dumps(subscribers)
                await self._cache_current_settings(cache_key, settings_map)
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
        cache_key = self._settings_cache_key()
        lock_token: Optional[str] = None
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            if chat_id not in parse_chat_ids(raw_chat_ids):
                return

            lock_token = await self._with_subscriber_lock()
            settings_map = await self._fetch_settings(cache_key, force_refresh=True) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id in subscribers:
                subscribers.remove(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = await api.integrations.connected_integration_setting.edit(
                        [
                            ConnectedIntegrationSettingEditItem(
                                key=TelegramSettings.CHAT_IDS.value,
                                value=_json_dumps(subscribers),
                                connected_integration_id=self.connected_integration_id,
                            )
                        ]
                    )
                success = getattr(edit_resp, "ok", None)
                if success is None:
                    success = bool(getattr(edit_resp, "result", edit_resp))
                if not success:
                    logger.error(
                        "Settings update failed (remove): ok=%s result=%s",
                        getattr(edit_resp, "ok", None),
                        getattr(edit_resp, "result", None),
                    )
                    raise RuntimeError("Failed to update settings")
                settings_map[TelegramSettings.CHAT_IDS.value.lower()] = _json_dumps(subscribers)
                await self._cache_current_settings(cache_key, settings_map)
                logger.info(
                    f"Removed subscriber {chat_id} for ID {self.connected_integration_id}"
                )
        except Exception as error:
            logger.error(f"Error removing subscriber {chat_id}: {error}")
            raise
        finally:
            await self._release_redis_lock(self._subscriber_update_lock_key(), lock_token)

    async def _replace_subscriber(self, old_chat_id: str, new_chat_id: str) -> bool:
        """Replace a migrated Telegram chat ID in settings."""
        old_chat_id = str(old_chat_id or "").strip()
        new_chat_id = str(new_chat_id or "").strip()
        if not old_chat_id or not new_chat_id or old_chat_id == new_chat_id:
            return False

        cache_key = self._settings_cache_key()
        lock_token: Optional[str] = None
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            if old_chat_id not in parse_chat_ids(raw_chat_ids):
                return False

            lock_token = await self._with_subscriber_lock()
            settings_map = await self._fetch_settings(cache_key, force_refresh=True) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)
            if old_chat_id not in subscribers:
                return False

            updated: List[str] = []
            for subscriber in subscribers:
                candidate = new_chat_id if subscriber == old_chat_id else subscriber
                if candidate not in updated:
                    updated.append(candidate)

            async with RegosAPI(
                connected_integration_id=self.connected_integration_id
            ) as api:
                edit_resp = await api.integrations.connected_integration_setting.edit(
                    [
                        ConnectedIntegrationSettingEditItem(
                            key=TelegramSettings.CHAT_IDS.value,
                            value=_json_dumps(updated),
                            connected_integration_id=self.connected_integration_id,
                        )
                    ]
                )
            success = getattr(edit_resp, "ok", None)
            if success is None:
                success = bool(getattr(edit_resp, "result", edit_resp))
            if not success:
                logger.error(
                    "Settings update failed (replace): ok=%s result=%s",
                    getattr(edit_resp, "ok", None),
                    getattr(edit_resp, "result", None),
                )
                raise RuntimeError("Failed to update settings")
            settings_map[TelegramSettings.CHAT_IDS.value.lower()] = _json_dumps(updated)
            await self._cache_current_settings(cache_key, settings_map)
            logger.info(
                "Replaced Telegram subscriber %s with %s for ID %s",
                old_chat_id,
                new_chat_id,
                self.connected_integration_id,
            )
            return True
        finally:
            await self._release_redis_lock(self._subscriber_update_lock_key(), lock_token)

    async def _initialize_bot(self, settings_map: Optional[Dict[str, str]] = None) -> None:
        """Initialize the Telegram bot if not already done."""
        if self.bot:
            return
        ci = str(self.connected_integration_id or "").strip()
        if not ci:
            raise ValueError("No connected_integration_id specified")
        if settings_map is None:
            settings_map = await self._fetch_settings(
                self._settings_cache_key()
            )
        bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
        if not bot_token:
            raise ValueError(
                f"Bot token not found for ID {self.connected_integration_id}"
            )
        if await self._is_invalid_bot_token_cached(bot_token):
            raise ValueError("Token is invalid!")
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
                if "token is invalid" in str(error).lower():
                    await self._mark_invalid_bot_token(bot_token)
                raise
            self._bot_token_fingerprint = token_fingerprint
            await self._setup_handlers()
            self._owns_bot_session = False
            _BOT_RUNTIME_CACHE[ci] = (token_fingerprint, self)

    async def _setup_handlers(self) -> None:
        """Set up command and callback handlers for the bot."""
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        @self.dispatcher.message(Command("start"))
        async def handle_start_command(message: types.Message):
            """Handle /start command to subscribe to notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._add_subscriber(chat_id)
                await message.answer(
                    "You are now subscribed to cheque and session notifications!"
                )
                logger.info(
                    f"Client {chat_id} subscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error subscribing. Please try again later.")

        @self.dispatcher.message(Command("stop"))
        async def handle_stop_command(message: types.Message):
            """Handle /stop command to unsubscribe from notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._remove_subscriber(chat_id)
                await message.answer("You are now unsubscribed from notifications.")
                logger.info(
                    f"Client {chat_id} unsubscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error unsubscribing. Please try again later.")

        @self.dispatcher.callback_query(lambda c: c.data.startswith("cdetails_"))
        async def handle_cheque_details(callback_query: types.CallbackQuery):
            try:
                _, uuid, _ = callback_query.data.split("_", 2)
            except Exception:
                await self._answer_callback_query(
                    callback_query, "Некорректные данные кнопки", show_alert=False
                )
                return

            try:
                async with RegosAPI(self.connected_integration_id) as api:
                    # Приводим чек к DocCheque
                    raw_cheques = (await api.docs.cheque.get_by_uuids([uuid])).result or []
                    if not raw_cheques:
                        await self._answer_callback_query(
                            callback_query, "Чек не найден", show_alert=True
                        )
                        return
                    cheque = (
                        raw_cheques[0]
                        if isinstance(raw_cheques[0], DocCheque)
                        else DocCheque.model_validate(raw_cheques[0])
                    )

                    # Приводим операции к DocChequeOperation
                    operations_raw = (
                        await api.docs.cheque_operation.get(
                            DocChequeOperationGetRequest(doc_sale_uuid=uuid)
                        )
                    ).result or []
                    operations = [
                        op if isinstance(op, DocChequeOperation)
                        else DocChequeOperation.model_validate(op)
                        for op in operations_raw
                    ]

                    # Приводим оплаты к DocChequePayment
                    payments_raw = (
                        await api.docs.cheque_payment.get(
                            DocChequePaymentGetRequest(doc_sale_uuid=uuid)
                        )
                    ).result or []
                    payments = [
                        p if isinstance(p, DocChequePayment)
                        else DocChequePayment.model_validate(p)
                        for p in payments_raw
                    ]
            except Exception as error:
                logger.error(f"Error fetching cheque details {uuid}: {error}")
                await self._answer_callback_query(
                    callback_query, "Ошибка получения данных", show_alert=True
                )
                return

            message_text = format_cheque_details(
                cheque=cheque, operations=operations, payments=payments
            )

            try:
                await self._edit_text_markdown_with_plain_fallback(
                    callback_query.message,
                    text=message_text,
                )
            except Exception as error:
                if self._is_message_not_modified_error(error):
                    logger.info("Ignoring unchanged cheque details edit %s", uuid)
                    await self._answer_callback_query(callback_query)
                    return
                logger.error(f"Error editing cheque details {uuid}: {error}")
                await self._answer_callback_query(
                    callback_query,
                    "Не удалось обновить сообщение", show_alert=True
                )
                return
            await self._answer_callback_query(callback_query)

        @self.dispatcher.callback_query(lambda c: c.data.startswith("sdetails_"))
        async def handle_session_details(callback_query: types.CallbackQuery):
            try:
                _, uuid, _ = callback_query.data.split("_", 2)
            except Exception:
                await self._answer_callback_query(
                    callback_query, "Некорректные данные кнопки", show_alert=False
                )
                return

            try:
                async with RegosAPI(self.connected_integration_id) as api:
                    sessions_resp = await api.docs.cash_session.get_by_uuids([uuid])
                    sessions = sessions_resp.result or []
                    if not sessions:
                        await self._answer_callback_query(
                            callback_query, "Смена не найдена", show_alert=True
                        )
                        return

                    session = sessions[0]

            
                    operations_raw = (
                        await api.docs.cash_operation.get_amount_details(
                            CashAmountDetailsGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_id=session.operating_cash_id,
                            )
                        )
                    ).result

                    
                    if isinstance(operations_raw, list):
                        operations = [
                            op if isinstance(op, CashAmountDetails)
                            else CashAmountDetails.model_validate(op)
                            for op in operations_raw
                        ]
                    
                    elif isinstance(operations_raw, dict):
                        operations = CashAmountDetails.model_validate(operations_raw)
                    else:
                        operations = operations_raw  

                    counts = (
                        await api.reports.retail_report.get_counts(
                            CountsGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_ids=[session.operating_cash_id],
                            )
                        )
                    ).result or []

                    payments = (
                        await api.reports.retail_report.get_payments(
                            PaymentGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_ids=[session.operating_cash_id],
                            )
                        )
                    ).result or []

            except Exception as error:
                logger.error(f"Error fetching session details {uuid}: {error}")
                await self._answer_callback_query(
                    callback_query, "Ошибка получения данных", show_alert=True
                )
                return

            
            message_text = format_session_details(
                session=session, operations=operations, counts=counts, payments=payments
            )

            try:
                await self._edit_text_markdown_with_plain_fallback(
                    callback_query.message,
                    text=message_text,
                )
            except Exception as error:
                if self._is_message_not_modified_error(error):
                    logger.info("Ignoring unchanged session details edit %s", uuid)
                    await self._answer_callback_query(callback_query)
                    return
                logger.error(f"Error editing session details {uuid}: {error}")
                await self._answer_callback_query(
                    callback_query, "Не удалось обновить сообщение", show_alert=True
                )
                return
            await self._answer_callback_query(callback_query)

        self.handlers_registered = True

    @retry(
        stop=stop_after_attempt(TelegramBotConfig.RETRY_ATTEMPTS),
        wait=wait_fixed(TelegramBotConfig.RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=lambda retry_state: logger.debug(
            f"Retry attempt: {retry_state.attempt_number}"
        ),
    )
    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Connect to Telegram and set up the webhook."""
        logger.info(
            f"Connecting to TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
        )
        cache_key = self._settings_cache_key()
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
            await self._initialize_bot(settings_map)
            await self._setup_handlers()

            if self._is_longpolling_mode():
                await self.bot.delete_webhook(drop_pending_updates=True)
                await self._clear_webhook_refresh_cache()
                await telegram_polling_manager.start(
                    self._polling_key(), self.bot, self.dispatcher
                )
                logger.info("Webhook deleted (longpolling mode).")
                return {"status": "connected", "mode": "longpolling"}

            await telegram_polling_manager.stop(self._polling_key())
            webhook_url = self._build_webhook_url()
            await self._ensure_webhook_from_regos(force=True)
            await self._ensure_stream_workers()
            logger.info(f"Webhook set: {webhook_url}")
            return {"status": "connected", "mode": "webhook", "webhook_url": webhook_url}
        except (httpx.RequestError, httpx.HTTPStatusError) as error:
            logger.error(f"Connection error: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected connection error: {error}")
            return self._create_error_response(1003, f"Webhook setup failed: {error}")

    async def disconnect(self, **kwargs) -> Dict:
        """Disconnect from Telegram and remove the webhook."""
        logger.info(
            f"Disconnecting from TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
        )
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
            return self._create_error_response(1004, f"Webhook removal failed: {error}")

    async def reconnect(self, **kwargs) -> Dict:
        """Reconnect to Telegram by disconnecting and connecting again."""
        logger.info(
            f"Reconnecting to TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
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
        cache_key = self._settings_cache_key()
        await self._clear_settings_cache(cache_key)
        await self._clear_webhook_refresh_cache()
        await self._close_bot_runtime_cache(self.connected_integration_id)
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    @staticmethod
    def _normalize_notification_input(
        action: Optional[str],
        data: Optional[Dict],
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        if isinstance(data, dict) and "action" in data:
            return data.get("action"), data.get("data", {}) or {}
        return action, data or {}

    @staticmethod
    def _notification_event_id(action: Optional[str], payload: Dict[str, Any]) -> str:
        uuid_value = str(payload.get("uuid") or payload.get("session_uuid") or "").strip()
        if uuid_value:
            return f"{action or 'unknown'}:{uuid_value}"
        return hashlib.sha256(
            _json_dumps({"action": action, "data": payload}).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _telegram_update_event_id(payload: Dict[str, Any]) -> str:
        update_id = str(payload.get("update_id") or "").strip()
        if update_id:
            return update_id
        return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict:
        webhook_action, webhook_data = self._normalize_notification_input(action, data)
        if not webhook_action:
            return self._create_error_response(1006, "No action specified in webhook")
        if webhook_action not in {
            "DocSessionOpened",
            "DocSessionClosed",
            "DocChequeClosed",
            "DocChequeCanceled",
        }:
            return self._create_error_response(
                1006, f"Unsupported action: {webhook_action}"
            )
        uuid_value = webhook_data.get("uuid") or webhook_data.get("session_uuid")
        if not uuid_value:
            return self._create_error_response(
                1007, "Webhook missing uuid/session_uuid"
            )
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            )
        queued = await self._enqueue_event(
            self.connected_integration_id,
            kind="crm_notification",
            payload=webhook_data,
            action=webhook_action,
            event_id=self._notification_event_id(webhook_action, webhook_data),
        )
        return {
            "status": "accepted",
            "queued": 1 if queued else 0,
            "kind": "crm_notification",
            "action": webhook_action,
            "uuid": uuid_value,
            "duplicate": not queued,
        }

    async def _process_notification_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict:
        """Process incoming webhook requests from the API."""
        logger.debug("Processing notification webhook for ID %s", self.connected_integration_id)

        # Унификация входа: либо {action, data}, либо отдельные аргументы
        webhook_action, webhook_data = self._normalize_notification_input(action, data)

        if not webhook_action:
            return self._create_error_response(1006, "No action specified in webhook")

        supported_actions = {
            "DocSessionOpened",
            "DocSessionClosed",
            "DocChequeClosed",
            "DocChequeCanceled",
        }
        if webhook_action not in supported_actions:
            return self._create_error_response(
                1006, f"Unsupported action: {webhook_action}"
            )

        uuid = webhook_data.get("uuid") or webhook_data.get("session_uuid")
        if not uuid:
            return self._create_error_response(
                1007, "Webhook missing uuid/session_uuid"
            )

        # Получаем настройки интеграции
        cache_key = self._settings_cache_key()
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            # --- Фильтр по складам (STOCK_IDS) ---
            allowed_stock_ids = self._parse_stock_ids(settings_map)
            # None -> фильтра нет, шлём по всем складам

            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
            await self._initialize_bot(settings_map)
            await self._ensure_webhook_from_regos()
            if not subscribers:
                logger.warning(f"No subscribers for {webhook_action} (uuid={uuid})")
                return {"status": "ok", "message": "No subscribers"}

            # Отключение чеков на уровне настройки CHEQUE_NOTIFICATION
            if webhook_action in {"DocChequeClosed", "DocChequeCanceled"}:
                if not self._cheque_notifications_enabled(settings_map):
                    logger.info(
                        f"Cheque notifications disabled by settings "
                        f"(ID={self.connected_integration_id}, uuid={uuid})"
                    )
                    return {
                        "status": "ok",
                        "message": "Cheque notifications disabled by CHEQUE_NOTIFICATION setting",
                        "action": webhook_action,
                        "uuid": uuid,
                    }

        except Exception as error:
            if not self._is_non_retryable_configuration_error(str(error)):
                logger.error(f"Error fetching settings: {error}")
            return self._create_error_response(
                1001, f"Settings retrieval error: {error}"
            )

        message_text = ""
        keyboard: Optional[InlineKeyboardMarkup] = None

        try:
            # ---------------- ЧЕК ----------------
            if webhook_action in {"DocChequeClosed", "DocChequeCanceled"}:
                async with RegosAPI(self.connected_integration_id) as api:
                    from schemas.api.references.operating_cash import (
                        OperatingCashGetRequest,
                    )

                    cheques_resp = await api.docs.cheque.get_by_uuids([uuid])
                    raw_cheques = getattr(cheques_resp, "result", cheques_resp) or []

                    if not raw_cheques:
                        logger.warning(f"Cheque with UUID {uuid} not found")
                        message_text = (
                            f"*Event:* `{webhook_action}`\n"
                            f"UUID: `{uuid}`\n"
                            f"Details: Cheque not found"
                        )
                    else:
                        # Приводим к DocCheque
                        cheque = (
                            raw_cheques[0]
                            if isinstance(raw_cheques[0], DocCheque)
                            else DocCheque.model_validate(raw_cheques[0])
                        )

                        # --- Фильтрация по STOCK_IDS через смену и кассу ---
                        stock_id_for_filter: Optional[int] = None
                        if allowed_stock_ids:
                            session_uuid = cheque.session  # UUID кассовой сессии

                            try:
                                # 1. Получаем смену
                                sessions_resp = await api.docs.cash_session.get_by_uuids(
                                    [session_uuid]
                                )
                                sessions = getattr(
                                    sessions_resp, "result", sessions_resp
                                ) or []

                                if sessions:
                                    session = sessions[0]

                                    # 2. Получаем кассу (OperatingCash)
                                    oc_resp = await api.references.operating_cash.get(
                                        OperatingCashGetRequest(
                                            ids=[session.operating_cash_id]
                                        )
                                    )
                                    oc_list = getattr(
                                        oc_resp, "result", oc_resp
                                    ) or []
                                    if oc_list:
                                        operating_cash = oc_list[0]
                                        stock = getattr(operating_cash, "stock", None)
                                        stock_id_for_filter = getattr(stock, "id", None)

                            except Exception as error:
                                logger.error(
                                    "Error fetching session/operating cash for cheque %s: %s",
                                    uuid,
                                    error,
                                )

                            # Если склад определён и не входит в список разрешённых — пропускаем вебхук
                            if (
                                stock_id_for_filter is not None
                                and stock_id_for_filter not in allowed_stock_ids
                            ):
                                logger.info(
                                    "Skipping cheque webhook %s due to STOCK_IDS filter "
                                    "(stock_id=%s, allowed=%s)",
                                    uuid,
                                    stock_id_for_filter,
                                    allowed_stock_ids,
                                )
                                return {
                                    "status": "ok",
                                    "message": "Cheque filtered by STOCK_IDS",
                                    "action": webhook_action,
                                    "uuid": uuid,
                                    "stock_id": stock_id_for_filter,
                                }

                        # Если фильтр не сработал / не задан — формируем уведомление как раньше
                        message_text = format_cheque_notification(
                            cheque=cheque, action=webhook_action
                        )
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="Детали чека",
                                        callback_data=f"cdetails_{uuid}_{webhook_action}",
                                    )
                                ]
                            ]
                        )

            # ---------------- СМЕНА ----------------
            elif webhook_action in {"DocSessionOpened", "DocSessionClosed"}:
                async with RegosAPI(self.connected_integration_id) as api:
                    from schemas.api.references.operating_cash import (
                        OperatingCashGetRequest,
                    )

                    sessions_resp = await api.docs.cash_session.get_by_uuids([uuid])
                    sessions = getattr(sessions_resp, "result", sessions_resp) or []

                    if not sessions:
                        logger.warning(f"Session with UUID {uuid} not found")
                        message_text = (
                            f"*Event:* `{webhook_action}`\n"
                            f"UUID: `{uuid}`\n"
                            f"Details: Session not found"
                        )
                    else:
                        session = sessions[0]

                        # --- Фильтр по STOCK_IDS через кассу ---
                        stock_id_for_filter: Optional[int] = None
                        if allowed_stock_ids:
                            try:
                                oc_resp = await api.references.operating_cash.get(
                                    OperatingCashGetRequest(
                                        ids=[session.operating_cash_id]
                                    )
                                )
                                oc_list = getattr(oc_resp, "result", oc_resp) or []
                                if oc_list:
                                    operating_cash = oc_list[0]
                                    stock = getattr(operating_cash, "stock", None)
                                    stock_id_for_filter = getattr(stock, "id", None)
                            except Exception as error:
                                logger.error(
                                    "Error fetching operating cash for session %s: %s",
                                    uuid,
                                    error,
                                )

                            if (
                                stock_id_for_filter is not None
                                and stock_id_for_filter not in allowed_stock_ids
                            ):
                                logger.info(
                                    "Skipping session webhook %s due to STOCK_IDS filter "
                                    "(stock_id=%s, allowed=%s)",
                                    uuid,
                                    stock_id_for_filter,
                                    allowed_stock_ids,
                                )
                                return {
                                    "status": "ok",
                                    "message": "Session filtered by STOCK_IDS",
                                    "action": webhook_action,
                                    "uuid": uuid,
                                    "stock_id": stock_id_for_filter,
                                }

                        # Формируем уведомление как раньше
                        message_text = format_session_notification(
                            session=session, action=webhook_action
                        )
                        if getattr(session, "closed", False):
                            keyboard = InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(
                                            text="Детали смены",
                                            callback_data=f"sdetails_{uuid}_{webhook_action}",
                                        )
                                    ]
                                ]
                            )

            else:
                # На всякий случай fallback (хотя все поддерживаемые action уже перечислены)
                message_text = "Webhook action not supported for notifications"

        except Exception as error:
            logger.error(f"Error formatting message: {error}")
            message_text = (
                f"*Event:* `{webhook_action}`\n"
                f"UUID: `{uuid}`\n"
                f"Details unavailable: `{str(error)}`"
            )

        # Рассылка сообщений подписчикам
        semaphore = asyncio.Semaphore(TelegramBotConfig.SEND_CONCURRENCY)

        async def send_to_subscriber(chat_id: str) -> Dict:
            async with semaphore:
                return await self._send_notification_to_subscriber(
                    chat_id=str(chat_id),
                    message_text=message_text,
                    keyboard=keyboard,
                )

        results = await asyncio.gather(
            *(send_to_subscriber(str(chat_id)) for chat_id in subscribers)
        )

        return {
            "status": "webhook processed",
            "action": webhook_action,
            "uuid": uuid,
            "sent_to": sum(1 for item in results if item.get("status") == "sent"),
            "details": results,
        }


    async def _send_notification_to_subscriber(
        self,
        *,
        chat_id: str,
        message_text: str,
        keyboard: Optional[InlineKeyboardMarkup],
    ) -> Dict:
        try:
            await self._send_message_markdown_with_plain_fallback(
                chat_id=chat_id,
                text=message_text,
                reply_markup=keyboard if keyboard else None,
            )
            return {"status": "sent", "chat_id": chat_id}
        except Exception as error:
            logger.error("Error sending message to chat %s: %s", chat_id, error)
            migrated_to = self._migrate_to_chat_id(error)
            if migrated_to:
                try:
                    await self._replace_subscriber(str(chat_id), migrated_to)
                except Exception as replace_error:
                    logger.warning(
                        "Failed to replace migrated subscriber %s -> %s: %s",
                        chat_id,
                        migrated_to,
                        replace_error,
                    )
                try:
                    await self._send_message_markdown_with_plain_fallback(
                        chat_id=migrated_to,
                        text=message_text,
                        reply_markup=keyboard if keyboard else None,
                    )
                    return {
                        "status": "sent",
                        "chat_id": migrated_to,
                        "migrated_from": str(chat_id),
                    }
                except Exception as retry_error:
                    logger.error(
                        "Error sending message to migrated chat %s from %s: %s",
                        migrated_to,
                        chat_id,
                        retry_error,
                    )
                    error = retry_error
                    chat_id = migrated_to

            await self._cleanup_failed_subscriber(str(chat_id), error)
            return {"status": "error", "chat_id": chat_id, "error": str(error)}


    async def send_messages(self, messages: List[Dict]) -> Dict:
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
            "duplicate": not queued,
        }

    async def _send_messages_now(self, messages: List[Dict]) -> Dict:
        """Send multiple messages to Telegram in batches."""
        logger.debug("Starting message send for ID %s", self.connected_integration_id)
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

        # Fetch bot token
        cache_key = self._settings_cache_key()
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
        except Exception as error:
            return self._create_error_response(
                1001, f"Settings retrieval error: {error}"
            )

        # Initialize bot and handlers
        await self._initialize_bot(settings_map)
        await self._setup_handlers()

        async def send_one(message: Dict) -> Dict:
            chat_id = str(message["recipient"])
            text = str(message["message"])
            try:
                await self._send_message_markdown_with_plain_fallback(
                    chat_id=chat_id,
                    text=text,
                )
                logger.debug("Sent Telegram message to chat %s", chat_id)
                return {"status": "sent", "chat_id": chat_id, "message": text}
            except Exception as error:
                logger.error("Telegram send error for chat %s: %s", chat_id, error)
                result = {
                    "status": "error",
                    "chat_id": chat_id,
                    "message": text,
                    "error": str(error),
                }
                migrated_to = self._migrate_to_chat_id(error)
                if migrated_to:
                    result["migrate_to_chat_id"] = str(migrated_to)
                return result

        semaphore = asyncio.Semaphore(TelegramBotConfig.SEND_CONCURRENCY)

        async def guarded_send(message: Dict) -> Dict:
            async with semaphore:
                return await send_one(message)

        results = []
        for i in range(0, len(messages), TelegramBotConfig.BATCH_SIZE):
            batch = messages[i : i + TelegramBotConfig.BATCH_SIZE]
            logger.debug(f"Sending batch {i}-{i + len(batch)}")
            try:
                details = await asyncio.gather(
                    *(guarded_send(message) for message in batch)
                )
                results.append(
                    {
                        "sent_messages": sum(
                            1 for item in details if item.get("status") == "sent"
                        ),
                        "details": details,
                    }
                )
            except Exception as error:
                logger.error(f"Error sending batch {i}: {error}")
                results.append({"error": str(error), "batch_index": i})

        for batch_result in results:
            details = batch_result.get("details") if isinstance(batch_result, dict) else None
            if not details:
                continue
            for detail in details:
                if not isinstance(detail, dict) or detail.get("status") != "error":
                    continue
                error_text = detail.get("error", "")
                chat_id = detail.get("chat_id")
                if not chat_id:
                    continue
                migrated_to = detail.get("migrate_to_chat_id") or self._migrate_to_chat_id(
                    error_text
                )
                if migrated_to:
                    try:
                        replaced = await self._replace_subscriber(
                            str(chat_id), str(migrated_to)
                        )
                        if replaced:
                            detail["migrated_to_chat_id"] = str(migrated_to)
                    except Exception as replace_error:
                        logger.warning(
                            "Failed to replace migrated subscriber %s -> %s: %s",
                            chat_id,
                            migrated_to,
                            replace_error,
                        )
                    continue
                await self._cleanup_failed_subscriber(str(chat_id), error_text)

        logger.debug("Message sending completed. Processed %s batches", len(results))
        return {"sent_batches": len(results), "details": results}

    async def handle_external(self, envelope: Dict) -> Dict:
        """Queue incoming Telegram updates."""
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._create_error_response(
                400, "Invalid request body: JSON object expected"
            ).dict()
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            ).dict()
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
        """Handle incoming Telegram updates."""
        if not isinstance(payload, dict):
            return self._create_error_response(
                400, "Invalid request body: JSON object expected"
            ).dict()

        await self._initialize_bot()
        await self._setup_handlers()

        chat_id = extract_chat_id(payload)
        if chat_id:
            try:
                await self._add_subscriber(chat_id)
            except Exception as error:
                logger.warning(f"Failed to add subscriber {chat_id}: {error}")

        try:
            telegram_update = TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error(f"Invalid Telegram update: {error}")
            return self._create_error_response(400, "Invalid Telegram update").dict()

        try:
            await self.dispatcher.feed_update(self.bot, telegram_update)
        except Exception as error:
            logger.exception(f"Error processing Telegram update: {error}")
            return self._create_error_response(
                500, "Error processing Telegram update"
            ).dict()

        return {
            "status": "processed",
            "connected_integration_id": self.connected_integration_id,
            "chat_id": chat_id,
        }
