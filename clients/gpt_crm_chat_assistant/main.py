from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import httpx

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from schemas.api.base import APIBaseResponse
from schemas.api.chat.chat_message import (
    ChatMessage,
    ChatMessageAddRequest,
    ChatMessageGetRequest,
    ChatMessageTypeEnum,
)
from schemas.api.files.file import FileGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("gpt_crm_chat_assistant")


class GptCrmChatAssistantConfig:
    INTEGRATION_KEY = "gpt_crm_chat_assistant"
    REDIS_PREFIX = "clients:gpt_crm_chat_assistant:"

    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
    BOT_CACHE_TTL_SEC = 24 * 60 * 60
    DEDUPE_TTL_SEC = 5 * 60
    OPENAI_TIMEOUT_SEC = 20
    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
    OPENAI_CONVERSATIONS_ENDPOINT = "https://api.openai.com/v1/conversations"
    MAX_CONTEXT_CHARS = 8000
    MAX_CONTEXT_FILE_IDS = 50
    MAX_FILES_PER_MESSAGE = 5
    MAX_CONTEXT_IMAGE_URLS = 4

    DEFAULT_SUGGESTIONS_COUNT = 3
    DEFAULT_HISTORY_LIMIT = 20
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_AUTO_JOIN_ENABLED = True
    DEFAULT_AUTO_JOIN_ENTITY_TYPES = {"lead", "deal", "task"}
    ALLOWED_AUTO_JOIN_ENTITY_TYPES = {"lead", "deal", "task"}
    DEFAULT_AUTO_SEND_ENABLED = False
    DEFAULT_AUTO_SEND_CONFIDENCE_THRESHOLD = 0.9
    DEFAULT_AUTO_SEND_MAX_PER_CHAT_HOUR = 3
    DEFAULT_AUTO_SEND_COOLDOWN_SEC = 60

    THREAD_FIELD_ENTITY_TYPES = ("Lead", "Deal", "Task")
    THREAD_FIELD_KEY = "gpt_thread_id"
    THREAD_FIELD_FULL_KEY = "field_gpt_thread_id"
    THREAD_FIELD_NAME = "GPT Thread ID"
    THREAD_FIELD_DATA_TYPE = "string"

    SUPPORTED_INBOUND_WEBHOOKS = {"ChatMessageAdded"}


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    assistant_api_key: str
    assistant_model: str
    assistant_prompt: str
    assistant_auto_join_enabled: bool
    assistant_auto_join_entities: Set[str]
    assistant_suggestions_count: int
    assistant_history_limit: int
    assistant_temperature: float
    assistant_include_staff_private: bool
    assistant_auto_send_enabled: bool
    assistant_auto_send_confidence_threshold: float
    assistant_auto_send_max_per_chat_hour: int
    assistant_auto_send_cooldown_sec: int


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_client is not None)


def _parse_bool(value: Any, default: bool = False) -> bool:
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


def _parse_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _parse_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _normalize_entity_type(value: Any) -> str:
    return str(value or "").strip().lower()


def _extract_connected_integration_active_flag(payload: Any) -> Optional[bool]:
    if isinstance(payload, dict):
        for key in ("is_active", "isActive"):
            if key in payload:
                return _parse_bool(payload.get(key), True)
        for nested_key in (
            "connected_integration",
            "integration",
            "item",
            "data",
            "result",
        ):
            nested = payload.get(nested_key)
            nested_value = _extract_connected_integration_active_flag(nested)
            if nested_value is not None:
                return nested_value
        return None
    if isinstance(payload, list):
        for row in payload:
            nested_value = _extract_connected_integration_active_flag(row)
            if nested_value is not None:
                return nested_value
    return None


def _extract_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    text = str(raw_text or "").strip()
    if not text:
        return None

    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_text_from_openai_content(raw_content: Any) -> str:
    if isinstance(raw_content, str):
        return raw_content
    if isinstance(raw_content, list):
        chunks: List[str] = []
        for item in raw_content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                chunks.append(text)
                continue
            value = item.get("value")
            if isinstance(value, str):
                chunks.append(value)
                continue
            content = item.get("content")
            if isinstance(content, str):
                chunks.append(content)
        return "\n".join(chunks)
    return ""


def _parse_auto_join_entities(raw: Any) -> Set[str]:
    default_entities = set(GptCrmChatAssistantConfig.DEFAULT_AUTO_JOIN_ENTITY_TYPES)
    tokens: List[str] = []
    if isinstance(raw, (list, tuple, set)):
        tokens = [str(item).strip().lower() for item in raw if str(item or "").strip()]
    else:
        text = str(raw or "").strip()
        if not text:
            return default_entities
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    tokens = [
                        str(item).strip().lower()
                        for item in parsed
                        if str(item or "").strip()
                    ]
            except Exception:
                tokens = []
        if not tokens:
            tokens = [token.strip().lower() for token in re.split(r"[,\s;|]+", text) if token.strip()]

    entities = {
        token
        for token in tokens
        if token in GptCrmChatAssistantConfig.ALLOWED_AUTO_JOIN_ENTITY_TYPES
    }
    if not entities:
        return default_entities
    return entities


