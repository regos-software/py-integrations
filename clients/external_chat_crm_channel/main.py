from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
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
from schemas.api.files.file import FileGetRequest
from schemas.api.integrations.connected_integration import (
    ConnectedIntegrationEditRequest,
    ConnectedIntegrationGetRequest,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("external_chat_crm_channel")

_BBCODE_SIMPLE_REPLACEMENTS: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"(?is)\[b\]"), "**"),
    (re.compile(r"(?is)\[/b\]"), "**"),
    (re.compile(r"(?is)\[i\]"), "_"),
    (re.compile(r"(?is)\[/i\]"), "_"),
    (re.compile(r"(?is)\[u\]"), "++"),
    (re.compile(r"(?is)\[/u\]"), "++"),
    (re.compile(r"(?is)\[s\]"), "~~"),
    (re.compile(r"(?is)\[/s\]"), "~~"),
    (re.compile(r"(?is)\[br\s*/?\]"), "\n"),
)
_BBCODE_URL_LABEL_RE = re.compile(r"(?is)\[url=(.*?)\](.*?)\[/url\]")
_BBCODE_URL_SIMPLE_RE = re.compile(r"(?is)\[url\](.*?)\[/url\]")
_BBCODE_CODE_RE = re.compile(r"(?is)\[code\](.*?)\[/code\]")
_BBCODE_QUOTE_RE = re.compile(r"(?is)\[quote\](.*?)\[/quote\]")
_IMAGE_FILE_EXTENSIONS = {
    "apng",
    "avif",
    "bmp",
    "gif",
    "heic",
    "heif",
    "ico",
    "jpeg",
    "jpg",
    "png",
    "svg",
    "webp",
}


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
    FILE_META_CACHE_TTL_SEC = 10 * 60
    MAX_FILE_META_BATCH = 200
    FILE_META_CACHE_MAX_ITEMS = 5000
    DEFAULT_CHAT_TITLE = "Support Chat"
    DEFAULT_SUBJECT_TEMPLATE = "{channel_name} {display_name}"
    CLOSED_ENTITY_ERROR_CODE = 1220
    CHAT_REVISION_DEFAULT = 1
    WEBHOOK_DEDUPE_TTL_SEC = 10 * 60
    EVENT_QUEUE_TTL_SEC = 6 * 60 * 60
    EVENT_QUEUE_MAX_ITEMS = 500
    EVENT_BATCH_MAX_ITEMS = 30
    EVENT_LONGPOLL_TIMEOUT_SEC = 25
    EVENT_LONGPOLL_TIMEOUT_MAX_SEC = 30
    RATING_POSITIVE_THRESHOLD = 4
    SUPPORTED_INBOUND_WEBHOOKS = {
        "ChatMessageAdded",
        "ChatMessageEdited",
        "ChatMessageDeleted",
        "TicketStatusSet",
        "TicketClosed",
    }


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    channel_id: int
    ticket_subject_template: str
    default_responsible_user_id: Optional[int]
    channel_name: str
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
    chat_css_url: Optional[str]


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


