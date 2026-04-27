from __future__ import annotations

import asyncio
import base64
import binascii
import html
import json
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse, Response

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from schemas.api.chat.chat import ChatEntityTypeEnum
from schemas.api.chat.chat_message import (
    ChatMessageAddFileRequest,
    ChatMessageAddRequest,
    ChatMessageGetRequest,
    ChatMessageMarkReadRequest,
    ChatMessageTypeEnum,
)
from schemas.api.crm.channel import Channel, ChannelGetRequest
from schemas.api.crm.client import Client, ClientAddRequest, ClientEditRequest, ClientGetRequest
from schemas.api.crm.ticket import (
    Ticket,
    TicketAddRequest,
    TicketDirectionEnum,
    TicketGetRequest,
    TicketSetRatingRequest,
    TicketStatusEnum,
)
from schemas.api.integrations.connected_integration import (
    ConnectedIntegrationEditRequest,
    ConnectedIntegrationGetRequest,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("external_chat_crm_channel")


class ExternalChatCrmChannelConfig:
    INTEGRATION_KEY = "external_chat_crm_channel"
    REDIS_PREFIX = "clients:external_chat_crm_channel:"
    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 30)
    CONTEXT_TTL_SEC = 7 * 24 * 60 * 60
    ACTIVE_CACHE_TTL_SEC = 30
    DEFAULT_HISTORY_LIMIT = 50
    MAX_HISTORY_LIMIT = 200
    MAX_MESSAGE_LENGTH = 4000
    MAX_UPLOAD_FILE_SIZE_BYTES = 20 * 1024 * 1024
    MAX_FILE_NAME_LENGTH = 160
    MAX_FILE_EXTENSION_LENGTH = 20
    DEFAULT_CHAT_TITLE = "Support Chat"
    DEFAULT_SUBJECT_TEMPLATE = "Web chat {visitor_id}"
    CLOSED_ENTITY_ERROR_CODE = 1220
    CHAT_REVISION_DEFAULT = 1
    WEBHOOK_DEDUPE_TTL_SEC = 10 * 60
    RATING_POSITIVE_THRESHOLD = 4
    SUPPORTED_INBOUND_WEBHOOKS = {
        "ChatMessageAdded",
        "ChatMessageEdited",
        "ChatMessageDeleted",
        "TicketStatusSet",
        "TicketClosed",
    }
    DEFAULT_THEME_VARS = {
        "--bg": "#f5f7fb",
        "--card": "#ffffff",
        "--line": "#dde3ef",
        "--text": "#132033",
        "--muted": "#6d7d95",
        "--accent": "#0a66c2",
        "--mine": "#e8f3ff",
        "--other": "#f1f4f9",
        "--system": "#fff6d8",
    }


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    channel_id: int
    ticket_subject_template: str
    default_responsible_user_id: Optional[int]
    chat_title: str
    channel_start_message: Optional[str]
    channel_end_message: Optional[str]
    channel_rating_enabled: bool
    channel_rating_message: Optional[str]
    channel_rating_positive_message: Optional[str]
    channel_rating_negative_message: Optional[str]
    require_display_name: bool
    require_phone: bool
    require_email: bool
    chat_theme_vars: Dict[str, str]


@dataclass
class ChatContext:
    visitor_id: str
    client_id: int
    ticket_id: int
    chat_id: str


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _parse_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text)
    except Exception:
        return default


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


def _normalize_text(value: Any, max_len: int = 500) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:max_len]


def _normalize_phone(value: Any) -> Optional[str]:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits or None


def _normalize_email(value: Any) -> Optional[str]:
    email = str(value or "").strip().lower()
    if not email or "@" not in email or " " in email:
        return None
    return email


def _normalize_rating(value: Any) -> Optional[int]:
    parsed = _parse_int(value, None)
    if parsed is None:
        return None
    if 1 <= int(parsed) <= 5:
        return int(parsed)
    return None


