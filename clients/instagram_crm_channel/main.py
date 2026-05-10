from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import hmac
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from fastapi.responses import HTMLResponse, Response

from clients.base import ClientBase
from clients.instagram_crm_channel.storage import (
    ensure_schema as ensure_instagram_db_schema,
    mark_business_map_inactive,
    resolve_ci_by_business_id as resolve_ci_by_business_id_db,
    upsert_business_map,
)
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_ops,
    redis_error_contains,
    redis_expire_if_due,
    redis_sadd_with_ttl,
    redis_stream_add_with_ttl,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)
from schemas.api.chat.chat import ChatGetRequest
from schemas.api.chat.chat_message import (
    ChatMessage,
    ChatMessageAddRequest,
    ChatMessageGetRequest,
    ChatMessageMarkSentRequest,
    ChatMessageTypeEnum,
)
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.client import Client, ClientAddRequest, ClientEditRequest, ClientGetRequest
from schemas.api.crm.ticket import (
    Ticket,
    TicketAddRequest,
    TicketDirectionEnum,
    TicketGetRequest,
    TicketStatusEnum,
)
from schemas.api.integrations.connected_integration import (
    ConnectedIntegrationEditRequest,
    ConnectedIntegrationGetRequest,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("instagram_crm_channel")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[int, asyncio.Task] = {}
_REDIS_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_CLAIM_TS: Dict[str, int] = {}


def _now_ts() -> int:
    return int(time.time())


class InstagramCrmChannelConfig:
    INTEGRATION_KEY = "instagram_crm_channel"
    REDIS_PREFIX = "igc:"

    GRAPH_BASE_URL = "https://graph.instagram.com/v20.0"
    OAUTH_DIALOG_URL = "https://www.instagram.com/oauth/authorize"
    OAUTH_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
    LONG_LIVED_TOKEN_URL = "https://graph.instagram.com/access_token"

    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
    MAP_TTL_SEC = 30 * 24 * 60 * 60
    DEDUPE_TTL_SEC = 24 * 60 * 60
    LOCK_TTL_SEC = 30
    OAUTH_STATE_TTL_SEC = 10 * 60
    WEBHOOK_DEBUG_TTL_SEC = 30
    ACTIVE_CACHE_TTL_SEC = 30
    HTTP_TIMEOUT_SEC = 30
    STREAM_GROUP = "instagram_crm_channel_workers"
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_MAXLEN = max(int(app_settings.instagram_crm_channel_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(app_settings.instagram_crm_channel_stream_batch_size or 0), 1)
    STREAM_WORKERS = max(int(app_settings.instagram_crm_channel_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = max(int(app_settings.instagram_crm_channel_stream_retry_limit or 0), 1)
    ACTIVE_CI_IDS_TTL_SEC = 7 * 24 * 60 * 60
    WORKER_HEARTBEAT_TTL_SEC = 60

    OAUTH_SCOPES = (
        "instagram_business_basic",
        "instagram_business_manage_messages",
    )

    ACTIVE_TICKET_STATUSES = (TicketStatusEnum.Open,)

    SUPPORTED_INBOUND_WEBHOOKS = {"ChatMessageAdded"}

    SETTING_AUTHORIZATION_STATUS = "instagram_authorization_status"


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    instagram_business_account_id: str
    pipeline_id: int
    channel_id: int
    default_responsible_user_id: Optional[int]
    ticket_subject_template: str
    webhook_verify_token: str
    access_token: Optional[str]
    access_token_expires_at: Optional[int]
    username: Optional[str]
    find_active_ticket_by_external_id: bool


@dataclass
class TicketContext:
    client_id: int
    ticket_id: int
    chat_id: str


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text)
    except Exception:
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _row_to_dict(row: Any) -> Dict[str, Any]:
    if isinstance(row, dict):
        return row
    if hasattr(row, "model_dump"):
        try:
            dumped = row.model_dump(mode="json")
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            return {}
    return {}


def _query_get(query: Dict[str, Any], key: str) -> Optional[str]:
    value = query.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    text = str(value or "").strip()
    return text or None


def _headers_ci(headers: Dict[str, Any], key: str) -> Optional[str]:
    key_lower = str(key or "").lower()
    for header_name, header_value in (headers or {}).items():
        if str(header_name or "").lower() == key_lower:
            value = str(header_value or "").strip()
            if value:
                return value
    return None


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_ops)


class InstagramCrmChannelIntegration(ClientBase):
    _ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
    _ACTIVE_CACHE_LOCK = asyncio.Lock()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.connected_integration_id: Optional[str] = None
        self.http_client = httpx.AsyncClient(timeout=InstagramCrmChannelConfig.HTTP_TIMEOUT_SEC)

    async def __aenter__(self) -> "InstagramCrmChannelIntegration":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.http_client.aclose()

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(result=IntegrationErrorModel(error=code, description=description))

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        return f"{InstagramCrmChannelConfig.REDIS_PREFIX}{':'.join(tokens)}"

    @classmethod
    def _settings_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("settings", connected_integration_id)

    @classmethod
    def _ci_active_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("ci_active", connected_integration_id)

    @classmethod
    def _webhooks_subscription_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("webhooks_subscribed", connected_integration_id)

    @classmethod
    def _stream_key(cls, connected_integration_id: Optional[str] = None) -> str:
        _ = connected_integration_id
        return cls._redis_key("stream")

    @classmethod
    def _dlq_stream_key(cls, connected_integration_id: Optional[str] = None) -> str:
        _ = connected_integration_id
        return cls._redis_key("stream", "dlq")

    @classmethod
    def _active_ci_ids_key(cls) -> str:
        return cls._redis_key("active_ci_ids")

    @classmethod
    def _worker_heartbeat_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("worker", "heartbeat", connected_integration_id)

    @classmethod
    def _webhook_debug_key(cls) -> str:
        return cls._redis_key("webhook_debug", str(_now_ts()), uuid.uuid4().hex)

    @staticmethod
    def _active_ci_ids_ttl() -> int:
        return redis_ttl_seconds(InstagramCrmChannelConfig.ACTIVE_CI_IDS_TTL_SEC)

    @staticmethod
    def _normalize_setting_key(key: Any) -> str:
        return str(key or "").strip().lower()

    @classmethod
    def _normalize_settings_map(cls, values: Dict[Any, Any]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for raw_key, raw_value in (values or {}).items():
            key = cls._normalize_setting_key(raw_key)
            if not key:
                continue
            value = str(raw_value or "").strip()
            if key not in normalized or (value and not normalized[key]):
                normalized[key] = value
        return normalized

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_ops.get(key)

    @staticmethod
    async def _redis_set(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> None:
        if not _redis_enabled():
            return
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        await redis_ops.set(key, value, ex=ttl)

    @staticmethod
    async def _redis_set_nx(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> bool:
        if not _redis_enabled():
            return False
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        return bool(await redis_ops.set(key, value, ex=ttl, nx=True))

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if rows:
            await redis_ops.delete(*rows)

    @classmethod
    async def _store_webhook_debug_snapshot(
        cls,
        *,
        envelope: Dict[str, Any],
        body: Any,
        raw_body: Any,
        resolved_ci: Optional[str],
    ) -> None:
        if not _redis_enabled():
            return
        if isinstance(raw_body, bytes):
            raw_text = raw_body.decode("utf-8", errors="replace")
        elif raw_body is None:
            raw_text = ""
        else:
            raw_text = str(raw_body)
        if isinstance(body, bytes):
            body_value: Any = body.decode("utf-8", errors="replace")
        elif isinstance(body, bytearray):
            body_value = bytes(body).decode("utf-8", errors="replace")
        else:
            body_value = body

        payload = {
            "ts": _now_ts(),
            "method": str(envelope.get("method") or ""),
            "path": str(envelope.get("path") or ""),
            "external_path": str(envelope.get("external_path") or ""),
            "connected_integration_id": str(resolved_ci or ""),
            "business_ids": cls._business_ids_from_webhook_body(body),
            "query": envelope.get("query") if isinstance(envelope.get("query"), dict) else {},
            "headers": envelope.get("headers") if isinstance(envelope.get("headers"), dict) else {},
            "body": body_value,
            "raw_body": raw_text,
        }
        await cls._redis_set(
            cls._webhook_debug_key(),
            _json_dumps(payload),
            InstagramCrmChannelConfig.WEBHOOK_DEBUG_TTL_SEC,
            min_ttl_sec=1,
        )

    @classmethod
    def _resolve_stream_ttl(cls) -> int:
        return redis_ttl_seconds(InstagramCrmChannelConfig.STREAM_TTL_SEC)

    @classmethod
    async def _touch_stream_ttl(cls, stream_key: str, *, force: bool = False) -> None:
        if not _redis_enabled():
            return
        await redis_expire_if_due(
            stream_key,
            cls._resolve_stream_ttl(),
            _REDIS_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str) -> None:
        if not _redis_enabled():
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            InstagramCrmChannelConfig.STREAM_GROUP,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )

    @classmethod
    async def _enqueue(cls, stream_key: str, fields: Dict[str, Any]) -> None:
        if not _redis_enabled():
            raise RuntimeError("Redis is not enabled")

        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = _json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)

        await redis_stream_add_with_ttl(
            stream_key,
            serialized,
            maxlen=InstagramCrmChannelConfig.STREAM_MAXLEN,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )

    @classmethod
    async def _mark_ci_active(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        await redis_sadd_with_ttl(cls._active_ci_ids_key(), ci, cls._active_ci_ids_ttl())
        _REDIS_TTL_TOUCH_TS[cls._active_ci_ids_key()] = _now_ts()

    @classmethod
    async def _touch_active_ci_ids_ttl(cls, *, force: bool = False) -> None:
        if not _redis_enabled():
            return
        await redis_expire_if_due(
            cls._active_ci_ids_key(),
            cls._active_ci_ids_ttl(),
            _REDIS_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=60,
            force=force,
        )

    @classmethod
    async def _mark_ci_inactive(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if ci:
            await redis_ops.srem(cls._active_ci_ids_key(), ci)

    @classmethod
    async def _set_worker_heartbeat(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        await redis_ops.setex(
            cls._worker_heartbeat_key(connected_integration_id),
            InstagramCrmChannelConfig.WORKER_HEARTBEAT_TTL_SEC,
            str(_now_ts()),
        )
        await cls._touch_active_ci_ids_ttl()

    @classmethod
    async def _fetch_settings_map(cls, connected_integration_id: str, force_refresh: bool = False) -> Dict[str, str]:
        cache_key = cls._settings_cache_key(connected_integration_id)
        if not force_refresh:
            raw = await cls._redis_get(cache_key)
            if raw:
                try:
                    cached = _json_loads(raw)
                    if isinstance(cached, dict):
                        return cls._normalize_settings_map(cached)
                except Exception:
                    pass

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=connected_integration_id)
            )

        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            data = _row_to_dict(row)
            key = cls._normalize_setting_key(
                data.get("key") if data else getattr(row, "key", "")
            )
            if key:
                raw_value = data.get("value") if data else getattr(row, "value", "")
                value = str(raw_value or "").strip()
                if key not in settings_map or (value and not settings_map[key]):
                    settings_map[key] = value

        await cls._redis_set(cache_key, _json_dumps(settings_map), InstagramCrmChannelConfig.SETTINGS_TTL_SEC)
        return settings_map

    @classmethod
    async def _cache_settings_map(cls, connected_integration_id: str, settings_map: Dict[Any, Any]) -> None:
        await cls._redis_set(
            cls._settings_cache_key(connected_integration_id),
            _json_dumps(cls._normalize_settings_map(settings_map)),
            InstagramCrmChannelConfig.SETTINGS_TTL_SEC,
        )

    @classmethod
    async def _edit_settings(
        cls,
        connected_integration_id: str,
        patch: Dict[str, str],
        *,
        settings_map: Optional[Dict[Any, Any]] = None,
    ) -> Dict[str, str]:
        rows = [
            ConnectedIntegrationSettingEditItem(
                connected_integration_id=connected_integration_id,
                key=str(key),
                value=str(value or ""),
            )
            for key, value in patch.items()
        ]
        if not rows:
            return cls._normalize_settings_map(settings_map or {})
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            await api.integrations.connected_integration_setting.edit(ConnectedIntegrationSettingEditRequest(rows))
        if settings_map is None:
            await cls._redis_delete(cls._settings_cache_key(connected_integration_id))
            return {}

        updated_settings = cls._normalize_settings_map(settings_map)
        updated_settings.update(cls._normalize_settings_map(patch))
        await cls._cache_settings_map(connected_integration_id, updated_settings)
        return updated_settings

    @classmethod
    async def _is_connected_integration_active(cls, connected_integration_id: str, force_refresh: bool = False) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return True

        now = time.monotonic()
        if not force_refresh:
            async with cls._ACTIVE_CACHE_LOCK:
                cached = cls._ACTIVE_CACHE.get(ci)
            if cached and cached[1] > now:
                return cached[0]

            cached_raw = await cls._redis_get(cls._ci_active_cache_key(ci))
            if cached_raw in {"0", "1"}:
                cached_value = cached_raw == "1"
                async with cls._ACTIVE_CACHE_LOCK:
                    cls._ACTIVE_CACHE[ci] = (
                        cached_value,
                        now + InstagramCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
                    )
                return cached_value

        detected: Optional[bool] = None
        last_error: Optional[Exception] = None
        try:
            async with RegosAPI(connected_integration_id=ci) as api:
                response = await api.integrations.connected_integration.get(
                    ConnectedIntegrationGetRequest(
                        connected_integration_ids=[ci],
                        include_name=False,
                        include_schedule=False,
                    )
                )
            if response.ok and isinstance(response.result, list):
                for row in response.result:
                    row_ci = str(getattr(row, "connected_integration_id", "") or "").strip()
                    if row_ci and row_ci != ci:
                        continue
                    row_active = getattr(row, "is_active", None)
                    if row_active is None:
                        continue
                    detected = bool(row_active)
                    break
        except httpx.HTTPStatusError as error:
            last_error = error
            status_code = (
                int(error.response.status_code)
                if error.response is not None
                else None
            )
            if status_code in {401, 403, 404}:
                detected = False
        except Exception as error:
            last_error = error
        if detected is None:
            if last_error is not None:
                raise RuntimeError(
                    f"ConnectedIntegration/Get failed for active check: ci={ci} error={last_error}"
                ) from last_error
            detected = False

        active = bool(detected)
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (active, now + InstagramCrmChannelConfig.ACTIVE_CACHE_TTL_SEC)
        await cls._redis_set(cls._ci_active_cache_key(ci), "1" if active else "0", InstagramCrmChannelConfig.ACTIVE_CACHE_TTL_SEC)
        return active

    @classmethod
    async def _load_runtime(
        cls,
        connected_integration_id: str,
        require_access_token: bool,
        require_business_id: bool = True,
    ) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(connected_integration_id)
        return cls._runtime_from_settings_map(
            connected_integration_id,
            settings_map,
            require_access_token=require_access_token,
            require_business_id=require_business_id,
        )

    @classmethod
    def _runtime_from_settings_map(
        cls,
        connected_integration_id: str,
        settings_map: Dict[Any, Any],
        *,
        require_access_token: bool,
        require_business_id: bool = True,
    ) -> RuntimeConfig:
        settings_map = cls._normalize_settings_map(settings_map)
        business_id = str(settings_map.get("instagram_business_account_id") or "").strip()
        pipeline_id = _to_int(settings_map.get("instagram_pipeline_id"), None)
        channel_id = _to_int(settings_map.get("instagram_channel_id"), None)
        if require_business_id and not business_id:
            raise ValueError("instagram_business_account_id is required")
        if not pipeline_id or pipeline_id <= 0:
            raise ValueError("instagram_pipeline_id must be > 0")
        if not channel_id or channel_id <= 0:
            raise ValueError("instagram_channel_id must be > 0")

        cls._instagram_app_config()

        access_token = str(settings_map.get("instagram_access_token") or "").strip() or None
        if require_access_token and (not business_id or not access_token):
            raise ValueError("Instagram authorization required: instagram_business_account_id and instagram_access_token")

        webhook_verify_token = cls._instagram_webhook_verify_token()
        access_token_expires_at = _to_int(settings_map.get("instagram_access_token_expires_at"), None)
        username = str(settings_map.get("instagram_username") or "").strip() or None

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            instagram_business_account_id=business_id,
            pipeline_id=int(pipeline_id),
            channel_id=int(channel_id),
            default_responsible_user_id=_to_int(settings_map.get("instagram_default_responsible_user_id"), None),
            ticket_subject_template=str(settings_map.get("instagram_ticket_subject_template") or "").strip() or "Instagram {client_id}",
            webhook_verify_token=webhook_verify_token,
            access_token=access_token,
            access_token_expires_at=access_token_expires_at,
            username=username,
            find_active_ticket_by_external_id=_to_bool(settings_map.get("instagram_find_active_ticket_by_external_user"), True),
        )

    @classmethod
    def _instagram_app_config(cls) -> Tuple[str, str, str]:
        app_id = str(app_settings.instagram_app_id or "").strip()
        app_secret = str(app_settings.instagram_app_secret or "").strip()
        redirect_uri = str(app_settings.instagram_redirect_uri or "").strip()
        if not app_id or not app_secret or not redirect_uri:
            raise ValueError("Service Instagram app config is required")
        return app_id, app_secret, redirect_uri

    @classmethod
    def _instagram_webhook_verify_token(cls) -> str:
        verify_token = str(app_settings.instagram_webhook_verify_token or "").strip()
        if not verify_token:
            raise ValueError("Service Instagram webhook verify token is required")
        return verify_token

    @classmethod
    async def _build_oauth_url(cls, connected_integration_id: str) -> str:
        app_id, _, redirect_uri = cls._instagram_app_config()
        nonce = uuid.uuid4().hex
        await cls._store_oauth_state(connected_integration_id, nonce)
        return f"{InstagramCrmChannelConfig.OAUTH_DIALOG_URL}?{urlencode({
            'enable_fb_login': '0',
            'force_authentication': '1',
            'client_id': app_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ','.join(InstagramCrmChannelConfig.OAUTH_SCOPES),
            'state': cls._encode_oauth_state(connected_integration_id, nonce),
        })}"

    @staticmethod
    def _is_runtime_authorized(runtime: RuntimeConfig) -> bool:
        return bool(runtime.instagram_business_account_id and runtime.access_token)

    @classmethod
    def _authorization_settings_patch(
        cls,
        *,
        authorized: bool,
    ) -> Dict[str, str]:
        if authorized:
            return {
                InstagramCrmChannelConfig.SETTING_AUTHORIZATION_STATUS: "authorized",
            }
        return {
            InstagramCrmChannelConfig.SETTING_AUTHORIZATION_STATUS: "authorization_required",
        }

    @classmethod
    async def _authorization_url(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
    ) -> str:
        if cls._is_runtime_authorized(runtime):
            return ""
        return await cls._build_oauth_url(connected_integration_id)

    @classmethod
    async def _write_business_mapping(
        cls,
        *,
        connected_integration_id: str,
        business_id: str,
        username: Optional[str],
        require_persistent_map: bool,
        ) -> None:
        ci = str(connected_integration_id or "").strip()
        business = str(business_id or "").strip()
        if not ci:
            if require_persistent_map:
                raise RuntimeError("connected_integration_id is required for persistent mapping")
            return
        if not business:
            if require_persistent_map:
                raise RuntimeError("instagram_business_account_id is required for persistent mapping")
            return

        await cls._redis_set(
            cls._redis_key("map", "business_ci", business),
            ci,
            InstagramCrmChannelConfig.MAP_TTL_SEC,
        )

        try:
            stored = await upsert_business_map(
                connected_integration_id=ci,
                business_id=business,
                username=username,
                is_active=True,
            )
        except Exception:
            if require_persistent_map:
                raise
            return
        if require_persistent_map and not stored:
            raise RuntimeError("Instagram business mapping was not stored")

    @classmethod
    async def _sync_reverse_indexes(
        cls,
        runtime: RuntimeConfig,
        *,
        persist_business_map: bool = False,
        require_persistent_map: bool = False,
    ) -> None:
        business_id = str(runtime.instagram_business_account_id or "").strip()
        if not business_id:
            if require_persistent_map:
                raise RuntimeError("instagram_business_account_id is required for persistent mapping")
            return

        if persist_business_map or require_persistent_map:
            await cls._write_business_mapping(
                connected_integration_id=runtime.connected_integration_id,
                business_id=business_id,
                username=runtime.username,
                require_persistent_map=require_persistent_map,
            )
            return

        await cls._redis_set(
            cls._redis_key("map", "business_ci", business_id),
            runtime.connected_integration_id,
            InstagramCrmChannelConfig.MAP_TTL_SEC,
        )

    @classmethod
    async def _subscribe_required_webhooks(
        cls,
        connected_integration_id: str,
    ) -> Dict[str, Any]:
        cache_key = cls._webhooks_subscription_cache_key(connected_integration_id)
        if await cls._redis_get(cache_key) == "1":
            return {"status": "cached"}

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration.edit(
                ConnectedIntegrationEditRequest(
                    connected_integration_id=connected_integration_id,
                    webhooks=sorted(InstagramCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS),
                )
            )
        if response.ok:
            await cls._redis_set(cache_key, "1", InstagramCrmChannelConfig.SETTINGS_TTL_SEC)
            return {"status": "ok"}
        logger.warning(
            "Instagram webhook subscription rejected: ci=%s payload=%s",
            connected_integration_id,
            response.result,
        )
        return {"status": "failed", "error": str(response.result)}

    @staticmethod
    def _encode_oauth_state(connected_integration_id: str, nonce: str) -> str:
        payload = _json_dumps({"ci": connected_integration_id, "nonce": nonce}).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_oauth_state(state: str) -> Tuple[Optional[str], Optional[str]]:
        token = str(state or "").strip()
        if not token:
            return None, None
        token += "=" * ((4 - (len(token) % 4)) % 4)
        try:
            payload = _json_loads(base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8"))
        except Exception:
            return None, None
        if not isinstance(payload, dict):
            return None, None
        return str(payload.get("ci") or "").strip() or None, str(payload.get("nonce") or "").strip() or None

    @classmethod
    async def _store_oauth_state(cls, connected_integration_id: str, nonce: str) -> None:
        await cls._redis_set(
            cls._redis_key("oauth_state", nonce),
            connected_integration_id,
            InstagramCrmChannelConfig.OAUTH_STATE_TTL_SEC,
            min_ttl_sec=30,
        )

    @classmethod
    async def _consume_oauth_state(cls, nonce: str) -> Optional[str]:
        key = cls._redis_key("oauth_state", nonce)
        value = await cls._redis_get(key)
        await cls._redis_delete(key)
        return str(value or "").strip() or None

    @staticmethod
    def _client_external_id(runtime: RuntimeConfig, external_user_id: str) -> str:
        return (
            f"ci:{runtime.connected_integration_id}:"
            f"ig:{runtime.instagram_business_account_id}:{external_user_id}"
        )

    @staticmethod
    def _ticket_external_dialog_id(runtime: RuntimeConfig, external_user_id: str) -> str:
        return (
            f"ci:{runtime.connected_integration_id}:"
            f"ig:{runtime.instagram_business_account_id}:{external_user_id}"
        )

    @classmethod
    def _parse_ticket_external_dialog_id(
        cls,
        runtime: RuntimeConfig,
        value: Optional[str],
    ) -> Optional[str]:
        text = str(value or "").strip()
        prefix = (
            f"ci:{runtime.connected_integration_id}:"
            f"ig:{runtime.instagram_business_account_id}:"
        )
        if not text.startswith(prefix):
            return None
        external_user_id = text[len(prefix):].strip()
        return external_user_id or None

    @classmethod
    def _extract_external_user_from_client_external_id(
        cls, runtime: RuntimeConfig, external_id: Optional[str]
    ) -> Optional[str]:
        value = str(external_id or "").strip()
        prefix = (
            f"ci:{runtime.connected_integration_id}:"
            f"ig:{runtime.instagram_business_account_id}:"
        )
        if not value.startswith(prefix):
            return None
        tail = value[len(prefix):].strip()
        return tail or None

    @classmethod
    async def _get_client_by_id(
        cls, runtime: RuntimeConfig, client_id: int
    ) -> Optional[Client]:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.client.get(
                ClientGetRequest(ids=[int(client_id)], limit=1, offset=0),
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        if not rows:
            return None
        return rows[0]

    @classmethod
    async def _find_client_by_instagram_id(
        cls, runtime: RuntimeConfig, external_user_id: str
    ) -> Optional[Client]:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.client.get(
                ClientGetRequest(
                    instagram_ids=[str(external_user_id or "").strip()],
                    limit=20,
                    offset=0,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        valid = [row for row in rows if row and row.id]
        if not valid:
            return None
        return max(valid, key=lambda row: int(row.id or 0))

    @classmethod
    async def _find_client_by_external_id(
        cls, runtime: RuntimeConfig, external_user_id: str
    ) -> Optional[Client]:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.client.get(
                ClientGetRequest(
                    external_ids=[cls._client_external_id(runtime, external_user_id)],
                    limit=1,
                    offset=0,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        if not rows:
            return None
        return rows[0]

    @classmethod
    async def _sync_instagram_client_identifiers(
        cls,
        runtime: RuntimeConfig,
        client: Client,
        external_user_id: str,
    ) -> Client:
        if not client or not client.id:
            return client

        instagram_id = str(external_user_id or "").strip() or None
        external_id = cls._client_external_id(runtime, external_user_id)
        patch: Dict[str, Any] = {}
        if instagram_id and not str(client.instagram_id or "").strip():
            patch["instagram_id"] = instagram_id
        if external_id and not str(client.external_id or "").strip():
            patch["external_id"] = external_id
        if not patch:
            return client

        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.client.edit(
                ClientEditRequest(id=int(client.id), **patch)
            )
        if not response.ok:
            payload = response.result if isinstance(response.result, dict) else {}
            logger.warning(
                "Client/Edit rejected while syncing Instagram identifiers: ci=%s client_id=%s payload=%s",
                runtime.connected_integration_id,
                client.id,
                payload,
            )
            return client
        refreshed = await cls._get_client_by_id(runtime, int(client.id))
        return refreshed or client

    @classmethod
    async def _resolve_or_create_client(
        cls, runtime: RuntimeConfig, external_user_id: str
    ) -> Client:
        existing = await cls._find_client_by_instagram_id(runtime, external_user_id)
        if existing and existing.id:
            return await cls._sync_instagram_client_identifiers(
                runtime,
                existing,
                external_user_id,
            )

        existing = await cls._find_client_by_external_id(runtime, external_user_id)
        if existing and existing.id:
            return await cls._sync_instagram_client_identifiers(
                runtime,
                existing,
                external_user_id,
            )

        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            add_response = await api.crm.client.add(
                ClientAddRequest(
                    external_id=cls._client_external_id(runtime, external_user_id),
                    instagram_id=external_user_id,
                    name=external_user_id,
                )
            )
        if not add_response.ok:
            payload = add_response.result if isinstance(add_response.result, dict) else {}
            # Allow concurrent create and duplicate handling without explicit merge.
            existing = await cls._find_client_by_instagram_id(runtime, external_user_id)
            if existing and existing.id:
                return await cls._sync_instagram_client_identifiers(
                    runtime,
                    existing,
                    external_user_id,
                )
            existing = await cls._find_client_by_external_id(runtime, external_user_id)
            if existing and existing.id:
                return await cls._sync_instagram_client_identifiers(
                    runtime,
                    existing,
                    external_user_id,
                )
            raise RuntimeError(
                "Client/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        new_id = (
            _to_int((add_response.result or {}).get("new_id"), None)
            if isinstance(add_response.result, dict)
            else None
        )
        if not new_id:
            raise RuntimeError("Client/Add did not return new_id")

        created = await cls._get_client_by_id(runtime, int(new_id))
        if not created or not created.id:
            raise RuntimeError(f"Client/Get did not return client after Client/Add: {new_id}")
        return await cls._sync_instagram_client_identifiers(
            runtime,
            created,
            external_user_id,
        )

    @classmethod
    async def _get_ticket_by_id(
        cls, runtime: RuntimeConfig, ticket_id: int
    ) -> Optional[Ticket]:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.get(
                TicketGetRequest(ids=[int(ticket_id)], limit=1, offset=0),
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        if not rows:
            return None
        return rows[0]

    @classmethod
    async def _find_open_ticket_for_client(
        cls,
        runtime: RuntimeConfig,
        client_id: int,
        external_user_id: str,
    ) -> Optional[Ticket]:
        filters = [
            Filter(
                field="external_dialog_id",
                operator=FilterOperator.Equal,
                value=cls._ticket_external_dialog_id(runtime, external_user_id),
            )
        ]
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.get(
                TicketGetRequest(
                    client_ids=[int(client_id)],
                    channel_ids=[int(runtime.channel_id)],
                    statuses=list(InstagramCrmChannelConfig.ACTIVE_TICKET_STATUSES),
                    filters=filters,
                    limit=20,
                    offset=0,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        valid = [row for row in rows if row and row.id and row.chat_id]
        if not valid:
            return None
        return max(valid, key=lambda row: int(row.id or 0))

    @classmethod
    async def _save_mapping(
        cls,
        runtime: RuntimeConfig,
        external_user_id: str,
        client_id: int,
        ticket_id: int,
        chat_id: str,
    ) -> None:
        payload = _json_dumps(
            {
                "external_user_id": external_user_id,
                "client_id": int(client_id),
                "ticket_id": int(ticket_id),
                "chat_id": str(chat_id),
            }
        )
        await cls._redis_set(cls._redis_key("map", "by_user", runtime.connected_integration_id, external_user_id), payload, InstagramCrmChannelConfig.MAP_TTL_SEC)
        await cls._redis_set(cls._redis_key("map", "by_chat", runtime.connected_integration_id, chat_id), payload, InstagramCrmChannelConfig.MAP_TTL_SEC)

    @classmethod
    async def _resolve_mapping_by_user(cls, runtime: RuntimeConfig, external_user_id: str) -> Optional[TicketContext]:
        raw = await cls._redis_get(cls._redis_key("map", "by_user", runtime.connected_integration_id, external_user_id))
        if raw:
            try:
                data = _json_loads(raw)
            except Exception:
                data = {}
            client_id = _to_int(data.get("client_id"), None) if isinstance(data, dict) else None
            ticket_id = _to_int(data.get("ticket_id"), None) if isinstance(data, dict) else None
            chat_id = str(data.get("chat_id") or "").strip() if isinstance(data, dict) else ""
            if ticket_id and chat_id:
                ticket = await cls._get_ticket_by_id(runtime, int(ticket_id))
                if ticket and ticket.status in InstagramCrmChannelConfig.ACTIVE_TICKET_STATUSES and str(ticket.chat_id or "") == chat_id:
                    resolved_client_id = _to_int(client_id, None) or _to_int(ticket.client_id, None)
                    if resolved_client_id:
                        return TicketContext(
                            client_id=int(resolved_client_id),
                            ticket_id=int(ticket_id),
                            chat_id=chat_id,
                        )

        client = await cls._find_client_by_instagram_id(runtime, external_user_id)
        if (not client or not client.id) and runtime.find_active_ticket_by_external_id:
            client = await cls._find_client_by_external_id(runtime, external_user_id)
        if client and client.id:
            ticket = await cls._find_open_ticket_for_client(
                runtime,
                int(client.id),
                external_user_id,
            )
            if ticket and ticket.id and ticket.chat_id:
                await cls._save_mapping(
                    runtime,
                    external_user_id,
                    int(client.id),
                    int(ticket.id),
                    str(ticket.chat_id),
                )
                return TicketContext(
                    client_id=int(client.id),
                    ticket_id=int(ticket.id),
                    chat_id=str(ticket.chat_id),
                )
        return None

    @classmethod
    async def _resolve_external_user_by_chat(cls, runtime: RuntimeConfig, chat_id: str) -> Optional[str]:
        raw = await cls._redis_get(cls._redis_key("map", "by_chat", runtime.connected_integration_id, chat_id))
        if raw:
            try:
                data = _json_loads(raw)
            except Exception:
                data = {}
            if isinstance(data, dict):
                external_user_id = str(data.get("external_user_id") or "").strip()
                if external_user_id:
                    return external_user_id

        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            chat_response = await api.chat.chat.get(
                ChatGetRequest(ids=[chat_id], limit=1, offset=0)
            )
        if not chat_response.ok or not isinstance(chat_response.result, list) or not chat_response.result:
            return None

        row = _row_to_dict(chat_response.result[0])
        participants = row.get("participants") if isinstance(row, dict) else None
        client_id: Optional[int] = None
        ticket_id: Optional[int] = None
        ticket: Optional[Ticket] = None
        linked_entity_type = str(row.get("entity_type") or "").strip().lower()
        linked_entity_id = _to_int(row.get("entity_id"), None)
        if linked_entity_type in {"ticket"} and linked_entity_id:
            ticket_id = int(linked_entity_id)
        if isinstance(participants, list):
            for part in participants:
                if not isinstance(part, dict):
                    continue
                entity_type = str(part.get("entity_type") or "").strip().lower()
                entity_id = _to_int(part.get("entity_id"), None)
                if not entity_id:
                    continue
                if entity_type in {"client", "3"}:
                    client_id = entity_id
                elif entity_type in {"ticket"}:
                    ticket_id = entity_id
        if ticket_id:
            ticket = await cls._get_ticket_by_id(runtime, int(ticket_id))

        if ticket:
            ticket_channel_id = _to_int(ticket.channel_id, None)
            if not ticket_channel_id or int(ticket_channel_id) != int(runtime.channel_id):
                return None
            external_user_id_from_ticket = cls._parse_ticket_external_dialog_id(
                runtime,
                ticket.external_dialog_id,
            )
            if not external_user_id_from_ticket:
                return None
            resolved_client_id = _to_int(ticket.client_id, None) or _to_int(client_id, None)
            if resolved_client_id and ticket.id:
                await cls._save_mapping(
                    runtime,
                    external_user_id_from_ticket,
                    int(resolved_client_id),
                    int(ticket.id),
                    chat_id,
                )
            return external_user_id_from_ticket

        if not client_id and ticket and ticket.client_id:
            client_id = _to_int(ticket.client_id, None)
        if not client_id:
            return None

        client = await cls._get_client_by_id(runtime, int(client_id))
        if not client:
            return None
        external_user_id = cls._extract_external_user_from_client_external_id(
            runtime,
            client.external_id,
        )
        if external_user_id:
            resolved_ticket_id = ticket_id
            if not resolved_ticket_id:
                maybe_ticket = await cls._find_open_ticket_for_client(
                    runtime,
                    int(client_id),
                    external_user_id,
                )
                resolved_ticket_id = _to_int(maybe_ticket.id if maybe_ticket else None, None)
            if resolved_ticket_id:
                await cls._save_mapping(
                    runtime,
                    external_user_id,
                    int(client.id),
                    int(resolved_ticket_id),
                    chat_id,
                )
        return external_user_id

    @classmethod
    def _render_ticket_subject(cls, runtime: RuntimeConfig, external_user_id: str) -> str:
        template = str(runtime.ticket_subject_template or "").strip() or "Instagram {client_id}"
        try:
            subject = template.format(client_id=external_user_id, external_user_id=external_user_id)
        except Exception:
            subject = template
        return str(subject or "").strip() or f"Instagram {external_user_id}"

    @classmethod
    async def _create_ticket_context(
        cls, runtime: RuntimeConfig, external_user_id: str
    ) -> TicketContext:
        client = await cls._resolve_or_create_client(runtime, external_user_id)
        if not client.id:
            raise RuntimeError("Client id is empty after resolve/create")
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.add(
                TicketAddRequest(
                    client_id=int(client.id),
                    channel_id=int(runtime.channel_id),
                    direction=TicketDirectionEnum.Inbound,
                    external_dialog_id=cls._ticket_external_dialog_id(runtime, external_user_id),
                    responsible_user_id=runtime.default_responsible_user_id,
                    subject=cls._render_ticket_subject(runtime, external_user_id),
                )
            )
        if not response.ok:
            payload = response.result if isinstance(response.result, dict) else {}
            raise RuntimeError(
                "Ticket/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        ticket_id = (
            _to_int((response.result or {}).get("new_id"), None)
            if isinstance(response.result, dict)
            else None
        )
        if not ticket_id:
            raise RuntimeError("Ticket/Add did not return new_id")

        ticket = await cls._get_ticket_by_id(runtime, int(ticket_id))
        if not ticket or not ticket.chat_id:
            raise RuntimeError(f"Ticket {ticket_id} has no chat_id")
        return TicketContext(
            client_id=int(client.id),
            ticket_id=int(ticket_id),
            chat_id=str(ticket.chat_id),
        )

    @classmethod
    async def _resolve_or_create_ticket(cls, runtime: RuntimeConfig, external_user_id: str) -> TicketContext:
        cached = await cls._resolve_mapping_by_user(runtime, external_user_id)
        if cached:
            return cached

        lock_key = cls._redis_key("lock", "ticket_create", runtime.connected_integration_id, external_user_id)
        lock_token = None
        if _redis_enabled():
            token = uuid.uuid4().hex
            if await cls._redis_set_nx(
                lock_key,
                token,
                InstagramCrmChannelConfig.LOCK_TTL_SEC,
                10,
            ):
                lock_token = token
            else:
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    cached = await cls._resolve_mapping_by_user(runtime, external_user_id)
                    if cached:
                        return cached
        try:
            cached = await cls._resolve_mapping_by_user(runtime, external_user_id)
            if cached:
                return cached
            context = await cls._create_ticket_context(runtime, external_user_id)
            await cls._save_mapping(
                runtime,
                external_user_id,
                context.client_id,
                context.ticket_id,
                context.chat_id,
            )
            return context
        finally:
            if lock_token:
                if await cls._redis_get(lock_key) == lock_token:
                    await cls._redis_delete(lock_key)

    @staticmethod
    def _is_internal_external_message(external_message_id: Optional[str]) -> bool:
        value = str(external_message_id or "").strip().lower()
        return value.startswith("igin:") or value.startswith("igout:")

    @staticmethod
    def _inbound_external_message_id(runtime: RuntimeConfig, external_user_id: str, message_id: str) -> str:
        return f"igin:{runtime.instagram_business_account_id}:{external_user_id}:{message_id}"[:150]

    @staticmethod
    def _outbound_external_message_id(runtime: RuntimeConfig, external_user_id: str, message_id: str) -> str:
        return f"igout:{runtime.instagram_business_account_id}:{external_user_id}:{message_id}"[:150]

    @staticmethod
    def _extract_message_text(event: Dict[str, Any]) -> Optional[str]:
        message = event.get("message") if isinstance(event, dict) else None
        if isinstance(message, dict):
            text = str(message.get("text") or "").strip()
            if text:
                return text
            attachments = message.get("attachments")
            if isinstance(attachments, list) and attachments:
                return "Attachment"
        postback = event.get("postback") if isinstance(event, dict) else None
        if isinstance(postback, dict):
            payload = str(postback.get("payload") or "").strip()
            if payload:
                return payload
        return None

    @classmethod
    async def _post_chat_message(cls, runtime: RuntimeConfig, ticket_ctx: TicketContext, external_user_id: str, text: str, message_id: str) -> None:
        external_message_id = cls._inbound_external_message_id(runtime, external_user_id, message_id)
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=ticket_ctx.chat_id,
                    author_entity_type="Client",
                    author_entity_id=ticket_ctx.client_id,
                    message_type=ChatMessageTypeEnum.Regular,
                    text=text,
                    external_message_id=external_message_id,
                ),
            )
        if not response.ok:
            payload = _row_to_dict(response.result)
            raise RuntimeError(f"ChatMessage/Add rejected: error={payload.get('error')} description={payload.get('description')}")

    @classmethod
    def _extract_messaging_events(cls, body: Any, runtime: RuntimeConfig) -> List[Dict[str, Any]]:
        if not isinstance(body, dict):
            return []
        obj = str(body.get("object") or "").strip().lower()
        if obj and obj != "instagram":
            return []

        events: List[Dict[str, Any]] = []
        direct_value = body.get("value")
        if str(body.get("field") or "").strip() == "messages" and isinstance(direct_value, dict):
            if cls._event_targets_business(direct_value, runtime.instagram_business_account_id):
                events.append(direct_value)

        for entry in body.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or "").strip()
            if entry_id and entry_id != runtime.instagram_business_account_id:
                continue
            for event in entry.get("messaging") or []:
                if isinstance(event, dict):
                    events.append(event)
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                if str(change.get("field") or "").strip() != "messages":
                    continue
                value = change.get("value")
                if isinstance(value, dict) and cls._event_targets_business(value, runtime.instagram_business_account_id):
                    events.append(value)
        return events

    @staticmethod
    def _event_targets_business(event: Dict[str, Any], business_id: str) -> bool:
        expected = str(business_id or "").strip()
        recipient = event.get("recipient") if isinstance(event, dict) else None
        actual = str((recipient or {}).get("id") or "").strip() if isinstance(recipient, dict) else ""
        return not actual or not expected or actual == expected

    @classmethod
    def _business_ids_from_webhook_body(cls, body: Any) -> List[str]:
        if not isinstance(body, dict):
            return []

        ids: List[str] = []

        def add(value: Any) -> None:
            text = str(value or "").strip()
            if text and text not in ids:
                ids.append(text)

        def add_event_recipient(event: Any) -> None:
            if not isinstance(event, dict):
                return
            recipient = event.get("recipient")
            if isinstance(recipient, dict):
                add(recipient.get("id"))

        direct_value = body.get("value")
        if str(body.get("field") or "").strip() == "messages" and isinstance(direct_value, dict):
            add_event_recipient(direct_value)

        for entry in body.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            add(entry.get("id"))
            for event in entry.get("messaging") or []:
                add_event_recipient(event)
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                value = change.get("value")
                add_event_recipient(value)
        return ids

    @classmethod
    async def _process_inbound_event(cls, runtime: RuntimeConfig, event: Dict[str, Any]) -> str:
        message = event.get("message") if isinstance(event, dict) else None
        if not isinstance(message, dict):
            return "ignored_no_message"
        if _to_bool(message.get("is_echo"), False):
            return "ignored_echo"

        sender = event.get("sender") if isinstance(event, dict) else None
        external_user_id = str((sender or {}).get("id") or "").strip() if isinstance(sender, dict) else ""
        if not external_user_id:
            return "ignored_no_sender"
        if external_user_id == runtime.instagram_business_account_id:
            return "ignored_own_sender"

        message_id = str(message.get("mid") or message.get("id") or "").strip()
        if not message_id:
            message_id = hashlib.md5(_json_dumps(event).encode("utf-8")).hexdigest()

        dedupe_key = cls._redis_key("dedupe", "inbound", runtime.connected_integration_id, message_id)
        dedupe_acquired = False
        if _redis_enabled():
            dedupe_acquired = await cls._redis_set_nx(
                dedupe_key,
                "1",
                InstagramCrmChannelConfig.DEDUPE_TTL_SEC,
            )
            if not dedupe_acquired:
                return "ignored_duplicate"

        text = cls._extract_message_text(event)
        if not text:
            return "ignored_empty"

        try:
            ticket_ctx = await cls._resolve_or_create_ticket(runtime, external_user_id)
            await cls._post_chat_message(runtime, ticket_ctx, external_user_id, text, message_id)
            return "accepted"
        except Exception:
            if dedupe_acquired:
                await cls._redis_delete(dedupe_key)
            raise

    @classmethod
    async def _process_instagram_webhook_body(
        cls,
        runtime: RuntimeConfig,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        events = cls._extract_messaging_events(body, runtime)
        if not events:
            return {"status": "ignored", "reason": "no_supported_events"}

        accepted = 0
        ignored = 0
        reasons: Dict[str, int] = {}
        errors: List[str] = []
        for event in events:
            try:
                decision = await cls._process_inbound_event(runtime, event)
                if decision == "accepted":
                    accepted += 1
                else:
                    ignored += 1
                    reasons[decision] = reasons.get(decision, 0) + 1
            except Exception as error:
                ignored += 1
                error_key = f"error:{type(error).__name__}"
                reasons[error_key] = reasons.get(error_key, 0) + 1
                errors.append(str(error))
                logger.exception("Inbound Instagram event failed: ci=%s", runtime.connected_integration_id)

        if errors:
            raise RuntimeError("; ".join(errors[:3]))
        return {
            "status": "accepted" if accepted else "ignored",
            "accepted": accepted,
            "ignored": ignored,
            "ignored_reasons": reasons,
        }

    async def _instagram_exchange_code(self, code: str) -> Tuple[str, str]:
        app_id, app_secret, redirect_uri = self._instagram_app_config()
        response = await self.http_client.post(
            InstagramCrmChannelConfig.OAUTH_TOKEN_URL,
            data={
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        token = str(payload.get("access_token") or "").strip()
        user_id = str(payload.get("user_id") or "").strip()
        if not token or not user_id:
            raise RuntimeError("Instagram OAuth token exchange did not return access_token and user_id")
        return token, user_id

    async def _instagram_exchange_long_lived(self, short_token: str) -> Tuple[str, Optional[int]]:
        _, app_secret, _ = self._instagram_app_config()
        response = await self.http_client.get(
            InstagramCrmChannelConfig.LONG_LIVED_TOKEN_URL,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": app_secret,
                "access_token": short_token,
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise RuntimeError("Instagram long-lived token exchange did not return access_token")
        expires_in = _to_int(payload.get("expires_in"), None)
        expires_at = _now_ts() + int(expires_in) if expires_in and expires_in > 0 else None
        return token, expires_at

    async def _instagram_resolve_account(
        self,
        runtime: RuntimeConfig,
        access_token: str,
        oauth_user_id: str,
    ) -> Tuple[str, Optional[str]]:
        response = await self.http_client.get(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/me",
            params={
                "access_token": access_token,
                "fields": "user_id,username,account_type",
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        account_id = str(
            payload.get("user_id")
            or payload.get("id")
            or oauth_user_id
            or ""
        ).strip()
        username = str(payload.get("username") or "").strip() or None
        if not account_id:
            raise RuntimeError("Instagram account id was not returned")
        if runtime.instagram_business_account_id and account_id != runtime.instagram_business_account_id:
            raise RuntimeError("Authorized Instagram account does not match configured instagram_business_account_id")
        return account_id, username

    async def _instagram_send_text_message(self, runtime: RuntimeConfig, external_user_id: str, text: str) -> Optional[str]:
        if not runtime.instagram_business_account_id or not runtime.access_token:
            raise RuntimeError("Instagram authorization is missing")

        response = await self.http_client.post(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/{runtime.instagram_business_account_id}/messages",
            params={"access_token": runtime.access_token},
            json={
                "recipient": {"id": external_user_id},
                "message": {"text": text},
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if isinstance(payload, dict):
            direct = str(payload.get("message_id") or "").strip()
            if direct:
                return direct
            rows = payload.get("messages")
            if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                return str(rows[0].get("id") or "").strip() or None
        return None

    @staticmethod
    def _verify_instagram_signature(
        headers: Dict[str, Any],
        raw_body: Any,
        app_secret: str,
    ) -> bool:
        signature_header = _headers_ci(headers, "x-hub-signature-256")
        if not signature_header or not str(signature_header).startswith("sha256="):
            return False
        if isinstance(raw_body, bytes):
            body_bytes = raw_body
        elif isinstance(raw_body, str):
            body_bytes = raw_body.encode("utf-8")
        else:
            return False
        expected = hmac.new(
            str(app_secret or "").encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        provided = str(signature_header).split("=", 1)[1].strip()
        return bool(provided) and hmac.compare_digest(provided, expected)

    @classmethod
    def _normalize_regos_webhook_payload(cls, action: Optional[str], data: Optional[Dict[str, Any]], extra: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str]]:
        action_value = str(action or "").strip()
        payload = data if isinstance(data, dict) else {}
        event_id = str(extra.get("event_id") or "").strip() or None

        if action_value and action_value != "HandleWebhook":
            if not event_id:
                event_id = str(payload.get("event_id") or "").strip() or None
            return action_value, payload, event_id

        nested_action = str(payload.get("action") or "").strip()
        nested_payload = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if not event_id:
            event_id = str(payload.get("event_id") or "").strip() or str(nested_payload.get("event_id") or "").strip() or None
        return nested_action, nested_payload, event_id

    @classmethod
    async def _load_chat_message(cls, connected_integration_id: str, chat_id: str, message_id: str) -> Optional[ChatMessage]:
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
        if not response.ok or not isinstance(response.result, list) or not response.result:
            return None
        row = response.result[0]
        if isinstance(row, ChatMessage):
            return row
        try:
            return ChatMessage.model_validate(row)
        except Exception:
            return None

    @classmethod
    async def _mark_chat_message_sent(cls, connected_integration_id: str, message_id: str, external_message_id: str) -> None:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.mark_sent(
                ChatMessageMarkSentRequest(
                    id=message_id,
                    external_message_id=external_message_id,
                )
            )
        if not response.ok:
            logger.warning("ChatMessage/MarkSent rejected: ci=%s message_id=%s payload=%s", connected_integration_id, message_id, response.result)

    async def _process_regos_chat_message_added(self, runtime: RuntimeConfig, payload: Dict[str, Any], event_id: Optional[str]) -> Dict[str, Any]:
        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return {"status": "ignored", "reason": "missing_chat_or_message_id"}

        dedupe_identity = str(event_id or message_id).strip()
        dedupe_key = self._redis_key("dedupe", "outbound", runtime.connected_integration_id, dedupe_identity)
        dedupe_set = await self._redis_set_nx(dedupe_key, "1", InstagramCrmChannelConfig.DEDUPE_TTL_SEC)
        if _redis_enabled() and not dedupe_set:
            return {"status": "ignored", "reason": "duplicate_event"}

        try:
            external_user_id = await self._resolve_external_user_by_chat(runtime, chat_id)
            if not external_user_id:
                return {"status": "ignored", "reason": "chat_mapping_not_found"}

            chat_message = await self._load_chat_message(runtime.connected_integration_id, chat_id, message_id)
            if not chat_message:
                return {"status": "ignored", "reason": "chat_message_not_found"}
            if self._is_internal_external_message(chat_message.external_message_id):
                return {"status": "ignored", "reason": "internal_message"}
            if chat_message.message_type != ChatMessageTypeEnum.Regular:
                return {"status": "ignored", "reason": f"unsupported_message_type:{chat_message.message_type}"}

            author_type = str(chat_message.author_entity_type or "").strip().lower()
            if author_type not in {"user", "1"}:
                return {"status": "ignored", "reason": f"unsupported_author:{chat_message.author_entity_type}"}

            text = str(chat_message.text or "").strip()
            if not text:
                text = "Attachment" if chat_message.file_ids else ""
            if not text:
                return {"status": "ignored", "reason": "empty_message"}

            remote_message_id = await self._instagram_send_text_message(runtime, external_user_id, text)
            external_message_id = self._outbound_external_message_id(runtime, external_user_id, remote_message_id or message_id)
            await self._mark_chat_message_sent(runtime.connected_integration_id, message_id, external_message_id)
            return {"status": "accepted", "chat_id": chat_id, "message_id": message_id}
        except Exception:
            if _redis_enabled():
                await self._redis_delete(dedupe_key)
            raise

    def _resolve_ci_from_envelope(self, envelope: Dict[str, Any]) -> Optional[str]:
        instance_ci = str(getattr(self, "connected_integration_id", "") or "").strip()
        if instance_ci:
            return instance_ci

        headers = envelope.get("headers") or {}
        query = envelope.get("query") or {}
        ci = _headers_ci(headers, "Connected-Integration-Id")
        if ci:
            return ci
        for key in ("connected_integration_id", "ci"):
            ci = _query_get(query, key)
            if ci:
                return ci

        body = envelope.get("body")
        if isinstance(body, dict):
            ci = str(body.get("connected_integration_id") or "").strip()
            if ci:
                return ci
        return None

    @classmethod
    async def _resolve_ci_by_business_id(cls, business_id: str) -> Optional[str]:
        value = await cls._redis_get(cls._redis_key("map", "business_ci", business_id))
        resolved = str(value or "").strip()
        if resolved:
            return resolved

        expected = str(business_id or "").strip()
        if not expected:
            return None
        try:
            resolved = str(await resolve_ci_by_business_id_db(expected) or "").strip()
        except Exception as error:
            logger.warning("Failed to resolve Instagram business mapping from MariaDB: business_id=%s error=%s", expected, error)
            resolved = ""
        if resolved:
            await cls._redis_set(
                cls._redis_key("map", "business_ci", expected),
                resolved,
                InstagramCrmChannelConfig.MAP_TTL_SEC,
            )
            return resolved

        if not _redis_enabled():
            return None
        for ci in await cls._active_ci_ids():
            try:
                runtime = await cls._load_runtime(
                    ci,
                    require_access_token=False,
                    require_business_id=False,
                )
                await cls._sync_reverse_indexes(runtime, persist_business_map=True)
            except Exception:
                continue
            if runtime.instagram_business_account_id == expected:
                return ci
        return None

    @classmethod
    async def _active_ci_ids(cls) -> List[str]:
        if not _redis_enabled():
            return []
        try:
            raw_ids = await redis_ops.smembers(cls._active_ci_ids_key())
        except Exception as error:
            logger.warning("Failed to read active Instagram integrations set: %s", error)
            return []
        return sorted(
            str(value or "").strip()
            for value in (raw_ids or set())
            if str(value or "").strip()
        )

    @classmethod
    async def _enqueue_event(
        cls,
        connected_integration_id: str,
        *,
        kind: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        attempt: int = 0,
        last_error: Optional[str] = None,
    ) -> None:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        await cls._ensure_stream_workers()
        await cls._mark_ci_active(ci)
        await cls._enqueue(
            cls._stream_key(),
            {
                "connected_integration_id": ci,
                "kind": kind,
                "payload": payload,
                "event_id": event_id or "",
                "attempt": str(max(int(attempt), 0)),
                "last_error": last_error or "",
                "enqueued_at": str(_now_ts()),
            },
        )

    @classmethod
    async def _ensure_stream_workers(cls) -> None:
        if not _redis_enabled():
            return
        await cls._ensure_consumer_group(cls._stream_key())
        async with _MANAGER_LOCK:
            for worker_index in range(InstagramCrmChannelConfig.STREAM_WORKERS):
                task = _WORKER_TASKS.get(worker_index)
                if task and not task.done():
                    continue
                _WORKER_TASKS[worker_index] = asyncio.create_task(
                    cls._stream_worker_loop(worker_index),
                    name=f"instagram_crm_channel_stream_{worker_index}",
                )

    @classmethod
    async def _ensure_stream_worker(cls, connected_integration_id: str) -> None:
        _ = connected_integration_id
        await cls._ensure_stream_workers()

    @classmethod
    async def _stop_stream_worker(cls, connected_integration_id: str) -> None:
        _ = connected_integration_id
        return

    @classmethod
    async def shutdown_all(cls) -> None:
        async with _MANAGER_LOCK:
            worker_tasks = list(_WORKER_TASKS.values())
            _WORKER_TASKS.clear()
        for task in worker_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping Instagram background task")

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not _redis_enabled():
            return {"total": 0, "restored": 0, "failed": 0}

        ci_ids = await cls._active_ci_ids()
        if not ci_ids:
            logger.info("Instagram auto-restore: no active integrations found")
            return {"total": 0, "restored": 0, "failed": 0}
        await cls._touch_active_ci_ids_ttl(force=True)
        await cls._ensure_stream_workers()

        restored = 0
        failed = 0
        for ci in ci_ids:
            try:
                if not await cls._is_connected_integration_active(ci, force_refresh=True):
                    await cls._mark_ci_inactive(ci)
                    failed += 1
                    logger.info("Instagram auto-restore skipped inactive integration: ci=%s", ci)
                    continue
                runtime = await cls._load_runtime(
                    ci,
                    require_access_token=False,
                    require_business_id=False,
                )
                await cls._sync_reverse_indexes(
                    runtime,
                    persist_business_map=True,
                    require_persistent_map=cls._is_runtime_authorized(runtime),
                )
                await cls._mark_ci_active(ci)
                restored += 1
            except Exception as error:
                failed += 1
                logger.exception("Instagram auto-restore failed: ci=%s error=%s", ci, error)

        logger.info(
            "Instagram auto-restore completed: total=%s restored=%s failed=%s",
            len(ci_ids),
            restored,
            failed,
        )
        return {"total": len(ci_ids), "restored": restored, "failed": failed}

    @classmethod
    def _stream_entry_attempt(cls, fields: Dict[str, Any]) -> int:
        return max(_to_int(fields.get("attempt"), 0) or 0, 0)

    @classmethod
    async def _ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_ops.xack(
            stream_key,
            InstagramCrmChannelConfig.STREAM_GROUP,
            entry_id,
        )

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                InstagramCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=InstagramCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=InstagramCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key)
                return []
            logger.warning("Instagram stream xautoclaim failed: stream=%s error=%s", stream_key, error)
            return []

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        stream_key = cls._stream_key()
        consumer = f"{_INSTANCE_ID}:{int(worker_index)}"
        worker = cls()
        logger.info("Instagram stream worker started: worker_index=%s stream=%s", worker_index, stream_key)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._touch_active_ci_ids_ttl()
                    await cls._touch_stream_ttl(stream_key)

                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= InstagramCrmChannelConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        for entry_id, fields in await cls._process_claimed_entries(stream_key, consumer):
                            await cls._process_stream_entry(
                                worker=worker,
                                stream_key=stream_key,
                                entry_id=entry_id,
                                fields=fields,
                            )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=InstagramCrmChannelConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=InstagramCrmChannelConfig.STREAM_BATCH_SIZE,
                            block=InstagramCrmChannelConfig.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(stream_key)
                            continue
                        raise

                    for _, entries in records or []:
                        for entry_id, fields in entries or []:
                            await cls._process_stream_entry(
                                worker=worker,
                                stream_key=stream_key,
                                entry_id=str(entry_id),
                                fields=fields if isinstance(fields, dict) else {},
                            )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception("Instagram stream worker error: worker_index=%s error=%s", worker_index, error)
                    await asyncio.sleep(2)
        finally:
            try:
                await worker.http_client.aclose()
            except Exception:
                logger.exception("Error while closing Instagram worker HTTP client")
            async with _MANAGER_LOCK:
                current = _WORKER_TASKS.get(worker_index)
                if current is asyncio.current_task():
                    _WORKER_TASKS.pop(worker_index, None)

    @classmethod
    def _decode_stream_payload(cls, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            payload = _json_loads(str(raw or ""))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    async def _process_stream_entry(
        cls,
        *,
        worker: "InstagramCrmChannelIntegration",
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        ci = str(fields.get("connected_integration_id") or "").strip()
        kind = str(fields.get("kind") or "").strip()
        payload = cls._decode_stream_payload(fields.get("payload"))
        event_id = str(fields.get("event_id") or "").strip() or None
        if not ci or kind not in {"instagram_in", "regos_in"} or not payload:
            logger.warning("Instagram stream entry has invalid payload: entry_id=%s fields=%s", entry_id, fields)
            await cls._ack_stream_entry(stream_key, entry_id)
            return
        worker.connected_integration_id = ci
        if not await cls._is_connected_integration_active(ci):
            await cls._mark_ci_inactive(ci)
            logger.info("Instagram stream entry skipped for inactive integration: ci=%s entry_id=%s", ci, entry_id)
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        attempt = cls._stream_entry_attempt(fields)
        try:
            if kind == "instagram_in":
                runtime = await cls._load_runtime(ci, require_access_token=False)
                await cls._sync_reverse_indexes(runtime)
                result = await cls._process_instagram_webhook_body(runtime, payload)
            else:
                runtime = await cls._load_runtime(ci, require_access_token=True)
                await cls._sync_reverse_indexes(runtime)
                result = await worker._process_regos_chat_message_added(runtime, payload, event_id)

            logger.info(
                "Instagram stream job processed: ci=%s kind=%s entry_id=%s status=%s",
                ci,
                kind,
                entry_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await cls._ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            next_attempt = attempt + 1
            if next_attempt >= InstagramCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(_now_ts())
                dlq_payload["error"] = str(error)
                await cls._enqueue(cls._dlq_stream_key(), dlq_payload)
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "Instagram stream job moved to DLQ: ci=%s kind=%s entry_id=%s error=%s",
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
                event_id=event_id,
                attempt=next_attempt,
                last_error=str(error),
            )
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "Instagram stream job requeued: ci=%s kind=%s entry_id=%s attempt=%s error=%s",
                ci,
                kind,
                entry_id,
                next_attempt,
                error,
            )

    @classmethod
    def _ui_message_page(cls, text: str, *, status: str = "info") -> str:
        title = "Подключение Instagram"
        safe_text = html.escape(str(text))
        safe_status = "ok" if status == "ok" else "warn"
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #172033; background: #f5f7fb; }}
    main {{ max-width: 680px; margin: 48px auto; padding: 0 20px; }}
    section {{ background: #fff; border: 1px solid #dce3ee; border-radius: 8px; padding: 24px; }}
    h1 {{ font-size: 24px; margin: 0 0 12px; }}
    p {{ margin: 0; color: #536176; line-height: 1.5; }}
    .badge {{ display: inline-block; margin-bottom: 16px; padding: 8px 10px; border-radius: 6px; font-weight: 600; }}
    .ok {{ background: #e7f7ee; color: #0d6b3f; }}
    .warn {{ background: #fff4d8; color: #7a5200; }}
  </style>
</head>
<body>
  <main>
    <section>
      <span class="badge {safe_status}">Instagram</span>
      <h1>{html.escape(title)}</h1>
      <p>{safe_text}</p>
    </section>
  </main>
</body>
</html>"""

    @classmethod
    def _ui_settings_error_message(cls, error: Exception) -> str:
        text = str(error or "")
        if "instagram_pipeline_id" in text:
            return "Выберите воронку CRM для обращений из Instagram."
        if "instagram_channel_id" in text:
            return "Выберите CRM-канал для обращений из Instagram."
        if "Service Instagram app config" in text or "Service Instagram webhook verify token" in text:
            return "Подключение Instagram пока недоступно. Обратитесь к администратору."
        if "Instagram authorization required" in text or "instagram_business_account_id" in text:
            return "Подключите аккаунт Instagram, чтобы начать получать и отправлять сообщения."
        return "Не удалось открыть подключение Instagram. Проверьте настройки интеграции и попробуйте снова."

    @staticmethod
    def _ui_page(
        *,
        title: str,
        authorized: bool,
        authorization_url: str,
        username: Optional[str],
        connected_integration_id: str,
    ) -> str:
        safe_title = html.escape(title)
        account_name = str(username or "").strip()
        account_label = f"@{account_name.lstrip('@')}" if account_name else "Аккаунт Instagram"
        safe_account = html.escape(account_label)
        safe_url = html.escape(authorization_url or "", quote=True)
        safe_ci = html.escape(connected_integration_id or "", quote=True)
        status_text = (
            "Аккаунт Instagram подключен. Сообщения клиентов будут поступать в CRM, а ответы операторов отправляться в Instagram."
            if authorized
            else "Подключите аккаунт Instagram, чтобы получать сообщения клиентов в CRM и отвечать им из карточки обращения."
        )
        safe_status_text = html.escape(status_text)
        action_html = (
            f"""
            <div class="actions">
              <span class="badge ok">Подключено</span>
              <form method="get">
                <input type="hidden" name="ci" value="{safe_ci}">
                <input type="hidden" name="action" value="disconnect">
                <button class="button danger" type="submit" onclick="return confirm('Отключить Instagram?')">Отключить</button>
              </form>
            </div>
            """
            if authorized
            else f"<a class='button' href='{safe_url}'>Подключить Instagram</a>"
            if authorization_url
            else "<span class='badge warn'>Подключение временно недоступно</span>"
        )
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #172033; background: #f5f7fb; }}
    main {{ max-width: 760px; margin: 40px auto; padding: 0 20px; }}
    section {{ background: #fff; border: 1px solid #dce3ee; border-radius: 8px; padding: 24px; }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    p {{ margin: 0 0 20px; color: #536176; }}
    .account {{ margin: 0 0 22px; color: #172033; font-weight: 600; overflow-wrap: anywhere; }}
    .actions {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }}
    form {{ margin: 0; }}
    .button {{ display: inline-block; padding: 10px 14px; border: 0; border-radius: 6px; background: #1769e0; color: #fff; text-decoration: none; font: inherit; font-weight: 600; cursor: pointer; }}
    .danger {{ background: #c93535; }}
    .badge {{ display: inline-block; padding: 8px 10px; border-radius: 6px; font-weight: 600; }}
    .ok {{ background: #e7f7ee; color: #0d6b3f; }}
    .warn {{ background: #fff4d8; color: #7a5200; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>{safe_title}</h1>
      <p>{safe_status_text}</p>
      <p class="account">{safe_account if authorized else "Аккаунт не подключен"}</p>
      {action_html}
    </section>
  </main>
</body>
</html>"""

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        ci = str(self.connected_integration_id)
        if not await self._is_connected_integration_active(ci):
            return self._error_response(1004, f"ConnectedIntegration '{ci}' is inactive").dict()

        try:
            await ensure_instagram_db_schema()
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_business_id=False,
            )
            await self._sync_reverse_indexes(
                runtime,
                persist_business_map=True,
                require_persistent_map=self._is_runtime_authorized(runtime),
            )
            subscribe_result = await self._subscribe_required_webhooks(ci)
            authorized = self._is_runtime_authorized(runtime)
            if authorized:
                authorization_url = ""
            else:
                authorization_url = await self._build_oauth_url(ci)
            await self._mark_ci_active(ci)
            try:
                await self._ensure_stream_workers()
            except Exception:
                await self._mark_ci_inactive(ci)
                raise
        except Exception as error:
            logger.exception("Instagram connect failed: ci=%s", ci)
            return self._error_response(1001, str(error)).dict()

        return {
            "status": "connected",
            "authorized": authorized,
            "instagram_business_account_id": runtime.instagram_business_account_id,
            "verify_token": runtime.webhook_verify_token,
            "webhooks_subscription": subscribe_result,
            "queue_enabled": True,
            "authorization_url": authorization_url,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id)
        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_business_id=False,
            )
            keys = []
            if runtime.instagram_business_account_id:
                keys.append(self._redis_key("map", "business_ci", runtime.instagram_business_account_id))
            try:
                await mark_business_map_inactive(
                    connected_integration_id=ci,
                    business_id=runtime.instagram_business_account_id or None,
                )
            except Exception as error:
                logger.warning(
                    "Failed to mark Instagram business mapping inactive: ci=%s error=%s",
                    ci,
                    error,
                )
            if keys:
                await self._redis_delete(*keys)
        except Exception:
            try:
                await mark_business_map_inactive(
                    connected_integration_id=ci,
                )
            except Exception as error:
                logger.warning(
                    "Failed to mark Instagram business mappings inactive by ci: ci=%s error=%s",
                    ci,
                    error,
                )
        await self._edit_settings(
            ci,
            {
                "instagram_business_account_id": "",
                "instagram_access_token": "",
                "instagram_access_token_expires_at": "",
                "instagram_username": "",
                **self._authorization_settings_patch(authorized=False),
            },
        )
        await self._mark_ci_inactive(ci)
        await self._redis_delete(
            self._settings_cache_key(ci),
            self._ci_active_cache_key(ci),
            self._webhooks_subscription_cache_key(ci),
        )
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Any:
        _ = settings
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        await self._redis_delete(self._settings_cache_key(ci))
        return {"status": "settings updated"}

    async def handle_ui(self, envelope: Dict[str, Any]) -> Any:
        if str(envelope.get("method") or "").upper() != "GET":
            return HTMLResponse(
                self._ui_message_page("Эта страница доступна только для просмотра."),
                status_code=405,
            )
        if not _redis_enabled():
            return HTMLResponse(
                self._ui_message_page("Подключение Instagram временно недоступно. Попробуйте позже."),
                status_code=503,
            )

        query = envelope.get("query") or {}
        ci = self._resolve_ci_from_envelope(envelope)

        state = _query_get(query, "state")
        state_ci, state_nonce = self._decode_oauth_state(state or "") if state else (None, None)
        if not ci and state_ci:
            ci = state_ci
        if not ci:
            return HTMLResponse(
                self._ui_message_page("Откройте страницу подключения из карточки интеграции."),
                status_code=400,
            )

        if not await self._is_connected_integration_active(ci):
            return HTMLResponse(
                self._ui_message_page("Интеграция отключена. Включите ее и попробуйте снова."),
                status_code=403,
            )

        action = _query_get(query, "action")
        if action == "disconnect":
            self.connected_integration_id = ci
            result = await self.disconnect()
            if isinstance(result, dict) and "result" in result:
                return HTMLResponse(
                    self._ui_message_page("Не удалось отключить аккаунт Instagram. Попробуйте еще раз."),
                    status_code=500,
                )
            try:
                runtime = await self._load_runtime(
                    ci,
                    require_access_token=False,
                    require_business_id=False,
                )
                authorization_url = await self._authorization_url(ci, runtime)
            except Exception:
                authorization_url = ""
            return HTMLResponse(
                self._ui_page(
                    title="Подключение Instagram",
                    authorized=False,
                    authorization_url=authorization_url,
                    username=None,
                    connected_integration_id=ci,
                ),
                status_code=200,
            )

        try:
            settings_map = await self._fetch_settings_map(ci, force_refresh=True)
            runtime = self._runtime_from_settings_map(
                ci,
                settings_map,
                require_access_token=False,
                require_business_id=False,
            )
            await self._sync_reverse_indexes(runtime)
        except Exception as error:
            return HTMLResponse(self._ui_message_page(self._ui_settings_error_message(error)), status_code=400)

        oauth_error = _query_get(query, "error")
        if oauth_error:
            return HTMLResponse(
                self._ui_message_page("Instagram не подтвердил подключение. Попробуйте подключить аккаунт еще раз."),
                status_code=400,
            )

        oauth_code = _query_get(query, "code")
        if oauth_code:
            if not state_ci or not state_nonce or state_ci != ci:
                return HTMLResponse(
                    self._ui_message_page("Сессия подключения истекла. Вернитесь к интеграции и попробуйте снова."),
                    status_code=400,
                )

            if _redis_enabled():
                cached_ci = await self._consume_oauth_state(state_nonce)
                if cached_ci != ci:
                    return HTMLResponse(
                        self._ui_message_page("Сессия подключения истекла. Вернитесь к интеграции и попробуйте снова."),
                        status_code=400,
                    )
            try:
                short_token, oauth_user_id = await self._instagram_exchange_code(oauth_code)
                long_token, expires_at = await self._instagram_exchange_long_lived(short_token)
                business_id, username = await self._instagram_resolve_account(runtime, long_token, oauth_user_id)
                await self._write_business_mapping(
                    connected_integration_id=ci,
                    business_id=business_id,
                    username=username,
                    require_persistent_map=True,
                )
                updated_settings_map = await self._edit_settings(ci, {
                    "instagram_business_account_id": business_id,
                    "instagram_access_token": long_token,
                    "instagram_access_token_expires_at": str(expires_at or ""),
                    "instagram_username": username or "",
                    **self._authorization_settings_patch(authorized=True),
                }, settings_map=settings_map)
                runtime = self._runtime_from_settings_map(
                    ci,
                    updated_settings_map,
                    require_access_token=True,
                )
                await self._mark_ci_active(ci)
                await self._ensure_stream_workers()
                return HTMLResponse(
                    self._ui_page(
                        title="Подключение Instagram",
                        authorized=True,
                        authorization_url="",
                        username=runtime.username,
                        connected_integration_id=ci,
                    ),
                    status_code=200,
                )
            except Exception as error:
                logger.exception("Instagram OAuth callback failed: ci=%s", ci)
                return HTMLResponse(
                    self._ui_message_page("Не удалось завершить подключение Instagram. Попробуйте еще раз."),
                    status_code=500,
                )

        authorization_url = await self._authorization_url(ci, runtime)
        authorized = self._is_runtime_authorized(runtime)
        return HTMLResponse(
            self._ui_page(
                title="Подключение Instagram",
                authorized=authorized,
                authorization_url=authorization_url,
                username=runtime.username,
                connected_integration_id=ci,
            ),
            status_code=200,
        )

    async def handle_external(self, envelope: Dict[str, Any]) -> Any:
        method = str(envelope.get("method") or "").upper()
        query = envelope.get("query") or {}
        body = envelope.get("body")
        raw_body = envelope.get("raw_body")
        headers = envelope.get("headers") or {}

        ci = self._resolve_ci_from_envelope(envelope)

        if method == "GET":
            verify_token = _query_get(query, "hub.verify_token") or _query_get(query, "verify_token")
            mode = _query_get(query, "hub.mode") or _query_get(query, "mode")
            challenge = _query_get(query, "hub.challenge") or _query_get(query, "challenge")
            try:
                expected_verify_token = self._instagram_webhook_verify_token()
            except Exception as error:
                return Response(status_code=400, content=str(error))

            if mode == "subscribe" and verify_token == expected_verify_token:
                return Response(status_code=200, content=str(challenge or ""), media_type="text/plain")
            return Response(status_code=403, content="Forbidden")

        if method != "POST":
            return Response(status_code=405, content="Method not allowed")
        if not _redis_enabled():
            return Response(
                status_code=503,
                content="Redis is required for this integration",
            )
        await self._store_webhook_debug_snapshot(
            envelope=envelope,
            body=body,
            raw_body=raw_body,
            resolved_ci=ci,
        )
        if not isinstance(body, dict):
            return self._error_response(400, "Invalid webhook payload").dict()

        if not ci:
            candidates: List[str] = []
            for business_id in self._business_ids_from_webhook_body(body):
                mapped = await self._resolve_ci_by_business_id(business_id)
                if mapped and mapped not in candidates:
                    candidates.append(mapped)
            if len(candidates) == 1:
                ci = candidates[0]

        if not ci:
            return {"status": "ignored", "reason": "connected_integration_id_not_resolved"}
        if not await self._is_connected_integration_active(ci):
            return {"status": "ignored", "reason": "connected_integration_inactive"}

        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_business_id=False,
            )
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        _, app_secret, _ = self._instagram_app_config()
        if not self._verify_instagram_signature(headers, raw_body, app_secret):
            return Response(status_code=403, content="Invalid signature")

        try:
            await self._sync_reverse_indexes(runtime)
            await self._enqueue_event(
                ci,
                kind="instagram_in",
                payload=body,
            )
        except Exception as error:
            logger.exception("Failed to enqueue Instagram inbound webhook: ci=%s", ci)
            return Response(
                status_code=503,
                content=_json_dumps(self._error_response(503, f"enqueue failed: {error}").dict()),
                media_type="application/json",
            )

        return {"status": "accepted", "queued": 1}

    async def handle_webhook(self, action: Optional[str] = None, data: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id)
        normalized_action, payload, event_id = self._normalize_regos_webhook_payload(action, data, extra)
        if normalized_action not in InstagramCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{normalized_action}"}

        try:
            await self._enqueue_event(
                ci,
                kind="regos_in",
                payload=payload,
                event_id=event_id,
            )
            return {"status": "accepted", "queued": 1, "action": normalized_action}
        except Exception as error:
            logger.exception("Failed to enqueue Instagram REGOS webhook: ci=%s action=%s", ci, normalized_action)
            return self._error_response(1002, str(error)).dict()
