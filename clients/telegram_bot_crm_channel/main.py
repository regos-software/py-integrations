from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import socket
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx
from aiogram import Bot
from starlette.responses import JSONResponse

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from schemas.api.base import APIBaseResponse
from schemas.api.chat.chat_message import (
    ChatMessageAddFileRequest,
    ChatMessageAddRequest,
    ChatMessageGetRequest,
    ChatMessageMarkSentRequest,
    ChatMessageTypeEnum,
)
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.lead import Lead, LeadAddRequest, LeadGetRequest, LeadStatusEnum
from schemas.api.crm.pipeline import CrmEntityTypeEnum, PipelineGetRequest
from schemas.api.files.file import FileGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse
from schemas.integration.telegram_integration_base import IntegrationTelegramBase

logger = setup_logger("telegram_bot_crm_channel")


class TelegramBotCrmChannelConfig:
    INTEGRATION_KEY = "telegram_bot_crm_channel"
    REDIS_PREFIX = "clients:tg_crm_channel:"

    SETTINGS_TTL = max(int(app_settings.redis_cache_ttl or 60), 30)
    DEFAULT_DEDUPE_TTL_SEC = 24 * 60 * 60
    DEFAULT_STATE_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = 10000
    STREAM_GROUP = "tg_crm_channel_workers"
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_READ_BLOCK_MS = 5000
    STREAM_BATCH_SIZE = 20
    STREAM_MAX_RETRIES = 5

    POLLING_LOCK_TTL_SEC = 30

    SUPPORTED_INBOUND_WEBHOOKS = {
        "ChatMessageAdded",
        "ChatMessageEdited",
        "ChatMessageDeleted",
        "ChatWriting",
        "LeadClosed",
    }


@dataclass
class BotSlotConfig:
    slot: int
    token: str
    pipeline_id: int
    channel_id: int
    lead_subject_template: Optional[str]
    default_responsible_user_id: Optional[int]
    bot_hash: str


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    bots: List[BotSlotConfig]
    bots_by_hash: Dict[str, BotSlotConfig]
    update_mode: str
    telegram_secret_token: Optional[str]
    lead_dedupe_ttl_sec: int
    state_ttl_sec: int
    send_private_messages: bool
    forward_system_messages: bool
    lead_closed_message_template: Optional[str]


_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[Tuple[str, str], asyncio.Task] = {}
_POLLER_TASKS: Dict[Tuple[str, str], asyncio.Task] = {}
_BOT_CLIENTS: Dict[str, Bot] = {}
_BOT_CLIENTS_LOCK = asyncio.Lock()
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
_INSTANCE_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_client is not None)


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def _bot_hash(token: str) -> str:
    return hashlib.md5(token.encode("utf-8")).hexdigest()


def _update_mode_from_value(raw: Optional[str]) -> str:
    mode = str(raw or "").strip().lower()
    if mode in {"longpolling", "long_polling", "long-polling", "polling"}:
        return "longpolling"
    return "webhook"


def _tg_chat_id_cast(chat_id: str) -> Any:
    value = str(chat_id).strip()
    if value.lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return value
    return value


def _sanitize_file_name(name: str) -> str:
    trimmed = (name or "").strip()
    if not trimmed:
        return "file.bin"
    return trimmed[:200]


def _file_ext_from_name(name: str, fallback: str = "bin") -> str:
    if "." not in name:
        return fallback
    ext = name.rsplit(".", 1)[-1].strip().lower()
    if not ext:
        return fallback
    return ext[:10]


def _is_photo_extension(extension: Optional[str]) -> bool:
    return str(extension or "").lower() in {"jpg", "jpeg", "png", "webp"}


def _headers_ci(headers: Dict[str, Any], key: str) -> Optional[str]:
    key_l = key.lower()
    for h_key, h_value in (headers or {}).items():
        if str(h_key).lower() == key_l:
            return str(h_value)
    return None


class TelegramBotCrmChannelIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _settings_cache_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}settings:{connected_integration_id}"
        )

    @staticmethod
    def _stream_key(kind: str, connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}stream:{kind}:{connected_integration_id}"
        )

    @staticmethod
    def _dlq_stream_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}stream:dlq:{connected_integration_id}"
        )

    @staticmethod
    def _active_ci_ids_key() -> str:
        return f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}active_ci_ids"

    @staticmethod
    def _lead_by_tg_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lead_by_tg:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _chat_by_lead_key(connected_integration_id: str, lead_id: int) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}chat_by_lead:"
            f"{connected_integration_id}:{lead_id}"
        )

    @staticmethod
    def _tg_by_chat_key(connected_integration_id: str, chat_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}tg_by_chat:"
            f"{connected_integration_id}:{chat_id}"
        )

    @staticmethod
    def _msgmap_regos_to_tg_key(connected_integration_id: str, chat_message_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}msgmap:regos_to_tg:"
            f"{connected_integration_id}:{chat_message_id}"
        )

    @staticmethod
    def _dedupe_tg_update_key(
        connected_integration_id: str, bot_hash: str, update_id: int
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}dedupe:telegram_update:"
            f"{connected_integration_id}:{bot_hash}:{update_id}"
        )

    @staticmethod
    def _dedupe_webhook_key(connected_integration_id: str, event_hash: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}dedupe:webhook:"
            f"{connected_integration_id}:{event_hash}"
        )

    @staticmethod
    def _lock_connect_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:connect:"
            f"{connected_integration_id}"
        )

    @staticmethod
    def _lock_create_lead_key(
        connected_integration_id: str, bot_hash: str, tg_chat_id: str
    ) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:create_lead:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _lock_polling_owner_key(bot_hash: str) -> str:
        return f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}lock:polling_owner:{bot_hash}"

    @staticmethod
    def _typing_key(connected_integration_id: str, bot_hash: str, tg_chat_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}typing:"
            f"{connected_integration_id}:{bot_hash}:{tg_chat_id}"
        )

    @staticmethod
    def _worker_heartbeat_key(connected_integration_id: str) -> str:
        return (
            f"{TelegramBotCrmChannelConfig.REDIS_PREFIX}worker:heartbeat:"
            f"{connected_integration_id}:{_INSTANCE_ID}"
        )

    @staticmethod
    async def _redis_set_mapping(key: str, value: str) -> None:
        if not _redis_enabled():
            return
        await redis_client.set(key, value)

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set_nx_with_ttl(key: str, value: str, ttl_sec: int) -> bool:
        if not _redis_enabled():
            return False
        result = await redis_client.set(key, value, ex=max(ttl_sec, 1), nx=True)
        return bool(result)

    @staticmethod
    async def _acquire_lock(key: str, ttl_sec: int) -> Optional[str]:
        if not _redis_enabled():
            return None
        token = uuid.uuid4().hex
        ok = await redis_client.set(key, token, ex=max(ttl_sec, 1), nx=True)
        return token if ok else None

    @staticmethod
    async def _release_lock(key: str, token: Optional[str]) -> None:
        if not (_redis_enabled() and token):
            return
        script = (
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end"
        )
        try:
            await redis_client.eval(script, 1, key, token)
        except Exception:
            pass

    @staticmethod
    async def _fetch_settings_map(connected_integration_id: str) -> Dict[str, str]:
        cache_key = TelegramBotCrmChannelIntegration._settings_cache_key(
            connected_integration_id
        )
        if _redis_enabled():
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    return _json_loads(cached)
            except Exception as error:
                logger.warning("Failed to read settings cache: %s", error)

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    integration_key=TelegramBotCrmChannelConfig.INTEGRATION_KEY
                )
            )
        settings_map = {
            str(row.key).strip().lower(): row.value
            for row in (response.result or [])
            if getattr(row, "key", None)
        }

        if _redis_enabled():
            try:
                await redis_client.setex(
                    cache_key,
                    TelegramBotCrmChannelConfig.SETTINGS_TTL,
                    _json_dumps(settings_map),
                )
            except Exception as error:
                logger.warning("Failed to write settings cache: %s", error)

        return settings_map

    @staticmethod
    async def _clear_settings_cache(connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        try:
            await redis_client.delete(
                TelegramBotCrmChannelIntegration._settings_cache_key(
                    connected_integration_id
                )
            )
        except Exception as error:
            logger.warning("Failed to clear settings cache: %s", error)

    @staticmethod
    def _parse_bots(settings_map: Dict[str, str]) -> List[BotSlotConfig]:
        bots: List[BotSlotConfig] = []
        bot_hashes: set[str] = set()

        for slot in range(1, 6):
            enabled = _parse_bool(settings_map.get(f"bot_{slot}_enabled"), False)
            if not enabled:
                continue

            token = str(settings_map.get(f"bot_{slot}_token") or "").strip()
            pipeline_id = _parse_int(settings_map.get(f"bot_{slot}_pipeline_id"))
            channel_id = _parse_int(settings_map.get(f"bot_{slot}_channel_id"))
            if not token:
                raise ValueError(f"BOT_{slot}_TOKEN is required when BOT_{slot}_ENABLED=true")
            if not pipeline_id or pipeline_id <= 0:
                raise ValueError(
                    f"BOT_{slot}_PIPELINE_ID must be a positive integer for enabled bot"
                )
            if not channel_id or channel_id <= 0:
                raise ValueError(
                    f"BOT_{slot}_CHANNEL_ID must be a positive integer for enabled bot"
                )

            token_hash = _bot_hash(token)
            if token_hash in bot_hashes:
                raise ValueError("Bot tokens must be unique per connected integration")
            bot_hashes.add(token_hash)

            bots.append(
                BotSlotConfig(
                    slot=slot,
                    token=token,
                    pipeline_id=pipeline_id,
                    channel_id=channel_id,
                    lead_subject_template=str(
                        settings_map.get(f"bot_{slot}_lead_subject_template") or ""
                    ).strip()
                    or None,
                    default_responsible_user_id=_parse_int(
                        settings_map.get(f"bot_{slot}_default_responsible_user_id")
                    ),
                    bot_hash=token_hash,
                )
            )

        if not bots:
            raise ValueError("At least one BOT_{N}_ENABLED=true is required")
        return bots

    @staticmethod
    async def _load_runtime(connected_integration_id: str) -> RuntimeConfig:
        settings_map = await TelegramBotCrmChannelIntegration._fetch_settings_map(
            connected_integration_id
        )
        bots = TelegramBotCrmChannelIntegration._parse_bots(settings_map)
        mode = _update_mode_from_value(
            settings_map.get("telegram_update_mode") or app_settings.telegram_update_mode
        )

        runtime = RuntimeConfig(
            connected_integration_id=connected_integration_id,
            bots=bots,
            bots_by_hash={bot.bot_hash: bot for bot in bots},
            update_mode=mode,
            telegram_secret_token=str(
                settings_map.get("telegram_secret_token") or ""
            ).strip()
            or None,
            lead_dedupe_ttl_sec=max(
                _parse_int(
                    settings_map.get("lead_dedupe_ttl_sec"),
                    TelegramBotCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                )
                or TelegramBotCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                60,
            ),
            state_ttl_sec=max(
                _parse_int(
                    settings_map.get("state_ttl_sec"),
                    TelegramBotCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                )
                or TelegramBotCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                60,
            ),
            send_private_messages=_parse_bool(
                settings_map.get("send_private_messages"), False
            ),
            forward_system_messages=_parse_bool(
                settings_map.get("forward_system_messages"), False
            ),
            lead_closed_message_template=str(
                settings_map.get("lead_closed_message_template") or ""
            ).strip()
            or None,
        )
        return runtime

    @staticmethod
    async def _get_bot(token: str) -> Bot:
        async with _BOT_CLIENTS_LOCK:
            bot = _BOT_CLIENTS.get(token)
            if bot:
                return bot
            bot = Bot(token=token)
            _BOT_CLIENTS[token] = bot
            return bot

    @staticmethod
    async def _get_http_client() -> httpx.AsyncClient:
        global _HTTP_CLIENT
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.AsyncClient(timeout=90)
        return _HTTP_CLIENT

    @staticmethod
    async def _validate_pipelines(runtime: RuntimeConfig) -> None:
        pipeline_ids = sorted({bot.pipeline_id for bot in runtime.bots})
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.pipeline.get(
                PipelineGetRequest(
                    entity_type=CrmEntityTypeEnum.Lead,
                    ids=pipeline_ids,
                    active=True,
                    limit=max(len(pipeline_ids), 1),
                    offset=0,
                )
            )
        found_ids = {row.id for row in (response.result or []) if row and row.id}
        missing = [pid for pid in pipeline_ids if pid not in found_ids]
        if missing:
            raise ValueError(f"Pipeline not found or inactive: {missing}")

    @staticmethod
    async def _subscribe_required_webhooks(
        connected_integration_id: str,
    ) -> Dict[str, Any]:
        payload = {
            "webhooks": sorted(TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS)
        }
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                await api.call("ConnectedIntegration/Edit", payload, APIBaseResponse)
            return {"status": "ok"}
        except Exception as error:
            logger.warning("Webhook subscription failed for %s: %s", connected_integration_id, error)
            return {"status": "failed", "error": str(error)}

    @staticmethod
    async def _enqueue(
        stream_key: str,
        fields: Dict[str, Any],
    ) -> None:
        if not _redis_enabled():
            raise RuntimeError("Redis is not enabled")
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[key] = _json_dumps(value)
            elif value is None:
                serialized[key] = ""
            else:
                serialized[key] = str(value)
        await redis_client.xadd(
            stream_key,
            serialized,
            maxlen=TelegramBotCrmChannelConfig.STREAM_MAXLEN,
            approximate=True,
        )

    @staticmethod
    async def _ensure_consumer_group(stream_key: str) -> None:
        if not _redis_enabled():
            return
        try:
            await redis_client.xgroup_create(
                stream_key,
                TelegramBotCrmChannelConfig.STREAM_GROUP,
                id="0-0",
                mkstream=True,
            )
        except Exception as error:
            if "BUSYGROUP" not in str(error):
                raise

    @classmethod
    async def _ensure_stream_workers(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            for kind in ("telegram_in", "regos_in"):
                key = (connected_integration_id, kind)
                task = _WORKER_TASKS.get(key)
                if task and not task.done():
                    continue
                _WORKER_TASKS[key] = asyncio.create_task(
                    cls._stream_worker_loop(connected_integration_id, kind),
                    name=f"tg_crm_stream_{kind}_{connected_integration_id}",
                )

    @classmethod
    async def _stop_stream_workers(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            keys = [k for k in _WORKER_TASKS if k[0] == connected_integration_id]
            tasks = [_WORKER_TASKS.pop(k) for k in keys]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping stream worker")

    @classmethod
    async def _ensure_poller(
        cls, connected_integration_id: str, bot_config: BotSlotConfig
    ) -> None:
        key = (connected_integration_id, bot_config.bot_hash)
        async with _MANAGER_LOCK:
            task = _POLLER_TASKS.get(key)
            if task and not task.done():
                return
            _POLLER_TASKS[key] = asyncio.create_task(
                cls._polling_loop(connected_integration_id, bot_config),
                name=f"tg_crm_poll_{connected_integration_id}_{bot_config.bot_hash}",
            )

    @classmethod
    async def _stop_pollers_for_ci(
        cls, connected_integration_id: str, keep_hashes: Optional[set[str]] = None
    ) -> None:
        keep_hashes = keep_hashes or set()
        async with _MANAGER_LOCK:
            keys = [
                key
                for key in _POLLER_TASKS
                if key[0] == connected_integration_id and key[1] not in keep_hashes
            ]
            tasks = [_POLLER_TASKS.pop(key) for key in keys]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping poller")

    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        lock_key = self._lock_connect_key(self.connected_integration_id)
        lock_token = await self._acquire_lock(lock_key, 30)
        if not lock_token:
            return self._error_response(1002, "connect is already running").dict()

        try:
            runtime = await self._load_runtime(self.connected_integration_id)
            await self._validate_pipelines(runtime)
            webhook_subscribe = await self._subscribe_required_webhooks(
                self.connected_integration_id
            )
            await self._ensure_stream_workers(self.connected_integration_id)
            await redis_client.sadd(self._active_ci_ids_key(), self.connected_integration_id)

            if runtime.update_mode == "longpolling":
                keep_hashes = {bot.bot_hash for bot in runtime.bots}
                await self._stop_pollers_for_ci(
                    self.connected_integration_id, keep_hashes=keep_hashes
                )
                for bot_cfg in runtime.bots:
                    bot = await self._get_bot(bot_cfg.token)
                    await bot.delete_webhook(drop_pending_updates=True)
                    await self._ensure_poller(self.connected_integration_id, bot_cfg)
                return {
                    "status": "connected",
                    "mode": "longpolling",
                    "bots": len(runtime.bots),
                    "webhooks_subscription": webhook_subscribe,
                }

            await self._stop_pollers_for_ci(self.connected_integration_id)
            webhook_urls: Dict[str, str] = {}
            for bot_cfg in runtime.bots:
                bot = await self._get_bot(bot_cfg.token)
                url = (
                    f"{app_settings.integration_url.rstrip('/')}/external/"
                    f"{self.connected_integration_id}/external/?bot_hash={bot_cfg.bot_hash}"
                )
                await bot.delete_webhook(drop_pending_updates=True)
                kwargs_set_webhook: Dict[str, Any] = {"url": url}
                if runtime.telegram_secret_token:
                    kwargs_set_webhook["secret_token"] = runtime.telegram_secret_token
                await bot.set_webhook(**kwargs_set_webhook)
                webhook_urls[bot_cfg.bot_hash] = url

            return {
                "status": "connected",
                "mode": "webhook",
                "bots": len(runtime.bots),
                "webhook_urls": webhook_urls,
                "webhooks_subscription": webhook_subscribe,
            }
        except Exception as error:
            logger.exception("connect failed: %s", error)
            return self._error_response(1003, f"connect failed: {error}").dict()
        finally:
            await self._release_lock(lock_key, lock_token)

    async def disconnect(self, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        try:
            runtime: Optional[RuntimeConfig] = None
            try:
                runtime = await self._load_runtime(self.connected_integration_id)
            except Exception:
                runtime = None

            await self._stop_pollers_for_ci(self.connected_integration_id)
            if runtime:
                for bot_cfg in runtime.bots:
                    try:
                        bot = await self._get_bot(bot_cfg.token)
                        await bot.delete_webhook(drop_pending_updates=True)
                    except Exception as error:
                        logger.warning(
                            "Failed to delete webhook for bot_hash=%s: %s",
                            bot_cfg.bot_hash,
                            error,
                        )

            await self._stop_stream_workers(self.connected_integration_id)
            await redis_client.srem(self._active_ci_ids_key(), self.connected_integration_id)
            return {"status": "disconnected"}
        except Exception as error:
            logger.exception("disconnect failed: %s", error)
            return self._error_response(1004, f"disconnect failed: {error}").dict()

    async def reconnect(self, **kwargs) -> Dict[str, Any]:
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, **kwargs) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._clear_settings_cache(self.connected_integration_id)
        result = await self.reconnect()
        return {"status": "settings updated", "reconnect": result}

    async def send_messages(self, messages: List[Dict]) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        try:
            runtime = await self._load_runtime(self.connected_integration_id)
            details: List[Dict[str, Any]] = []
            for item in messages:
                text = str(item.get("message") or "").strip()
                recipient = str(item.get("recipient") or "").strip()
                bot_hash = str(item.get("bot_hash") or "").strip()
                if not text or not recipient:
                    details.append({"status": "error", "error": "recipient/message required"})
                    continue
                if not bot_hash:
                    bot_hash = runtime.bots[0].bot_hash
                bot_cfg = runtime.bots_by_hash.get(bot_hash)
                if not bot_cfg:
                    details.append({"status": "error", "error": f"unknown bot_hash={bot_hash}"})
                    continue
                bot = await self._get_bot(bot_cfg.token)
                sent = await bot.send_message(chat_id=_tg_chat_id_cast(recipient), text=text)
                details.append(
                    {
                        "status": "sent",
                        "bot_hash": bot_hash,
                        "recipient": recipient,
                        "telegram_message_id": sent.message_id,
                    }
                )
            return {"sent": len([row for row in details if row["status"] == "sent"]), "details": details}
        except Exception as error:
            logger.exception("send_messages failed: %s", error)
            return self._error_response(1005, f"send_messages failed: {error}").dict()

    async def handle_external(self, envelope: Dict) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return JSONResponse(
                status_code=503,
                content=self._error_response(1001, "Redis is required for this integration").dict(),
            )

        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._error_response(400, "Invalid Telegram payload").dict()

        runtime = await self._load_runtime(self.connected_integration_id)
        query = envelope.get("query") or {}
        bot_hash = str(query.get("bot_hash") or "").strip()
        if not bot_hash and len(runtime.bots) == 1:
            bot_hash = runtime.bots[0].bot_hash
        if bot_hash not in runtime.bots_by_hash:
            return self._error_response(400, "Unknown bot_hash for Telegram webhook").dict()

        if runtime.telegram_secret_token:
            headers = envelope.get("headers") or {}
            actual_secret = _headers_ci(headers, "x-telegram-bot-api-secret-token")
            if actual_secret != runtime.telegram_secret_token:
                return self._error_response(403, "Invalid Telegram secret token").dict()

        try:
            await self._enqueue(
                self._stream_key("telegram_in", self.connected_integration_id),
                {
                    "connected_integration_id": self.connected_integration_id,
                    "bot_hash": bot_hash,
                    "payload": payload,
                    "attempt": "0",
                    "enqueued_at": str(_now_ts()),
                },
            )
        except Exception as error:
            logger.exception("Failed to enqueue Telegram event: %s", error)
            return JSONResponse(
                status_code=503,
                content=self._error_response(503, f"enqueue failed: {error}").dict(),
            )

        await self._ensure_stream_workers(self.connected_integration_id)
        return {"status": "accepted"}

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        event_action, event_data, event_id = self._normalize_regos_webhook_payload(
            action=action,
            data=data,
            kwargs=kwargs,
        )
        if not event_action:
            return self._error_response(400, "Webhook action is not provided").dict()
        if event_action not in TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "action": event_action}

        try:
            await self._enqueue(
                self._stream_key("regos_in", self.connected_integration_id),
                {
                    "connected_integration_id": self.connected_integration_id,
                    "action": event_action,
                    "payload": event_data or {},
                    "event_id": event_id or "",
                    "attempt": "0",
                    "enqueued_at": str(_now_ts()),
                },
            )
        except Exception as error:
            logger.exception("Failed to enqueue REGOS webhook: %s", error)
            return self._error_response(503, f"enqueue failed: {error}").dict()

        await self._ensure_stream_workers(self.connected_integration_id)
        return {"status": "accepted", "action": event_action}

    @staticmethod
    def _normalize_regos_webhook_payload(
        action: Optional[str], data: Optional[Dict], kwargs: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
        event_action: Optional[str] = None
        event_data: Dict[str, Any] = {}
        event_id: Optional[str] = None

        if isinstance(action, str) and action in TelegramBotCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            event_action = action
            event_data = data or {}
            event_id = kwargs.get("event_id")
            return event_action, event_data, event_id

        if action == "HandleWebhook":
            payload = data or {}
            event_id = str(payload.get("event_id") or kwargs.get("event_id") or "").strip() or None
            nested = payload.get("data")
            if isinstance(nested, dict):
                nested_action = nested.get("action")
                nested_data = nested.get("data")
                if isinstance(nested_action, str):
                    event_action = nested_action
                if isinstance(nested_data, dict):
                    event_data = nested_data
                elif isinstance(nested, dict):
                    event_data = dict(nested)
            return event_action, event_data, event_id

        if isinstance(data, dict):
            if isinstance(data.get("action"), str) and isinstance(data.get("data"), dict):
                event_action = data.get("action")
                event_data = data.get("data") or {}
                event_id = str(data.get("event_id") or kwargs.get("event_id") or "").strip() or None
                return event_action, event_data, event_id

        if isinstance(action, str):
            event_action = action
            event_data = data or {}
            event_id = kwargs.get("event_id")
            return event_action, event_data, event_id

        return None, {}, None

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _build_subject(template: Optional[str], message: Dict[str, Any], tg_chat_id: str) -> str:
        author = message.get("from") or {}
        payload = {
            "chat_id": tg_chat_id,
            "first_name": str(author.get("first_name") or "").strip(),
            "last_name": str(author.get("last_name") or "").strip(),
            "username": str(author.get("username") or "").strip(),
        }
        if template:
            try:
                result = template.format_map(payload).strip()
                if result:
                    return result[:250]
            except Exception:
                pass
        default_name = payload["first_name"] or payload["username"] or tg_chat_id
        return f"Telegram: {default_name}"[:250]

    @classmethod
    async def _set_worker_heartbeat(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        await redis_client.setex(
            cls._worker_heartbeat_key(connected_integration_id), 30, str(_now_ts())
        )

    @classmethod
    async def _stream_worker_loop(cls, connected_integration_id: str, kind: str) -> None:
        stream_key = cls._stream_key(kind, connected_integration_id)
        consumer = f"{_INSTANCE_ID}:{kind}"
        await cls._ensure_consumer_group(stream_key)
        logger.info("Stream worker started for %s (%s)", connected_integration_id, kind)

        while True:
            try:
                await cls._set_worker_heartbeat(connected_integration_id)
                await cls._process_claimed_entries(
                    stream_key, consumer, connected_integration_id, kind
                )
                records = await redis_client.xreadgroup(
                    groupname=TelegramBotCrmChannelConfig.STREAM_GROUP,
                    consumername=consumer,
                    streams={stream_key: ">"},
                    count=TelegramBotCrmChannelConfig.STREAM_BATCH_SIZE,
                    block=TelegramBotCrmChannelConfig.STREAM_READ_BLOCK_MS,
                )
                if not records:
                    continue

                for _, entries in records:
                    for message_id, fields in entries:
                        await cls._process_stream_entry(
                            stream_key=stream_key,
                            message_id=message_id,
                            fields=fields,
                            connected_integration_id=connected_integration_id,
                            kind=kind,
                        )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.exception(
                    "Stream worker error for %s (%s): %s",
                    connected_integration_id,
                    kind,
                    error,
                )
                await asyncio.sleep(1.0)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
        connected_integration_id: str,
        kind: str,
    ) -> None:
        claimed_raw = await redis_client.xautoclaim(
            stream_key,
            TelegramBotCrmChannelConfig.STREAM_GROUP,
            consumer,
            min_idle_time=TelegramBotCrmChannelConfig.STREAM_MIN_IDLE_MS,
            start_id="0-0",
            count=TelegramBotCrmChannelConfig.STREAM_BATCH_SIZE,
        )
        entries = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        for message_id, fields in entries:
            await cls._process_stream_entry(
                stream_key=stream_key,
                message_id=message_id,
                fields=fields,
                connected_integration_id=connected_integration_id,
                kind=kind,
            )

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        message_id: str,
        fields: Dict[str, str],
        connected_integration_id: str,
        kind: str,
    ) -> None:
        attempts = int(str(fields.get("attempt") or "0"))
        try:
            if kind == "telegram_in":
                await cls._process_telegram_event(connected_integration_id, fields)
            else:
                await cls._process_regos_event(connected_integration_id, fields)
            await redis_client.xack(
                stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
            )
        except Exception as error:
            attempts += 1
            if attempts >= TelegramBotCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["error"] = str(error)
                dlq_payload["attempt"] = str(attempts)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_message_id"] = message_id
                await cls._enqueue(cls._dlq_stream_key(connected_integration_id), dlq_payload)
                await redis_client.xack(
                    stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
                )
                logger.error(
                    "Moved message to DLQ: ci=%s kind=%s message_id=%s error=%s",
                    connected_integration_id,
                    kind,
                    message_id,
                    error,
                )
                return

            retry_payload = dict(fields)
            retry_payload["attempt"] = str(attempts)
            retry_payload["last_error"] = str(error)
            await cls._enqueue(stream_key, retry_payload)
            await redis_client.xack(
                stream_key, TelegramBotCrmChannelConfig.STREAM_GROUP, message_id
            )
            logger.warning(
                "Requeued stream event: ci=%s kind=%s attempt=%s message_id=%s",
                connected_integration_id,
                kind,
                attempts,
                message_id,
            )

    @classmethod
    async def _polling_loop(
        cls, connected_integration_id: str, bot_config: BotSlotConfig
    ) -> None:
        bot = await cls._get_bot(bot_config.token)
        offset: Optional[int] = None
        lock_key = cls._lock_polling_owner_key(bot_config.bot_hash)
        owner = _INSTANCE_ID
        logger.info(
            "Longpolling worker started for bot_hash=%s ci=%s",
            bot_config.bot_hash,
            connected_integration_id,
        )

        try:
            while True:
                try:
                    acquired = await redis_client.set(
                        lock_key,
                        owner,
                        ex=TelegramBotCrmChannelConfig.POLLING_LOCK_TTL_SEC,
                        nx=True,
                    )
                    if not acquired:
                        current_owner = await redis_client.get(lock_key)
                        if current_owner == owner:
                            await redis_client.expire(
                                lock_key, TelegramBotCrmChannelConfig.POLLING_LOCK_TTL_SEC
                            )
                            acquired = True

                    if not acquired:
                        await asyncio.sleep(1.5)
                        continue

                    updates = await bot.get_updates(
                        offset=offset,
                        timeout=20,
                        allowed_updates=["message", "edited_message"],
                    )
                    if not updates:
                        await asyncio.sleep(0.1)
                        continue

                    for update in updates:
                        offset = int(update.update_id) + 1
                        await cls._enqueue(
                            cls._stream_key("telegram_in", connected_integration_id),
                            {
                                "connected_integration_id": connected_integration_id,
                                "bot_hash": bot_config.bot_hash,
                                "payload": update.model_dump(mode="json"),
                                "attempt": "0",
                                "enqueued_at": str(_now_ts()),
                            },
                        )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.warning(
                        "Polling loop transient error for bot_hash=%s ci=%s: %s",
                        bot_config.bot_hash,
                        connected_integration_id,
                        error,
                    )
                    await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            raise
        finally:
            await cls._release_lock(lock_key, owner)

    @classmethod
    async def _process_telegram_event(
        cls, connected_integration_id: str, fields: Dict[str, str]
    ) -> None:
        runtime = await cls._load_runtime(connected_integration_id)
        bot_hash = str(fields.get("bot_hash") or "").strip()
        if bot_hash not in runtime.bots_by_hash:
            logger.warning("Unknown bot_hash in Telegram stream: %s", bot_hash)
            return
        bot_cfg = runtime.bots_by_hash[bot_hash]

        payload_raw = fields.get("payload")
        payload = _json_loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        if not isinstance(payload, dict):
            return

        update_id = payload.get("update_id")
        if update_id is None:
            return
        try:
            update_id_int = int(update_id)
        except (TypeError, ValueError):
            return

        dedupe_key = cls._dedupe_tg_update_key(
            connected_integration_id, bot_hash, update_id_int
        )
        inserted = await cls._redis_set_nx_with_ttl(
            dedupe_key, "1", runtime.lead_dedupe_ttl_sec
        )
        if not inserted:
            return

        message = payload.get("message") or payload.get("edited_message")
        if not isinstance(message, dict):
            return

        author = message.get("from") or {}
        if bool(author.get("is_bot")):
            return

        chat = message.get("chat") or {}
        tg_chat_id = str(chat.get("id") or "").strip()
        if not tg_chat_id:
            return

        lead_id, chat_id = await cls._resolve_or_create_lead(
            connected_integration_id=connected_integration_id,
            runtime=runtime,
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            message=message,
        )
        if not lead_id or not chat_id:
            return

        text = str(message.get("text") or message.get("caption") or "").strip() or None
        file_ids = await cls._upload_telegram_files(
            connected_integration_id=connected_integration_id,
            bot_cfg=bot_cfg,
            chat_id=chat_id,
            message=message,
        )
        if not text and not file_ids:
            return

        tg_message_id = message.get("message_id")
        event_id = f"tgupd:{bot_hash}:{update_id_int}"
        ext_message_id = f"tgmsg:{bot_hash}:{tg_chat_id}:{tg_message_id}"

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=chat_id,
                    message_type=ChatMessageTypeEnum.Regular,
                    text=text,
                    file_ids=file_ids or None,
                    event_id=event_id,
                    external_message_id=ext_message_id,
                )
            )

    @classmethod
    async def _resolve_or_create_lead(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        message: Dict[str, Any],
    ) -> Tuple[Optional[int], Optional[str]]:
        lead_key = cls._lead_by_tg_key(connected_integration_id, bot_cfg.bot_hash, tg_chat_id)
        lead_id_raw = await cls._redis_get(lead_key)
        if lead_id_raw:
            lead_id = _parse_int(lead_id_raw)
            if lead_id:
                chat_id = await cls._redis_get(cls._chat_by_lead_key(connected_integration_id, lead_id))
                if chat_id:
                    return lead_id, chat_id

        recovered = await cls._recover_lead_by_external_chat(
            connected_integration_id=connected_integration_id,
            bot_hash=bot_cfg.bot_hash,
            tg_chat_id=tg_chat_id,
        )
        if recovered:
            await cls._save_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
                lead=recovered,
            )
            return recovered.id, recovered.chat_id

        lock_key = cls._lock_create_lead_key(connected_integration_id, bot_cfg.bot_hash, tg_chat_id)
        lock_token = await cls._acquire_lock(lock_key, runtime.state_ttl_sec)
        if not lock_token:
            await asyncio.sleep(0.25)
            lead_id_raw = await cls._redis_get(lead_key)
            if lead_id_raw:
                lead_id = _parse_int(lead_id_raw)
                if lead_id:
                    chat_id = await cls._redis_get(
                        cls._chat_by_lead_key(connected_integration_id, lead_id)
                    )
                    if chat_id:
                        return lead_id, chat_id
            return None, None

        try:
            lead_id_raw = await cls._redis_get(lead_key)
            if lead_id_raw:
                lead_id = _parse_int(lead_id_raw)
                if lead_id:
                    chat_id = await cls._redis_get(
                        cls._chat_by_lead_key(connected_integration_id, lead_id)
                    )
                    if chat_id:
                        return lead_id, chat_id

            author = message.get("from") or {}
            lead_subject = cls._build_subject(
                bot_cfg.lead_subject_template, message, tg_chat_id
            )

            client_name = " ".join(
                [str(author.get("first_name") or "").strip(), str(author.get("last_name") or "").strip()]
            ).strip() or str(author.get("username") or "").strip() or None

            client_phone = None
            contact = message.get("contact")
            if isinstance(contact, dict):
                client_phone = str(contact.get("phone_number") or "").strip() or None

            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                add_resp = await api.crm.lead.add(
                    LeadAddRequest(
                        channel_id=bot_cfg.channel_id,
                        pipeline_id=bot_cfg.pipeline_id,
                        responsible_user_id=bot_cfg.default_responsible_user_id,
                        subject=lead_subject,
                        client_name=client_name,
                        client_phone=client_phone,
                        external_chat_id=tg_chat_id,
                        bot_id=bot_cfg.bot_hash,
                    )
                )
                new_id = None
                if add_resp.result:
                    new_id = _parse_int(str(add_resp.result.new_id))
                if not new_id:
                    raise RuntimeError("Lead/Add did not return new_id")

                lead = await api.crm.lead.get_by_id(new_id)
                if not lead or not lead.chat_id:
                    raise RuntimeError("Lead/Get did not return chat_id")

            await cls._save_lead_mapping(
                connected_integration_id=connected_integration_id,
                bot_hash=bot_cfg.bot_hash,
                tg_chat_id=tg_chat_id,
                lead=lead,
            )
            return lead.id, lead.chat_id
        finally:
            await cls._release_lock(lock_key, lock_token)

    @classmethod
    async def _recover_lead_by_external_chat(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
    ) -> Optional[Lead]:
        filters = [
            Filter(field="bot_id", operator=FilterOperator.Equal, value=bot_hash),
            Filter(
                field="external_chat_id",
                operator=FilterOperator.Equal,
                value=tg_chat_id,
            ),
        ]
        statuses = [
            LeadStatusEnum.New,
            LeadStatusEnum.InProgress,
            LeadStatusEnum.WaitingClient,
        ]
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.crm.lead.get(
                LeadGetRequest(filters=filters, statuses=statuses, limit=1, offset=0)
            )
        if not response.result:
            return None
        lead = response.result[0]
        if not lead or not lead.id or not lead.chat_id:
            return None
        return lead

    @classmethod
    async def _save_lead_mapping(
        cls,
        connected_integration_id: str,
        bot_hash: str,
        tg_chat_id: str,
        lead: Lead,
    ) -> None:
        if not (lead.id and lead.chat_id):
            return
        await cls._redis_set_mapping(
            cls._lead_by_tg_key(connected_integration_id, bot_hash, tg_chat_id),
            str(lead.id),
        )
        await cls._redis_set_mapping(
            cls._chat_by_lead_key(connected_integration_id, lead.id),
            str(lead.chat_id),
        )
        await cls._redis_set_mapping(
            cls._tg_by_chat_key(connected_integration_id, str(lead.chat_id)),
            _json_dumps({"bot_hash": bot_hash, "tg_chat_id": tg_chat_id}),
        )

    @classmethod
    async def _upload_telegram_files(
        cls,
        connected_integration_id: str,
        bot_cfg: BotSlotConfig,
        chat_id: str,
        message: Dict[str, Any],
    ) -> List[int]:
        files = cls._extract_files_from_message(message)
        if not files:
            return []

        uploaded_ids: List[int] = []
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            for file_meta in files:
                file_bytes = await cls._download_telegram_file(
                    token=bot_cfg.token, file_id=file_meta["file_id"]
                )
                payload_b64 = base64.b64encode(file_bytes).decode("ascii")
                response = await api.chat.chat_message.add_file(
                    ChatMessageAddFileRequest(
                        chat_id=chat_id,
                        name=file_meta["name"],
                        extension=file_meta["extension"],
                        data=payload_b64,
                    )
                )
                file_id = None
                if response.result:
                    file_id = _parse_int(str(response.result.file_id))
                if file_id:
                    uploaded_ids.append(file_id)
        return uploaded_ids

    @staticmethod
    def _extract_files_from_message(message: Dict[str, Any]) -> List[Dict[str, str]]:
        result: List[Dict[str, str]] = []
        message_id = str(message.get("message_id") or _now_ts())

        document = message.get("document")
        if isinstance(document, dict) and document.get("file_id"):
            file_name = _sanitize_file_name(str(document.get("file_name") or "document.bin"))
            result.append(
                {
                    "file_id": str(document["file_id"]),
                    "name": file_name,
                    "extension": _file_ext_from_name(file_name, "bin"),
                }
            )

        photos = message.get("photo")
        if isinstance(photos, list) and photos:
            best_photo = max(
                [row for row in photos if isinstance(row, dict) and row.get("file_id")],
                key=lambda row: int(row.get("file_size") or 0),
                default=None,
            )
            if best_photo:
                result.append(
                    {
                        "file_id": str(best_photo["file_id"]),
                        "name": f"photo_{message_id}.jpg",
                        "extension": "jpg",
                    }
                )
        return result

    @classmethod
    async def _download_telegram_file(cls, token: str, file_id: str) -> bytes:
        bot = await cls._get_bot(token)
        file_info = await bot.get_file(file_id)
        file_path = str(file_info.file_path or "").strip()
        if not file_path:
            raise RuntimeError("Telegram file_path is empty")
        url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        client = await cls._get_http_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.content

    @classmethod
    async def _process_regos_event(
        cls, connected_integration_id: str, fields: Dict[str, str]
    ) -> None:
        runtime = await cls._load_runtime(connected_integration_id)
        action = str(fields.get("action") or "").strip()
        payload_raw = fields.get("payload")
        payload = _json_loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        if not isinstance(payload, dict):
            payload = {}

        event_id_raw = str(fields.get("event_id") or "").strip()
        if not event_id_raw:
            stable = f"{action}:{_json_dumps(payload)}"
            event_id_raw = hashlib.md5(stable.encode("utf-8")).hexdigest()
        dedupe_key = cls._dedupe_webhook_key(connected_integration_id, event_id_raw)
        inserted = await cls._redis_set_nx_with_ttl(
            dedupe_key, "1", runtime.lead_dedupe_ttl_sec
        )
        if not inserted:
            return

        if action == "ChatMessageAdded":
            await cls._handle_chat_message_added(connected_integration_id, runtime, payload)
            return
        if action == "ChatMessageEdited":
            await cls._handle_chat_message_edited(connected_integration_id, runtime, payload)
            return
        if action == "ChatMessageDeleted":
            await cls._handle_chat_message_deleted(connected_integration_id, runtime, payload)
            return
        if action == "ChatWriting":
            await cls._handle_chat_writing(connected_integration_id, runtime, payload)
            return
        if action == "LeadClosed":
            await cls._handle_lead_closed(connected_integration_id, runtime, payload)
            return

    @classmethod
    async def _resolve_target_by_chat(
        cls, connected_integration_id: str, chat_id: str
    ) -> Optional[Tuple[str, str]]:
        cached = await cls._redis_get(cls._tg_by_chat_key(connected_integration_id, chat_id))
        if cached:
            try:
                parsed = _json_loads(cached)
                bot_hash = str(parsed.get("bot_hash") or "").strip()
                tg_chat_id = str(parsed.get("tg_chat_id") or "").strip()
                if bot_hash and tg_chat_id:
                    return bot_hash, tg_chat_id
            except Exception:
                pass

        filters = [Filter(field="chat_id", operator=FilterOperator.Equal, value=chat_id)]
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.crm.lead.get(
                LeadGetRequest(filters=filters, limit=1, offset=0)
            )
        if not response.result:
            return None
        lead = response.result[0]
        if not (lead and lead.bot_id and lead.external_chat_id and lead.id):
            return None
        await cls._redis_set_mapping(
            cls._chat_by_lead_key(connected_integration_id, lead.id), str(chat_id)
        )
        await cls._redis_set_mapping(
            cls._tg_by_chat_key(connected_integration_id, chat_id),
            _json_dumps(
                {"bot_hash": str(lead.bot_id), "tg_chat_id": str(lead.external_chat_id)}
            ),
        )
        return str(lead.bot_id), str(lead.external_chat_id)

    @classmethod
    async def _handle_chat_message_added(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return

        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=chat_id,
                    ids=[message_id],
                    limit=1,
                    offset=0,
                    include_staff_private=True,
                )
            )
            if not response.result:
                return
            msg = response.result[0]
            if not msg:
                return
            if str(msg.external_message_id or "").startswith("tgmsg:"):
                return
            if msg.message_type == ChatMessageTypeEnum.Private and not runtime.send_private_messages:
                return
            if msg.message_type == ChatMessageTypeEnum.System and not runtime.forward_system_messages:
                return

            sent_tg_message_id = await cls._send_chat_message_to_telegram(
                bot_cfg=bot_cfg,
                tg_chat_id=tg_chat_id,
                text=msg.text or "",
                file_ids=msg.file_ids or [],
                connected_integration_id=connected_integration_id,
            )
            if not sent_tg_message_id:
                return

            await api.chat.chat_message.mark_sent(
                ChatMessageMarkSentRequest(
                    id=message_id,
                    external_message_id=f"tgout:{bot_hash}:{sent_tg_message_id}",
                )
            )
            await cls._redis_set_mapping(
                cls._msgmap_regos_to_tg_key(connected_integration_id, message_id),
                str(sent_tg_message_id),
            )

    @classmethod
    async def _send_chat_message_to_telegram(
        cls,
        bot_cfg: BotSlotConfig,
        tg_chat_id: str,
        text: str,
        file_ids: List[int],
        connected_integration_id: str,
    ) -> Optional[int]:
        bot = await cls._get_bot(bot_cfg.token)
        target_chat = _tg_chat_id_cast(tg_chat_id)
        first_sent_id: Optional[int] = None
        caption_used = False

        files_map: Dict[int, Any] = {}
        if file_ids:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                files_resp = await api.files.file.get(
                    FileGetRequest(ids=file_ids, limit=len(file_ids), offset=0)
                )
            files_map = {int(item.id): item for item in (files_resp.result or []) if item and item.id}

        for file_id in file_ids:
            file_model = files_map.get(int(file_id))
            if not file_model or not file_model.url:
                continue
            caption = None
            if text and not caption_used:
                caption = text
                caption_used = True

            if _is_photo_extension(file_model.extension):
                sent = await bot.send_photo(
                    chat_id=target_chat,
                    photo=str(file_model.url),
                    caption=caption,
                )
            else:
                sent = await bot.send_document(
                    chat_id=target_chat,
                    document=str(file_model.url),
                    caption=caption,
                )
            if not first_sent_id:
                first_sent_id = int(sent.message_id)

        if text and not caption_used:
            sent = await bot.send_message(chat_id=target_chat, text=text)
            if not first_sent_id:
                first_sent_id = int(sent.message_id)

        return first_sent_id

    @classmethod
    async def _handle_chat_message_edited(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return

        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        mapped_id_raw = await cls._redis_get(
            cls._msgmap_regos_to_tg_key(connected_integration_id, message_id)
        )
        mapped_id = _parse_int(mapped_id_raw)

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=chat_id,
                    ids=[message_id],
                    limit=1,
                    offset=0,
                    include_staff_private=True,
                )
            )
            if not response.result:
                return
            msg = response.result[0]
            if not msg:
                return
            if str(msg.external_message_id or "").startswith("tgmsg:"):
                return

        bot = await cls._get_bot(bot_cfg.token)
        target_chat = _tg_chat_id_cast(tg_chat_id)
        text = (msg.text or "").strip()

        if mapped_id and text:
            try:
                await bot.edit_message_text(
                    chat_id=target_chat,
                    message_id=int(mapped_id),
                    text=text,
                )
                return
            except Exception:
                pass

        edited_text = f"(edited)\n{text}".strip()
        sent_id = await cls._send_chat_message_to_telegram(
            bot_cfg=bot_cfg,
            tg_chat_id=tg_chat_id,
            text=edited_text,
            file_ids=msg.file_ids or [],
            connected_integration_id=connected_integration_id,
        )
        if sent_id:
            await cls._redis_set_mapping(
                cls._msgmap_regos_to_tg_key(connected_integration_id, message_id),
                str(sent_id),
            )

    @classmethod
    async def _handle_chat_message_deleted(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return
        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return
        mapped_id_raw = await cls._redis_get(
            cls._msgmap_regos_to_tg_key(connected_integration_id, message_id)
        )
        mapped_id = _parse_int(mapped_id_raw)
        if not mapped_id:
            return
        bot = await cls._get_bot(bot_cfg.token)
        try:
            await bot.delete_message(
                chat_id=_tg_chat_id_cast(tg_chat_id), message_id=int(mapped_id)
            )
        except Exception:
            pass

    @classmethod
    async def _handle_chat_writing(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            return
        target = await cls._resolve_target_by_chat(connected_integration_id, chat_id)
        if not target:
            return
        bot_hash, tg_chat_id = target
        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return

        throttle_key = cls._typing_key(connected_integration_id, bot_hash, tg_chat_id)
        can_send = await cls._redis_set_nx_with_ttl(throttle_key, "1", 3)
        if not can_send:
            return

        bot = await cls._get_bot(bot_cfg.token)
        try:
            await bot.send_chat_action(
                chat_id=_tg_chat_id_cast(tg_chat_id), action="typing"
            )
        except Exception:
            pass

    @classmethod
    async def _handle_lead_closed(
        cls, connected_integration_id: str, runtime: RuntimeConfig, payload: Dict[str, Any]
    ) -> None:
        lead_id = _parse_int(str(payload.get("id") or ""))
        if not lead_id:
            return
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            lead = await api.crm.lead.get_by_id(lead_id)
        if not lead:
            return

        text = runtime.lead_closed_message_template or "Обращение закрыто. Спасибо за обращение."
        if not text.strip():
            return

        bot_hash = str(lead.bot_id or "").strip()
        tg_chat_id = str(lead.external_chat_id or "").strip()
        if not bot_hash or not tg_chat_id:
            if lead.chat_id:
                target = await cls._resolve_target_by_chat(connected_integration_id, str(lead.chat_id))
                if target:
                    bot_hash, tg_chat_id = target
        if not bot_hash or not tg_chat_id:
            return

        bot_cfg = runtime.bots_by_hash.get(bot_hash)
        if not bot_cfg:
            return
        bot = await cls._get_bot(bot_cfg.token)
        await bot.send_message(chat_id=_tg_chat_id_cast(tg_chat_id), text=text)

    @staticmethod
    def _is_longpolling_mode() -> bool:
        return _update_mode_from_value(app_settings.telegram_update_mode) == "longpolling"