def _normalize_file_name(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "file.bin"
    raw = raw.replace("\\", "/").split("/")[-1]
    cleaned = "".join(ch for ch in raw if 31 < ord(ch) < 127 and ch not in {"<", ">", ":", "\"", "|", "?", "*"})
    cleaned = cleaned.strip(" .")
    if not cleaned:
        cleaned = "file.bin"
    return cleaned[: ExternalChatCrmChannelConfig.MAX_FILE_NAME_LENGTH]


def _normalize_file_extension(value: Any) -> str:
    raw = str(value or "").strip().lower().lstrip(".")
    if not raw:
        return ""
    cleaned = "".join(ch for ch in raw if ch.isalnum())
    return cleaned[: ExternalChatCrmChannelConfig.MAX_FILE_EXTENSION_LENGTH]


def _guess_extension_from_name(file_name: str) -> str:
    name = str(file_name or "").strip()
    if "." not in name:
        return ""
    return _normalize_file_extension(name.rsplit(".", 1)[-1])


def _extract_base64_payload(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("data:"):
        _, sep, tail = raw.partition(",")
        if sep:
            raw = tail.strip()
    return raw


_ALLOWED_THEME_KEYS = set(ExternalChatCrmChannelConfig.DEFAULT_THEME_VARS.keys())
_THEME_KEY_ALIASES = {
    "bg": "--bg",
    "card": "--card",
    "line": "--line",
    "text": "--text",
    "muted": "--muted",
    "accent": "--accent",
    "mine": "--mine",
    "other": "--other",
    "system": "--system",
}
_THEME_VALUE_RE = re.compile(r"^[a-zA-Z0-9#(),.%\-\s/+]*$")


def _normalize_theme_key(value: Any) -> Optional[str]:
    key = str(value or "").strip().lower()
    if not key:
        return None
    if key in _THEME_KEY_ALIASES:
        return _THEME_KEY_ALIASES[key]
    if key.startswith("--") and key in _ALLOWED_THEME_KEYS:
        return key
    if not key.startswith("--"):
        alias = f"--{key}"
        if alias in _ALLOWED_THEME_KEYS:
            return alias
    return None


def _sanitize_theme_value(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    if not text or len(text) > 120:
        return None
    lowered = text.lower()
    forbidden_tokens = ("javascript:", "expression(", "@import", "</style")
    if any(token in lowered for token in forbidden_tokens):
        return None
    if not _THEME_VALUE_RE.fullmatch(text):
        return None
    return text


def _parse_chat_theme_vars(raw: Any) -> Dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, str):
        payload_raw = raw.strip()
        if not payload_raw:
            return {}
        try:
            payload = _json_loads(payload_raw)
        except Exception as error:
            raise ValueError("chat_theme_vars must be valid JSON object") from error
    elif isinstance(raw, dict):
        payload = raw
    else:
        raise ValueError("chat_theme_vars must be JSON object")

    if not isinstance(payload, dict):
        raise ValueError("chat_theme_vars must be JSON object")

    parsed: Dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        key = _normalize_theme_key(raw_key)
        if not key:
            continue
        safe_value = _sanitize_theme_value(raw_value)
        if not safe_value:
            continue
        parsed[key] = safe_value
    return parsed


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_client is not None)


def _headers_ci(headers: Dict[str, Any], key: str) -> Optional[str]:
    key_lower = str(key or "").lower()
    for name, value in (headers or {}).items():
        if str(name or "").lower() != key_lower:
            continue
        text = str(value or "").strip()
        if text:
            return text
    return None


def _query_get(query: Dict[str, Any], key: str) -> Optional[str]:
    value = query.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    text = str(value or "").strip()
    return text or None


def _result_get(result: Any, key: str) -> Any:
    if isinstance(result, dict):
        return result.get(key)
    return getattr(result, key, None)


def _result_to_dict(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        try:
            dumped = result.model_dump(mode="json")
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            return {}
    return {}


def _extract_add_new_id(result: Any) -> Optional[int]:
    direct = _parse_int(str(result), None)
    if direct and direct > 0:
        return int(direct)
    for key in ("new_id", "id", "ticket_id", "client_id"):
        value = _parse_int(str(_result_get(result, key) or ""), None)
        if value and value > 0:
            return int(value)
    return None


def _enum_value(value: Any) -> str:
    if value is None:
        return ""
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value or "")
    return str(value or "")


class ChatMessageAddClosedEntityError(RuntimeError):
    pass


class ExternalChatCrmChannelIntegration(ClientBase):
    _ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
    _UI_TEMPLATE_CACHE: Optional[str] = None
    _UI_TEMPLATE_PATH = Path(__file__).with_name("ui_template.html")

    _ACTIVE_CACHE_LOCK = asyncio.Lock()

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        return f"{ExternalChatCrmChannelConfig.REDIS_PREFIX}{':'.join(tokens)}"

    @classmethod
    def _settings_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("settings", connected_integration_id)

    @classmethod
    def _active_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("active", connected_integration_id)

    @classmethod
    def _context_cache_key(cls, connected_integration_id: str, visitor_id: str) -> str:
        return cls._redis_key("context", connected_integration_id, visitor_id)

    @classmethod
    def _chat_revision_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("chat_revision", connected_integration_id, chat_id)

    @classmethod
    def _ticket_state_cache_key(cls, connected_integration_id: str, ticket_id: int) -> str:
        return cls._redis_key("ticket_state", connected_integration_id, ticket_id)

    @classmethod
    def _ticket_chat_index_key(cls, connected_integration_id: str, ticket_id: int) -> str:
        return cls._redis_key("ticket_chat", connected_integration_id, ticket_id)

    @classmethod
    def _ticket_once_flag_key(
        cls,
        connected_integration_id: str,
        ticket_id: int,
        flag: str,
    ) -> str:
        return cls._redis_key(
            "ticket_once",
            connected_integration_id,
            int(ticket_id),
            str(flag or "").strip().lower(),
        )

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set(key: str, value: str, ttl_sec: int) -> None:
        if not _redis_enabled():
            return
        await redis_client.set(key, value, ex=max(int(ttl_sec or 1), 1))

    @staticmethod
    async def _redis_set_nx(key: str, value: str, ttl_sec: int) -> bool:
        if not _redis_enabled():
            return False
        inserted = await redis_client.set(
            key,
            value,
            ex=max(int(ttl_sec or 1), 1),
            nx=True,
        )
        return bool(inserted)

    @staticmethod
    async def _redis_incr(key: str, ttl_sec: int) -> int:
        if not _redis_enabled():
            return 0
        value = await redis_client.incr(key)
        await redis_client.expire(key, max(int(ttl_sec or 1), 1))
        return int(value or 0)

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        valid = [str(key).strip() for key in keys if str(key or "").strip()]
        if not valid:
            return
        await redis_client.delete(*valid)

    @classmethod
    async def _is_connected_integration_active(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return False

        now = time.monotonic()
        if not force_refresh:
            async with cls._ACTIVE_CACHE_LOCK:
                cached = cls._ACTIVE_CACHE.get(ci)
            if cached and cached[1] > now:
                return cached[0]

        cache_key = cls._active_cache_key(ci)
        if _redis_enabled() and not force_refresh:
            cached_raw = await cls._redis_get(cache_key)
            if cached_raw in {"0", "1"}:
                active = cached_raw == "1"
                async with cls._ACTIVE_CACHE_LOCK:
                    cls._ACTIVE_CACHE[ci] = (
                        active,
                        now + ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
                    )
                return active

        detected: Optional[bool] = None
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
                    active_value = getattr(row, "is_active", None)
                    if active_value is None:
                        continue
                    detected = bool(active_value)
                    break
        except Exception as error:
            logger.warning(
                "ConnectedIntegration/Get failed for active check: ci=%s error=%s",
                ci,
                error,
            )

        if detected is None:
            detected = True

        active = bool(detected)
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (
                active,
                now + ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
            )
        if _redis_enabled():
            await cls._redis_set(
                cache_key,
                "1" if active else "0",
                ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
            )
        return active

    @classmethod
    async def _fetch_settings_map(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        cache_key = cls._settings_cache_key(connected_integration_id)
        if _redis_enabled() and not force_refresh:
            cached_raw = await cls._redis_get(cache_key)
            if cached_raw:
                try:
                    cached = _json_loads(cached_raw)
                    if isinstance(cached, dict):
                        return {str(k): str(v or "") for k, v in cached.items()}
                except Exception:
                    pass

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id,
                )
            )

        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            key = str(getattr(row, "key", "") or "").strip().lower()
            if not key:
                continue
            settings_map[key] = str(getattr(row, "value", "") or "").strip()

        if _redis_enabled():
            await cls._redis_set(
                cache_key,
                _json_dumps(settings_map),
                ExternalChatCrmChannelConfig.SETTINGS_TTL_SEC,
            )
        return settings_map

    @classmethod
    async def _get_channel(cls, connected_integration_id: str, channel_id: int) -> Optional[Channel]:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.crm.channel.get(
                ChannelGetRequest(ids=[int(channel_id)], limit=1, offset=0)
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    async def _load_runtime(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(
            connected_integration_id,
            force_refresh=force_refresh,
        )

        channel_id = _parse_int(settings_map.get("chat_channel_id"), None)
        if not channel_id or channel_id <= 0:
            raise ValueError("chat_channel_id must be a positive integer")

        ticket_subject_template = (
            _normalize_text(settings_map.get("ticket_subject_template"), 200)
            or ExternalChatCrmChannelConfig.DEFAULT_SUBJECT_TEMPLATE
        )
        require_display_name = _parse_bool(
            settings_map.get("require_name_on_open"),
            False,
        )
        require_phone = _parse_bool(
            settings_map.get("require_phone_on_open"),
            False,
        )
        require_email = _parse_bool(
            settings_map.get("require_email_on_open"),
            False,
        )
        chat_theme_vars = _parse_chat_theme_vars(settings_map.get("chat_theme_vars"))
        channel = await cls._get_channel(connected_integration_id, int(channel_id))
        channel_name = _normalize_text(getattr(channel, "name", None), 80)
        chat_title = (
            channel_name
            or _normalize_text(settings_map.get("chat_title"), 80)
            or ExternalChatCrmChannelConfig.DEFAULT_CHAT_TITLE
        )
        channel_start_message = (
            _normalize_text(getattr(channel, "start_message", None), 300) or None
        )
        channel_end_message = (
            _normalize_text(getattr(channel, "end_message", None), 300) or None
        )
        channel_rating_enabled = bool(getattr(channel, "rating_enabled", False))
        channel_rating_message = (
            _normalize_text(getattr(channel, "rating_message", None), 300) or None
        )
        channel_rating_positive_message = (
            _normalize_text(getattr(channel, "rating_positive_message", None), 300) or None
        )
        channel_rating_negative_message = (
            _normalize_text(getattr(channel, "rating_negative_message", None), 300) or None
        )

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            channel_id=int(channel_id),
            ticket_subject_template=ticket_subject_template,
            default_responsible_user_id=_parse_int(
                settings_map.get("default_responsible_user_id"), None
            ),
            chat_title=chat_title,
            channel_start_message=channel_start_message,
            channel_end_message=channel_end_message,
            channel_rating_enabled=channel_rating_enabled,
            channel_rating_message=channel_rating_message,
            channel_rating_positive_message=channel_rating_positive_message,
            channel_rating_negative_message=channel_rating_negative_message,
            require_display_name=require_display_name,
            require_phone=require_phone,
            require_email=require_email,
            chat_theme_vars=chat_theme_vars,
        )

    @staticmethod
    def _build_client_external_id(
        connected_integration_id: str, visitor_id: str
    ) -> str:
        return f"webchat:client:{connected_integration_id}:{visitor_id}"

    @staticmethod
    def _build_ticket_external_dialog_id(
        connected_integration_id: str, visitor_id: str
    ) -> str:
        return f"webchat:dialog:{connected_integration_id}:{visitor_id}"

    @classmethod
    def _normalize_visitor_id(cls, value: Any) -> Optional[str]:
        raw = str(value or "").strip()
        if not raw:
            return None
        allowed = []
        for ch in raw:
            if ch.isalnum() or ch in {"-", "_", ":"}:
                allowed.append(ch)
        normalized = "".join(allowed).strip(":-_")
        if not normalized:
            return None
        return normalized[:120]

    @staticmethod
    def _build_subject(template: str, visitor_id: str, profile: Dict[str, Any]) -> str:
        display_name = _normalize_text(profile.get("display_name"), 120) or "Guest"
        current_date = time.strftime("%Y-%m-%d")
        try:
            subject = str(template or "").format(
                visitor_id=visitor_id,
                display_name=display_name,
                current_date=current_date,
            )
        except Exception:
            subject = f"Web chat {visitor_id}"
        normalized = _normalize_text(subject, 200)
        return normalized or f"Web chat {visitor_id}"

    @staticmethod
    def _default_ticket_state() -> Dict[str, Any]:
        return {
            "ticket_status": "",
            "ticket_closed": False,
            "can_write": True,
            "ticket_rating": None,
        }

    @classmethod
    def _normalize_ticket_state(cls, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = cls._default_ticket_state()
        if not isinstance(payload, dict):
            return normalized

        status_value = _enum_value(payload.get("ticket_status")).strip()
        ticket_closed = bool(payload.get("ticket_closed"))
        if status_value == TicketStatusEnum.Closed.value:
            ticket_closed = True
        can_write_raw = payload.get("can_write")
        can_write = bool(can_write_raw) if can_write_raw is not None else not ticket_closed
        if ticket_closed:
            can_write = False

        if status_value:
            normalized["ticket_status"] = status_value
        normalized["ticket_closed"] = ticket_closed
        normalized["can_write"] = can_write
        normalized["ticket_rating"] = _normalize_rating(payload.get("ticket_rating"))
        return normalized

    @classmethod
    def _compose_ticket_view_state(
        cls,
        runtime: RuntimeConfig,
        ticket_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        base = cls._normalize_ticket_state(ticket_state)
        ticket_rating = _normalize_rating(base.get("ticket_rating"))
        rating_enabled = bool(runtime.channel_rating_enabled)
        rating_submitted = ticket_rating is not None
        rating_required = bool(
            rating_enabled
            and bool(base.get("ticket_closed"))
            and not rating_submitted
        )
        return {
            **base,
            "ticket_rating": ticket_rating,
            "rating_enabled": rating_enabled,
            "rating_submitted": rating_submitted,
            "rating_required": rating_required,
            "rating_message": str(runtime.channel_rating_message or ""),
        }

    @staticmethod
    def _ticket_closed_response(
        visitor_id: str,
        ticket_view: Dict[str, Any],
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error": 409,
                "description": "Ticket is closed",
                "visitor_id": visitor_id,
                **ticket_view,
            },
        )

    async def _load_ticket_view_for_write(
        self,
        runtime: RuntimeConfig,
        *,
        connected_integration_id: str,
        ticket_id: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        ticket_state = await self._get_ticket_write_state(
            connected_integration_id,
            int(ticket_id),
        )
        ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
        if ticket_state.get("can_write", True):
            return ticket_state, ticket_view
        refreshed_state = await self._get_ticket_write_state(
            connected_integration_id,
            int(ticket_id),
            force_refresh=True,
        )
        refreshed_view = self._compose_ticket_view_state(runtime, refreshed_state)
        return refreshed_state, refreshed_view

    async def _cache_closed_ticket_view(
        self,
        runtime: RuntimeConfig,
        *,
        connected_integration_id: str,
        ticket_id: int,
    ) -> Dict[str, Any]:
        closed_state = await self._cache_ticket_state(
            connected_integration_id,
            int(ticket_id),
            {
                "ticket_status": TicketStatusEnum.Closed.value,
                "ticket_closed": True,
                "can_write": False,
            },
        )
        return self._compose_ticket_view_state(runtime, closed_state)

    @classmethod
    async def _set_ticket_chat_index(
        cls,
        connected_integration_id: str,
        ticket_id: int,
        chat_id: str,
    ) -> None:
        if not ticket_id or not chat_id:
            return
        if not _redis_enabled():
            return
        ttl = ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC
        await cls._redis_set(
            cls._ticket_chat_index_key(connected_integration_id, int(ticket_id)),
            str(chat_id),
            ttl,
        )

    @classmethod
    async def _get_ticket_chat_index(
        cls,
        connected_integration_id: str,
        ticket_id: int,
    ) -> Optional[str]:
        if not ticket_id:
            return None
        if not _redis_enabled():
            return None
        value = await cls._redis_get(
            cls._ticket_chat_index_key(connected_integration_id, int(ticket_id))
        )
        text = str(value or "").strip()
        return text or None

    @classmethod
    async def _ensure_chat_revision_exists(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> int:
        chat_id_raw = str(chat_id or "").strip()
        if not chat_id_raw:
            return 0
        if not _redis_enabled():
            return 0

        key = cls._chat_revision_key(connected_integration_id, chat_id_raw)
        current = await cls._redis_get(key)
        parsed = _parse_int(current, None)
        if parsed and parsed > 0:
            return int(parsed)
        await cls._redis_set(
            key,
            str(ExternalChatCrmChannelConfig.CHAT_REVISION_DEFAULT),
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )
        return int(ExternalChatCrmChannelConfig.CHAT_REVISION_DEFAULT)

    @classmethod
    async def _get_chat_revision(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> int:
        chat_id_raw = str(chat_id or "").strip()
        if not chat_id_raw:
            return 0
        if not _redis_enabled():
            return 0

        current = await cls._redis_get(
            cls._chat_revision_key(connected_integration_id, chat_id_raw)
        )
        parsed = _parse_int(current, None)
        if parsed and parsed > 0:
            return int(parsed)
        return await cls._ensure_chat_revision_exists(connected_integration_id, chat_id_raw)

    @classmethod
    async def _bump_chat_revision(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> int:
        chat_id_raw = str(chat_id or "").strip()
        if not chat_id_raw:
            return 0
        if not _redis_enabled():
            return 0

        key = cls._chat_revision_key(connected_integration_id, chat_id_raw)
        try:
            value = await cls._redis_incr(
                key,
                ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
            )
            return int(value or 0)
        except Exception:
            # Redis value may contain invalid data from old versions. Reset and retry.
            await cls._redis_set(
                key,
                str(ExternalChatCrmChannelConfig.CHAT_REVISION_DEFAULT),
                ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
            )
            value = await cls._redis_incr(
                key,
                ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
            )
            return int(value or 0)

    @classmethod
    async def _cache_ticket_state(
        cls,
        connected_integration_id: str,
        ticket_id: int,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await cls._get_cached_ticket_state(connected_integration_id, int(ticket_id))
        merged: Dict[str, Any] = dict(existing or {})
        if isinstance(state, dict):
            merged.update(state)
        normalized = cls._normalize_ticket_state(merged)
        if not ticket_id:
            return normalized
        if not _redis_enabled():
            return normalized

        await cls._redis_set(
            cls._ticket_state_cache_key(connected_integration_id, int(ticket_id)),
            _json_dumps(normalized),
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )
        return normalized

    @classmethod
    async def _get_cached_ticket_state(
        cls,
        connected_integration_id: str,
        ticket_id: int,
    ) -> Optional[Dict[str, Any]]:
        if not ticket_id:
            return None
        if not _redis_enabled():
            return None
        raw = await cls._redis_get(
            cls._ticket_state_cache_key(connected_integration_id, int(ticket_id))
        )
        if not raw:
            return None
        try:
            parsed = _json_loads(raw)
        except Exception:
            return None
        return cls._normalize_ticket_state(parsed if isinstance(parsed, dict) else {})

    @classmethod
    async def _load_cached_context(
        cls, connected_integration_id: str, visitor_id: str
    ) -> Optional[ChatContext]:
        raw = await cls._redis_get(cls._context_cache_key(connected_integration_id, visitor_id))
        if not raw:
            return None
        try:
            payload = _json_loads(raw)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        client_id = _parse_int(payload.get("client_id"), None)
        ticket_id = _parse_int(payload.get("ticket_id"), None)
        chat_id = str(payload.get("chat_id") or "").strip()
        if not client_id or not ticket_id or not chat_id:
            return None
        return ChatContext(
            visitor_id=visitor_id,
            client_id=int(client_id),
            ticket_id=int(ticket_id),
            chat_id=chat_id,
        )

    @classmethod
    async def _save_cached_context(
        cls,
        connected_integration_id: str,
        context: ChatContext,
    ) -> None:
        payload = _json_dumps(
            {
                "visitor_id": context.visitor_id,
                "client_id": context.client_id,
                "ticket_id": context.ticket_id,
                "chat_id": context.chat_id,
            }
        )
        await cls._redis_set(
            cls._context_cache_key(connected_integration_id, context.visitor_id),
            payload,
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )
        await cls._set_ticket_chat_index(
            connected_integration_id,
            int(context.ticket_id),
            str(context.chat_id),
        )
        await cls._ensure_chat_revision_exists(
            connected_integration_id,
            str(context.chat_id),
        )

    @classmethod
    async def _find_client_by_external_id(
        cls,
        api: RegosAPI,
        external_id: str,
    ) -> Optional[Client]:
        response = await api.crm.client.get(
            ClientGetRequest(external_ids=[external_id], limit=1, offset=0)
        )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    async def _find_ticket_by_external_dialog_id(
        cls,
        api: RegosAPI,
        external_dialog_id: str,
        channel_id: int,
    ) -> Optional[Ticket]:
        response = await api.crm.ticket.get(
            TicketGetRequest(
                external_dialog_id=external_dialog_id,
                channel_ids=[int(channel_id)],
                limit=50,
                offset=0,
            )
        )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        if not rows:
            return None

        open_rows = [
            row
            for row in rows
            if _enum_value(getattr(row, "status", None)).strip() != TicketStatusEnum.Closed.value
        ]
        source = open_rows if open_rows else rows
        return max(source, key=lambda item: int(getattr(item, "id", 0) or 0))

    @classmethod
    async def _load_ticket_by_id(
        cls,
        api: RegosAPI,
        ticket_id: int,
    ) -> Optional[Ticket]:
        response = await api.crm.ticket.get(
            TicketGetRequest(ids=[int(ticket_id)], limit=1, offset=0)
        )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    async def _get_ticket_write_state(
        cls,
        connected_integration_id: str,
        ticket_id: int,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        state = cls._default_ticket_state()
        if not force_refresh:
            cached_state = await cls._get_cached_ticket_state(connected_integration_id, int(ticket_id))
            if cached_state:
                return cls._normalize_ticket_state(cached_state)

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                ticket = await cls._load_ticket_by_id(api, int(ticket_id))
        except Exception as error:
            logger.warning(
                "Ticket/Get failed for write-state check: ci=%s ticket_id=%s error=%s",
                connected_integration_id,
                ticket_id,
                error,
            )
            cached_state = await cls._get_cached_ticket_state(connected_integration_id, int(ticket_id))
            return cls._normalize_ticket_state(cached_state) if cached_state else state

        if not ticket:
            return state

        status_value = _enum_value(getattr(ticket, "status", None)).strip()
        ticket_closed = status_value == TicketStatusEnum.Closed.value
        resolved_state = {
            "ticket_status": status_value,
            "ticket_closed": ticket_closed,
            "can_write": not ticket_closed,
            "ticket_rating": _normalize_rating(getattr(ticket, "rating", None)),
        }
        return await cls._cache_ticket_state(
            connected_integration_id,
            int(ticket_id),
            resolved_state,
        )

    @classmethod
    async def _create_client(
        cls,
        api: RegosAPI,
        *,
        external_id: str,
        profile: Dict[str, Any],
    ) -> Client:
        add_response = await api.crm.client.add(
            ClientAddRequest(
                external_id=external_id,
                name=_normalize_text(profile.get("display_name"), 120) or "Guest",
                phone=_normalize_phone(profile.get("phone")),
                email=_normalize_email(profile.get("email")),
            )
        )
        if not add_response.ok:
            payload = _result_to_dict(add_response.result)
            raise RuntimeError(
                "Client/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )
        new_client_id = _extract_add_new_id(add_response.result)
        if not new_client_id:
            raise RuntimeError("Client/Add did not return new_id")

        get_response = await api.crm.client.get(
            ClientGetRequest(ids=[int(new_client_id)], limit=1, offset=0)
        )
        rows = get_response.result if get_response.ok and isinstance(get_response.result, list) else []
        if not rows:
            raise RuntimeError("Client/Get did not return created client")
        return rows[0]

    @classmethod
    async def _sync_client_profile_if_needed(
        cls,
        api: RegosAPI,
        client: Client,
        profile: Dict[str, Any],
    ) -> None:
        if not client or not client.id:
            return
        patch: Dict[str, Any] = {}
        display_name = _normalize_text(profile.get("display_name"), 120)
        phone = _normalize_phone(profile.get("phone"))
        email = _normalize_email(profile.get("email"))
        if display_name and _normalize_text(client.name, 120) != display_name:
            patch["name"] = display_name
        if phone and not _normalize_phone(client.phone):
            patch["phone"] = phone
        if email and not _normalize_email(client.email):
            patch["email"] = email
        if not patch:
            return
        await api.crm.client.edit(ClientEditRequest(id=int(client.id), **patch))

    @classmethod
    async def _create_ticket(
        cls,
        api: RegosAPI,
        *,
        runtime: RuntimeConfig,
        client_id: int,
        external_dialog_id: str,
        subject: str,
    ) -> Ticket:
        add_response = await api.crm.ticket.add(
            TicketAddRequest(
                client_id=int(client_id),
                channel_id=int(runtime.channel_id),
                direction=TicketDirectionEnum.Inbound,
                external_dialog_id=external_dialog_id,
                subject=subject,
                responsible_user_id=runtime.default_responsible_user_id,
            )
        )
        if not add_response.ok:
            payload = _result_to_dict(add_response.result)
            raise RuntimeError(
                "Ticket/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        ticket_id = _extract_add_new_id(add_response.result)
        if not ticket_id:
            raise RuntimeError("Ticket/Add did not return new_id")

        get_response = await api.crm.ticket.get(
            TicketGetRequest(ids=[int(ticket_id)], limit=1, offset=0)
        )
        rows = get_response.result if get_response.ok and isinstance(get_response.result, list) else []
        if not rows:
            raise RuntimeError("Ticket/Get did not return created ticket")
        ticket = rows[0]
        if not getattr(ticket, "chat_id", None):
            raise RuntimeError("Ticket/Get did not include chat_id")
        return ticket

    @classmethod
    async def _ensure_chat_context(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        profile: Dict[str, Any],
    ) -> ChatContext:
        cached = await cls._load_cached_context(connected_integration_id, visitor_id)
        if cached:
            await cls._set_ticket_chat_index(
                connected_integration_id,
                int(cached.ticket_id),
                str(cached.chat_id),
            )
            await cls._ensure_chat_revision_exists(
                connected_integration_id,
                str(cached.chat_id),
            )
            return cached

        external_client_id = cls._build_client_external_id(connected_integration_id, visitor_id)
        external_dialog_id = cls._build_ticket_external_dialog_id(connected_integration_id, visitor_id)

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            created_ticket_now = False
            client = await cls._find_client_by_external_id(api, external_client_id)
            if not client or not client.id:
                client = await cls._create_client(
                    api,
                    external_id=external_client_id,
                    profile=profile,
                )
            await cls._sync_client_profile_if_needed(api, client, profile)

            ticket = await cls._find_ticket_by_external_dialog_id(
                api,
                external_dialog_id,
                runtime.channel_id,
            )

            if not ticket or not ticket.id or not getattr(ticket, "chat_id", None):
                subject = cls._build_subject(runtime.ticket_subject_template, visitor_id, profile)
                ticket = await cls._create_ticket(
                    api,
                    runtime=runtime,
                    client_id=int(client.id),
                    external_dialog_id=external_dialog_id,
                    subject=subject,
                )
                created_ticket_now = True

            if (
                created_ticket_now
                and runtime.channel_start_message
                and getattr(ticket, "chat_id", None)
            ):
                try:
                    await api.chat.chat_message.add(
                        ChatMessageAddRequest(
                            chat_id=str(ticket.chat_id),
                            message_type=ChatMessageTypeEnum.Regular,
                            text=runtime.channel_start_message,
                            external_message_id=f"webchat:channel_start:{visitor_id}:{int(ticket.id)}",
                        )
                    )
                except Exception as error:
                    logger.warning(
                        "Failed to send channel start message: ci=%s ticket_id=%s visitor_id=%s error=%s",
                        connected_integration_id,
                        getattr(ticket, "id", None),
                        visitor_id,
                        error,
                    )

        ticket_status = _enum_value(getattr(ticket, "status", None)).strip()
        await cls._cache_ticket_state(
            connected_integration_id,
            int(ticket.id),
            {
                "ticket_status": ticket_status,
                "ticket_closed": ticket_status == TicketStatusEnum.Closed.value,
                "can_write": ticket_status != TicketStatusEnum.Closed.value,
                "ticket_rating": _normalize_rating(getattr(ticket, "rating", None)),
            },
        )
        context = ChatContext(
            visitor_id=visitor_id,
            client_id=int(client.id),
            ticket_id=int(ticket.id),
            chat_id=str(ticket.chat_id),
        )
        await cls._save_cached_context(connected_integration_id, context)
        return context

    @classmethod
    async def _add_message_from_visitor(
        cls,
        connected_integration_id: str,
        context: ChatContext,
        text: str,
        external_message_id: str,
    ) -> str:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=context.chat_id,
                    author_entity_type=ChatEntityTypeEnum.Client,
                    author_entity_id=int(context.client_id),
                    message_type=ChatMessageTypeEnum.Regular,
                    text=text,
                    external_message_id=external_message_id,
                )
            )
        if response.ok:
            new_uuid = str(_result_get(response.result, "new_uuid") or "").strip()
            await cls._bump_chat_revision(
                connected_integration_id,
                str(context.chat_id),
            )
            return new_uuid

        payload = _result_to_dict(response.result)
        error_code = _parse_int(payload.get("error"), None)
        if error_code == ExternalChatCrmChannelConfig.CLOSED_ENTITY_ERROR_CODE:
            raise ChatMessageAddClosedEntityError("ChatMessage/Add rejected for closed entity")
        raise RuntimeError(
            "ChatMessage/Add rejected: "
            f"error={payload.get('error')} description={payload.get('description')}"
        )

    @classmethod
    def _extract_upload_payload(
        cls,
        data: Dict[str, Any],
    ) -> Tuple[str, str, str, int]:
        file_name = _normalize_file_name(
            data.get("file_name") or data.get("name") or data.get("filename")
        )
        extension = _normalize_file_extension(
            data.get("extension") or _guess_extension_from_name(file_name)
        )
        if not extension:
            extension = "bin"

        payload_raw = _extract_base64_payload(
            data.get("data") or data.get("file_data") or data.get("payload")
        )
        payload_compact = "".join(payload_raw.split())
        if not payload_compact:
            raise ValueError("file data is required")
        try:
            file_bytes = base64.b64decode(payload_compact, validate=True)
        except binascii.Error as error:
            raise ValueError("file data must be valid base64") from error
        if not file_bytes:
            raise ValueError("file data is empty")
        max_size = int(ExternalChatCrmChannelConfig.MAX_UPLOAD_FILE_SIZE_BYTES)
        if len(file_bytes) > max_size:
            raise ValueError(f"file is too large (max {max_size} bytes)")

        return file_name, extension, payload_compact, len(file_bytes)

    @classmethod
    async def _add_file_message_from_visitor(
        cls,
        connected_integration_id: str,
        context: ChatContext,
        *,
        text: Optional[str],
        file_name: str,
        extension: str,
        payload_b64: str,
        external_message_id: str,
    ) -> Tuple[str, int]:
        safe_text = _normalize_text(text, ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH)
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            add_file_response = await api.chat.chat_message.add_file(
                ChatMessageAddFileRequest(
                    chat_id=context.chat_id,
                    name=file_name,
                    extension=extension,
                    data=payload_b64,
                )
            )
            if not add_file_response.ok:
                file_payload = _result_to_dict(add_file_response.result)
                file_error_code = _parse_int(file_payload.get("error"), None)
                if file_error_code == ExternalChatCrmChannelConfig.CLOSED_ENTITY_ERROR_CODE:
                    raise ChatMessageAddClosedEntityError("ChatMessage/AddFile rejected for closed entity")
                raise RuntimeError(
                    "ChatMessage/AddFile rejected: "
                    f"error={file_payload.get('error')} description={file_payload.get('description')}"
                )
            file_id = _parse_int(_result_get(add_file_response.result, "file_id"), None)
            if not file_id:
                raise RuntimeError("ChatMessage/AddFile did not return file_id")

            add_message_response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=context.chat_id,
                    author_entity_type=ChatEntityTypeEnum.Client,
                    author_entity_id=int(context.client_id),
                    message_type=ChatMessageTypeEnum.Regular,
                    text=safe_text or None,
                    file_ids=[int(file_id)],
                    external_message_id=external_message_id,
                )
            )
            if not add_message_response.ok:
                message_payload = _result_to_dict(add_message_response.result)
                message_error_code = _parse_int(message_payload.get("error"), None)
                if message_error_code == ExternalChatCrmChannelConfig.CLOSED_ENTITY_ERROR_CODE:
                    raise ChatMessageAddClosedEntityError("ChatMessage/Add rejected for closed entity")
                raise RuntimeError(
                    "ChatMessage/Add rejected: "
                    f"error={message_payload.get('error')} description={message_payload.get('description')}"
                )
            message_id = str(_result_get(add_message_response.result, "new_uuid") or "").strip()
            if not message_id:
                raise RuntimeError("ChatMessage/Add did not return new_uuid")

        await cls._bump_chat_revision(
            connected_integration_id,
            str(context.chat_id),
        )
        return message_id, int(file_id)

    @staticmethod
    def _is_duplicate_external_message_error(payload: Dict[str, Any]) -> bool:
        description = str(payload.get("description") or "").strip().lower()
        if not description:
            return False
        return any(
            token in description
            for token in ("duplicate", "already", "exists", "external_message_id")
        )

    @classmethod
    async def _mark_ticket_once_flag(
        cls,
        connected_integration_id: str,
        ticket_id: int,
        flag: str,
    ) -> bool:
        if not ticket_id or not str(flag or "").strip():
            return False
        if not _redis_enabled():
            return True
        return await cls._redis_set_nx(
            cls._ticket_once_flag_key(connected_integration_id, int(ticket_id), flag),
            "1",
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )

    @classmethod
    async def _add_system_message(
        cls,
        connected_integration_id: str,
        *,
        chat_id: str,
        text: str,
        external_message_id: str,
    ) -> bool:
        safe_chat_id = str(chat_id or "").strip()
        safe_text = _normalize_text(text, 300)
        safe_external_message_id = str(external_message_id or "").strip()
        if not safe_chat_id or not safe_text or not safe_external_message_id:
            return False

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=safe_chat_id,
                    message_type=ChatMessageTypeEnum.Regular,
                    text=safe_text,
                    external_message_id=safe_external_message_id,
                )
            )
        if response.ok:
            await cls._bump_chat_revision(
                connected_integration_id,
                safe_chat_id,
            )
            return True

        payload = _result_to_dict(response.result)
        if cls._is_duplicate_external_message_error(payload):
            return False
        logger.warning(
            "ChatMessage/Add rejected for system message: ci=%s chat_id=%s external_message_id=%s payload=%s",
            connected_integration_id,
            safe_chat_id,
            safe_external_message_id,
            response.result,
        )
        return False

    @classmethod
    async def _send_ticket_closed_message_if_needed(
        cls,
        connected_integration_id: str,
        *,
        runtime: RuntimeConfig,
        ticket_id: int,
        chat_id: str,
    ) -> bool:
        if not runtime.channel_end_message:
            return False
        if not await cls._mark_ticket_once_flag(
            connected_integration_id,
            int(ticket_id),
            "end_message_sent",
        ):
            return False
        return await cls._add_system_message(
            connected_integration_id,
            chat_id=chat_id,
            text=runtime.channel_end_message,
            external_message_id=f"webchat:channel_end:{int(ticket_id)}",
        )

    @classmethod
    async def _read_history(
        cls,
        connected_integration_id: str,
        context: ChatContext,
        limit: int,
    ) -> List[Dict[str, Any]]:
        resolved_limit = min(
            max(int(limit or ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT), 1),
            ExternalChatCrmChannelConfig.MAX_HISTORY_LIMIT,
        )
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=context.chat_id,
                    limit=resolved_limit,
                    offset=0,
                    include_staff_private=False,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        history: List[Dict[str, Any]] = []
        for row in rows:
            message_type = _enum_value(getattr(row, "message_type", None)).strip() or ChatMessageTypeEnum.Regular.value
            if message_type in {
                ChatMessageTypeEnum.Private.value,
                ChatMessageTypeEnum.System.value,
            }:
                continue
            author_type = _enum_value(getattr(row, "author_entity_type", None)).strip().lower()
            author_id = _parse_int(getattr(row, "author_entity_id", None), None)
            mine = author_type == ChatEntityTypeEnum.Client.value.lower() and author_id == context.client_id
            text = _normalize_text(getattr(row, "text", ""), ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH)
            if not text and getattr(row, "file_ids", None):
                text = "[Attachment]"
            history.append(
                {
                    "id": str(getattr(row, "id", "") or ""),
                    "text": text,
                    "created_date": _parse_int(getattr(row, "created_date", None), 0) or 0,
                    "message_type": message_type,
                    "mine": bool(mine),
                    "edited": bool(getattr(row, "edited", False)),
                    "author_name": _normalize_text(getattr(row, "author_entity_name", ""), 120),
                }
            )
        history.sort(key=lambda item: (int(item.get("created_date") or 0), str(item.get("id") or "")))
        return history[-resolved_limit:]

    @classmethod
    async def _mark_read(
        cls,
        connected_integration_id: str,
        context: ChatContext,
    ) -> None:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            await api.chat.chat_message.mark_read(
                ChatMessageMarkReadRequest(chat_id=context.chat_id)
            )

    @staticmethod
    def _extract_profile(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "display_name": _normalize_text(data.get("display_name"), 120),
            "email": _normalize_email(data.get("email")),
            "phone": _normalize_phone(data.get("phone")),
        }

    @staticmethod
    def _missing_required_profile_fields(
        runtime: RuntimeConfig,
        profile: Dict[str, Any],
    ) -> List[str]:
        missing: List[str] = []
        if runtime.require_display_name and not _normalize_text(profile.get("display_name"), 120):
            missing.append("display_name")
        if runtime.require_phone and not _normalize_phone(profile.get("phone")):
            missing.append("phone")
        if runtime.require_email and not _normalize_email(profile.get("email")):
            missing.append("email")
        return missing

    def _resolve_ci_from_envelope(self, envelope: Dict[str, Any]) -> Optional[str]:
        if self.connected_integration_id:
            return str(self.connected_integration_id).strip()

        headers = envelope.get("headers") or {}
        query = envelope.get("query") or {}
        body = envelope.get("body")

        ci = _headers_ci(headers, "Connected-Integration-Id")
        if ci:
            return ci

        for key in ("ci", "connected_integration_id", "connected-integration-id"):
            ci = _query_get(query, key)
            if ci:
                return ci

        if isinstance(body, dict):
            for key in ("ci", "connected_integration_id"):
                value = str(body.get(key) or "").strip()
                if value:
                    return value
        return None

    @classmethod
    def _load_ui_template(cls) -> str:
        if cls._UI_TEMPLATE_CACHE is not None:
            return cls._UI_TEMPLATE_CACHE

        try:
            cls._UI_TEMPLATE_CACHE = cls._UI_TEMPLATE_PATH.read_text(encoding="utf-8")
        except Exception as error:
            logger.exception("Failed to load UI template: %s", error)
            cls._UI_TEMPLATE_CACHE = "<!doctype html><html><body><h1>UI template is unavailable</h1></body></html>"
        return cls._UI_TEMPLATE_CACHE

    @staticmethod
    def _ui_html(
        *,
        connected_integration_id: str,
        title: str,
        require_display_name: bool,
        require_phone: bool,
        require_email: bool,
        chat_theme_vars: Dict[str, str],
    ) -> str:
        safe_title = html.escape(title)
        safe_ci = html.escape(connected_integration_id)
        safe_require_display_name = "true" if require_display_name else "false"
        safe_require_phone = "true" if require_phone else "false"
        safe_require_email = "true" if require_email else "false"

        theme_vars = dict(ExternalChatCrmChannelConfig.DEFAULT_THEME_VARS)
        for key, value in (chat_theme_vars or {}).items():
            if key in _ALLOWED_THEME_KEYS:
                theme_vars[key] = value
        theme_vars_css = "\n".join(
            f"      {key}: {value};" for key, value in theme_vars.items()
        )

        template = ExternalChatCrmChannelIntegration._load_ui_template()
        prepared_template = template.replace(
            "{ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH}",
            str(ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH),
        ).replace(
            "{ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT}",
            str(ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT),
        ).replace(
            "{ExternalChatCrmChannelConfig.MAX_UPLOAD_FILE_SIZE_BYTES}",
            str(ExternalChatCrmChannelConfig.MAX_UPLOAD_FILE_SIZE_BYTES),
        )
        return prepared_template.format(
            safe_title=safe_title,
            safe_ci=safe_ci,
            safe_require_display_name=safe_require_display_name,
            safe_require_phone=safe_require_phone,
            safe_require_email=safe_require_email,
            theme_vars_css=theme_vars_css,
        )

    @classmethod
    async def _subscribe_required_webhooks(
        cls,
        connected_integration_id: str,
    ) -> Dict[str, Any]:
        required = sorted(ExternalChatCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS)
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.integrations.connected_integration.edit(
                    ConnectedIntegrationEditRequest(
                        connected_integration_id=connected_integration_id,
                        webhooks=required,
                    )
                )
            if not response.ok:
                logger.warning(
                    "Webhook subscription rejected for %s: %s",
                    connected_integration_id,
                    response.result,
                )
                return {"status": "failed", "error": str(response.result), "webhooks": required}
            return {"status": "ok", "webhooks": required}
        except Exception as error:
            logger.warning(
                "Webhook subscription failed for %s: %s",
                connected_integration_id,
                error,
            )
            return {"status": "failed", "error": str(error), "webhooks": required}

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        if not await self._is_connected_integration_active(ci, force_refresh=True):
            return self._error_response(1001, f"ConnectedIntegration '{ci}' is inactive").dict()
        try:
            runtime = await self._load_runtime(ci)
        except Exception as error:
            return self._error_response(1002, str(error)).dict()
        webhook_subscribe = await self._subscribe_required_webhooks(ci)
        return {
            "status": "connected",
            "channel_id": runtime.channel_id,
            "chat_title": runtime.chat_title,
            "chat_theme_vars": runtime.chat_theme_vars,
            "required_profile_fields": {
                "display_name": runtime.require_display_name,
                "phone": runtime.require_phone,
                "email": runtime.require_email,
            },
            "webhooks_subscription": webhook_subscribe,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        await self._redis_delete(self._settings_cache_key(ci), self._active_cache_key(ci))
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Any:
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Any:
        _ = settings
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        await self._redis_delete(self._settings_cache_key(ci), self._active_cache_key(ci))
        return {"status": "settings updated", "reconnect": await self.reconnect()}

    @staticmethod
    def _normalize_regos_webhook_payload(
        action: Optional[str],
        data: Optional[Dict[str, Any]],
        extra: Dict[str, Any],
    ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
        event_id = str(extra.get("event_id") or "").strip() or None

        if isinstance(action, str) and action in ExternalChatCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
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

        return None, {}, event_id

    @staticmethod
    def _build_webhook_event_key(
        webhook_action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
    ) -> str:
        event_id_value = str(event_id or "").strip()
        if event_id_value:
            return f"event:{event_id_value}"

        ticket_id = _parse_int(payload.get("id"), None)
        chat_id = str(payload.get("chat_id") or "").strip()
        if chat_id and ticket_id:
            return f"{webhook_action}:chat:{chat_id}:ticket:{ticket_id}"
        if chat_id:
            return f"{webhook_action}:chat:{chat_id}"
        if ticket_id:
            return f"{webhook_action}:ticket:{ticket_id}"
        try:
            payload_key = _json_dumps(payload)
        except Exception:
            payload_key = str(payload or "")
        return f"{webhook_action}:{payload_key}"

    async def _is_duplicate_webhook_event(
        self,
        connected_integration_id: str,
        event_key: str,
    ) -> bool:
        if not _redis_enabled():
            return False
        ttl = ExternalChatCrmChannelConfig.WEBHOOK_DEDUPE_TTL_SEC
        inserted = await self._redis_set_nx(
            self._redis_key("webhook_dedupe", connected_integration_id, event_key),
            "1",
            ttl,
        )
        return not inserted

    @classmethod
    async def _apply_chat_message_webhook(
        cls,
        connected_integration_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            return {"status": "ignored", "reason": "invalid_payload:chat_id"}

        revision = await cls._bump_chat_revision(connected_integration_id, chat_id)
        return {"status": "processed", "chat_id": chat_id, "chat_revision": revision}

    @classmethod
    async def _apply_ticket_webhook(
        cls,
        connected_integration_id: str,
        webhook_action: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        ticket_id = _parse_int(payload.get("id"), None)
        if not ticket_id:
            return {"status": "ignored", "reason": "invalid_payload:id"}

        status_value = _enum_value(payload.get("status")).strip()
        if webhook_action == "TicketClosed" and not status_value:
            status_value = TicketStatusEnum.Closed.value
        ticket_closed = status_value == TicketStatusEnum.Closed.value
        ticket_rating = _normalize_rating(payload.get("rating"))

        state = await cls._cache_ticket_state(
            connected_integration_id,
            int(ticket_id),
            {
                "ticket_status": status_value,
                "ticket_closed": ticket_closed,
                "can_write": not ticket_closed,
                "ticket_rating": ticket_rating,
            },
        )

        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            chat_id = await cls._get_ticket_chat_index(connected_integration_id, int(ticket_id)) or ""
        else:
            await cls._set_ticket_chat_index(
                connected_integration_id,
                int(ticket_id),
                chat_id,
            )

        ticket: Optional[Ticket] = None
        if not status_value or not chat_id:
            try:
                async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                    ticket = await cls._load_ticket_by_id(api, int(ticket_id))
            except Exception:
                ticket = None
            if ticket:
                ticket_rating = _normalize_rating(getattr(ticket, "rating", None))
                if not status_value:
                    status_value = _enum_value(getattr(ticket, "status", None)).strip()
                    ticket_closed = status_value == TicketStatusEnum.Closed.value
                if not chat_id:
                    chat_id = str(getattr(ticket, "chat_id", "") or "").strip()
                    if chat_id:
                        await cls._set_ticket_chat_index(
                            connected_integration_id,
                            int(ticket_id),
                            chat_id,
                        )
                state = await cls._cache_ticket_state(
                    connected_integration_id,
                    int(ticket_id),
                    {
                        "ticket_status": status_value,
                        "ticket_closed": ticket_closed,
                        "can_write": not ticket_closed,
                        "ticket_rating": ticket_rating,
                    },
                )

        revision = 0
        if chat_id:
            revision = await cls._bump_chat_revision(connected_integration_id, chat_id)
            if ticket_closed:
                try:
                    runtime = await cls._load_runtime(connected_integration_id)
                    await cls._send_ticket_closed_message_if_needed(
                        connected_integration_id,
                        runtime=runtime,
                        ticket_id=int(ticket_id),
                        chat_id=chat_id,
                    )
                except Exception as error:
                    logger.warning(
                        "Failed to send ticket close message: ci=%s ticket_id=%s chat_id=%s error=%s",
                        connected_integration_id,
                        ticket_id,
                        chat_id,
                        error,
                    )

        return {
            "status": "processed",
            "ticket_id": int(ticket_id),
            "chat_id": chat_id or None,
            "chat_revision": revision,
            **state,
        }

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id).strip()
        if not await self._is_connected_integration_active(ci):
            return {"status": "ignored", "reason": "connected_integration_inactive"}

        webhook_action, payload, event_id = self._normalize_regos_webhook_payload(
            action=action,
            data=data,
            extra=extra,
        )
        if webhook_action not in ExternalChatCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{webhook_action}"}

        event_key = self._build_webhook_event_key(webhook_action, payload, event_id)
        if await self._is_duplicate_webhook_event(ci, event_key):
            return {"status": "ignored", "reason": "duplicate_event"}

        try:
            if webhook_action in {"ChatMessageAdded", "ChatMessageEdited", "ChatMessageDeleted"}:
                result = await self._apply_chat_message_webhook(ci, payload)
            else:
                result = await self._apply_ticket_webhook(ci, webhook_action, payload)
        except Exception as error:
            logger.exception(
                "Webhook processing failed: ci=%s action=%s payload=%s",
                ci,
                webhook_action,
                payload,
            )
            return self._error_response(1002, str(error)).dict()

        return {
            "status": result.get("status", "processed"),
            "action": webhook_action,
            "event_id": event_id,
            **{key: value for key, value in result.items() if key != "status"},
        }

    async def handle_ui(self, envelope: Dict[str, Any]) -> Any:
        if str(envelope.get("method") or "").upper() != "GET":
            return Response(status_code=405, content="Method not allowed")

        ci = self._resolve_ci_from_envelope(envelope)
        if not ci:
            return HTMLResponse("<h1>Missing connected integration id</h1>", status_code=400)

        if not await self._is_connected_integration_active(ci):
            return HTMLResponse(
                f"<h1>ConnectedIntegration '{html.escape(ci)}' is inactive</h1>",
                status_code=403,
            )
        try:
            runtime = await self._load_runtime(ci)
        except Exception as error:
            return HTMLResponse(
                f"<h1>Configuration error</h1><p>{html.escape(str(error))}</p>",
                status_code=400,
            )

        return HTMLResponse(
            self._ui_html(
                connected_integration_id=ci,
                title=runtime.chat_title,
                require_display_name=runtime.require_display_name,
                require_phone=runtime.require_phone,
                require_email=runtime.require_email,
                chat_theme_vars=runtime.chat_theme_vars,
            ),
            status_code=200,
        )

    async def handle_external(self, envelope: Dict[str, Any]) -> Any:
        method = str(envelope.get("method") or "").upper()
        body = envelope.get("body")

        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", errors="ignore")
        if isinstance(body, str):
            try:
                body = _json_loads(body)
            except Exception:
                body = {}
        if body is None:
            body = {}
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"error": 400, "description": "Invalid JSON body"})

        ci = self._resolve_ci_from_envelope({**envelope, "body": body})
        if not ci:
            return JSONResponse(
                status_code=400,
                content={"error": 400, "description": "connected_integration_id is required"},
            )

        if not await self._is_connected_integration_active(ci):
            return JSONResponse(
                status_code=403,
                content={"error": 403, "description": f"ConnectedIntegration '{ci}' is inactive"},
            )

        if method == "GET":
            return {"status": "ok", "connected_integration_id": ci}
        if method != "POST":
            return JSONResponse(status_code=405, content={"error": 405, "description": "Method not allowed"})

        action = _normalize_text(body.get("action"), 64).lower()
        data = body.get("data")
        data = data if isinstance(data, dict) else {}

        visitor_id = self._normalize_visitor_id(data.get("visitor_id"))
        if action == "init" and not visitor_id:
            visitor_id = self._normalize_visitor_id(uuid.uuid4().hex)
        if not visitor_id:
            return JSONResponse(
                status_code=400,
                content={"error": 400, "description": "visitor_id is required"},
            )

        try:
            runtime = await self._load_runtime(ci)
        except Exception as error:
            return JSONResponse(
                status_code=400,
                content={"error": 400, "description": str(error)},
            )

        profile = self._extract_profile(data)
        missing_required_fields = self._missing_required_profile_fields(runtime, profile)
        if missing_required_fields:
            return JSONResponse(
                status_code=400,
                content={
                    "error": 400,
                    "description": "Missing required profile fields",
                    "missing_fields": missing_required_fields,
                    "required_profile_fields": {
                        "display_name": runtime.require_display_name,
                        "phone": runtime.require_phone,
                        "email": runtime.require_email,
                    },
                },
            )

        context = await self._ensure_chat_context(
            connected_integration_id=ci,
            runtime=runtime,
            visitor_id=visitor_id,
            profile=profile,
        )

        try:
            if action == "init":
                ticket_state = await self._get_ticket_write_state(
                    ci,
                    int(context.ticket_id),
                    force_refresh=True,
                )
                ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                history = await self._read_history(
                    ci,
                    context,
                    ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT,
                )
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "chat_title": runtime.chat_title,
                    "chat_theme_vars": runtime.chat_theme_vars,
                    "required_profile_fields": {
                        "display_name": runtime.require_display_name,
                        "phone": runtime.require_phone,
                        "email": runtime.require_email,
                    },
                    "chat_revision": chat_revision,
                    "history_changed": True,
                    **ticket_view,
                    "history": history,
                }

            if action == "history":
                force_full = _parse_bool(data.get("force_full"), False)
                ticket_state = await self._get_ticket_write_state(
                    ci,
                    int(context.ticket_id),
                    force_refresh=force_full,
                )
                ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                known_revision = _parse_int(data.get("known_revision"), None)
                limit = _parse_int(
                    data.get("limit"),
                    ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT,
                )
                if (
                    not force_full
                    and known_revision is not None
                    and int(chat_revision) > 0
                    and int(known_revision) == int(chat_revision)
                ):
                    return {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        "chat_revision": chat_revision,
                        "history_changed": False,
                        **ticket_view,
                    }
                history = await self._read_history(
                    ci,
                    context,
                    int(limit or ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT),
                )
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "chat_revision": chat_revision,
                    "history_changed": True,
                    **ticket_view,
                    "history": history,
                }

            if action == "send_message":
                text = _normalize_text(
                    data.get("text"),
                    ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
                )
                if not text:
                    return JSONResponse(
                        status_code=400,
                        content={"error": 400, "description": "text is required"},
                    )
                ticket_state, ticket_view = await self._load_ticket_view_for_write(
                    runtime,
                    connected_integration_id=ci,
                    ticket_id=int(context.ticket_id),
                )
                if not ticket_state.get("can_write", True):
                    return self._ticket_closed_response(visitor_id, ticket_view)
                ext_id = f"webchat:msg:{visitor_id}:{uuid.uuid4().hex[:12]}"
                try:
                    message_id = await self._add_message_from_visitor(
                        connected_integration_id=ci,
                        context=context,
                        text=text,
                        external_message_id=ext_id,
                    )
                except ChatMessageAddClosedEntityError:
                    closed_view = await self._cache_closed_ticket_view(
                        runtime,
                        connected_integration_id=ci,
                        ticket_id=int(context.ticket_id),
                    )
                    return self._ticket_closed_response(visitor_id, closed_view)
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "message_id": message_id,
                    "chat_revision": chat_revision,
                    **ticket_view,
                }

            if action == "send_file":
                try:
                    file_name, extension, payload_b64, file_size = self._extract_upload_payload(data)
                except ValueError as error:
                    return JSONResponse(
                        status_code=400,
                        content={"error": 400, "description": str(error)},
                    )
                text = _normalize_text(
                    data.get("text"),
                    ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
                )
                ticket_state, ticket_view = await self._load_ticket_view_for_write(
                    runtime,
                    connected_integration_id=ci,
                    ticket_id=int(context.ticket_id),
                )
                if not ticket_state.get("can_write", True):
                    return self._ticket_closed_response(visitor_id, ticket_view)

                ext_id = f"webchat:file:{visitor_id}:{uuid.uuid4().hex[:12]}"
                try:
                    message_id, file_id = await self._add_file_message_from_visitor(
                        connected_integration_id=ci,
                        context=context,
                        text=text,
                        file_name=file_name,
                        extension=extension,
                        payload_b64=payload_b64,
                        external_message_id=ext_id,
                    )
                except ChatMessageAddClosedEntityError:
                    closed_view = await self._cache_closed_ticket_view(
                        runtime,
                        connected_integration_id=ci,
                        ticket_id=int(context.ticket_id),
                    )
                    return self._ticket_closed_response(visitor_id, closed_view)
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "message_id": message_id,
                    "file_id": int(file_id),
                    "file_name": file_name,
                    "file_size": int(file_size),
                    "chat_revision": chat_revision,
                    **ticket_view,
                }

            if action == "set_rating":
                rating = _normalize_rating(data.get("rating"))
                if rating is None:
                    return JSONResponse(
                        status_code=400,
                        content={"error": 400, "description": "rating must be integer from 1 to 5"},
                    )

                ticket_state = await self._get_ticket_write_state(
                    ci,
                    int(context.ticket_id),
                    force_refresh=True,
                )
                ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
                if not ticket_view.get("ticket_closed", False):
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": 409,
                            "description": "Ticket is not closed",
                            "visitor_id": visitor_id,
                            **ticket_view,
                        },
                    )
                if not ticket_view.get("rating_enabled", False):
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": 409,
                            "description": "Rating is disabled",
                            "visitor_id": visitor_id,
                            **ticket_view,
                        },
                    )
                if ticket_view.get("rating_submitted", False):
                    return {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        "rating_saved": False,
                        "already_rated": True,
                        **ticket_view,
                    }

                async with RegosAPI(connected_integration_id=ci) as api:
                    set_rating_response = await api.crm.ticket.set_rating(
                        TicketSetRatingRequest(
                            id=int(context.ticket_id),
                            rating=int(rating),
                        )
                    )

                if not set_rating_response.ok:
                    payload = _result_to_dict(set_rating_response.result)
                    description = str(payload.get("description") or "").strip().lower()
                    already_rated = any(
                        token in description
                        for token in ("already", "repeat", "rated", "exists")
                    )
                    refreshed_state = await self._get_ticket_write_state(
                        ci,
                        int(context.ticket_id),
                        force_refresh=True,
                    )
                    refreshed_view = self._compose_ticket_view_state(runtime, refreshed_state)
                    if already_rated or refreshed_view.get("rating_submitted", False):
                        return {
                            "status": "ok",
                            "visitor_id": visitor_id,
                            "rating_saved": False,
                            "already_rated": True,
                            **refreshed_view,
                        }
                    return JSONResponse(
                        status_code=500,
                        content={
                            "error": 500,
                            "description": "Failed to save rating",
                            "visitor_id": visitor_id,
                            **refreshed_view,
                        },
                    )

                saved_state = await self._cache_ticket_state(
                    ci,
                    int(context.ticket_id),
                    {"ticket_rating": int(rating)},
                )
                followup_text = (
                    runtime.channel_rating_positive_message
                    if int(rating) >= ExternalChatCrmChannelConfig.RATING_POSITIVE_THRESHOLD
                    else runtime.channel_rating_negative_message
                )
                if followup_text:
                    await self._add_system_message(
                        ci,
                        chat_id=context.chat_id,
                        text=followup_text,
                        external_message_id=(
                            f"webchat:channel_rating_result:{int(context.ticket_id)}:{int(rating)}"
                        ),
                    )
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                saved_view = self._compose_ticket_view_state(runtime, saved_state)
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "rating_saved": True,
                    "already_rated": False,
                    "chat_revision": chat_revision,
                    **saved_view,
                }

            if action == "mark_read":
                await self._mark_read(ci, context)
                ticket_state = await self._get_ticket_write_state(ci, int(context.ticket_id))
                ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "chat_revision": chat_revision,
                    **ticket_view,
                }

            return JSONResponse(
                status_code=400,
                content={"error": 400, "description": f"Unsupported action '{action}'"},
            )
        except Exception as error:
            logger.exception(
                "External chat action failed: ci=%s action=%s visitor_id=%s",
                ci,
                action,
                visitor_id,
            )
            return JSONResponse(
                status_code=500,
                content={"error": 500, "description": str(error)},
            )