class GptCrmChatAssistantIntegration(ClientBase):
    _CHAT_ENTITY_TO_RESOURCE: Dict[str, Dict[str, str]] = {
        "lead": {
            "field_entity_type": "Lead",
            "get_path": "Lead/Get",
            "edit_path": "Lead/Edit",
        },
        "deal": {
            "field_entity_type": "Deal",
            "get_path": "Deal/Get",
            "edit_path": "Deal/Edit",
        },
        "task": {
            "field_entity_type": "Task",
            "get_path": "ProjectTask/Get",
            "edit_path": "ProjectTask/Edit",
        },
    }

    _ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
    _ACTIVE_CACHE_LOCK = asyncio.Lock()

    _LOCAL_DEDUPE: Dict[str, float] = {}
    _LOCAL_DEDUPE_LOCK = asyncio.Lock()

    _LOCAL_BOT_CACHE: Dict[str, Tuple[int, float]] = {}
    _LOCAL_BOT_CACHE_LOCK = asyncio.Lock()
    _LOCAL_AUTO_SEND_COOLDOWN: Dict[str, float] = {}
    _LOCAL_AUTO_SEND_HOURLY: Dict[str, int] = {}
    _LOCAL_AUTO_SEND_LOCK = asyncio.Lock()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.http_client = httpx.AsyncClient(timeout=GptCrmChatAssistantConfig.OPENAI_TIMEOUT_SEC)

    async def __aenter__(self) -> "GptCrmChatAssistantIntegration":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.http_client.aclose()

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        return f"{GptCrmChatAssistantConfig.REDIS_PREFIX}{':'.join(tokens)}"

    @classmethod
    def _settings_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("settings", connected_integration_id)

    @classmethod
    def _ci_active_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("ci_active", connected_integration_id)

    @classmethod
    def _bot_cache_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("bot_cache", connected_integration_id, chat_id)

    @classmethod
    def _dedupe_key(cls, connected_integration_id: str, event_key: str) -> str:
        return cls._redis_key("dedupe", connected_integration_id, event_key)

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set(key: str, value: str, ttl_sec: int) -> None:
        if not _redis_enabled():
            return
        await redis_client.set(key, value, ex=max(int(ttl_sec), 1))

    @staticmethod
    async def _redis_set_nx(key: str, value: str, ttl_sec: int) -> bool:
        if not _redis_enabled():
            return False
        return bool(await redis_client.set(key, value, ex=max(int(ttl_sec), 1), nx=True))

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if rows:
            await redis_client.delete(*rows)

    @classmethod
    async def _fetch_settings_map(
        cls,
        connected_integration_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        cache_key = cls._settings_cache_key(connected_integration_id)
        if not force_refresh:
            cached = await cls._redis_get(cache_key)
            if cached:
                try:
                    payload = json.loads(cached)
                    if isinstance(payload, dict):
                        return {str(k).lower(): str(v or "") for k, v in payload.items()}
                except Exception:
                    pass

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id
                )
            )

        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            key = str(getattr(row, "key", "") or "").strip().lower()
            if key:
                settings_map[key] = str(getattr(row, "value", "") or "").strip()

        await cls._redis_set(
            cache_key,
            json.dumps(settings_map, ensure_ascii=False, separators=(",", ":")),
            GptCrmChatAssistantConfig.SETTINGS_TTL_SEC,
        )
        return settings_map

    @classmethod
    async def _clear_settings_cache(cls, connected_integration_id: str) -> None:
        await cls._redis_delete(
            cls._settings_cache_key(connected_integration_id),
            cls._ci_active_cache_key(connected_integration_id),
        )

    @classmethod
    async def _is_connected_integration_active(
        cls, connected_integration_id: str, force_refresh: bool = False
    ) -> bool:
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
                    cls._ACTIVE_CACHE[ci] = (cached_value, now + 60)
                return cached_value

        detected: Optional[bool] = None
        for payload in ({}, {"connected_integration_id": ci, "limit": 1, "offset": 0}):
            try:
                async with RegosAPI(connected_integration_id=ci) as api:
                    response = await api.call(
                        "ConnectedIntegration/Get",
                        payload,
                        APIBaseResponse[Any],
                    )
                if response.ok:
                    detected = _extract_connected_integration_active_flag(response.result)
                    if detected is not None:
                        break
            except Exception:
                continue

        if detected is None:
            detected = True

        active = bool(detected)
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (active, now + 60)
        await cls._redis_set(cls._ci_active_cache_key(ci), "1" if active else "0", 60)
        return active

    @classmethod
    def _build_runtime(
        cls, connected_integration_id: str, settings_map: Dict[str, str]
    ) -> RuntimeConfig:
        api_key = str(settings_map.get("assistant_api_key") or "").strip()
        model = str(settings_map.get("assistant_model") or "").strip()
        prompt = str(settings_map.get("assistant_prompt") or "").strip()

        if not api_key:
            raise ValueError("assistant_api_key is required")
        if not model:
            raise ValueError("assistant_model is required")
        if not prompt:
            raise ValueError("assistant_prompt is required")

        suggestions_count = _parse_int(
            settings_map.get("assistant_suggestions_count"),
            GptCrmChatAssistantConfig.DEFAULT_SUGGESTIONS_COUNT,
        )
        suggestions_count = max(1, min(5, suggestions_count))

        history_limit = _parse_int(
            settings_map.get("assistant_history_limit"),
            GptCrmChatAssistantConfig.DEFAULT_HISTORY_LIMIT,
        )
        history_limit = max(1, min(100, history_limit))

        temperature = _parse_float(
            settings_map.get("assistant_temperature"),
            GptCrmChatAssistantConfig.DEFAULT_TEMPERATURE,
        )
        temperature = min(max(temperature, 0.0), 2.0)

        auto_join_enabled = _parse_bool(
            settings_map.get("assistant_auto_join_enabled"),
            GptCrmChatAssistantConfig.DEFAULT_AUTO_JOIN_ENABLED,
        )
        auto_join_entities = _parse_auto_join_entities(
            settings_map.get("assistant_auto_join_entities")
        )

        include_staff_private = _parse_bool(
            settings_map.get("assistant_include_staff_private"),
            False,
        )

        auto_send_enabled = _parse_bool(
            settings_map.get("assistant_auto_send_enabled"),
            GptCrmChatAssistantConfig.DEFAULT_AUTO_SEND_ENABLED,
        )
        auto_send_confidence_threshold = _parse_float(
            settings_map.get("assistant_auto_send_confidence_threshold"),
            GptCrmChatAssistantConfig.DEFAULT_AUTO_SEND_CONFIDENCE_THRESHOLD,
        )
        auto_send_confidence_threshold = min(max(auto_send_confidence_threshold, 0.0), 1.0)

        auto_send_max_per_chat_hour = _parse_int(
            settings_map.get("assistant_auto_send_max_per_chat_hour"),
            GptCrmChatAssistantConfig.DEFAULT_AUTO_SEND_MAX_PER_CHAT_HOUR,
        )
        auto_send_max_per_chat_hour = max(1, min(100, auto_send_max_per_chat_hour))

        auto_send_cooldown_sec = _parse_int(
            settings_map.get("assistant_auto_send_cooldown_sec"),
            GptCrmChatAssistantConfig.DEFAULT_AUTO_SEND_COOLDOWN_SEC,
        )
        auto_send_cooldown_sec = max(0, min(3600, auto_send_cooldown_sec))

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            assistant_api_key=api_key,
            assistant_model=model,
            assistant_prompt=prompt,
            assistant_auto_join_enabled=auto_join_enabled,
            assistant_auto_join_entities=auto_join_entities,
            assistant_suggestions_count=suggestions_count,
            assistant_history_limit=history_limit,
            assistant_temperature=temperature,
            assistant_include_staff_private=include_staff_private,
            assistant_auto_send_enabled=auto_send_enabled,
            assistant_auto_send_confidence_threshold=auto_send_confidence_threshold,
            assistant_auto_send_max_per_chat_hour=auto_send_max_per_chat_hour,
            assistant_auto_send_cooldown_sec=auto_send_cooldown_sec,
        )

    @classmethod
    async def _load_runtime(
        cls, connected_integration_id: str, force_refresh_settings: bool = False
    ) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(
            connected_integration_id,
            force_refresh=force_refresh_settings,
        )
        return cls._build_runtime(connected_integration_id, settings_map)

    @classmethod
    async def _subscribe_required_webhooks(
        cls,
        connected_integration_id: str,
    ) -> Dict[str, Any]:
        payload = {
            "connected_integration_id": connected_integration_id,
            "webhooks": sorted(GptCrmChatAssistantConfig.SUPPORTED_INBOUND_WEBHOOKS),
        }
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                await api.call("ConnectedIntegration/Edit", payload, APIBaseResponse)
            return {"status": "ok"}
        except Exception as error:
            logger.warning(
                "Webhook subscription failed for %s: %s",
                connected_integration_id,
                error,
            )
            return {"status": "failed", "error": str(error)}

    @classmethod
    async def _field_exists(
        cls,
        connected_integration_id: str,
        entity_type: str,
        full_key: str,
        raw_key: str,
    ) -> bool:
        payload = {
            "entity_type": entity_type,
            "keys": [full_key, raw_key],
        }
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "Field/Get",
                payload,
                APIBaseResponse[List[Dict[str, Any]]],
            )

        if not response.ok:
            raise RuntimeError(
                f"Field/Get rejected: entity_type={entity_type} payload={response.result}"
            )
        rows = response.result if isinstance(response.result, list) else []
        expected_keys = {full_key.strip().lower(), raw_key.strip().lower()}
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_key = str(row.get("key") or "").strip().lower()
            if row_key in expected_keys:
                return True
        return False

    @classmethod
    async def _ensure_thread_custom_field(
        cls,
        connected_integration_id: str,
        entity_type: str,
    ) -> Dict[str, Any]:
        raw_key = GptCrmChatAssistantConfig.THREAD_FIELD_KEY
        full_key = GptCrmChatAssistantConfig.THREAD_FIELD_FULL_KEY

        if await cls._field_exists(
            connected_integration_id=connected_integration_id,
            entity_type=entity_type,
            full_key=full_key,
            raw_key=raw_key,
        ):
            return {
                "entity_type": entity_type,
                "key": full_key,
                "status": "exists",
            }

        payload = {
            "key": raw_key,
            "name": GptCrmChatAssistantConfig.THREAD_FIELD_NAME,
            "entity_type": entity_type,
            "data_type": GptCrmChatAssistantConfig.THREAD_FIELD_DATA_TYPE,
            "required": False,
        }
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "Field/Add",
                payload,
                APIBaseResponse[Dict[str, Any]],
            )

        if response.ok:
            result_payload = response.result if isinstance(response.result, dict) else {}
            return {
                "entity_type": entity_type,
                "key": full_key,
                "status": "created",
                "new_id": _parse_int(result_payload.get("new_id"), 0),
            }

        logger.warning(
            "Field/Add rejected while ensuring thread field: ci=%s entity_type=%s payload=%s",
            connected_integration_id,
            entity_type,
            response.result,
        )
        # Another worker may create the field concurrently; re-check before failing.
        if await cls._field_exists(
            connected_integration_id=connected_integration_id,
            entity_type=entity_type,
            full_key=full_key,
            raw_key=raw_key,
        ):
            return {
                "entity_type": entity_type,
                "key": full_key,
                "status": "exists_after_retry",
            }

        raise RuntimeError(
            f"Field/Add rejected for required key={raw_key} entity_type={entity_type}: {response.result}"
        )

    @classmethod
    async def _ensure_thread_custom_fields(
        cls,
        connected_integration_id: str,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for entity_type in GptCrmChatAssistantConfig.THREAD_FIELD_ENTITY_TYPES:
            result = await cls._ensure_thread_custom_field(
                connected_integration_id=connected_integration_id,
                entity_type=entity_type,
            )
            rows.append(result)
        return rows

    async def connect(self, **_: Any) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id).strip()
        if not await self._is_connected_integration_active(ci, force_refresh=True):
            return {
                "status": "ignored",
                "reason": "connected_integration_inactive",
            }

        try:
            field_ensure_result = await self._ensure_thread_custom_fields(ci)
        except Exception as error:
            logger.warning("Required CRM field ensure failed: ci=%s error=%s", ci, error)
            return self._error_response(1003, str(error)).dict()

        try:
            runtime = await self._load_runtime(ci, force_refresh_settings=True)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        subscribe_result = await self._subscribe_required_webhooks(ci)
        return {
            "status": "connected",
            "integration_key": GptCrmChatAssistantConfig.INTEGRATION_KEY,
            "model": runtime.assistant_model,
            "webhooks_subscription": subscribe_result,
            "required_fields": field_ensure_result,
            "auto_join_enabled": runtime.assistant_auto_join_enabled,
            "auto_join_entities": sorted(runtime.assistant_auto_join_entities),
            "auto_send_enabled": runtime.assistant_auto_send_enabled,
            "auto_send_confidence_threshold": runtime.assistant_auto_send_confidence_threshold,
        }

    async def disconnect(self, **_: Any) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._clear_settings_cache(str(self.connected_integration_id))
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Dict[str, Any]:
        _ = settings
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._clear_settings_cache(str(self.connected_integration_id))
        return {"status": "settings updated"}

    async def handle_external(self, data: dict) -> Any:
        _ = data
        return {"status": "ignored"}

    @staticmethod
    def _normalize_regos_webhook_payload(
        action: Optional[str],
        data: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any],
    ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
        event_id = str(kwargs.get("event_id") or "").strip() or None

        if isinstance(action, str) and action in GptCrmChatAssistantConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return action, data or {}, event_id

        if action == "HandleWebhook":
            payload = data if isinstance(data, dict) else {}
            nested = payload.get("data")
            wrapped_event_id = str(payload.get("event_id") or event_id or "").strip() or None
            if not isinstance(nested, dict):
                return None, {}, wrapped_event_id
            nested_action = nested.get("action")
            nested_data = nested.get("data")
            if not isinstance(nested_action, str) or not isinstance(nested_data, dict):
                return None, {}, wrapped_event_id
            return nested_action, nested_data, wrapped_event_id

        if isinstance(data, dict):
            nested_action = data.get("action")
            nested_data = data.get("data")
            nested_event_id = str(data.get("event_id") or event_id or "").strip() or None
            if isinstance(nested_action, str) and isinstance(nested_data, dict):
                return nested_action, nested_data, nested_event_id

        return None, {}, event_id

    @staticmethod
    def _event_key(
        chat_id: str,
        message_id: str,
        event_id: Optional[str],
    ) -> str:
        eid = str(event_id or "").strip()
        if eid:
            return f"event:{eid}"
        return f"chat:{chat_id}:message:{message_id}"

    async def _is_duplicate_event(
        self,
        connected_integration_id: str,
        event_key: str,
    ) -> bool:
        dedupe_key = self._dedupe_key(connected_integration_id, event_key)
        if _redis_enabled():
            inserted = await self._redis_set_nx(
                dedupe_key,
                "1",
                GptCrmChatAssistantConfig.DEDUPE_TTL_SEC,
            )
            return not inserted

        now = time.monotonic()
        async with self._LOCAL_DEDUPE_LOCK:
            expired_keys = [
                key for key, expires_at in self._LOCAL_DEDUPE.items() if expires_at <= now
            ]
            for key in expired_keys:
                self._LOCAL_DEDUPE.pop(key, None)
            if dedupe_key in self._LOCAL_DEDUPE:
                return True
            self._LOCAL_DEDUPE[dedupe_key] = now + GptCrmChatAssistantConfig.DEDUPE_TTL_SEC
        return False

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id).strip()
        if not await self._is_connected_integration_active(ci):
            return {"status": "ignored", "reason": "connected_integration_inactive"}

        normalized_action, payload, event_id = self._normalize_regos_webhook_payload(
            action=action,
            data=data,
            kwargs=kwargs,
        )
        if normalized_action not in GptCrmChatAssistantConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{normalized_action}"}

        chat_id = str(payload.get("chat_id") or "").strip()
        message_id = str(payload.get("id") or "").strip()
        if not chat_id or not message_id:
            return {"status": "ignored", "reason": "invalid_payload"}

        if await self._is_duplicate_event(ci, self._event_key(chat_id, message_id, event_id)):
            return {"status": "ignored", "reason": "duplicate_event"}

        try:
            runtime = await self._load_runtime(ci)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        try:
            return await self._process_chat_message_added(
                runtime=runtime,
                chat_id=chat_id,
                message_id=message_id,
            )
        except Exception as error:
            logger.exception(
                "ChatMessageAdded processing failed: ci=%s chat_id=%s message_id=%s",
                ci,
                chat_id,
                message_id,
            )
            return self._error_response(1002, str(error)).dict()

    async def _process_chat_message_added(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
        message_id: str,
    ) -> Dict[str, Any]:
        message = await self._get_chat_message(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
            message_id=message_id,
        )
        if not message:
            return {"status": "ignored", "reason": "message_not_found"}

        if not self._should_generate_for_message(message):
            return {"status": "ignored", "reason": "message_filtered"}

        conversation_state = await self._resolve_or_create_chat_conversation(
            runtime=runtime,
            chat_id=chat_id,
        )
        conversation_status = str(conversation_state.get("status") or "")
        if conversation_status == "unsupported_entity_type":
            reason = conversation_status or "unsupported_entity_type"
            return {"status": "ignored", "reason": reason}

        conversation_id = (
            str(conversation_state.get("conversation_id") or "").strip()
            if conversation_status == "ok"
            else ""
        ) or None

        bot_id = await self._resolve_or_join_chatbot(
            runtime=runtime,
            chat_id=chat_id,
        )
        if not bot_id:
            return {"status": "ignored", "reason": "chatbot_not_available"}

        context, context_image_urls = await self._build_chat_context(
            runtime=runtime,
            chat_id=chat_id,
            source_message=message,
        )
        generation_result = await self._generate_suggestions(
            runtime=runtime,
            source_message=message,
            context=context,
            context_image_urls=context_image_urls,
            conversation_id=conversation_id,
        )
        suggestions = generation_result.get("suggestions") or []
        best_reply = _normalize_text(generation_result.get("best_reply"))
        confidence = _parse_float(generation_result.get("confidence"), 0.0)
        confidence = min(max(confidence, 0.0), 1.0)
        if not suggestions:
            return {"status": "ignored", "reason": "empty_suggestions"}

        auto_sent = False
        if self._can_auto_send_reply(
            runtime=runtime,
            confidence=confidence,
            best_reply=best_reply,
        ):
            allowed_by_limits = await self._acquire_auto_send_slot(
                runtime=runtime,
                chat_id=chat_id,
            )
            if allowed_by_limits:
                auto_sent = await self._publish_auto_reply(
                    runtime=runtime,
                    chat_id=chat_id,
                    source_message_id=message_id,
                    bot_entity_id=bot_id,
                    text=best_reply,
                )

        if not auto_sent:
            await self._publish_suggestions(
                runtime=runtime,
                chat_id=chat_id,
                source_message_id=message_id,
                bot_entity_id=bot_id,
                suggestions=suggestions,
            )

        return {
            "status": "accepted",
            "chat_id": chat_id,
            "message_id": message_id,
            "suggestions_count": len(suggestions),
            "auto_sent": auto_sent,
            "confidence": confidence,
            "entity_type": conversation_state.get("entity_type"),
            "entity_id": conversation_state.get("entity_id"),
            "thread_id": conversation_id or "",
            "thread_status": conversation_status or "unavailable",
            "thread_created": bool(conversation_state.get("created")),
            "thread_persisted": bool(conversation_state.get("persisted")),
        }

    @staticmethod
    def _should_generate_for_message(message: ChatMessage) -> bool:
        if message.message_type != ChatMessageTypeEnum.Regular:
            return False
        author_entity_type = _normalize_entity_type(message.author_entity_type)
        if author_entity_type in {"user", "chatbot"}:
            return False
        if _normalize_text(message.text):
            return True
        return bool(GptCrmChatAssistantIntegration._extract_message_file_ids(message))

    async def _get_chat_message(
        self,
        connected_integration_id: str,
        chat_id: str,
        message_id: str,
    ) -> Optional[ChatMessage]:
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
        if not response.ok or not response.result:
            return None
        return response.result[0] if response.result else None

    @staticmethod
    def _author_role(author_entity_type: Optional[str], message_type: Optional[ChatMessageTypeEnum]) -> str:
        normalized = _normalize_entity_type(author_entity_type)
        if message_type == ChatMessageTypeEnum.System:
            return "system"
        if message_type == ChatMessageTypeEnum.Private:
            return "staff_note"
        if normalized == "user":
            return "operator"
        if normalized == "chatbot":
            return "assistant"
        return "client"

    @staticmethod
    def _extract_message_file_ids(message: ChatMessage) -> List[int]:
        file_ids_raw = getattr(message, "file_ids", None)
        if not isinstance(file_ids_raw, list):
            return []
        resolved: List[int] = []
        for item in file_ids_raw:
            value = _parse_int(item, 0)
            if value > 0:
                resolved.append(int(value))
        return resolved[: GptCrmChatAssistantConfig.MAX_FILES_PER_MESSAGE]

    @staticmethod
    def _format_file_size(size_bytes: Any) -> str:
        size = _parse_int(size_bytes, 0)
        if size <= 0:
            return ""
        units = ["B", "KB", "MB", "GB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(value)}{unit}"
                return f"{value:.1f}{unit}"
            value /= 1024
        return ""

    @staticmethod
    def _normalize_public_url(value: Any) -> Optional[str]:
        url = str(value or "").strip()
        if not url:
            return None
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return None

    @staticmethod
    def _is_image_file(file_row: Dict[str, Any]) -> bool:
        mime = str(file_row.get("mime_type") or "").strip().lower()
        if mime.startswith("image/"):
            return True
        ext = str(file_row.get("extension") or "").strip().lower()
        return ext in {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tif", "tiff", "heic", "heif"}

    async def _fetch_files_map(
        self,
        connected_integration_id: str,
        file_ids: Sequence[int],
    ) -> Dict[int, Dict[str, Any]]:
        unique_ids = sorted({int(fid) for fid in file_ids if int(fid) > 0})
        if not unique_ids:
            return {}
        unique_ids = unique_ids[: GptCrmChatAssistantConfig.MAX_CONTEXT_FILE_IDS]

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.files.file.get(
                    FileGetRequest(
                        ids=unique_ids,
                        limit=len(unique_ids),
                        offset=0,
                    )
                )
        except Exception as error:
            logger.warning(
                "File/Get failed while building context: ci=%s ids=%s error=%s",
                connected_integration_id,
                unique_ids,
                error,
            )
            return {}

        files_map: Dict[int, Dict[str, Any]] = {}
        if not response.ok or not isinstance(response.result, list):
            return files_map

        for row in response.result:
            file_id = _parse_int(getattr(row, "id", 0), 0)
            if file_id <= 0:
                continue
            files_map[int(file_id)] = {
                "id": int(file_id),
                "name": str(getattr(row, "name", "") or "").strip(),
                "extension": str(getattr(row, "extension", "") or "").strip().lower(),
                "mime_type": str(getattr(row, "mime_type", "") or "").strip().lower(),
                "size": _parse_int(getattr(row, "size", 0), 0),
                "url": str(getattr(row, "url", "") or "").strip(),
            }
        return files_map

    def _render_message_context_line(
        self,
        role: str,
        text: str,
        file_ids: Sequence[int],
        files_map: Dict[int, Dict[str, Any]],
    ) -> Tuple[str, List[str]]:
        normalized_text = _normalize_text(text)
        file_descriptors: List[str] = []
        image_urls: List[str] = []

        for file_id in list(file_ids)[: GptCrmChatAssistantConfig.MAX_FILES_PER_MESSAGE]:
            file_row = files_map.get(int(file_id))
            if not file_row:
                file_descriptors.append(f"file_id={int(file_id)}")
                continue

            file_name = str(file_row.get("name") or "").strip() or f"file_{int(file_id)}"
            mime = str(file_row.get("mime_type") or "").strip().lower()
            size_text = self._format_file_size(file_row.get("size"))

            details: List[str] = []
            if mime:
                details.append(mime)
            if size_text:
                details.append(size_text)

            if details:
                file_descriptors.append(f"{file_name} ({', '.join(details)})")
            else:
                file_descriptors.append(file_name)

            public_url = self._normalize_public_url(file_row.get("url"))
            if public_url and self._is_image_file(file_row):
                image_urls.append(public_url)

        body = normalized_text or ("[сообщение без текста]" if file_descriptors else "")
        if file_descriptors:
            body = (
                f"{body} [files: {', '.join(file_descriptors)}]"
                if body
                else f"[files: {', '.join(file_descriptors)}]"
            )
        body = body or "[empty]"
        return f"{role}: {body}", image_urls

    async def _build_chat_context(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
        source_message: ChatMessage,
    ) -> Tuple[str, List[str]]:
        rows: List[ChatMessage] = []
        try:
            async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
                response = await api.chat.chat_message.get(
                    ChatMessageGetRequest(
                        chat_id=chat_id,
                        limit=runtime.assistant_history_limit,
                        offset=0,
                        include_staff_private=runtime.assistant_include_staff_private,
                    )
                )
            if response.ok and isinstance(response.result, list):
                rows = response.result
        except Exception as error:
            logger.warning(
                "ChatMessage/Get failed while building context: ci=%s chat_id=%s error=%s",
                runtime.connected_integration_id,
                chat_id,
                error,
            )

        all_file_ids: List[int] = []
        for row in rows:
            all_file_ids.extend(self._extract_message_file_ids(row))
        if not rows:
            all_file_ids.extend(self._extract_message_file_ids(source_message))
        files_map = await self._fetch_files_map(
            connected_integration_id=runtime.connected_integration_id,
            file_ids=all_file_ids,
        )

        lines: List[Tuple[int, str]] = []
        collected_image_urls: List[str] = []
        seen_image_urls: Set[str] = set()
        for row in rows:
            text = str(getattr(row, "text", None) or "")
            message_file_ids = self._extract_message_file_ids(row)
            if not _normalize_text(text) and not message_file_ids:
                continue
            role = self._author_role(
                getattr(row, "author_entity_type", None),
                getattr(row, "message_type", None),
            )
            created_date = _parse_int(getattr(row, "created_date", 0), 0)
            rendered_line, image_urls = self._render_message_context_line(
                role=role,
                text=text,
                file_ids=message_file_ids,
                files_map=files_map,
            )
            lines.append((created_date, rendered_line))

            for url in image_urls:
                if url in seen_image_urls:
                    continue
                seen_image_urls.add(url)
                collected_image_urls.append(url)
                if len(collected_image_urls) >= GptCrmChatAssistantConfig.MAX_CONTEXT_IMAGE_URLS:
                    break
            if len(collected_image_urls) >= GptCrmChatAssistantConfig.MAX_CONTEXT_IMAGE_URLS:
                continue

        if not lines:
            fallback_line, fallback_images = self._render_message_context_line(
                role="client",
                text=str(source_message.text or ""),
                file_ids=self._extract_message_file_ids(source_message),
                files_map=files_map,
            )
            return fallback_line, fallback_images[: GptCrmChatAssistantConfig.MAX_CONTEXT_IMAGE_URLS]

        lines.sort(key=lambda item: item[0])
        raw_lines = [item[1] for item in lines]
        context = self._trim_context_lines(
            raw_lines,
            GptCrmChatAssistantConfig.MAX_CONTEXT_CHARS,
        )
        return context, collected_image_urls[: GptCrmChatAssistantConfig.MAX_CONTEXT_IMAGE_URLS]

    @staticmethod
    def _trim_context_lines(lines: Sequence[str], max_chars: int) -> str:
        selected: List[str] = []
        total = 0
        for line in reversed(list(lines)):
            line_len = len(line) + 1
            if selected and total + line_len > max_chars:
                break
            selected.append(line)
            total += line_len
        selected.reverse()
        return "\n".join(selected)

    @classmethod
    def _entity_resource(cls, chat_entity_type: str) -> Optional[Dict[str, str]]:
        return cls._CHAT_ENTITY_TO_RESOURCE.get(_normalize_entity_type(chat_entity_type))

    @staticmethod
    def _extract_field_value(fields_raw: Any, key: str) -> Optional[str]:
        if not isinstance(fields_raw, list):
            return None
        expected_key = str(key or "").strip().lower()
        if not expected_key:
            return None

        for row in fields_raw:
            if isinstance(row, dict):
                row_key = str(row.get("key") or "").strip().lower()
                row_value = row.get("value")
            else:
                row_key = str(getattr(row, "key", "") or "").strip().lower()
                row_value = getattr(row, "value", None)

            if row_key != expected_key:
                continue
            value = str(row_value or "").strip()
            if value:
                return value
        return None

    @staticmethod
    def _api_error_description(result: Any) -> str:
        if isinstance(result, dict):
            return str(result.get("description") or "").strip()
        return str(result or "").strip()

    @classmethod
    def _is_unknown_field_error(cls, result: Any, field_key: str) -> bool:
        description = cls._api_error_description(result).lower()
        target_key = str(field_key or "").strip().lower()
        if not description or not target_key:
            return False
        return "unknown fields" in description and target_key in description

    @staticmethod
    def _normalize_conversation_id(value: Any) -> Optional[str]:
        text = str(value or "").strip()
        if not text:
            return None
        return text if text.startswith(("conv_", "conversation_")) else None

    async def _get_entity_row(
        self,
        connected_integration_id: str,
        chat_entity_type: str,
        entity_id: int,
    ) -> Dict[str, Any]:
        resource = self._entity_resource(chat_entity_type)
        if not resource or entity_id <= 0:
            return {}

        payload = {"ids": [int(entity_id)], "limit": 1, "offset": 0}
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                resource["get_path"],
                payload,
                APIBaseResponse[List[Dict[str, Any]]],
            )
        if not response.ok:
            logger.warning(
                "%s rejected while loading entity: ci=%s entity_type=%s entity_id=%s payload=%s",
                resource["get_path"],
                connected_integration_id,
                chat_entity_type,
                entity_id,
                response.result,
            )
            return {}
        if not isinstance(response.result, list) or not response.result:
            return {}
        row = response.result[0]
        return row if isinstance(row, dict) else {}

    async def _set_entity_thread_id(
        self,
        connected_integration_id: str,
        chat_entity_type: str,
        entity_id: int,
        conversation_id: str,
    ) -> bool:
        resource = self._entity_resource(chat_entity_type)
        if not resource or entity_id <= 0 or not conversation_id:
            return False

        async def send_edit(field_key: str) -> APIBaseResponse[Dict[str, Any]]:
            payload = {
                "id": int(entity_id),
                "fields": [
                    {
                        "key": field_key,
                        "value": conversation_id,
                    }
                ],
            }
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                return await api.call(
                    resource["edit_path"],
                    payload,
                    APIBaseResponse[Dict[str, Any]],
                )

        full_key = GptCrmChatAssistantConfig.THREAD_FIELD_FULL_KEY
        raw_key = GptCrmChatAssistantConfig.THREAD_FIELD_KEY

        response = await send_edit(full_key)
        if response.ok:
            return True

        # Compatibility fallback: some entity handlers may expect key without `field_` prefix.
        response_raw = await send_edit(raw_key)
        if response_raw.ok:
            return True

        # Self-healing for integrations that started before field bootstrap/reconnect.
        field_entity_type = str(resource.get("field_entity_type") or "").strip()
        unknown_full = self._is_unknown_field_error(response.result, full_key)
        unknown_raw = self._is_unknown_field_error(response_raw.result, raw_key)
        if field_entity_type and (unknown_full or unknown_raw):
            try:
                await self._ensure_thread_custom_field(
                    connected_integration_id=connected_integration_id,
                    entity_type=field_entity_type,
                )
            except Exception as error:
                logger.warning(
                    "Field self-heal failed while persisting conversation id: ci=%s entity_type=%s entity_id=%s error=%s",
                    connected_integration_id,
                    chat_entity_type,
                    entity_id,
                    error,
                )

            retry_full = await send_edit(full_key)
            if retry_full.ok:
                return True

            retry_raw = await send_edit(raw_key)
            if retry_raw.ok:
                return True

            logger.warning(
                "%s rejected after self-heal while persisting conversation id: ci=%s entity_type=%s entity_id=%s full=%s raw=%s",
                resource["edit_path"],
                connected_integration_id,
                chat_entity_type,
                entity_id,
                retry_full.result,
                retry_raw.result,
            )
            return False

        logger.warning(
            "%s rejected while persisting conversation id: ci=%s entity_type=%s entity_id=%s full=%s raw=%s",
            resource["edit_path"],
            connected_integration_id,
            chat_entity_type,
            entity_id,
            response.result,
            response_raw.result,
        )
        return False

    async def _create_openai_conversation(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
        chat_entity_type: str,
        entity_id: int,
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {runtime.assistant_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "metadata": {
                "integration_key": GptCrmChatAssistantConfig.INTEGRATION_KEY,
                "connected_integration_id": runtime.connected_integration_id,
                "chat_id": chat_id,
                "entity_type": chat_entity_type,
                "entity_id": str(int(entity_id)),
            }
        }
        try:
            response = await self.http_client.post(
                GptCrmChatAssistantConfig.OPENAI_CONVERSATIONS_ENDPOINT,
                headers=headers,
                json=payload,
            )
            if response.status_code >= 400:
                logger.warning(
                    "OpenAI conversation create failed: status=%s chat_id=%s entity_type=%s entity_id=%s body=%s",
                    response.status_code,
                    chat_id,
                    chat_entity_type,
                    entity_id,
                    response.text[:1000],
                )
                return None
            raw = response.json()
        except Exception as error:
            logger.warning(
                "OpenAI conversation create error: chat_id=%s entity_type=%s entity_id=%s error=%s",
                chat_id,
                chat_entity_type,
                entity_id,
                error,
            )
            return None

        conversation_id = self._normalize_conversation_id((raw or {}).get("id"))
        if not conversation_id:
            logger.warning(
                "OpenAI conversation create returned empty id: chat_id=%s entity_type=%s entity_id=%s payload=%s",
                chat_id,
                chat_entity_type,
                entity_id,
                str(raw)[:1000],
            )
            return None
        return conversation_id

    async def _resolve_or_create_chat_conversation(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
    ) -> Dict[str, Any]:
        chat_row = await self._get_chat_row(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
        )
        if not chat_row:
            return {"status": "chat_not_found"}

        chat_entity_type = _normalize_entity_type(chat_row.get("entity_type"))
        resource = self._entity_resource(chat_entity_type)
        if not resource:
            return {
                "status": "unsupported_entity_type",
                "entity_type": chat_entity_type,
            }

        entity_id = _parse_int(chat_row.get("entity_id"), 0)
        if entity_id <= 0:
            return {
                "status": "invalid_entity_binding",
                "entity_type": chat_entity_type,
                "entity_id": entity_id,
            }

        entity_row = await self._get_entity_row(
            connected_integration_id=runtime.connected_integration_id,
            chat_entity_type=chat_entity_type,
            entity_id=entity_id,
        )
        if not entity_row:
            return {
                "status": "entity_not_found",
                "entity_type": chat_entity_type,
                "entity_id": entity_id,
            }

        existing = self._normalize_conversation_id(
            self._extract_field_value(
                entity_row.get("fields"),
                GptCrmChatAssistantConfig.THREAD_FIELD_FULL_KEY,
            )
            or self._extract_field_value(
                entity_row.get("fields"),
                GptCrmChatAssistantConfig.THREAD_FIELD_KEY,
            )
        )
        if existing:
            return {
                "status": "ok",
                "entity_type": chat_entity_type,
                "entity_id": entity_id,
                "conversation_id": existing,
                "created": False,
                "persisted": True,
            }

        created = await self._create_openai_conversation(
            runtime=runtime,
            chat_id=chat_id,
            chat_entity_type=chat_entity_type,
            entity_id=entity_id,
        )
        if not created:
            return {
                "status": "conversation_create_failed",
                "entity_type": chat_entity_type,
                "entity_id": entity_id,
            }

        persisted = await self._set_entity_thread_id(
            connected_integration_id=runtime.connected_integration_id,
            chat_entity_type=chat_entity_type,
            entity_id=entity_id,
            conversation_id=created,
        )
        return {
            "status": "ok",
            "entity_type": chat_entity_type,
            "entity_id": entity_id,
            "conversation_id": created,
            "created": True,
            "persisted": persisted,
        }

    async def _resolve_or_join_chatbot(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
    ) -> Optional[int]:
        cached_bot_id = await self._get_cached_bot_id(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
        )

        chat_row = await self._get_chat_row(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
        )
        participants = self._extract_chatbot_participants(chat_row)
        resolved = self._choose_chatbot_id(
            participants=participants,
            connected_integration_id=runtime.connected_integration_id,
            cached_bot_id=cached_bot_id,
        )
        if resolved:
            await self._set_cached_bot_id(
                connected_integration_id=runtime.connected_integration_id,
                chat_id=chat_id,
                bot_id=resolved,
            )
            return resolved

        chat_entity_type = _normalize_entity_type((chat_row or {}).get("entity_type"))
        allow_auto_join = (
            runtime.assistant_auto_join_enabled
            and chat_entity_type in runtime.assistant_auto_join_entities
        )
        if not allow_auto_join:
            return None

        await self._add_bot_to_chat(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
        )
        chat_row = await self._get_chat_row(
            connected_integration_id=runtime.connected_integration_id,
            chat_id=chat_id,
        )
        participants = self._extract_chatbot_participants(chat_row)
        resolved = self._choose_chatbot_id(
            participants=participants,
            connected_integration_id=runtime.connected_integration_id,
            cached_bot_id=cached_bot_id,
        )
        if not resolved and participants:
            resolved = max(item["entity_id"] for item in participants)
            logger.warning(
                "Fallback chatbot resolution used max entity_id: ci=%s chat_id=%s bot_id=%s",
                runtime.connected_integration_id,
                chat_id,
                resolved,
            )
        if resolved:
            await self._set_cached_bot_id(
                connected_integration_id=runtime.connected_integration_id,
                chat_id=chat_id,
                bot_id=resolved,
            )
        return resolved

    async def _get_chat_row(
        self,
        connected_integration_id: str,
        chat_id: str,
    ) -> Dict[str, Any]:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "Chat/Get",
                {"ids": [chat_id], "limit": 1, "offset": 0},
                APIBaseResponse[List[Dict[str, Any]]],
            )
        if not response.ok or not isinstance(response.result, list) or not response.result:
            return {}
        row = response.result[0]
        return row if isinstance(row, dict) else {}

    @staticmethod
    def _extract_chatbot_participants(chat_row: Dict[str, Any]) -> List[Dict[str, Any]]:
        participants_raw = chat_row.get("participants")
        if not isinstance(participants_raw, list):
            return []

        parsed: List[Dict[str, Any]] = []
        for row in participants_raw:
            if not isinstance(row, dict):
                continue
            if _normalize_entity_type(row.get("entity_type")) != "chatbot":
                continue
            entity_id = _parse_int(row.get("entity_id"), 0)
            if entity_id <= 0:
                continue
            chatbot_ci = str(row.get("connected_integration_id") or "").strip()
            parsed.append(
                {
                    "entity_id": int(entity_id),
                    "connected_integration_id": chatbot_ci,
                }
            )
        return parsed

    @staticmethod
    def _choose_chatbot_id(
        participants: List[Dict[str, Any]],
        connected_integration_id: str,
        cached_bot_id: Optional[int],
    ) -> Optional[int]:
        if cached_bot_id and any(int(row.get("entity_id") or 0) == int(cached_bot_id) for row in participants):
            return int(cached_bot_id)

        for row in participants:
            ci = str(row.get("connected_integration_id") or "").strip()
            if ci and ci == connected_integration_id:
                return int(row.get("entity_id") or 0)

        unique_ids = sorted(
            {
                int(row.get("entity_id") or 0)
                for row in participants
                if int(row.get("entity_id") or 0) > 0
            }
        )
        if len(unique_ids) == 1:
            return unique_ids[0]
        return None

    async def _add_bot_to_chat(
        self,
        connected_integration_id: str,
        chat_id: str,
    ) -> None:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "Chat/AddBot",
                {
                    "chat_id": chat_id,
                    "connected_integration_id": connected_integration_id,
                },
                APIBaseResponse[Dict[str, Any]],
            )
        if not response.ok:
            logger.warning(
                "Chat/AddBot rejected: ci=%s chat_id=%s payload=%s",
                connected_integration_id,
                chat_id,
                response.result,
            )

    async def _get_cached_bot_id(
        self,
        connected_integration_id: str,
        chat_id: str,
    ) -> Optional[int]:
        cache_key = self._bot_cache_key(connected_integration_id, chat_id)
        raw = await self._redis_get(cache_key)
        if raw:
            parsed = _parse_int(raw, 0)
            if parsed > 0:
                return parsed

        now = time.monotonic()
        async with self._LOCAL_BOT_CACHE_LOCK:
            row = self._LOCAL_BOT_CACHE.get(cache_key)
            if row and row[1] > now:
                return row[0]
            if row:
                self._LOCAL_BOT_CACHE.pop(cache_key, None)
        return None

    async def _set_cached_bot_id(
        self,
        connected_integration_id: str,
        chat_id: str,
        bot_id: int,
    ) -> None:
        if bot_id <= 0:
            return
        cache_key = self._bot_cache_key(connected_integration_id, chat_id)
        await self._redis_set(
            cache_key,
            str(bot_id),
            GptCrmChatAssistantConfig.BOT_CACHE_TTL_SEC,
        )
        async with self._LOCAL_BOT_CACHE_LOCK:
            self._LOCAL_BOT_CACHE[cache_key] = (
                int(bot_id),
                time.monotonic() + GptCrmChatAssistantConfig.BOT_CACHE_TTL_SEC,
            )

    async def _generate_suggestions(
        self,
        runtime: RuntimeConfig,
        source_message: ChatMessage,
        context: str,
        context_image_urls: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        source_text = _normalize_text(source_message.text)
        if not source_text and self._extract_message_file_ids(source_message):
            source_text = "[клиент отправил вложение без текста]"
        if not source_text:
            return {"suggestions": [], "best_reply": "", "confidence": 0.0}

        system_instruction = (
            "Ты помощник оператора CRM. На основе диалога предложи короткие готовые ответы оператору. "
            "Сохраняй язык клиента и деловой тон. "
            "Верни только JSON-объект без markdown: "
            '{"suggestions":["..."],"best_reply":"...","confidence":0.0}.'
        )
        user_payload = (
            f"Количество подсказок: {runtime.assistant_suggestions_count}\n"
            f"Последнее сообщение клиента: {source_text}\n\n"
            f"Контекст диалога:\n{context}"
        )
        unique_image_urls: List[str] = []
        seen_image_urls: Set[str] = set()
        for value in context_image_urls or []:
            normalized_url = self._normalize_public_url(value)
            if not normalized_url or normalized_url in seen_image_urls:
                continue
            seen_image_urls.add(normalized_url)
            unique_image_urls.append(normalized_url)
            if len(unique_image_urls) >= GptCrmChatAssistantConfig.MAX_CONTEXT_IMAGE_URLS:
                break

        def build_input(use_images: bool) -> List[Dict[str, Any]]:
            user_content: Any = user_payload
            if use_images and unique_image_urls:
                user_parts: List[Dict[str, Any]] = [{"type": "input_text", "text": user_payload}]
                for url in unique_image_urls:
                    user_parts.append({"type": "input_image", "image_url": url})
                user_content = user_parts
            return [{"role": "user", "content": user_content}]

        def build_payload(
            use_conversation: bool,
            use_images: bool,
            conversation_key_mode: str = "conversation",
        ) -> Dict[str, Any]:
            payload: Dict[str, Any] = {
                "model": runtime.assistant_model,
                "instructions": f"{runtime.assistant_prompt}\n\n{system_instruction}",
                "input": build_input(use_images=use_images),
                "temperature": runtime.assistant_temperature,
                "store": True,
            }
            if use_conversation and conversation_id:
                if conversation_key_mode == "conversation_id":
                    payload["conversation_id"] = conversation_id
                else:
                    payload["conversation"] = conversation_id
            return payload

        headers = {
            "Authorization": f"Bearer {runtime.assistant_api_key}",
            "Content-Type": "application/json",
        }

        try:
            use_conversation = bool(self._normalize_conversation_id(conversation_id))
            use_images = bool(unique_image_urls)
            attempts: List[Tuple[bool, bool, str]] = []
            for flags in (
                (use_conversation, use_images, "conversation"),
                (use_conversation, use_images, "conversation_id"),
                (use_conversation, False, "conversation"),
                (use_conversation, False, "conversation_id"),
                (False, use_images, "conversation"),
                (False, False, "conversation"),
            ):
                if flags in attempts:
                    continue
                attempts.append(flags)

            raw: Optional[Dict[str, Any]] = None
            for try_index, (try_conversation, try_images, try_conversation_key) in enumerate(
                attempts, start=1
            ):
                payload = build_payload(
                    use_conversation=try_conversation,
                    use_images=try_images,
                    conversation_key_mode=try_conversation_key,
                )
                response = await self.http_client.post(
                    GptCrmChatAssistantConfig.OPENAI_RESPONSES_ENDPOINT,
                    headers=headers,
                    json=payload,
                )
                if response.status_code >= 400:
                    logger.warning(
                        "OpenAI request failed: attempt=%s status=%s conversation=%s conversation_key=%s images=%s body=%s",
                        try_index,
                        response.status_code,
                        "on" if try_conversation else "off",
                        try_conversation_key if try_conversation else "-",
                        "on" if try_images else "off",
                        response.text[:1000],
                    )
                    continue
                raw = response.json()
                break

            if raw is None:
                return {"suggestions": [], "best_reply": "", "confidence": 0.0}
        except Exception as error:
            logger.warning("OpenAI request error: %s", error)
            return {"suggestions": [], "best_reply": "", "confidence": 0.0}

        raw_text = self._extract_model_output(raw)
        return self._normalize_generation_output(
            raw_text=raw_text,
            max_items=runtime.assistant_suggestions_count,
        )

    @staticmethod
    def _extract_model_output(payload: Dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0] if isinstance(choices[0], dict) else {}
            message = first.get("message") if isinstance(first, dict) else {}
            if isinstance(message, dict):
                content = message.get("content")
                return _extract_text_from_openai_content(content)
        return ""

    @staticmethod
    def _normalize_suggestions(raw_text: str, max_items: int) -> List[str]:
        rows: List[str] = []
        payload = _extract_json_object(raw_text)
        if payload and isinstance(payload.get("suggestions"), list):
            for item in payload.get("suggestions") or []:
                rows.append(str(item or ""))
        else:
            for line in re.split(r"[\r\n]+", str(raw_text or "")):
                cleaned = re.sub(r"^\s*[-*•\d\.\)\(]+\s*", "", line).strip()
                if cleaned:
                    rows.append(cleaned)

        normalized: List[str] = []
        seen: Set[str] = set()
        for row in rows:
            text = _normalize_text(row)
            if not text:
                continue
            if len(text) > 200:
                text = text[:200].rstrip()
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(text)
            if len(normalized) >= max_items:
                break
        return normalized

    @classmethod
    def _normalize_generation_output(
        cls,
        raw_text: str,
        max_items: int,
    ) -> Dict[str, Any]:
        suggestions = cls._normalize_suggestions(raw_text, max_items)
        best_reply = suggestions[0] if suggestions else ""
        confidence = 0.0

        payload = _extract_json_object(raw_text)
        if isinstance(payload, dict):
            best_reply_candidate = _normalize_text(payload.get("best_reply"))
            if best_reply_candidate:
                best_reply = best_reply_candidate[:200].rstrip()

            confidence = _parse_float(payload.get("confidence"), 0.0)
            confidence = min(max(confidence, 0.0), 1.0)

            payload_suggestions = payload.get("suggestions")
            if isinstance(payload_suggestions, list):
                normalized: List[str] = []
                seen: Set[str] = set()
                for item in payload_suggestions:
                    text = _normalize_text(item)
                    if not text:
                        continue
                    if len(text) > 200:
                        text = text[:200].rstrip()
                    key = text.casefold()
                    if key in seen:
                        continue
                    seen.add(key)
                    normalized.append(text)
                    if len(normalized) >= max_items:
                        break
                if normalized:
                    suggestions = normalized
                    if not best_reply:
                        best_reply = normalized[0]

        if not best_reply and suggestions:
            best_reply = suggestions[0]
        if best_reply and not suggestions:
            suggestions = [best_reply]

        return {
            "suggestions": suggestions,
            "best_reply": best_reply,
            "confidence": confidence,
        }

    @staticmethod
    def _can_auto_send_reply(
        runtime: RuntimeConfig,
        confidence: float,
        best_reply: str,
    ) -> bool:
        if not runtime.assistant_auto_send_enabled:
            return False
        if not best_reply:
            return False
        return confidence >= runtime.assistant_auto_send_confidence_threshold

    @classmethod
    def _auto_send_cooldown_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("auto_send", "cooldown", connected_integration_id, chat_id)

    @classmethod
    def _auto_send_hour_key(
        cls, connected_integration_id: str, chat_id: str, hour_bucket: int
    ) -> str:
        return cls._redis_key("auto_send", "hour", connected_integration_id, chat_id, hour_bucket)

    async def _acquire_auto_send_slot(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
    ) -> bool:
        if runtime.assistant_auto_send_cooldown_sec <= 0 and runtime.assistant_auto_send_max_per_chat_hour <= 0:
            return True

        now_unix = int(time.time())
        hour_bucket = now_unix // 3600

        cooldown_key = self._auto_send_cooldown_key(runtime.connected_integration_id, chat_id)
        hour_key = self._auto_send_hour_key(runtime.connected_integration_id, chat_id, hour_bucket)

        if _redis_enabled():
            if runtime.assistant_auto_send_cooldown_sec > 0:
                ok = await self._redis_set_nx(
                    cooldown_key,
                    str(now_unix),
                    runtime.assistant_auto_send_cooldown_sec,
                )
                if not ok:
                    return False

            max_per_hour = runtime.assistant_auto_send_max_per_chat_hour
            if max_per_hour > 0:
                try:
                    sent_count = int(await redis_client.incr(hour_key))
                    if sent_count == 1:
                        await redis_client.expire(hour_key, 3700)
                    if sent_count > max_per_hour:
                        return False
                except Exception as error:
                    logger.warning(
                        "Failed to enforce redis auto-send hour limit: ci=%s chat_id=%s error=%s",
                        runtime.connected_integration_id,
                        chat_id,
                        error,
                    )
            return True

        async with self._LOCAL_AUTO_SEND_LOCK:
            now_mono = time.monotonic()

            expired_cooldowns = [
                key
                for key, expires_at in self._LOCAL_AUTO_SEND_COOLDOWN.items()
                if expires_at <= now_mono
            ]
            for key in expired_cooldowns:
                self._LOCAL_AUTO_SEND_COOLDOWN.pop(key, None)

            old_hour_keys: List[str] = []
            for key in self._LOCAL_AUTO_SEND_HOURLY.keys():
                try:
                    key_hour = int(str(key).rsplit(":", 1)[-1])
                except Exception:
                    key_hour = hour_bucket
                if key_hour < hour_bucket - 1:
                    old_hour_keys.append(key)
            for key in old_hour_keys:
                self._LOCAL_AUTO_SEND_HOURLY.pop(key, None)

            if runtime.assistant_auto_send_cooldown_sec > 0:
                if cooldown_key in self._LOCAL_AUTO_SEND_COOLDOWN:
                    return False
                self._LOCAL_AUTO_SEND_COOLDOWN[cooldown_key] = (
                    now_mono + runtime.assistant_auto_send_cooldown_sec
                )

            max_per_hour = runtime.assistant_auto_send_max_per_chat_hour
            if max_per_hour > 0:
                count = int(self._LOCAL_AUTO_SEND_HOURLY.get(hour_key, 0)) + 1
                self._LOCAL_AUTO_SEND_HOURLY[hour_key] = count
                if count > max_per_hour:
                    return False

        return True

    async def _publish_auto_reply(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
        source_message_id: str,
        bot_entity_id: int,
        text: str,
    ) -> bool:
        if not text:
            return False

        external_message_id = f"gptauto:{source_message_id}"[:150]
        request = ChatMessageAddRequest(
            chat_id=chat_id,
            author_entity_type="ChatBot",
            author_entity_id=int(bot_entity_id),
            message_type=ChatMessageTypeEnum.Regular,
            text=text,
            external_message_id=external_message_id,
        )
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.chat.chat_message.add(request)

        if not response.ok:
            logger.warning(
                "ChatMessage/Add auto-reply rejected: ci=%s chat_id=%s source_message_id=%s payload=%s",
                runtime.connected_integration_id,
                chat_id,
                source_message_id,
                response.result,
            )
            return False
        return True

    async def _publish_suggestions(
        self,
        runtime: RuntimeConfig,
        chat_id: str,
        source_message_id: str,
        bot_entity_id: int,
        suggestions: List[str],
    ) -> None:
        payload = {
            "chat_id": chat_id,
            "author_entity_type": "ChatBot",
            "author_entity_id": int(bot_entity_id),
            "suggestions": suggestions,
            "source_message_id": source_message_id,
        }
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/Suggest",
                payload,
                APIBaseResponse[Dict[str, Any]],
            )
        if not response.ok:
            logger.warning(
                "ChatMessage/Suggest rejected: ci=%s chat_id=%s source_message_id=%s payload=%s",
                runtime.connected_integration_id,
                chat_id,
                source_message_id,
                response.result,
            )