def _normalize_message_markup(value: Any, max_len: int = 500) -> str:
    normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""

    for pattern, replacement in _BBCODE_SIMPLE_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)

    def _replace_url_with_label(match: re.Match) -> str:
        url = str(match.group(1) or "").strip()
        label = str(match.group(2) or "").strip()
        if not url and not label:
            return ""
        final_url = url or label
        final_label = label or final_url
        return f"[{final_label}]({final_url})"

    def _replace_url_simple(match: re.Match) -> str:
        url = str(match.group(1) or "").strip()
        if not url:
            return ""
        return f"[{url}]({url})"

    def _replace_code(match: re.Match) -> str:
        body = str(match.group(1) or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not body:
            return ""
        return f"```\n{body}\n```"

    def _replace_quote(match: re.Match) -> str:
        body = str(match.group(1) or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not body:
            return ""
        lines = body.split("\n")
        return "\n".join(f"> {line}" if line else ">" for line in lines)

    normalized = _BBCODE_URL_LABEL_RE.sub(_replace_url_with_label, normalized)
    normalized = _BBCODE_URL_SIMPLE_RE.sub(_replace_url_simple, normalized)
    normalized = _BBCODE_CODE_RE.sub(_replace_code, normalized)
    normalized = _BBCODE_QUOTE_RE.sub(_replace_quote, normalized)
    return _normalize_text(normalized, max_len)


def _parse_file_ids(value: Any) -> List[int]:
    if not isinstance(value, list):
        return []
    seen: Dict[int, bool] = {}
    normalized: List[int] = []
    for row in value:
        file_id = _parse_int(row, None)
        if not file_id or int(file_id) <= 0:
            continue
        safe_file_id = int(file_id)
        if seen.get(safe_file_id):
            continue
        seen[safe_file_id] = True
        normalized.append(safe_file_id)
    return normalized


def _is_image_file(extension: Any, mime_type: Any) -> bool:
    ext = _normalize_file_extension(extension)
    mime = str(mime_type or "").strip().lower()
    if mime.startswith("image/"):
        return True
    return ext in _IMAGE_FILE_EXTENSIONS


def _parse_chat_css_url(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if len(value) > 500:
        raise ValueError("chat_css_url is too long")
    lowered = value.lower()
    if lowered.startswith(("javascript:", "data:", "vbscript:")):
        raise ValueError("chat_css_url has unsupported scheme")
    if any(ch.isspace() for ch in value):
        raise ValueError("chat_css_url must not contain spaces")
    if any(ch in value for ch in {'"', "'", "<", ">", "`"}):
        raise ValueError("chat_css_url contains unsupported characters")
    if lowered.startswith(("http://", "https://")):
        return value
    if value.startswith(("/", "./", "../")):
        return value
    raise ValueError("chat_css_url must be http(s) URL or relative path")


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


def _payload_fingerprint(payload: Any) -> str:
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        raw = str(payload or "")
    digest = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()
    return digest[:24]


def _extract_add_new_id(result: Any) -> Optional[int]:
    direct = _parse_int(str(result), None)
    if direct and direct > 0:
        return int(direct)
    for key in ("new_id", "id", "ticket_id", "client_id"):
        value = _parse_int(str(_result_get(result, key) or ""), None)
        if value and value > 0:
            return int(value)
    return None


def _looks_like_duplicate_error(payload: Dict[str, Any]) -> bool:
    description = str(payload.get("description") or "").strip().lower()
    if not description:
        return False
    return any(
        token in description
        for token in (
            "duplicate",
            "already",
            "exists",
            "unique",
            "external_id",
            "external_message_id",
            "external dialog",
            "external_dialog",
        )
    )


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
    _FILE_META_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
    _UI_TEMPLATE_CACHE: Optional[str] = None
    _UI_CSS_TEMPLATE_CACHE: Optional[str] = None
    _UI_I18N_CACHE: Optional[Dict[str, Dict[str, str]]] = None
    _UI_TEMPLATE_PATH = Path(__file__).with_name("ui_template.html")
    _UI_CSS_TEMPLATE_PATH = Path(__file__).with_name("ui_template.css")
    _UI_I18N_DIR_PATH = Path(__file__).with_name("i18n")

    _ACTIVE_CACHE_LOCK = asyncio.Lock()
    _FILE_META_CACHE_LOCK = asyncio.Lock()

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
    def _chat_events_stream_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("events_stream", connected_integration_id, chat_id)

    @classmethod
    def _chat_events_revision_dedupe_key(
        cls,
        connected_integration_id: str,
        chat_id: str,
        chat_revision: int,
    ) -> str:
        return cls._redis_key("events_stream_dedupe", connected_integration_id, chat_id, int(chat_revision))

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
    async def _publish_chat_event(
        cls,
        connected_integration_id: str,
        *,
        chat_id: str,
        event_type: str,
        source_action: Optional[str] = None,
        chat_revision: Optional[int] = None,
        ticket_id: Optional[int] = None,
        force_full: bool = False,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        safe_chat_id = str(chat_id or "").strip()
        if not safe_chat_id or not _redis_enabled():
            return
        safe_revision = int(chat_revision or 0)
        if safe_revision > 0:
            dedupe_key = cls._chat_events_revision_dedupe_key(
                connected_integration_id,
                safe_chat_id,
                safe_revision,
            )
            is_first = await cls._redis_set_nx(
                dedupe_key,
                "1",
                max(int(ExternalChatCrmChannelConfig.WEBHOOK_DEDUPE_TTL_SEC or 1), 1),
            )
            if not is_first:
                return

        stream_key = cls._chat_events_stream_key(connected_integration_id, safe_chat_id)
        ttl_sec = max(int(ExternalChatCrmChannelConfig.EVENT_QUEUE_TTL_SEC or 1), 1)
        max_items = max(int(ExternalChatCrmChannelConfig.EVENT_QUEUE_MAX_ITEMS or 1), 1)

        event: Dict[str, Any] = {
            "type": str(event_type or "").strip() or "chat_event",
            "source_action": str(source_action or "").strip() or None,
            "chat_id": safe_chat_id,
            "ticket_id": int(ticket_id) if ticket_id else None,
            "chat_revision": safe_revision if safe_revision > 0 else None,
            "api_action": "history",
            "force_full": bool(force_full),
            "created_at": int(time.time()),
            "payload": payload if isinstance(payload, dict) else {},
        }
        serialized = _json_dumps(event)
        await redis_client.xadd(
            stream_key,
            {"payload": serialized},
            maxlen=max_items,
            approximate=True,
        )
        await redis_client.expire(stream_key, ttl_sec)

    @classmethod
    async def _poll_chat_events(
        cls,
        connected_integration_id: str,
        *,
        chat_id: str,
        last_event_id: str,
        timeout_sec: int,
        max_items: int,
    ) -> List[Dict[str, Any]]:
        safe_chat_id = str(chat_id or "").strip()
        if not safe_chat_id or not _redis_enabled():
            return []

        stream_key = cls._chat_events_stream_key(connected_integration_id, safe_chat_id)
        resolved_timeout = min(
            max(int(timeout_sec or ExternalChatCrmChannelConfig.EVENT_LONGPOLL_TIMEOUT_SEC), 1),
            int(ExternalChatCrmChannelConfig.EVENT_LONGPOLL_TIMEOUT_MAX_SEC),
        )
        resolved_max_items = min(
            max(int(max_items or 1), 1),
            int(ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS),
        )
        cursor = str(last_event_id or "").strip()
        if not re.fullmatch(r"\d+-\d+|\$", cursor):
            cursor = "$"
        stream_rows = await redis_client.xread(
            {stream_key: cursor},
            count=resolved_max_items,
            block=resolved_timeout * 1000,
        )
        if not stream_rows:
            return []

        events: List[Dict[str, Any]] = []
        for stream_row in stream_rows:
            if not isinstance(stream_row, (tuple, list)) or len(stream_row) != 2:
                continue
            entries = stream_row[1]
            if not isinstance(entries, list):
                continue
            for item in entries:
                if not isinstance(item, (tuple, list)) or len(item) != 2:
                    continue
                event_id = str(item[0] or "").strip()
                fields = item[1] if isinstance(item[1], dict) else {}
                raw = str(fields.get("payload") or "")
                if not raw:
                    continue
                try:
                    payload = _json_loads(raw)
                except Exception:
                    continue
                if not isinstance(payload, dict):
                    continue
                payload["id"] = event_id
                events.append(payload)

        if events:
            await redis_client.expire(
                stream_key,
                max(int(ExternalChatCrmChannelConfig.EVENT_QUEUE_TTL_SEC or 1), 1),
            )
        return events

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
        chat_css_url = _parse_chat_css_url(settings_map.get("chat_css_url"))
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
            channel_name=channel_name or chat_title,
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
            chat_css_url=chat_css_url,
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
    def _build_subject(
        template: str,
        channel_name: str,
        visitor_id: str,
        profile: Dict[str, Any],
    ) -> str:
        safe_channel_name = _normalize_text(channel_name, 80) or "Support Chat"
        display_name = _normalize_text(profile.get("display_name"), 120) or "Guest"
        current_date = time.strftime("%Y-%m-%d")
        try:
            subject = str(template or "").format(
                channel_name=safe_channel_name,
                visitor_id=visitor_id,
                display_name=display_name,
                current_date=current_date,
            )
        except Exception:
            subject = f"{safe_channel_name} {display_name}"
        normalized = _normalize_text(subject, 200)
        return normalized or f"{safe_channel_name} {display_name}"

    @classmethod
    def _file_meta_cache_key(cls, connected_integration_id: str, file_id: int) -> str:
        return f"{connected_integration_id}:{int(file_id)}"

    @staticmethod
    def _build_file_view(file_model: Any) -> Optional[Dict[str, Any]]:
        file_id = _parse_int(getattr(file_model, "id", None), None)
        if not file_id or int(file_id) <= 0:
            return None

        file_name = _normalize_file_name(getattr(file_model, "name", None))
        extension = _normalize_file_extension(
            getattr(file_model, "extension", None) or _guess_extension_from_name(file_name)
        )
        mime_type = _normalize_text(getattr(file_model, "mime_type", None), 120)
        file_size = _parse_int(getattr(file_model, "size", None), None)
        url = _normalize_text(getattr(file_model, "url", None), 2000)
        return {
            "id": int(file_id),
            "name": file_name,
            "url": url,
            "size": int(file_size) if file_size and int(file_size) > 0 else 0,
            "extension": extension,
            "mime_type": mime_type,
            "is_image": _is_image_file(extension, mime_type),
        }

    @classmethod
    async def _read_cached_file_views(
        cls,
        connected_integration_id: str,
        file_ids: List[int],
    ) -> Tuple[Dict[int, Dict[str, Any]], List[int]]:
        if not file_ids:
            return {}, []
        now = time.time()
        cached: Dict[int, Dict[str, Any]] = {}
        missing: List[int] = []
        async with cls._FILE_META_CACHE_LOCK:
            for file_id in file_ids:
                cache_key = cls._file_meta_cache_key(connected_integration_id, int(file_id))
                cache_row = cls._FILE_META_CACHE.get(cache_key)
                if not cache_row:
                    missing.append(int(file_id))
                    continue
                payload, valid_till = cache_row
                if float(valid_till) <= now:
                    cls._FILE_META_CACHE.pop(cache_key, None)
                    missing.append(int(file_id))
                    continue
                cached[int(file_id)] = dict(payload)
        return cached, missing

    @classmethod
    async def _write_cached_file_views(
        cls,
        connected_integration_id: str,
        views: Dict[int, Dict[str, Any]],
    ) -> None:
        if not views:
            return
        valid_till = time.time() + max(int(ExternalChatCrmChannelConfig.FILE_META_CACHE_TTL_SEC), 1)
        async with cls._FILE_META_CACHE_LOCK:
            for file_id, payload in views.items():
                cache_key = cls._file_meta_cache_key(connected_integration_id, int(file_id))
                cls._FILE_META_CACHE[cache_key] = (dict(payload), valid_till)
            max_items = max(int(ExternalChatCrmChannelConfig.FILE_META_CACHE_MAX_ITEMS), 1000)
            if len(cls._FILE_META_CACHE) > max_items:
                now = time.time()
                expired_keys = [
                    key
                    for key, cache_row in cls._FILE_META_CACHE.items()
                    if float(cache_row[1]) <= now
                ]
                for key in expired_keys:
                    cls._FILE_META_CACHE.pop(key, None)
                while len(cls._FILE_META_CACHE) > max_items:
                    first_key = next(iter(cls._FILE_META_CACHE), None)
                    if first_key is None:
                        break
                    cls._FILE_META_CACHE.pop(first_key, None)

    @classmethod
    async def _load_file_views(
        cls,
        *,
        api: RegosAPI,
        connected_integration_id: str,
        file_ids: List[int],
    ) -> Dict[int, Dict[str, Any]]:
        unique_ids: List[int] = []
        seen: Dict[int, bool] = {}
        for file_id in file_ids:
            safe_id = int(file_id)
            if safe_id <= 0 or seen.get(safe_id):
                continue
            seen[safe_id] = True
            unique_ids.append(safe_id)
        if not unique_ids:
            return {}

        resolved, missing = await cls._read_cached_file_views(
            connected_integration_id,
            unique_ids,
        )
        if not missing:
            return resolved

        loaded: Dict[int, Dict[str, Any]] = {}
        batch_size = max(int(ExternalChatCrmChannelConfig.MAX_FILE_META_BATCH), 1)
        for offset in range(0, len(missing), batch_size):
            batch_ids = missing[offset : offset + batch_size]
            try:
                response = await api.files.file.get(
                    FileGetRequest(
                        ids=batch_ids,
                        limit=len(batch_ids),
                        offset=0,
                    )
                )
            except Exception as error:
                logger.warning(
                    "Files/Get failed while loading chat file metadata: ci=%s ids=%s error=%s",
                    connected_integration_id,
                    batch_ids,
                    error,
                )
                continue

            rows = response.result if response.ok and isinstance(response.result, list) else []
            for row in rows:
                payload = cls._build_file_view(row)
                if not payload:
                    continue
                loaded[int(payload["id"])] = payload

        if loaded:
            await cls._write_cached_file_views(
                connected_integration_id,
                loaded,
            )
        resolved.update(loaded)
        return resolved

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
        default_revision = int(ExternalChatCrmChannelConfig.CHAT_REVISION_DEFAULT)
        inserted = await cls._redis_set_nx(
            key,
            str(default_revision),
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )
        if inserted:
            return default_revision

        current = await cls._redis_get(key)
        parsed = _parse_int(current, None)
        if parsed and parsed > 0:
            await redis_client.expire(key, max(int(ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC or 1), 1))
            return int(parsed)
        return default_revision

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
            if _looks_like_duplicate_error(payload):
                existing = await cls._find_client_by_external_id(api, external_id)
                if existing and getattr(existing, "id", None):
                    return existing
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
            if _looks_like_duplicate_error(payload):
                existing = await cls._find_ticket_by_external_dialog_id(
                    api,
                    external_dialog_id,
                    int(runtime.channel_id),
                )
                if existing and getattr(existing, "id", None) and getattr(existing, "chat_id", None):
                    return existing
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
        *,
        require_writable: bool = False,
        force_refresh: bool = False,
    ) -> ChatContext:
        cached = None
        if not force_refresh:
            cached = await cls._load_cached_context(connected_integration_id, visitor_id)
        if cached:
            cached_state = await cls._get_ticket_write_state(
                connected_integration_id,
                int(cached.ticket_id),
                force_refresh=require_writable,
            )
            if require_writable and not cached_state.get("can_write", True):
                cached = None
            else:
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

        if not cached:
            cached = await cls._load_cached_context(connected_integration_id, visitor_id)
        cached_client_id = int(cached.client_id) if cached and cached.client_id else None

        external_client_id = cls._build_client_external_id(connected_integration_id, visitor_id)
        external_dialog_id = cls._build_ticket_external_dialog_id(connected_integration_id, visitor_id)

        start_message_for_new_ticket: Optional[str] = None
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            created_ticket_now = False
            client = None
            if cached_client_id:
                client = await cls._load_client_by_id(api, int(cached_client_id))
            if not client or not client.id:
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
            ticket_status = _enum_value(getattr(ticket, "status", None)).strip() if ticket else ""
            ticket_closed = ticket_status == TicketStatusEnum.Closed.value

            if (
                not ticket
                or not ticket.id
                or not getattr(ticket, "chat_id", None)
                or (require_writable and ticket_closed)
            ):
                subject = cls._build_subject(
                    runtime.ticket_subject_template,
                    runtime.channel_name,
                    visitor_id,
                    profile,
                )
                ticket = await cls._create_ticket(
                    api,
                    runtime=runtime,
                    client_id=int(client.id),
                    external_dialog_id=external_dialog_id,
                    subject=subject,
                )
                created_ticket_now = True

            if created_ticket_now and runtime.channel_start_message and getattr(ticket, "chat_id", None):
                start_message_for_new_ticket = runtime.channel_start_message

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
        if start_message_for_new_ticket:
            try:
                await cls._send_channel_auto_message_if_needed(
                    connected_integration_id,
                    ticket_id=int(context.ticket_id),
                    chat_id=str(context.chat_id),
                    text=start_message_for_new_ticket,
                    once_flag="start_message_sent",
                    external_message_id=f"webchat:channel_start:{int(context.ticket_id)}",
                )
            except Exception as error:
                logger.warning(
                    "Failed to send channel start message: ci=%s ticket_id=%s visitor_id=%s error=%s",
                    connected_integration_id,
                    int(context.ticket_id),
                    visitor_id,
                    error,
                )
        return context

    @classmethod
    async def _load_client_by_id(
        cls,
        api: RegosAPI,
        client_id: int,
    ) -> Optional[Client]:
        if not client_id:
            return None
        response = await api.crm.client.get(
            ClientGetRequest(ids=[int(client_id)], limit=1, offset=0)
        )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    async def _refresh_writable_context(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        profile: Dict[str, Any],
    ) -> ChatContext:
        return await cls._ensure_chat_context(
            connected_integration_id=connected_integration_id,
            runtime=runtime,
            visitor_id=visitor_id,
            profile=profile,
            require_writable=True,
            force_refresh=True,
        )

    @classmethod
    async def _send_visitor_message_with_reopen(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        profile: Dict[str, Any],
        context: ChatContext,
        text: str,
        external_message_id: str,
    ) -> Tuple[ChatContext, str]:
        try:
            message_id = await cls._add_message_from_visitor(
                connected_integration_id=connected_integration_id,
                context=context,
                text=text,
                external_message_id=external_message_id,
            )
            return context, message_id
        except ChatMessageAddClosedEntityError:
            refreshed_context = await cls._refresh_writable_context(
                connected_integration_id=connected_integration_id,
                runtime=runtime,
                visitor_id=visitor_id,
                profile=profile,
            )
            message_id = await cls._add_message_from_visitor(
                connected_integration_id=connected_integration_id,
                context=refreshed_context,
                text=text,
                external_message_id=external_message_id,
            )
            return refreshed_context, message_id

    @classmethod
    async def _send_visitor_file_with_reopen(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        profile: Dict[str, Any],
        context: ChatContext,
        *,
        text: Optional[str],
        file_name: str,
        extension: str,
        payload_b64: str,
        external_message_id: str,
    ) -> Tuple[ChatContext, str, int]:
        try:
            message_id, file_id = await cls._add_file_message_from_visitor(
                connected_integration_id=connected_integration_id,
                context=context,
                text=text,
                file_name=file_name,
                extension=extension,
                payload_b64=payload_b64,
                external_message_id=external_message_id,
            )
            return context, message_id, int(file_id)
        except ChatMessageAddClosedEntityError:
            refreshed_context = await cls._refresh_writable_context(
                connected_integration_id=connected_integration_id,
                runtime=runtime,
                visitor_id=visitor_id,
                profile=profile,
            )
            message_id, file_id = await cls._add_file_message_from_visitor(
                connected_integration_id=connected_integration_id,
                context=refreshed_context,
                text=text,
                file_name=file_name,
                extension=extension,
                payload_b64=payload_b64,
                external_message_id=external_message_id,
            )
            return refreshed_context, message_id, int(file_id)

    @classmethod
    async def _compose_context_ticket_view(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        context: ChatContext,
    ) -> Dict[str, Any]:
        ticket_state = await cls._get_ticket_write_state(
            connected_integration_id,
            int(context.ticket_id),
        )
        return cls._compose_ticket_view_state(runtime, ticket_state)

    @classmethod
    async def _compose_context_ticket_view_fresh(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        context: ChatContext,
    ) -> Dict[str, Any]:
        ticket_state = await cls._get_ticket_write_state(
            connected_integration_id,
            int(context.ticket_id),
            force_refresh=True,
        )
        return cls._compose_ticket_view_state(runtime, ticket_state)

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
            revision = await cls._bump_chat_revision(
                connected_integration_id,
                str(context.chat_id),
            )
            await cls._publish_chat_event(
                connected_integration_id,
                chat_id=str(context.chat_id),
                event_type="chat_message_changed",
                source_action="local_send_message",
                chat_revision=int(revision or 0),
                ticket_id=int(context.ticket_id),
                force_full=False,
                payload={
                    "message_id": new_uuid or None,
                },
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
        safe_text = _normalize_message_markup(text, ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH)
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

        revision = await cls._bump_chat_revision(
            connected_integration_id,
            str(context.chat_id),
        )
        await cls._publish_chat_event(
            connected_integration_id,
            chat_id=str(context.chat_id),
            event_type="chat_message_changed",
            source_action="local_send_file",
            chat_revision=int(revision or 0),
            ticket_id=int(context.ticket_id),
            force_full=False,
            payload={
                "message_id": message_id,
                "file_id": int(file_id),
            },
        )
        return message_id, int(file_id)

    @staticmethod
    def _is_duplicate_external_message_error(payload: Dict[str, Any]) -> bool:
        return _looks_like_duplicate_error(payload)

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
        safe_text = _normalize_message_markup(text, 300)
        safe_external_message_id = str(external_message_id or "").strip()
        if not safe_chat_id or not safe_text or not safe_external_message_id:
            return False

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=safe_chat_id,
                    message_type=ChatMessageTypeEnum.System,
                    text=safe_text,
                    external_message_id=safe_external_message_id,
                )
            )
        if response.ok:
            revision = await cls._bump_chat_revision(
                connected_integration_id,
                safe_chat_id,
            )
            await cls._publish_chat_event(
                connected_integration_id,
                chat_id=safe_chat_id,
                event_type="chat_message_changed",
                source_action="local_system_message",
                chat_revision=int(revision or 0),
                force_full=False,
                payload={},
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
    async def _send_channel_auto_message_if_needed(
        cls,
        connected_integration_id: str,
        *,
        ticket_id: int,
        chat_id: str,
        text: Optional[str],
        once_flag: str,
        external_message_id: str,
    ) -> bool:
        safe_text = _normalize_message_markup(text, 300)
        if not safe_text:
            return False
        if not await cls._mark_ticket_once_flag(
            connected_integration_id,
            int(ticket_id),
            once_flag,
        ):
            return False
        return await cls._add_system_message(
            connected_integration_id,
            chat_id=chat_id,
            text=safe_text,
            external_message_id=external_message_id,
        )

    @classmethod
    async def _send_ticket_closed_auto_messages_if_needed(
        cls,
        connected_integration_id: str,
        *,
        runtime: RuntimeConfig,
        ticket_id: int,
        chat_id: str,
    ) -> bool:
        sent_any = False
        sent_end = await cls._send_channel_auto_message_if_needed(
            connected_integration_id,
            ticket_id=int(ticket_id),
            chat_id=chat_id,
            text=runtime.channel_end_message,
            once_flag="end_message_sent",
            external_message_id=f"webchat:channel_end:{int(ticket_id)}",
        )
        sent_any = sent_any or sent_end
        if runtime.channel_rating_enabled and runtime.channel_rating_message:
            sent_rating_prompt = await cls._send_channel_auto_message_if_needed(
                connected_integration_id,
                ticket_id=int(ticket_id),
                chat_id=chat_id,
                text=runtime.channel_rating_message,
                once_flag="rating_prompt_sent",
                external_message_id=f"webchat:channel_rating_prompt:{int(ticket_id)}",
            )
            sent_any = sent_any or sent_rating_prompt
        return sent_any

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
            visible_rows: List[Tuple[Any, str, bool, List[int]]] = []
            all_file_ids: List[int] = []
            for row in rows:
                message_type = (
                    _enum_value(getattr(row, "message_type", None)).strip()
                    or ChatMessageTypeEnum.Regular.value
                )
                if message_type == ChatMessageTypeEnum.Private.value:
                    continue
                author_type = _enum_value(getattr(row, "author_entity_type", None)).strip().lower()
                author_id = _parse_int(getattr(row, "author_entity_id", None), None)
                mine = (
                    author_type == ChatEntityTypeEnum.Client.value.lower()
                    and author_id == context.client_id
                )
                file_ids = _parse_file_ids(getattr(row, "file_ids", None))
                if file_ids:
                    all_file_ids.extend(file_ids)
                visible_rows.append((row, message_type, bool(mine), file_ids))

            file_views_map = await cls._load_file_views(
                api=api,
                connected_integration_id=connected_integration_id,
                file_ids=all_file_ids,
            )

        history: List[Dict[str, Any]] = []
        for row, message_type, mine, file_ids in visible_rows:
            files: List[Dict[str, Any]] = []
            for file_id in file_ids:
                payload = file_views_map.get(int(file_id))
                if payload:
                    files.append(payload)

            text = _normalize_message_markup(
                getattr(row, "text", ""),
                ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
            )
            if not text and files:
                text = ""
            history.append(
                {
                    "id": str(getattr(row, "id", "") or ""),
                    "text": text,
                    "files": files,
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

    @classmethod
    def _load_ui_css_template(cls) -> str:
        if cls._UI_CSS_TEMPLATE_CACHE is not None:
            return cls._UI_CSS_TEMPLATE_CACHE

        try:
            cls._UI_CSS_TEMPLATE_CACHE = cls._UI_CSS_TEMPLATE_PATH.read_text(encoding="utf-8")
        except Exception as error:
            logger.exception("Failed to load UI CSS template: %s", error)
            cls._UI_CSS_TEMPLATE_CACHE = (
                ":root {\n"
                "  --bg: #c2d2df;\n"
                "  --card: #f7f9fc;\n"
                "  --line: #d7dfea;\n"
                "  --text: #243247;\n"
                "  --muted: #6f7d95;\n"
                "  --accent: #3a6fa6;\n"
                "  --mine: #ffffff;\n"
                "  --other: #f7f9fc;\n"
                "  --system: #f2f5fa;\n"
                "}\n"
                "body { margin: 0; font-family: Manrope, sans-serif; }\n"
            )
        return cls._UI_CSS_TEMPLATE_CACHE

    @classmethod
    def _load_ui_i18n_bundle(cls) -> Dict[str, Dict[str, str]]:
        if cls._UI_I18N_CACHE is not None:
            return cls._UI_I18N_CACHE

        bundle: Dict[str, Dict[str, str]] = {}
        for lang in ("ru", "uz", "en"):
            file_path = cls._UI_I18N_DIR_PATH / f"{lang}.json"
            try:
                payload_raw = file_path.read_text(encoding="utf-8")
                payload = _json_loads(payload_raw)
                if not isinstance(payload, dict):
                    raise ValueError("i18n payload must be an object")
                normalized: Dict[str, str] = {}
                for raw_key, raw_value in payload.items():
                    key = str(raw_key or "").strip()
                    if not key:
                        continue
                    normalized[key] = str(raw_value or "")
                bundle[lang] = normalized
            except Exception as error:
                logger.exception("Failed to load UI i18n file: %s (%s)", file_path, error)
                bundle[lang] = {}

        if "en" not in bundle or not bundle["en"]:
            bundle["en"] = {
                "status_connecting": "connecting...",
                "status_online": "online",
                "status_initializing": "initializing...",
            }
        for lang in ("ru", "uz"):
            if lang not in bundle or not bundle[lang]:
                bundle[lang] = dict(bundle["en"])

        cls._UI_I18N_CACHE = bundle
        return bundle

    @staticmethod
    def _ui_html(
        *,
        connected_integration_id: str,
        title: str,
        require_display_name: bool,
        require_phone: bool,
        require_email: bool,
        chat_css_url: Optional[str],
        i18n_bundle: Dict[str, Dict[str, str]],
    ) -> str:
        safe_title = html.escape(title)
        safe_ci = html.escape(connected_integration_id)
        safe_require_display_name = "true" if require_display_name else "false"
        safe_require_phone = "true" if require_phone else "false"
        safe_require_email = "true" if require_email else "false"
        safe_i18n_bundle = _json_dumps(i18n_bundle or {}).replace("</", "<\\/")

        if chat_css_url:
            safe_css_url = html.escape(chat_css_url, quote=True)
            style_block = f'  <link rel="stylesheet" href="{safe_css_url}">'
        else:
            css_template = ExternalChatCrmChannelIntegration._load_ui_css_template()
            style_block = f"  <style>\n{css_template}\n  </style>"

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
            style_block=style_block,
            safe_i18n_bundle=safe_i18n_bundle,
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
            "chat_css_url": runtime.chat_css_url,
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
        fingerprint = _payload_fingerprint(payload if isinstance(payload, dict) else {})
        ticket_id = _parse_int(
            payload.get("ticket_id")
            if payload.get("ticket_id") is not None
            else payload.get("id"),
            None,
        )
        message_id = str(
            payload.get("message_id")
            if payload.get("message_id") is not None
            else payload.get("id")
            or ""
        ).strip()
        chat_id = str(
            payload.get("chat_id")
            if payload.get("chat_id") is not None
            else payload.get("chatId")
            or ""
        ).strip()
        event_id_value = str(event_id or "").strip()
        if event_id_value:
            base = f"event:{event_id_value}:{webhook_action}"
            if webhook_action.startswith("ChatMessage"):
                if chat_id and message_id:
                    return f"{base}:chat:{chat_id}:message:{message_id}"
                if message_id:
                    return f"{base}:message:{message_id}"
                if chat_id:
                    return f"{base}:chat:{chat_id}"
            if chat_id and ticket_id:
                return f"{base}:chat:{chat_id}:ticket:{ticket_id}"
            if ticket_id:
                return f"{base}:ticket:{ticket_id}"
            if chat_id:
                return f"{base}:chat:{chat_id}"
            return f"{base}:{fingerprint}"

        if webhook_action.startswith("ChatMessage"):
            if chat_id and message_id:
                return f"{webhook_action}:chat:{chat_id}:message:{message_id}:{fingerprint}"
            if chat_id:
                return f"{webhook_action}:chat:{chat_id}:{fingerprint}"
        if chat_id and ticket_id:
            return f"{webhook_action}:chat:{chat_id}:ticket:{ticket_id}:{fingerprint}"
        if chat_id:
            return f"{webhook_action}:chat:{chat_id}:{fingerprint}"
        if ticket_id:
            return f"{webhook_action}:ticket:{ticket_id}:{fingerprint}"
        return f"{webhook_action}:{fingerprint}"

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
        webhook_action: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            return {"status": "ignored", "reason": "invalid_payload:chat_id"}

        revision = await cls._bump_chat_revision(connected_integration_id, chat_id)
        await cls._publish_chat_event(
            connected_integration_id,
            chat_id=chat_id,
            event_type="chat_message_changed",
            source_action=webhook_action,
            chat_revision=int(revision or 0),
            force_full=False,
            payload={
                "message_id": str(payload.get("id") or "").strip() or None,
            },
        )
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
                    await cls._send_ticket_closed_auto_messages_if_needed(
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
            revision = await cls._get_chat_revision(connected_integration_id, chat_id)
            await cls._publish_chat_event(
                connected_integration_id,
                chat_id=chat_id,
                event_type="ticket_state_changed",
                source_action=webhook_action,
                chat_revision=int(revision or 0),
                ticket_id=int(ticket_id),
                force_full=True,
                payload={
                    "ticket_status": status_value or None,
                    "ticket_closed": bool(ticket_closed),
                    "ticket_rating": ticket_rating,
                },
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
                result = await self._apply_chat_message_webhook(ci, webhook_action, payload)
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
                chat_css_url=runtime.chat_css_url,
                i18n_bundle=self._load_ui_i18n_bundle(),
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

        require_writable_context = action in {"send_message", "send_file"}
        context = await self._ensure_chat_context(
            connected_integration_id=ci,
            runtime=runtime,
            visitor_id=visitor_id,
            profile=profile,
            require_writable=require_writable_context,
        )

        try:
            if action == "init":
                ticket_view = await self._compose_context_ticket_view_fresh(
                    ci,
                    runtime,
                    context,
                )
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
                if force_full:
                    ticket_view = await self._compose_context_ticket_view_fresh(
                        ci,
                        runtime,
                        context,
                    )
                else:
                    ticket_view = await self._compose_context_ticket_view(
                        ci,
                        runtime,
                        context,
                    )
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

            if action == "events":
                timeout_sec = _parse_int(
                    data.get("timeout_sec"),
                    ExternalChatCrmChannelConfig.EVENT_LONGPOLL_TIMEOUT_SEC,
                )
                max_events = _parse_int(
                    data.get("max_events"),
                    ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS,
                )
                last_event_id = str(data.get("last_event_id") or "").strip() or "$"
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                known_revision = _parse_int(data.get("known_revision"), None)
                if (
                    known_revision is not None
                    and int(chat_revision) > 0
                    and int(known_revision) != int(chat_revision)
                ):
                    ticket_view = await self._compose_context_ticket_view(
                        ci,
                        runtime,
                        context,
                    )
                    return {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        "chat_revision": chat_revision,
                        "last_event_id": last_event_id,
                        "events": [
                            {
                                "id": str(last_event_id),
                                "type": "chat_revision_changed",
                                "source_action": "revision_sync",
                                "chat_id": str(context.chat_id),
                                "ticket_id": int(context.ticket_id),
                                "chat_revision": int(chat_revision),
                                "api_action": "history",
                                "force_full": False,
                                "created_at": int(time.time()),
                                "payload": {},
                            }
                        ],
                        **ticket_view,
                    }

                events = await self._poll_chat_events(
                    ci,
                    chat_id=str(context.chat_id),
                    last_event_id=last_event_id,
                    timeout_sec=int(timeout_sec or ExternalChatCrmChannelConfig.EVENT_LONGPOLL_TIMEOUT_SEC),
                    max_items=int(max_events or ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS),
                )
                if events:
                    last_event_id = str(events[-1].get("id") or last_event_id)
                if events:
                    chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                ticket_view = await self._compose_context_ticket_view(
                    ci,
                    runtime,
                    context,
                )
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "chat_revision": chat_revision,
                    "last_event_id": last_event_id,
                    "events": events,
                    **ticket_view,
                }

            if action == "send_message":
                text = _normalize_message_markup(
                    data.get("text"),
                    ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
                )
                if not text:
                    return JSONResponse(
                        status_code=400,
                        content={"error": 400, "description": "text is required"},
                    )
                ext_id = f"webchat:msg:{visitor_id}:{uuid.uuid4().hex[:12]}"
                context, message_id = await self._send_visitor_message_with_reopen(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=profile,
                    context=context,
                    text=text,
                    external_message_id=ext_id,
                )
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                ticket_view = await self._compose_context_ticket_view(ci, runtime, context)
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
                text = _normalize_message_markup(
                    data.get("text"),
                    ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
                )
                ext_id = f"webchat:file:{visitor_id}:{uuid.uuid4().hex[:12]}"
                context, message_id, file_id = await self._send_visitor_file_with_reopen(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=profile,
                    context=context,
                    text=text,
                    file_name=file_name,
                    extension=extension,
                    payload_b64=payload_b64,
                    external_message_id=ext_id,
                )
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                ticket_view = await self._compose_context_ticket_view(ci, runtime, context)
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
                await self._publish_chat_event(
                    ci,
                    chat_id=str(context.chat_id),
                    event_type="ticket_state_changed",
                    source_action="local_set_rating",
                    chat_revision=int(chat_revision or 0),
                    ticket_id=int(context.ticket_id),
                    force_full=True,
                    payload={
                        "ticket_rating": int(rating),
                        "ticket_closed": True,
                    },
                )
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
