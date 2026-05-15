from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import html
import httpx
import json
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse, RedirectResponse, Response

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_ops,
    redis_error_contains,
    redis_expire_if_due,
    redis_incr_with_ttl,
    redis_stream_add_with_ttl,
    redis_stream_ack_delete,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
    redis_zadd_with_ttl,
    redis_zrangebyscore_with_ttl,
)
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
    TicketEditRequest,
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
from schemas.api.references.field import FieldGetRequest
from schemas.api.references.fields import FieldValueAdd, FieldValueEdit
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
    REDIS_PREFIX = "ecc:"
    STREAM_REDIS_PREFIX = "ecc"
    UI_ASSET_VERSION = "20260505-1"
    UI_ASSET_VERSION_PARAM = "v"
    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 30)
    SETTINGS_STALE_TTL_SEC = max(SETTINGS_TTL_SEC * 10, 10 * 60)
    SETTINGS_LOCAL_TTL_SEC = min(30, max(5, SETTINGS_TTL_SEC // 4))
    SETTINGS_LOCAL_MAX = 10000
    SETTINGS_LOCK_TTL_SEC = 10
    SETTINGS_LOCK_WAIT_SEC = 2.0
    RUNTIME_LOCAL_TTL_SEC = min(30, max(5, SETTINGS_TTL_SEC // 4))
    CONTEXT_TTL_SEC = 7 * 24 * 60 * 60
    ACTIVE_CACHE_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
    ACTIVE_LOCK_TTL_SEC = 10
    ACTIVE_LOCK_WAIT_SEC = 0.5
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
    CHANNEL_AUTO_MESSAGE_MAX_LENGTH = MAX_MESSAGE_LENGTH
    CHAT_REVISION_DEFAULT = 1
    WEBHOOK_DEDUPE_TTL_SEC = 10 * 60
    EVENT_QUEUE_TTL_SEC = 6 * 60 * 60
    EVENT_QUEUE_MAX_ITEMS = 500
    EVENT_BATCH_MAX_ITEMS = 30
    STREAM_TTL_SEC = 24 * 60 * 60
    STREAM_GROUP = "eccw"
    STREAM_MAXLEN = max(int(app_settings.external_chat_crm_channel_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(app_settings.external_chat_crm_channel_stream_batch_size or 0), 1)
    STREAM_WORKERS = max(int(app_settings.external_chat_crm_channel_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = max(int(app_settings.external_chat_crm_channel_stream_retry_limit or 0), 1)
    EVENT_CONCURRENCY = max(int(app_settings.external_chat_crm_channel_event_concurrency or 0), 1)
    LOCK_TTL_SEC = 30
    PROCESSING_LOCK_TTL_SEC = 60
    HEARTBEAT_TTL_SEC = 30
    CLIENT_NOTICE_TTL_SEC = 10 * 60
    CLIENT_NOTICE_MAX_ITEMS = 100
    PENDING_PARAMS_TTL_SEC = 6 * 60 * 60
    PENDING_PARAMS_MAX_ITEMS = 100
    RATING_POSITIVE_THRESHOLD = 4
    MAX_CUSTOM_FIELD_KEY_LENGTH = 160
    MAX_CUSTOM_FIELD_VALUE_LENGTH = 4000
    MAX_CLIENT_INFO_PARAM_KEY_LENGTH = 120
    FIELD_EXISTS_CACHE_TTL_SEC = max(SETTINGS_TTL_SEC, 5 * 60)
    CREATE_CONTEXT_ACTIONS = {"send_message", "send_file"}
    READ_CONTEXT_ACTIONS = {"init", "history", "getupdates", "notification_count", "mark_read"}
    EXISTING_CONTEXT_ACTIONS = READ_CONTEXT_ACTIONS | {"set_rating"}
    SUPPORTED_EXTERNAL_ACTIONS = CREATE_CONTEXT_ACTIONS | EXISTING_CONTEXT_ACTIONS
    PENDING_PARAM_CAPTURE_ACTIONS = {"init"}
    SUPPORTED_INBOUND_WEBHOOKS = {
        "ChatMessageAdded",
        "ChatMessageEdited",
        "ChatMessageDeleted",
        "ChatMessageRead",
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


@dataclass
class PreparedWriteParams:
    profile: Dict[str, Any]
    client_field_adds: List[FieldValueAdd]
    client_field_edits: List[FieldValueEdit]
    ticket_field_adds: List[FieldValueAdd]
    ticket_field_edits: List[FieldValueEdit]
    sync_client_info: bool
    sync_ticket_fields: bool


_INSTANCE_ID = f"external_chat:{uuid.uuid4().hex[:12]}"
_STREAM_WORKER_TASKS: Dict[int, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_GROUP_READY: Set[str] = set()
_STREAM_CLAIM_TS: Dict[str, int] = {}
_SETTINGS_LOCAL_CACHE: Dict[str, Tuple[int, Dict[str, str]]] = {}
_RUNTIME_LOCAL_CACHE: Dict[str, Tuple[int, RuntimeConfig]] = {}
_RUNTIME_LOCAL_LOCK = asyncio.Lock()

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


def _normalize_channel_auto_message(value: Any) -> str:
    return _normalize_message_markup(
        value,
        ExternalChatCrmChannelConfig.CHANNEL_AUTO_MESSAGE_MAX_LENGTH,
    )


def _normalize_custom_field_key(value: Any) -> str:
    key = str(value or "").strip()
    if not key:
        return ""
    return key[: ExternalChatCrmChannelConfig.MAX_CUSTOM_FIELD_KEY_LENGTH]


def _normalize_custom_field_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (dict, list)):
        text = _json_dumps(value)
    else:
        text = str(value or "")
    return text.strip()[: ExternalChatCrmChannelConfig.MAX_CUSTOM_FIELD_VALUE_LENGTH]


_CLIENT_INFO_IGNORED_KEYS = {
    "action",
    "ci",
    "client_custom_fields",
    "client_fields",
    "client_params",
    "connected-integration-id",
    "connected_integration_id",
    "custom_fields",
    "data",
    "fields",
    "file",
    "file_data",
    "force_full",
    "known_revision",
    "limit",
    "max_events",
    "payload",
    "payload_b64",
    "text",
    "ticket_custom_fields",
    "ticket_fields",
    "visitor",
    "visitor_id",
    "visitorid",
    "vid",
}
_CLIENT_PROFILE_ALIAS_KEYS = {
    "display_name",
    "email",
    "full_name",
    "mail",
    "name",
    "phone",
    "phone_number",
    "tel",
}
_CLIENT_INFO_SENSITIVE_KEY_RE = re.compile(
    r"(^|[_.:-])(api_key|apikey|auth|authorization|password|passwd|secret|signature|token)([_.:-]|$)",
    flags=re.IGNORECASE,
)


def _normalize_client_info_param_key(value: Any) -> str:
    key = re.sub(r"[\r\n\t]+", " ", str(value or "")).strip()
    return key[: ExternalChatCrmChannelConfig.MAX_CLIENT_INFO_PARAM_KEY_LENGTH]


def _is_client_info_param_allowed(key: str) -> bool:
    normalized = _normalize_client_info_param_key(key)
    if not normalized:
        return False
    lowered = normalized.strip().lower()
    if lowered in _CLIENT_INFO_IGNORED_KEYS:
        return False
    return _CLIENT_INFO_SENSITIVE_KEY_RE.search(lowered) is None


def _iter_client_info_param_rows(value: Any) -> List[Tuple[Any, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = _json_loads(raw)
        except Exception:
            return []
        return _iter_client_info_param_rows(parsed)
    if isinstance(value, dict):
        if "key" in value:
            return [(value.get("key"), value.get("value"))]
        return list(value.items())
    if isinstance(value, (list, tuple)):
        rows: List[Tuple[Any, Any]] = []
        for item in value:
            if isinstance(item, dict):
                rows.extend(_iter_client_info_param_rows(item))
                continue
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                rows.append((item[0], item[1]))
        return rows
    return []


def _client_field_key_from_param_key(value: Any, *, allow_unprefixed: bool) -> str:
    key = str(value or "").strip()
    if not key:
        return ""
    lowered = key.lower()
    if lowered in _CLIENT_PROFILE_ALIAS_KEYS:
        return ""
    if key.startswith("client_field_"):
        return key[len("client_field_") :]
    if key.startswith("client_field."):
        return key[len("client_field.") :]
    if key.startswith(("ticket_field_", "ticket_field.")):
        return ""
    if key.startswith("field_"):
        return key
    if allow_unprefixed and _is_client_info_param_allowed(key):
        return key
    return ""


def _iter_ticket_field_rows(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = _json_loads(raw)
        except Exception:
            return []
        return _iter_ticket_field_rows(parsed)
    if isinstance(value, dict):
        if "key" in value:
            return [value]
        rows: List[Dict[str, Any]] = []
        for raw_key, raw_value in value.items():
            rows.append({"key": raw_key, "value": raw_value})
        return rows
    if isinstance(value, (list, tuple)):
        rows = []
        for item in value:
            if isinstance(item, dict):
                rows.extend(_iter_ticket_field_rows(item))
                continue
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                rows.append({"key": item[0], "value": item[1]})
        return rows
    return []


def _extract_ticket_field_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    container_keys = ("ticket_fields", "ticket_custom_fields", "custom_fields", "fields")
    for key in container_keys:
        if key not in data:
            continue
        rows.extend(_iter_ticket_field_rows(data.get(key)))
    for raw_key, raw_value in data.items():
        key = str(raw_key or "").strip()
        if not key or key in container_keys:
            continue
        field_key = ""
        if key.startswith("ticket_field_"):
            field_key = key[len("ticket_field_") :]
        elif key.startswith("ticket_field."):
            field_key = key[len("ticket_field.") :]
        elif key.startswith("field_"):
            field_key = key
        if field_key:
            rows.append({"key": field_key, "value": raw_value})
    return rows


def _extract_client_field_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    container_keys = ("client_fields", "client_custom_fields")
    for key in container_keys:
        if key not in data:
            continue
        rows.extend(_iter_ticket_field_rows(data.get(key)))

    for raw_key, raw_value in _iter_client_info_param_rows(data.get("client_params")):
        key = str(raw_key or "").strip()
        if not key:
            continue
        if key in container_keys:
            rows.extend(_iter_ticket_field_rows(raw_value))
            continue
        field_key = _client_field_key_from_param_key(key, allow_unprefixed=True)
        if field_key:
            rows.append({"key": field_key, "value": raw_value})

    ignored_top_level_keys = {
        *container_keys,
        "client_params",
        "custom_fields",
        "fields",
        "ticket_custom_fields",
        "ticket_fields",
    }
    for raw_key, raw_value in data.items():
        key = str(raw_key or "").strip()
        if not key or key in ignored_top_level_keys:
            continue
        field_key = _client_field_key_from_param_key(key, allow_unprefixed=True)
        if field_key:
            rows.append({"key": field_key, "value": raw_value})
    return rows


def _normalize_field_adds(rows: List[Dict[str, Any]]) -> List[FieldValueAdd]:
    fields_by_key: Dict[str, FieldValueAdd] = {}
    for row in rows:
        key = _normalize_custom_field_key(row.get("key"))
        if not key:
            continue
        if _parse_bool(row.get("deleted"), False):
            continue
        value = _normalize_custom_field_value(row.get("value"))
        if value is None:
            continue
        fields_by_key[key] = FieldValueAdd(key=key, value=value)
    return list(fields_by_key.values())


def _normalize_field_edits(rows: List[Dict[str, Any]]) -> List[FieldValueEdit]:
    fields_by_key: Dict[str, FieldValueEdit] = {}
    for row in rows:
        key = _normalize_custom_field_key(row.get("key"))
        if not key:
            continue
        deleted = _parse_bool(row.get("deleted"), False)
        value = _normalize_custom_field_value(row.get("value"))
        if deleted:
            fields_by_key[key] = FieldValueEdit(key=key, deleted=True)
            continue
        if value is None:
            continue
        fields_by_key[key] = FieldValueEdit(key=key, value=value, deleted=False)
    return list(fields_by_key.values())


def _normalize_ticket_field_adds(data: Dict[str, Any]) -> List[FieldValueAdd]:
    return _normalize_field_adds(_extract_ticket_field_rows(data))


def _normalize_client_field_adds(data: Dict[str, Any]) -> List[FieldValueAdd]:
    return _normalize_field_adds(_extract_client_field_rows(data))


def _normalize_ticket_field_edits(data: Dict[str, Any]) -> List[FieldValueEdit]:
    return _normalize_field_edits(_extract_ticket_field_rows(data))


def _normalize_client_field_edits(data: Dict[str, Any]) -> List[FieldValueEdit]:
    return _normalize_field_edits(_extract_client_field_rows(data))


_PENDING_PROFILE_KEYS = (
    "display_name",
    "email",
    "full_name",
    "mail",
    "name",
    "phone",
    "phone_number",
    "tel",
)
_PENDING_CLIENT_FIELD_CONTAINER_KEYS = ("client_fields", "client_custom_fields")
_PENDING_TICKET_FIELD_CONTAINER_KEYS = (
    "ticket_fields",
    "ticket_custom_fields",
    "custom_fields",
    "fields",
)


def _append_pending_field_row(rows: List[Dict[str, Any]], row: Dict[str, Any]) -> None:
    key = _normalize_custom_field_key(row.get("key"))
    if not key:
        return
    if len(rows) >= ExternalChatCrmChannelConfig.PENDING_PARAMS_MAX_ITEMS:
        return
    if _parse_bool(row.get("deleted"), False):
        rows.append({"key": key, "deleted": True})
        return
    value = _normalize_custom_field_value(row.get("value"))
    if value is None:
        return
    rows.append({"key": key, "value": value})


def _extract_pending_request_params(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    pending: Dict[str, Any] = {}
    client_params: Dict[str, Any] = {}
    client_field_rows: List[Dict[str, Any]] = []
    ticket_field_rows: List[Dict[str, Any]] = []

    for key in _PENDING_PROFILE_KEYS:
        if key not in data:
            continue
        value = _normalize_custom_field_value(data.get(key))
        if value:
            pending[key] = value

    for raw_key, raw_value in _iter_client_info_param_rows(data.get("client_params")):
        key = _normalize_client_info_param_key(raw_key)
        if not key:
            continue
        lowered = key.lower()
        if lowered in _PENDING_CLIENT_FIELD_CONTAINER_KEYS:
            for row in _iter_ticket_field_rows(raw_value):
                _append_pending_field_row(client_field_rows, row)
            continue
        if lowered in _CLIENT_PROFILE_ALIAS_KEYS or _is_client_info_param_allowed(key):
            value = _normalize_custom_field_value(raw_value)
            if (
                value is not None
                and (value or lowered not in _CLIENT_PROFILE_ALIAS_KEYS)
                and len(client_params) < ExternalChatCrmChannelConfig.PENDING_PARAMS_MAX_ITEMS
            ):
                client_params[key] = value

    for container_key in _PENDING_CLIENT_FIELD_CONTAINER_KEYS:
        for row in _iter_ticket_field_rows(data.get(container_key)):
            _append_pending_field_row(client_field_rows, row)

    for container_key in _PENDING_TICKET_FIELD_CONTAINER_KEYS:
        for row in _iter_ticket_field_rows(data.get(container_key)):
            _append_pending_field_row(ticket_field_rows, row)

    ignored_keys = {
        "client_params",
        *_PENDING_CLIENT_FIELD_CONTAINER_KEYS,
        *_PENDING_TICKET_FIELD_CONTAINER_KEYS,
        *_PENDING_PROFILE_KEYS,
    }
    for raw_key, raw_value in data.items():
        key = str(raw_key or "").strip()
        if not key or key in ignored_keys:
            continue
        client_field_key = _client_field_key_from_param_key(key, allow_unprefixed=True)
        if client_field_key and key.startswith(("client_field_", "client_field.", "field_")):
            _append_pending_field_row(client_field_rows, {"key": client_field_key, "value": raw_value})
            if key.startswith("field_"):
                _append_pending_field_row(ticket_field_rows, {"key": key, "value": raw_value})
            continue
        ticket_field_key = ""
        if key.startswith("ticket_field_"):
            ticket_field_key = key[len("ticket_field_") :]
        elif key.startswith("ticket_field."):
            ticket_field_key = key[len("ticket_field.") :]
        if ticket_field_key:
            _append_pending_field_row(ticket_field_rows, {"key": ticket_field_key, "value": raw_value})
            continue
        if _is_client_info_param_allowed(key):
            value = _normalize_custom_field_value(raw_value)
            if value is not None and len(client_params) < ExternalChatCrmChannelConfig.PENDING_PARAMS_MAX_ITEMS:
                client_params[key] = value

    if client_params:
        pending["client_params"] = client_params
    if client_field_rows:
        pending["client_fields"] = client_field_rows
    if ticket_field_rows:
        pending["ticket_fields"] = ticket_field_rows
    return pending


def _merge_profiles(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = {
        "display_name": _normalize_text((base or {}).get("display_name"), 120),
        "email": _normalize_email((base or {}).get("email")),
        "phone": _normalize_phone((base or {}).get("phone")),
    }
    for key in ("display_name", "email", "phone"):
        value = (override or {}).get(key)
        if key == "display_name":
            normalized = _normalize_text(value, 120)
        elif key == "email":
            normalized = _normalize_email(value)
        else:
            normalized = _normalize_phone(value)
        if normalized:
            merged[key] = normalized
    return merged


def _field_model_key(field: Any) -> str:
    if isinstance(field, dict):
        return _normalize_custom_field_key(field.get("key"))
    return _normalize_custom_field_key(getattr(field, "key", None))


def _merge_field_adds(
    base: Optional[List[FieldValueAdd]],
    override: Optional[List[FieldValueAdd]],
) -> List[FieldValueAdd]:
    fields_by_key: Dict[str, FieldValueAdd] = {}
    for field in list(base or []) + list(override or []):
        key = _field_model_key(field)
        if key:
            fields_by_key[key] = field
    return list(fields_by_key.values())


def _merge_field_edits(
    base: Optional[List[FieldValueEdit]],
    override: Optional[List[FieldValueEdit]],
) -> List[FieldValueEdit]:
    fields_by_key: Dict[str, FieldValueEdit] = {}
    for field in list(base or []) + list(override or []):
        key = _field_model_key(field)
        if key:
            fields_by_key[key] = field
    return list(fields_by_key.values())


def _is_meaningful_system_text(value: str) -> bool:
    normalized = str(value or "").strip()
    if not normalized:
        return False
    if normalized.lower().startswith(("http://", "https://")):
        return True
    if re.search(r"[^\W\d_]", normalized, flags=re.UNICODE):
        return True
    return False


def _extract_system_message_payload_text(value: Any, max_len: int = 500) -> str:
    """Extract displayable text from structured system payloads without falling back to IDs."""
    if value is None:
        return ""

    if isinstance(value, dict):
        preferred_value_candidates: List[Any] = []
        nested_payload_candidates: List[Any] = []
        direct_text_candidates: List[str] = []
        for raw_key, raw_value in value.items():
            key = str(raw_key or "").strip().lower()
            if not key:
                continue

            if key in {
                "text",
                "message",
                "title",
                "description",
                "body",
                "comment",
                "content",
                "caption",
                "value",
                "status_text",
            } or any(
                token in key for token in ("text", "message", "title", "description", "comment", "content", "caption")
            ):
                preferred_value_candidates.append(raw_value)
                continue

            if key in {"payload", "data", "details", "meta", "result", "context", "extra"}:
                nested_payload_candidates.append(raw_value)
                continue

            if isinstance(raw_value, str):
                normalized = _normalize_message_markup(raw_value, max_len)
                if _is_meaningful_system_text(normalized):
                    direct_text_candidates.append(normalized)

        for candidate in preferred_value_candidates:
            extracted = _extract_system_message_payload_text(candidate, max_len)
            if extracted:
                return extracted

        for candidate in nested_payload_candidates:
            extracted = _extract_system_message_payload_text(candidate, max_len)
            if extracted:
                return extracted

        if direct_text_candidates:
            return max(direct_text_candidates, key=len)
        return ""

    if isinstance(value, (list, tuple)):
        for nested in value:
            extracted = _extract_system_message_payload_text(nested, max_len)
            if extracted:
                return extracted
        return ""

    if not isinstance(value, str):
        return ""
    text = _normalize_message_markup(value, max_len)
    if not _is_meaningful_system_text(text):
        return ""
    return text


def _resolve_history_message_text(
    row: Any,
    message_type: str,
    *,
    max_len: int,
) -> str:
    text = _normalize_message_markup(getattr(row, "text", ""), max_len)
    if text or message_type != ChatMessageTypeEnum.System.value:
        return text

    payload_raw = getattr(row, "action_payload", None)
    payload_candidate: Any = payload_raw
    if isinstance(payload_raw, str):
        payload_text = payload_raw.strip()
        if payload_text:
            try:
                payload_candidate = _json_loads(payload_text)
            except Exception:
                payload_candidate = payload_text

    for candidate in (payload_candidate, getattr(row, "replay_text", None)):
        extracted = _extract_system_message_payload_text(candidate, max_len)
        if extracted:
            return extracted
    return ""


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


def _url_with_query_param(raw_url: str, key: str, value: str) -> str:
    url = str(raw_url or "").strip()
    safe_key = str(key or "").strip()
    safe_value = str(value or "").strip()
    if not url or not safe_key:
        return url
    parts = urlsplit(url)
    query_items = [
        (item_key, item_value)
        for item_key, item_value in parse_qsl(parts.query, keep_blank_values=True)
        if item_key != safe_key
    ]
    query_items.append((safe_key, safe_value))
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query_items),
            parts.fragment,
        )
    )


def _url_with_ui_asset_version(raw_url: str) -> str:
    return _url_with_query_param(
        raw_url,
        ExternalChatCrmChannelConfig.UI_ASSET_VERSION_PARAM,
        ExternalChatCrmChannelConfig.UI_ASSET_VERSION,
    )


def _relative_query_with_ui_asset_version(query: Dict[str, Any]) -> str:
    version_key = ExternalChatCrmChannelConfig.UI_ASSET_VERSION_PARAM
    query_items: List[Tuple[str, str]] = []
    for raw_key, raw_value in (query or {}).items():
        key = str(raw_key or "").strip()
        if not key or key == version_key:
            continue
        if isinstance(raw_value, (list, tuple)):
            for item in raw_value:
                query_items.append((key, str(item or "")))
            continue
        query_items.append((key, str(raw_value or "")))
    query_items.append((version_key, ExternalChatCrmChannelConfig.UI_ASSET_VERSION))
    return f"?{urlencode(query_items)}"


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_ops)


def _require_redis() -> None:
    if not _redis_enabled():
        raise RuntimeError("Redis is required for external_chat_crm_channel")


def _now_ts() -> int:
    return int(time.time())


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


class ConnectedIntegrationInactiveError(RuntimeError):
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
    _EVENTS_DEQUEUE_LUA = (
        "local count = tonumber(ARGV[1]) or 1 "
        "if count < 1 then count = 1 end "
        "local items = redis.call('LRANGE', KEYS[1], 0, count - 1) "
        "if #items > 0 then "
        "  redis.call('LTRIM', KEYS[1], count, -1) "
        "  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[2]) or 1) "
        "end "
        "return items"
    )

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        tokens = [str(item).strip() for item in parts if str(item or "").strip()]
        return f"{ExternalChatCrmChannelConfig.REDIS_PREFIX}{':'.join(tokens)}"

    @staticmethod
    def _stream_redis_key(*parts: Any) -> str:
        tokens = [str(item).strip(":") for item in parts if str(item or "").strip()]
        prefix = ExternalChatCrmChannelConfig.STREAM_REDIS_PREFIX
        return f"{prefix}:{':'.join(tokens)}" if tokens else prefix

    @classmethod
    def _settings_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("settings", connected_integration_id)

    @classmethod
    def _settings_stale_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("settings_stale", connected_integration_id)

    @classmethod
    def _settings_fetch_lock_key(cls, connected_integration_id: str) -> str:
        return cls._stream_redis_key("stl", connected_integration_id)

    @classmethod
    def _active_cache_key(cls, connected_integration_id: str) -> str:
        return cls._redis_key("active", connected_integration_id)

    @classmethod
    def _active_fetch_lock_key(cls, connected_integration_id: str) -> str:
        return cls._stream_redis_key("al", connected_integration_id)

    @classmethod
    def _stream_key(cls) -> str:
        return cls._stream_redis_key("s", "w")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return cls._stream_redis_key("s", "dlq")

    @classmethod
    def _worker_heartbeat_key(cls, worker_index: int) -> str:
        return cls._stream_redis_key("w", worker_index, _INSTANCE_ID)

    @classmethod
    def _webhook_enqueue_dedupe_key(
        cls,
        connected_integration_id: str,
        event_key: str,
    ) -> str:
        event_hash = hashlib.sha256(str(event_key or "").encode("utf-8")).hexdigest()[:24]
        return cls._stream_redis_key("d", connected_integration_id, event_hash)

    @classmethod
    def _webhook_processing_lock_key(
        cls,
        connected_integration_id: str,
        webhook_action: str,
        payload: Dict[str, Any],
    ) -> str:
        chat_id = str(payload.get("chat_id") or payload.get("chatId") or "").strip()
        ticket_id = _parse_int(payload.get("ticket_id") if payload.get("ticket_id") is not None else payload.get("id"), None)
        message_id = str(payload.get("message_id") if payload.get("message_id") is not None else payload.get("id") or "").strip()
        if chat_id:
            resource = f"chat:{chat_id}"
        elif ticket_id:
            resource = f"ticket:{ticket_id}"
        elif message_id:
            resource = f"message:{message_id}"
        else:
            resource = _payload_fingerprint(payload)
        resource_hash = hashlib.sha256(resource.encode("utf-8", errors="ignore")).hexdigest()[:24]
        action_code = "cm" if str(webhook_action or "").startswith("ChatMessage") else "tk"
        return cls._stream_redis_key("l", connected_integration_id, action_code, resource_hash)

    @classmethod
    def _context_cache_key(cls, connected_integration_id: str, visitor_id: str) -> str:
        return cls._redis_key("context", connected_integration_id, visitor_id)

    @classmethod
    def _pending_params_cache_key(cls, connected_integration_id: str, visitor_id: str) -> str:
        return cls._redis_key("pending_params", connected_integration_id, visitor_id)

    @classmethod
    def _chat_context_cache_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("context_by_chat", connected_integration_id, chat_id)

    @classmethod
    def _chat_notification_count_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("notification_count", connected_integration_id, chat_id)

    @classmethod
    def _chat_revision_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("chat_revision", connected_integration_id, chat_id)

    @classmethod
    def _visitor_chat_revision_key(
        cls,
        connected_integration_id: str,
        visitor_id: str,
        chat_id: str,
    ) -> str:
        return cls._redis_key(
            "visitor_revision",
            connected_integration_id,
            visitor_id,
            chat_id,
        )

    @classmethod
    def _chat_events_queue_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("events_queue", connected_integration_id, chat_id)

    @classmethod
    def _client_notice_key(cls, connected_integration_id: str, chat_id: str) -> str:
        return cls._redis_key("client_notice", connected_integration_id, chat_id)

    @classmethod
    def _chat_events_revision_dedupe_key(
        cls,
        connected_integration_id: str,
        chat_id: str,
        chat_revision: int,
    ) -> str:
        return cls._redis_key("events_queue_dedupe", connected_integration_id, chat_id, int(chat_revision))

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

    @classmethod
    def _field_exists_cache_key(
        cls,
        connected_integration_id: str,
        entity_type: str,
        field_key: str,
    ) -> str:
        normalized_entity_type = str(entity_type or "").strip().lower()
        normalized_key = _normalize_custom_field_key(field_key).strip().lower()
        digest = hashlib.sha1(normalized_key.encode("utf-8", errors="ignore")).hexdigest()
        return cls._redis_key("field_exists", connected_integration_id, normalized_entity_type, digest)

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        _require_redis()
        return await redis_ops.get(key)

    @staticmethod
    async def _redis_set(key: str, value: str, ttl_sec: int) -> None:
        _require_redis()
        await redis_ops.set(key, value, ex=max(int(ttl_sec or 1), 1))

    @staticmethod
    async def _redis_set_nx(key: str, value: str, ttl_sec: int) -> bool:
        _require_redis()
        inserted = await redis_ops.set(
            key,
            value,
            ex=max(int(ttl_sec or 1), 1),
            nx=True,
        )
        return bool(inserted)

    @staticmethod
    async def _redis_incr(key: str, ttl_sec: int) -> int:
        _require_redis()
        return await redis_incr_with_ttl(key, max(int(ttl_sec or 1), 1))

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        _require_redis()
        valid = [str(key).strip() for key in keys if str(key or "").strip()]
        if not valid:
            return
        await redis_ops.delete(*valid)

    @classmethod
    async def _acquire_lock_wait(
        cls,
        lock_key: str,
        ttl_sec: int,
        *,
        wait_seconds: float = 0.0,
    ) -> Optional[str]:
        _require_redis()
        token = uuid.uuid4().hex
        deadline = asyncio.get_running_loop().time() + max(float(wait_seconds or 0.0), 0.0)
        while True:
            ok = await cls._redis_set_nx(lock_key, token, ttl_sec)
            if ok:
                return token
            if asyncio.get_running_loop().time() >= deadline:
                return None
            await asyncio.sleep(0.05)

    @staticmethod
    async def _release_lock(lock_key: str, token: Optional[str]) -> None:
        if not lock_key or not token:
            return
        _require_redis()
        script = (
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end"
        )
        try:
            await redis_ops.eval(script, 1, lock_key, token)
        except Exception:
            current = await redis_ops.get(lock_key)
            if current == token:
                await redis_ops.delete(lock_key)

    @staticmethod
    def _client_notice_kind(external_message_id: str) -> str:
        safe_id = str(external_message_id or "").strip()
        if safe_id.startswith("webchat:channel_start:"):
            return "channel_start"
        if safe_id.startswith("webchat:channel_end:"):
            return "channel_end"
        if safe_id.startswith("webchat:channel_rating_prompt:"):
            return "rating_prompt"
        if safe_id.startswith("webchat:channel_rating_result:"):
            return "rating_result"
        return "system"

    @classmethod
    def _build_client_notice(
        cls,
        *,
        text: str,
        external_message_id: str,
        created_date: int,
        expires_at: int,
    ) -> Dict[str, Any]:
        safe_external_message_id = str(external_message_id or "").strip()
        return {
            "id": f"client_notice:{safe_external_message_id}",
            "text": text,
            "files": [],
            "created_date": int(created_date),
            "message_type": ChatMessageTypeEnum.System.value,
            "mine": False,
            "edited": False,
            "author_name": "",
            "expires_at": int(expires_at),
            "notice_kind": cls._client_notice_kind(safe_external_message_id),
        }

    @classmethod
    async def _cache_client_notice(
        cls,
        connected_integration_id: str,
        *,
        chat_id: str,
        text: str,
        external_message_id: str,
        created_date: int,
    ) -> None:
        _require_redis()
        safe_chat_id = str(chat_id or "").strip()
        safe_text = _normalize_channel_auto_message(text)
        safe_external_message_id = str(external_message_id or "").strip()
        if not safe_chat_id or not safe_text or not safe_external_message_id:
            return

        now_ts = int(time.time())
        ttl_sec = max(int(ExternalChatCrmChannelConfig.CLIENT_NOTICE_TTL_SEC or 1), 1)
        created_ts = int(created_date or now_ts)
        expires_at = now_ts + ttl_sec
        notice = cls._build_client_notice(
            text=safe_text,
            external_message_id=safe_external_message_id,
            created_date=created_ts,
            expires_at=expires_at,
        )
        await redis_zadd_with_ttl(
            cls._client_notice_key(connected_integration_id, safe_chat_id),
            _json_dumps(notice),
            expires_at,
            ttl_sec,
            max_items=max(int(ExternalChatCrmChannelConfig.CLIENT_NOTICE_MAX_ITEMS or 1), 1),
            prune_max_score=now_ts,
        )

    @classmethod
    def _parse_client_notice(cls, raw: str, now_ts: int) -> Optional[Dict[str, Any]]:
        try:
            payload = _json_loads(str(raw or ""))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None

        expires_at = _parse_int(payload.get("expires_at"), None)
        if not expires_at or int(expires_at) <= int(now_ts):
            return None
        notice_id = _normalize_text(payload.get("id"), 200)
        text = _normalize_channel_auto_message(payload.get("text"))
        created_date = _parse_int(payload.get("created_date"), None)
        if not notice_id or not text or not created_date:
            return None
        return {
            "id": notice_id,
            "text": text,
            "files": [],
            "created_date": int(created_date),
            "message_type": ChatMessageTypeEnum.System.value,
            "mine": False,
            "edited": False,
            "author_name": "",
            "expires_at": int(expires_at),
            "notice_kind": _normalize_text(payload.get("notice_kind"), 60) or "system",
        }

    @classmethod
    async def _read_client_notices(
        cls,
        connected_integration_id: str,
        chat_id: str,
    ) -> List[Dict[str, Any]]:
        _require_redis()
        safe_chat_id = str(chat_id or "").strip()
        if not safe_chat_id:
            return []

        now_ts = int(time.time())
        ttl_sec = max(int(ExternalChatCrmChannelConfig.CLIENT_NOTICE_TTL_SEC or 1), 1)
        rows = await redis_zrangebyscore_with_ttl(
            cls._client_notice_key(connected_integration_id, safe_chat_id),
            now_ts + 1,
            "+inf",
            ttl_sec,
            max_items=max(int(ExternalChatCrmChannelConfig.CLIENT_NOTICE_MAX_ITEMS or 1), 1),
            prune_max_score=now_ts,
        )
        notices: List[Dict[str, Any]] = []
        for raw in rows:
            notice = cls._parse_client_notice(raw, now_ts)
            if notice:
                notices.append(notice)
        return notices

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
        if not safe_chat_id:
            return
        _require_redis()
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

        queue_key = cls._chat_events_queue_key(connected_integration_id, safe_chat_id)
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
        event["id"] = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        serialized = _json_dumps(event)
        async with redis_ops.pipeline(transaction=True) as pipe:
            await pipe.rpush(queue_key, serialized)
            await pipe.ltrim(queue_key, -max_items, -1)
            await pipe.expire(queue_key, ttl_sec)
            await pipe.execute()

    @staticmethod
    def _build_revision_sync_event(
        *,
        chat_id: str,
        ticket_id: int,
        chat_revision: int,
        source_action: str,
    ) -> Dict[str, Any]:
        safe_revision = int(chat_revision or 0)
        return {
            "id": f"{int(time.time() * 1000)}-sync",
            "type": "chat_revision_changed",
            "source_action": str(source_action or "").strip() or "revision_sync",
            "chat_id": str(chat_id or ""),
            "ticket_id": int(ticket_id or 0),
            "chat_revision": safe_revision,
            "api_action": "history",
            "force_full": False,
            "created_at": int(time.time()),
            "payload": {},
        }

    @classmethod
    async def _poll_chat_events(
        cls,
        connected_integration_id: str,
        *,
        chat_id: str,
        max_items: int,
    ) -> List[Dict[str, Any]]:
        safe_chat_id = str(chat_id or "").strip()
        if not safe_chat_id:
            return []
        _require_redis()

        queue_key = cls._chat_events_queue_key(connected_integration_id, safe_chat_id)
        resolved_max_items = min(
            max(int(max_items or 1), 1),
            int(ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS),
        )
        ttl_sec = max(int(ExternalChatCrmChannelConfig.EVENT_QUEUE_TTL_SEC or 1), 1)
        rows = await redis_ops.eval(
            cls._EVENTS_DEQUEUE_LUA,
            1,
            queue_key,
            resolved_max_items,
            ttl_sec,
        )
        if not isinstance(rows, list) or not rows:
            return []

        events: List[Dict[str, Any]] = []
        for raw in rows:
            text = str(raw or "")
            if not text:
                continue
            try:
                payload = _json_loads(text)
            except Exception:
                continue
            if isinstance(payload, dict):
                events.append(payload)
        return events

    @classmethod
    async def _write_active_cache(
        cls,
        connected_integration_id: str,
        active: bool,
    ) -> None:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return

        now = time.monotonic()
        active_value = bool(active)
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (
                active_value,
                now + ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
            )

        await cls._redis_set(
            cls._active_cache_key(ci),
            "1" if active_value else "0",
            ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
        )

    @classmethod
    async def _is_connected_integration_active(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        _require_redis()
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
        if not force_refresh:
            cached_raw = await cls._redis_get(cache_key)
            if cached_raw in {"0", "1"}:
                active = cached_raw == "1"
                async with cls._ACTIVE_CACHE_LOCK:
                    cls._ACTIVE_CACHE[ci] = (
                        active,
                        now + ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
                    )
                return active

        lock_token = await cls._acquire_lock_wait(
            cls._active_fetch_lock_key(ci),
            ExternalChatCrmChannelConfig.ACTIVE_LOCK_TTL_SEC,
            wait_seconds=(
                ExternalChatCrmChannelConfig.SETTINGS_LOCK_WAIT_SEC
                if force_refresh
                else ExternalChatCrmChannelConfig.ACTIVE_LOCK_WAIT_SEC
            ),
        )
        if not lock_token:
            raise TimeoutError(f"Timed out waiting for active check lock for ID {ci}")

        detected: Optional[bool] = None
        try:
            if not force_refresh:
                cached_raw = await cls._redis_get(cache_key)
                if cached_raw in {"0", "1"}:
                    active = cached_raw == "1"
                    async with cls._ACTIVE_CACHE_LOCK:
                        cls._ACTIVE_CACHE[ci] = (
                            active,
                            now + ExternalChatCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
                        )
                    return active

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
            if isinstance(error, httpx.HTTPStatusError):
                status_code = (
                    int(error.response.status_code)
                    if error.response is not None
                    else None
                )
                if status_code in {401, 403, 404}:
                    await cls._write_active_cache(ci, False)
                    return False
            raise RuntimeError(
                f"ConnectedIntegration/Get failed for active check: ci={ci} error={error}"
            ) from error
        finally:
            await cls._release_lock(cls._active_fetch_lock_key(ci), lock_token)

        active = bool(detected)
        await cls._write_active_cache(ci, active)
        return active

    @classmethod
    async def _ensure_connected_integration_active(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> None:
        if await cls._is_connected_integration_active(
            connected_integration_id,
            force_refresh=force_refresh,
        ):
            return
        raise ConnectedIntegrationInactiveError(
            f"ConnectedIntegration {connected_integration_id} is inactive"
        )

    @staticmethod
    def _normalize_settings_map(raw: Dict[str, Any]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in (raw or {}).items():
            normalized_key = str(key or "").strip().lower()
            if normalized_key:
                normalized[normalized_key] = str(value or "").strip()
        return normalized

    @classmethod
    def _read_local_settings_cache(cls, cache_key: str) -> Optional[Dict[str, str]]:
        cached = _SETTINGS_LOCAL_CACHE.get(cache_key)
        if not cached:
            return None
        expires_at, settings_map = cached
        if expires_at <= _now_ts():
            _SETTINGS_LOCAL_CACHE.pop(cache_key, None)
            return None
        return dict(settings_map)

    @classmethod
    def _write_local_settings_cache(cls, cache_key: str, settings_map: Dict[str, str]) -> None:
        now_ts = _now_ts()
        if len(_SETTINGS_LOCAL_CACHE) >= ExternalChatCrmChannelConfig.SETTINGS_LOCAL_MAX:
            for key, (expires_at, _) in list(_SETTINGS_LOCAL_CACHE.items()):
                if expires_at <= now_ts:
                    _SETTINGS_LOCAL_CACHE.pop(key, None)
            while len(_SETTINGS_LOCAL_CACHE) >= ExternalChatCrmChannelConfig.SETTINGS_LOCAL_MAX:
                _SETTINGS_LOCAL_CACHE.pop(next(iter(_SETTINGS_LOCAL_CACHE)), None)
        _SETTINGS_LOCAL_CACHE[cache_key] = (
            now_ts + ExternalChatCrmChannelConfig.SETTINGS_LOCAL_TTL_SEC,
            dict(settings_map),
        )

    @classmethod
    async def _read_settings_stale_cache(
        cls,
        connected_integration_id: str,
    ) -> Optional[Dict[str, str]]:
        stale_key = cls._settings_stale_cache_key(connected_integration_id)
        local = cls._read_local_settings_cache(stale_key)
        if local is not None:
            return local
        try:
            cached_raw = await cls._redis_get(stale_key)
            if not cached_raw:
                return None
            cached = _json_loads(str(cached_raw))
            if not isinstance(cached, dict):
                return None
            settings_map = cls._normalize_settings_map(cached)
            cls._write_local_settings_cache(stale_key, settings_map)
            return settings_map
        except Exception:
            return None

    @classmethod
    async def _clear_settings_runtime_cache(cls, connected_integration_id: str) -> None:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        lock_token = await cls._acquire_lock_wait(
            cls._settings_fetch_lock_key(ci),
            ExternalChatCrmChannelConfig.SETTINGS_LOCK_TTL_SEC,
            wait_seconds=ExternalChatCrmChannelConfig.SETTINGS_LOCK_WAIT_SEC,
        )
        if not lock_token:
            raise TimeoutError(f"Timed out waiting for external chat settings lock for ID {ci}")
        try:
            async with cls._ACTIVE_CACHE_LOCK:
                cls._ACTIVE_CACHE.pop(ci, None)
            _SETTINGS_LOCAL_CACHE.pop(cls._settings_cache_key(ci), None)
            _SETTINGS_LOCAL_CACHE.pop(cls._settings_stale_cache_key(ci), None)
            async with _RUNTIME_LOCAL_LOCK:
                _RUNTIME_LOCAL_CACHE.pop(ci, None)
            await cls._redis_delete(
                cls._settings_cache_key(ci),
                cls._settings_stale_cache_key(ci),
                cls._active_cache_key(ci),
            )
        finally:
            await cls._release_lock(cls._settings_fetch_lock_key(ci), lock_token)

    @classmethod
    async def _fetch_settings_map(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        _require_redis()
        cache_key = cls._settings_cache_key(connected_integration_id)
        if not force_refresh:
            local = cls._read_local_settings_cache(cache_key)
            if local is not None:
                return local
            cached_raw = await cls._redis_get(cache_key)
            if cached_raw:
                try:
                    cached = _json_loads(cached_raw)
                    if isinstance(cached, dict):
                        settings_map = cls._normalize_settings_map(cached)
                        cls._write_local_settings_cache(cache_key, settings_map)
                        return settings_map
                except Exception:
                    pass

        lock_token = await cls._acquire_lock_wait(
            cls._settings_fetch_lock_key(connected_integration_id),
            ExternalChatCrmChannelConfig.SETTINGS_LOCK_TTL_SEC,
            wait_seconds=ExternalChatCrmChannelConfig.SETTINGS_LOCK_WAIT_SEC,
        )
        if not lock_token:
            stale = await cls._read_settings_stale_cache(connected_integration_id)
            if stale is not None:
                return stale
            raise TimeoutError(
                f"Timed out waiting for external chat settings refresh for ID {connected_integration_id}"
        )

        try:
            if not force_refresh:
                cached_raw = await cls._redis_get(cache_key)
                if cached_raw:
                    cached = _json_loads(cached_raw)
                    if isinstance(cached, dict):
                        settings_map = cls._normalize_settings_map(cached)
                        cls._write_local_settings_cache(cache_key, settings_map)
                        return settings_map

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

            settings_map = cls._normalize_settings_map(settings_map)
            payload = _json_dumps(settings_map)
            stale_key = cls._settings_stale_cache_key(connected_integration_id)
            cls._write_local_settings_cache(cache_key, settings_map)
            cls._write_local_settings_cache(stale_key, settings_map)
            async with redis_ops.pipeline(transaction=True) as pipe:
                await pipe.set(cache_key, payload, ex=ExternalChatCrmChannelConfig.SETTINGS_TTL_SEC)
                await pipe.set(stale_key, payload, ex=ExternalChatCrmChannelConfig.SETTINGS_STALE_TTL_SEC)
                await pipe.execute()
            return settings_map
        except Exception:
            stale = await cls._read_settings_stale_cache(connected_integration_id)
            if stale is not None:
                return stale
            raise
        finally:
            await cls._release_lock(
                cls._settings_fetch_lock_key(connected_integration_id),
                lock_token,
            )

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
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        await cls._ensure_connected_integration_active(ci, force_refresh=force_refresh)
        now_ts = _now_ts()
        if not force_refresh:
            async with _RUNTIME_LOCAL_LOCK:
                cached = _RUNTIME_LOCAL_CACHE.get(ci)
                if cached and cached[0] > now_ts:
                    return cached[1]
                if cached:
                    _RUNTIME_LOCAL_CACHE.pop(ci, None)

        settings_map = await cls._fetch_settings_map(
            ci,
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
        channel = await cls._get_channel(ci, int(channel_id))
        channel_name = _normalize_text(getattr(channel, "name", None), 80)
        chat_title = (
            channel_name
            or _normalize_text(settings_map.get("chat_title"), 80)
            or ExternalChatCrmChannelConfig.DEFAULT_CHAT_TITLE
        )
        channel_start_message = (
            _normalize_channel_auto_message(getattr(channel, "start_message", None)) or None
        )
        channel_end_message = (
            _normalize_channel_auto_message(getattr(channel, "end_message", None)) or None
        )
        channel_rating_enabled = bool(getattr(channel, "rating_enabled", False))
        channel_rating_message = (
            _normalize_channel_auto_message(getattr(channel, "rating_message", None)) or None
        )
        channel_rating_positive_message = (
            _normalize_channel_auto_message(getattr(channel, "rating_positive_message", None)) or None
        )
        channel_rating_negative_message = (
            _normalize_channel_auto_message(getattr(channel, "rating_negative_message", None)) or None
        )

        runtime = RuntimeConfig(
            connected_integration_id=ci,
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
        async with _RUNTIME_LOCAL_LOCK:
            _RUNTIME_LOCAL_CACHE[ci] = (
                _now_ts() + ExternalChatCrmChannelConfig.RUNTIME_LOCAL_TTL_SEC,
                runtime,
            )
        return runtime

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

    @staticmethod
    def _is_own_ticket(ticket: Optional[Ticket], runtime: RuntimeConfig) -> bool:
        if not ticket:
            return False
        external_dialog_id = str(getattr(ticket, "external_dialog_id", "") or "").strip()
        expected_prefix = f"webchat:dialog:{runtime.connected_integration_id}:"
        if not external_dialog_id.startswith(expected_prefix):
            return False
        ticket_channel_id = _parse_int(str(getattr(ticket, "channel_id", "") or ""), None)
        return bool(ticket_channel_id and int(ticket_channel_id) == int(runtime.channel_id))

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
        _require_redis()
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
        _require_redis()
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
        _require_redis()

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
            await redis_ops.expire(key, max(int(ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC or 1), 1))
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
        _require_redis()

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
        _require_redis()

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
    async def _get_visitor_known_revision(
        cls,
        connected_integration_id: str,
        visitor_id: str,
        chat_id: str,
    ) -> Optional[int]:
        safe_visitor_id = cls._normalize_visitor_id(visitor_id)
        safe_chat_id = str(chat_id or "").strip()
        if not safe_visitor_id or not safe_chat_id:
            return None
        raw = await cls._redis_get(
            cls._visitor_chat_revision_key(
                connected_integration_id,
                safe_visitor_id,
                safe_chat_id,
            )
        )
        parsed = _parse_int(raw, None)
        if parsed is None or int(parsed) < 0:
            return None
        return int(parsed)

    @classmethod
    async def _remember_visitor_revision(
        cls,
        connected_integration_id: str,
        visitor_id: str,
        chat_id: str,
        chat_revision: Any,
    ) -> None:
        safe_visitor_id = cls._normalize_visitor_id(visitor_id)
        safe_chat_id = str(chat_id or "").strip()
        revision = _parse_int(chat_revision, None)
        if not safe_visitor_id or not safe_chat_id or revision is None or int(revision) <= 0:
            return
        await cls._redis_set(
            cls._visitor_chat_revision_key(
                connected_integration_id,
                safe_visitor_id,
                safe_chat_id,
            ),
            str(int(revision)),
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )

    @classmethod
    async def _with_visitor_revision(
        cls,
        connected_integration_id: str,
        visitor_id: str,
        context: Optional[ChatContext],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        if context:
            await cls._remember_visitor_revision(
                connected_integration_id,
                visitor_id,
                str(context.chat_id),
                payload.get("chat_revision"),
            )
        return payload

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
        _require_redis()

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
        _require_redis()
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

    @staticmethod
    def _context_from_payload(payload: Any, visitor_id: Optional[str] = None) -> Optional[ChatContext]:
        if not isinstance(payload, dict):
            return None
        resolved_visitor_id = str(visitor_id or payload.get("visitor_id") or "").strip()
        client_id = _parse_int(payload.get("client_id"), None)
        ticket_id = _parse_int(payload.get("ticket_id"), None)
        chat_id = str(payload.get("chat_id") or "").strip()
        if not resolved_visitor_id or not client_id or not ticket_id or not chat_id:
            return None
        return ChatContext(
            visitor_id=resolved_visitor_id,
            client_id=int(client_id),
            ticket_id=int(ticket_id),
            chat_id=chat_id,
        )

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
        return cls._context_from_payload(payload, visitor_id)

    @classmethod
    async def _save_pending_params(
        cls,
        connected_integration_id: str,
        visitor_id: str,
        data: Dict[str, Any],
        *,
        clear_empty: bool = False,
    ) -> None:
        pending = _extract_pending_request_params(data)
        if not pending:
            if clear_empty:
                await cls._redis_delete(cls._pending_params_cache_key(connected_integration_id, visitor_id))
            return
        await cls._redis_set(
            cls._pending_params_cache_key(connected_integration_id, visitor_id),
            _json_dumps(pending),
            ExternalChatCrmChannelConfig.PENDING_PARAMS_TTL_SEC,
        )

    @classmethod
    async def _load_pending_params(
        cls,
        connected_integration_id: str,
        visitor_id: str,
    ) -> Dict[str, Any]:
        raw = await cls._redis_get(cls._pending_params_cache_key(connected_integration_id, visitor_id))
        if not raw:
            return {}
        try:
            payload = _json_loads(raw)
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    async def _delete_pending_params(cls, connected_integration_id: str, visitor_id: str) -> None:
        await cls._redis_delete(cls._pending_params_cache_key(connected_integration_id, visitor_id))

    @classmethod
    async def _load_cached_context_by_chat(
        cls, connected_integration_id: str, chat_id: str
    ) -> Optional[ChatContext]:
        raw = await cls._redis_get(cls._chat_context_cache_key(connected_integration_id, chat_id))
        if not raw:
            return None
        try:
            payload = _json_loads(raw)
        except Exception:
            return None
        return cls._context_from_payload(payload)

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
        await asyncio.gather(
            cls._redis_set(
                cls._context_cache_key(connected_integration_id, context.visitor_id),
                payload,
                ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
            ),
            cls._redis_set(
                cls._chat_context_cache_key(connected_integration_id, context.chat_id),
                payload,
                ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
            ),
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
        client_fields: Optional[List[FieldValueAdd]] = None,
    ) -> Client:
        add_response = await api.crm.client.add(
            ClientAddRequest(
                external_id=external_id,
                name=_normalize_text(profile.get("display_name"), 120) or "Guest",
                phone=_normalize_phone(profile.get("phone")),
                email=_normalize_email(profile.get("email")),
                fields=client_fields or None,
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

    @staticmethod
    def _existing_field_values_by_key(fields: Optional[List[Any]]) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for field in fields or []:
            raw_key = field.get("key") if isinstance(field, dict) else getattr(field, "key", None)
            key = _normalize_custom_field_key(raw_key)
            if not key:
                continue
            raw_value = field.get("value") if isinstance(field, dict) else getattr(field, "value", None)
            value = _normalize_custom_field_value(raw_value)
            values[key.lower()] = value or ""
        return values

    @classmethod
    def _changed_field_edits(
        cls,
        existing_fields: Optional[List[Any]],
        requested_fields: Optional[List[FieldValueEdit]],
    ) -> List[FieldValueEdit]:
        if not requested_fields:
            return []
        existing_by_key = cls._existing_field_values_by_key(existing_fields)
        changed: List[FieldValueEdit] = []
        for field in requested_fields:
            key = _normalize_custom_field_key(getattr(field, "key", None))
            if not key:
                continue
            current_value_exists = key.lower() in existing_by_key
            current_value = existing_by_key.get(key.lower(), "")
            if bool(getattr(field, "deleted", False)):
                if current_value_exists:
                    changed.append(field)
                continue
            requested_value = _normalize_custom_field_value(getattr(field, "value", None)) or ""
            if not current_value_exists or current_value != requested_value:
                changed.append(field)
        return changed

    @classmethod
    async def _sync_client_profile_if_needed(
        cls,
        api: RegosAPI,
        client: Client,
        profile: Dict[str, Any],
        *,
        client_fields: Optional[List[FieldValueEdit]] = None,
    ) -> None:
        if not client or not client.id:
            return
        patch: Dict[str, Any] = {}
        display_name = _normalize_text(profile.get("display_name"), 120)
        phone = _normalize_phone(profile.get("phone"))
        email = _normalize_email(profile.get("email"))
        if display_name and _normalize_text(client.name, 120) != display_name:
            patch["name"] = display_name
        if phone and _normalize_phone(client.phone) != phone:
            patch["phone"] = phone
        if email and _normalize_email(client.email) != email:
            patch["email"] = email
        changed_fields = cls._changed_field_edits(
            getattr(client, "fields", None),
            client_fields,
        )
        if changed_fields:
            patch["fields"] = changed_fields
        if not patch:
            return
        response = await api.crm.client.edit(ClientEditRequest(id=int(client.id), **patch))
        if response.ok:
            return
        payload = _result_to_dict(response.result)
        raise RuntimeError(
            "Client/Edit rejected: "
            f"error={payload.get('error')} description={payload.get('description')}"
        )

    @classmethod
    async def _sync_client_profile_by_id(
        cls,
        connected_integration_id: str,
        *,
        client_id: int,
        profile: Dict[str, Any],
        client_fields: Optional[List[FieldValueEdit]] = None,
    ) -> None:
        if not client_id:
            return
        display_name = _normalize_text(profile.get("display_name"), 120)
        phone = _normalize_phone(profile.get("phone"))
        email = _normalize_email(profile.get("email"))
        profile_has_values = bool(display_name or phone or email)
        if not profile_has_values and not client_fields:
            return
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            client = await cls._load_client_by_id(api, int(client_id))
            if client and getattr(client, "id", None):
                await cls._sync_client_profile_if_needed(
                    api,
                    client,
                    profile,
                    client_fields=client_fields,
                )

    @classmethod
    async def _create_ticket(
        cls,
        api: RegosAPI,
        *,
        runtime: RuntimeConfig,
        client_id: int,
        external_dialog_id: str,
        subject: str,
        ticket_fields: Optional[List[FieldValueAdd]] = None,
    ) -> Ticket:
        add_response = await api.crm.ticket.add(
            TicketAddRequest(
                client_id=int(client_id),
                channel_id=int(runtime.channel_id),
                direction=TicketDirectionEnum.Inbound,
                external_dialog_id=external_dialog_id,
                subject=subject,
                responsible_user_id=runtime.default_responsible_user_id,
                fields=ticket_fields or None,
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
    async def _apply_ticket_fields(
        cls,
        api: RegosAPI,
        *,
        ticket_id: int,
        ticket_fields: Optional[List[FieldValueEdit]],
    ) -> None:
        if not ticket_id or not ticket_fields:
            return
        response = await api.crm.ticket.edit(
            TicketEditRequest(id=int(ticket_id), fields=ticket_fields)
        )
        if response.ok:
            return
        payload = _result_to_dict(response.result)
        raise RuntimeError(
            "Ticket/Edit rejected: "
            f"error={payload.get('error')} description={payload.get('description')}"
        )

    @classmethod
    async def _apply_ticket_fields_by_id(
        cls,
        connected_integration_id: str,
        *,
        ticket_id: int,
        ticket_fields: Optional[List[FieldValueEdit]],
    ) -> None:
        if not ticket_id or not ticket_fields:
            return
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            await cls._apply_ticket_fields(
                api,
                ticket_id=int(ticket_id),
                ticket_fields=ticket_fields,
            )

    @staticmethod
    def _custom_field_keys(
        *field_lists: Optional[List[Any]],
    ) -> List[str]:
        keys: Dict[str, str] = {}
        for field_list in field_lists:
            if not field_list:
                continue
            for field in field_list:
                raw_key = getattr(field, "key", None)
                if isinstance(field, dict):
                    raw_key = field.get("key")
                key = _normalize_custom_field_key(raw_key)
                if not key:
                    continue
                keys[key.strip().lower()] = key
        return list(keys.values())

    @classmethod
    async def _get_cached_field_exists(
        cls,
        connected_integration_id: str,
        entity_type: str,
        field_key: str,
    ) -> Optional[bool]:
        _require_redis()
        raw = await cls._redis_get(
            cls._field_exists_cache_key(connected_integration_id, entity_type, field_key)
        )
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            text = raw.decode("utf-8", errors="ignore").strip().lower()
        else:
            text = str(raw or "").strip().lower()
        if text in {"1", "true", "yes"}:
            return True
        if text in {"0", "false", "no"}:
            return False
        return None

    @classmethod
    async def _cache_field_exists(
        cls,
        connected_integration_id: str,
        entity_type: str,
        field_key: str,
        exists: bool,
    ) -> None:
        _require_redis()
        await cls._redis_set(
            cls._field_exists_cache_key(connected_integration_id, entity_type, field_key),
            "1" if exists else "0",
            ExternalChatCrmChannelConfig.FIELD_EXISTS_CACHE_TTL_SEC,
        )

    @staticmethod
    def _field_rows_from_result(result: Any) -> List[Any]:
        return result if isinstance(result, list) else []

    @classmethod
    async def _fetch_existing_field_keys(
        cls,
        api: RegosAPI,
        entity_type: str,
        field_keys: List[str],
    ) -> Dict[str, str]:
        normalized_keys = [key for key in (_normalize_custom_field_key(item) for item in field_keys) if key]
        if not normalized_keys:
            return {}
        normalized_entity_type = str(entity_type or "").strip()
        response = await api.references.field.get(
            FieldGetRequest(
                entity_type=normalized_entity_type,
                keys=normalized_keys,
                limit=max(len(normalized_keys), 1),
                offset=0,
            )
        )
        if not response.ok:
            raise RuntimeError(
                f"Field/Get rejected: entity_type={normalized_entity_type} payload={response.result}"
            )

        existing: Dict[str, str] = {}
        expected_entity_type = normalized_entity_type.lower()
        for row in cls._field_rows_from_result(response.result):
            row_key_raw = row.get("key") if isinstance(row, dict) else getattr(row, "key", None)
            row_entity_type_raw = (
                row.get("entity_type") if isinstance(row, dict) else getattr(row, "entity_type", None)
            )
            row_key = _normalize_custom_field_key(row_key_raw)
            if not row_key:
                continue
            row_entity_type = str(row_entity_type_raw or "").strip().lower()
            if row_entity_type and row_entity_type != expected_entity_type:
                continue
            existing[row_key.lower()] = row_key
        return existing

    @classmethod
    async def _find_existing_field_key_lowers(
        cls,
        connected_integration_id: str,
        entity_type: str,
        field_keys: List[str],
    ) -> Dict[str, str]:
        keys_by_lower: Dict[str, str] = {}
        for raw_key in field_keys:
            key = _normalize_custom_field_key(raw_key)
            if key:
                keys_by_lower[key.lower()] = key
        if not keys_by_lower:
            return {}

        existing_by_lower: Dict[str, str] = {}
        keys_to_fetch_by_lower: Dict[str, str] = {}
        for lowered, key in keys_by_lower.items():
            cached = await cls._get_cached_field_exists(
                connected_integration_id,
                entity_type,
                key,
            )
            if cached is True:
                existing_by_lower[lowered] = key
                continue
            if cached is False:
                continue
            keys_to_fetch_by_lower[lowered] = key

        if keys_to_fetch_by_lower:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                fetched_existing_by_lower = await cls._fetch_existing_field_keys(
                    api,
                    entity_type,
                    list(keys_to_fetch_by_lower.values()),
                )
            for lowered, key in keys_to_fetch_by_lower.items():
                exists = lowered in fetched_existing_by_lower
                await cls._cache_field_exists(
                    connected_integration_id,
                    entity_type,
                    key,
                    exists,
                )
                if exists:
                    existing_by_lower[lowered] = fetched_existing_by_lower[lowered]

        return existing_by_lower

    @classmethod
    async def _find_unknown_field_keys(
        cls,
        connected_integration_id: str,
        entity_type: str,
        field_keys: List[str],
    ) -> List[str]:
        keys_by_lower: Dict[str, str] = {}
        for raw_key in field_keys:
            key = _normalize_custom_field_key(raw_key)
            if key:
                keys_by_lower[key.lower()] = key
        if not keys_by_lower:
            return []
        existing_by_lower = await cls._find_existing_field_key_lowers(
            connected_integration_id,
            entity_type,
            list(keys_by_lower.values()),
        )
        return [
            key
            for lowered, key in keys_by_lower.items()
            if lowered not in existing_by_lower
        ]

    @classmethod
    async def _filter_existing_fields(
        cls,
        connected_integration_id: str,
        entity_type: str,
        *field_lists: Optional[List[Any]],
    ) -> Tuple[List[Any], ...]:
        field_keys = cls._custom_field_keys(*field_lists)
        existing_by_lower = await cls._find_existing_field_key_lowers(
            connected_integration_id,
            entity_type,
            field_keys,
        )
        if not existing_by_lower:
            return tuple([] for _ in field_lists)

        filtered: List[List[Any]] = []
        for field_list in field_lists:
            rows: List[Any] = []
            for field in field_list or []:
                raw_key = getattr(field, "key", None)
                if isinstance(field, dict):
                    raw_key = field.get("key")
                key = _normalize_custom_field_key(raw_key)
                if key and key.lower() in existing_by_lower:
                    rows.append(field)
            filtered.append(rows)
        return tuple(filtered)

    @classmethod
    async def _prepare_write_params(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        data: Dict[str, Any],
    ) -> Tuple[Optional[PreparedWriteParams], Optional[JSONResponse]]:
        pending_data = await cls._load_pending_params(connected_integration_id, visitor_id)
        profile = _merge_profiles(
            cls._extract_profile(pending_data),
            cls._extract_profile(data),
        )
        pending_client_field_adds = _normalize_client_field_adds(pending_data)
        pending_client_field_edits = _normalize_client_field_edits(pending_data)
        pending_ticket_field_adds = _normalize_ticket_field_adds(pending_data)
        pending_ticket_field_edits = _normalize_ticket_field_edits(pending_data)
        current_client_field_adds = _normalize_client_field_adds(data)
        current_client_field_edits = _normalize_client_field_edits(data)
        current_ticket_field_adds = _normalize_ticket_field_adds(data)
        current_ticket_field_edits = _normalize_ticket_field_edits(data)

        client_field_adds = _merge_field_adds(pending_client_field_adds, current_client_field_adds)
        client_field_edits = _merge_field_edits(pending_client_field_edits, current_client_field_edits)
        ticket_field_adds = _merge_field_adds(pending_ticket_field_adds, current_ticket_field_adds)
        ticket_field_edits = _merge_field_edits(pending_ticket_field_edits, current_ticket_field_edits)

        missing_required_fields = cls._missing_required_profile_fields(runtime, profile)
        if missing_required_fields:
            return None, JSONResponse(
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

        ticket_field_keys = cls._custom_field_keys(ticket_field_adds, ticket_field_edits)
        if ticket_field_keys:
            try:
                unknown_ticket_fields = await cls._find_unknown_field_keys(
                    connected_integration_id,
                    "Ticket",
                    ticket_field_keys,
                )
            except Exception as error:
                logger.exception(
                    "Ticket field validation failed: ci=%s visitor_id=%s fields=%s",
                    connected_integration_id,
                    visitor_id,
                    ticket_field_keys,
                )
                return None, JSONResponse(
                    status_code=500,
                    content={
                        "error": 500,
                        "description": f"Failed to validate ticket fields: {error}",
                    },
                )
            if unknown_ticket_fields:
                return None, JSONResponse(
                    status_code=400,
                    content={
                        "error": 400,
                        "description": "Unknown ticket fields",
                        "unknown_ticket_fields": unknown_ticket_fields,
                    },
                )

        if client_field_adds or client_field_edits:
            try:
                client_field_adds, client_field_edits = await cls._filter_existing_fields(
                    connected_integration_id,
                    "Client",
                    client_field_adds,
                    client_field_edits,
                )
            except Exception as error:
                logger.exception(
                    "Client field validation failed: ci=%s visitor_id=%s fields=%s",
                    connected_integration_id,
                    visitor_id,
                    cls._custom_field_keys(client_field_adds, client_field_edits),
                )
                return None, JSONResponse(
                    status_code=500,
                    content={
                        "error": 500,
                        "description": f"Failed to validate client fields: {error}",
                    },
                )

        sync_client_info = bool(pending_data or client_field_edits)
        sync_ticket_fields = bool(ticket_field_adds or ticket_field_edits)
        return PreparedWriteParams(
            profile=profile,
            client_field_adds=client_field_adds,
            client_field_edits=client_field_edits,
            ticket_field_adds=ticket_field_adds,
            ticket_field_edits=ticket_field_edits,
            sync_client_info=sync_client_info,
            sync_ticket_fields=sync_ticket_fields,
        ), None

    @classmethod
    async def _ensure_chat_context(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        visitor_id: str,
        profile: Dict[str, Any],
        *,
        client_field_adds: Optional[List[FieldValueAdd]] = None,
        client_field_edits: Optional[List[FieldValueEdit]] = None,
        sync_client_info: bool = False,
        sync_ticket_fields: bool = False,
        ticket_field_adds: Optional[List[FieldValueAdd]] = None,
        ticket_field_edits: Optional[List[FieldValueEdit]] = None,
        allow_create_ticket: bool = False,
        create_source: str = "",
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
                if sync_ticket_fields:
                    await cls._apply_ticket_fields_by_id(
                        connected_integration_id,
                        ticket_id=int(cached.ticket_id),
                        ticket_fields=ticket_field_edits,
                    )
                if sync_client_info:
                    await cls._sync_client_profile_by_id(
                        connected_integration_id,
                        client_id=int(cached.client_id),
                        profile=profile,
                        client_fields=client_field_edits,
                    )
                await cls._save_cached_context(connected_integration_id, cached)
                return cached

        if not cached:
            cached = await cls._load_cached_context(connected_integration_id, visitor_id)
        cached_client_id = int(cached.client_id) if cached and cached.client_id else None
        if not cached_client_id and not allow_create_ticket:
            raise RuntimeError("Chat context creation is not allowed for this action")

        external_client_id = cls._build_client_external_id(connected_integration_id, visitor_id)
        external_dialog_id = cls._build_ticket_external_dialog_id(connected_integration_id, visitor_id)

        start_message_for_new_ticket: Optional[str] = None
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            created_ticket_now = False
            created_client_now = False
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
                    client_fields=client_field_adds if sync_client_info else None,
                )
                created_client_now = True
            if sync_client_info and not created_client_now:
                await cls._sync_client_profile_if_needed(
                    api,
                    client,
                    profile,
                    client_fields=client_field_edits,
                )

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
                if not allow_create_ticket:
                    raise RuntimeError("Ticket creation is not allowed for this action")
                subject = cls._build_subject(
                    runtime.ticket_subject_template,
                    runtime.channel_name,
                    visitor_id,
                    profile,
                )
                logger.info(
                    "Creating external chat ticket: ci=%s visitor_id=%s source=%s",
                    connected_integration_id,
                    visitor_id,
                    str(create_source or "").strip() or "unknown",
                )
                ticket = await cls._create_ticket(
                    api,
                    runtime=runtime,
                    client_id=int(client.id),
                    external_dialog_id=external_dialog_id,
                    subject=subject,
                    ticket_fields=ticket_field_adds if sync_ticket_fields else None,
                )
                created_ticket_now = True
            elif sync_ticket_fields and ticket_field_edits:
                await cls._apply_ticket_fields(
                    api,
                    ticket_id=int(ticket.id),
                    ticket_fields=ticket_field_edits,
                )

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
        *,
        client_field_adds: Optional[List[FieldValueAdd]] = None,
        client_field_edits: Optional[List[FieldValueEdit]] = None,
        sync_client_info: bool = False,
        sync_ticket_fields: bool = False,
        ticket_field_adds: Optional[List[FieldValueAdd]] = None,
        ticket_field_edits: Optional[List[FieldValueEdit]] = None,
    ) -> ChatContext:
        return await cls._ensure_chat_context(
            connected_integration_id=connected_integration_id,
            runtime=runtime,
            visitor_id=visitor_id,
            profile=profile,
            client_field_adds=client_field_adds,
            client_field_edits=client_field_edits,
            sync_client_info=sync_client_info,
            sync_ticket_fields=sync_ticket_fields,
            ticket_field_adds=ticket_field_adds,
            ticket_field_edits=ticket_field_edits,
            allow_create_ticket=True,
            create_source="reopen_after_client_message",
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
        *,
        client_field_adds: Optional[List[FieldValueAdd]] = None,
        client_field_edits: Optional[List[FieldValueEdit]] = None,
        sync_client_info: bool = False,
        sync_ticket_fields: bool = False,
        ticket_field_adds: Optional[List[FieldValueAdd]] = None,
        ticket_field_edits: Optional[List[FieldValueEdit]] = None,
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
                client_field_adds=client_field_adds,
                client_field_edits=client_field_edits,
                sync_client_info=sync_client_info,
                sync_ticket_fields=sync_ticket_fields,
                ticket_field_adds=ticket_field_adds,
                ticket_field_edits=ticket_field_edits,
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
        client_field_adds: Optional[List[FieldValueAdd]] = None,
        client_field_edits: Optional[List[FieldValueEdit]] = None,
        sync_client_info: bool = False,
        sync_ticket_fields: bool = False,
        ticket_field_adds: Optional[List[FieldValueAdd]] = None,
        ticket_field_edits: Optional[List[FieldValueEdit]] = None,
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
                client_field_adds=client_field_adds,
                client_field_edits=client_field_edits,
                sync_client_info=sync_client_info,
                sync_ticket_fields=sync_ticket_fields,
                ticket_field_adds=ticket_field_adds,
                ticket_field_edits=ticket_field_edits,
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
        _require_redis()
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
        safe_text = _normalize_channel_auto_message(text)
        safe_external_message_id = str(external_message_id or "").strip()
        if not safe_chat_id or not safe_text or not safe_external_message_id:
            return False

        created_date = int(time.time())
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
            await cls._cache_client_notice(
                connected_integration_id,
                chat_id=safe_chat_id,
                text=safe_text,
                external_message_id=safe_external_message_id,
                created_date=created_date,
            )
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
        safe_text = _normalize_channel_auto_message(text)
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
                if message_type in {
                    ChatMessageTypeEnum.Private.value,
                    ChatMessageTypeEnum.System.value,
                }:
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

            text = _resolve_history_message_text(
                row,
                message_type,
                max_len=ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH,
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
        history.extend(await cls._read_client_notices(connected_integration_id, context.chat_id))
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
        await cls._reset_notification_count(connected_integration_id, context)

    @classmethod
    async def _get_notification_count(
        cls,
        connected_integration_id: str,
        context: ChatContext,
    ) -> int:
        raw = await cls._redis_get(
            cls._chat_notification_count_key(connected_integration_id, context.chat_id)
        )
        return max(_parse_int(raw, 0) or 0, 0)

    @classmethod
    async def _increment_notification_count(
        cls,
        connected_integration_id: str,
        context: ChatContext,
    ) -> int:
        _require_redis()
        return await cls._redis_incr(
            cls._chat_notification_count_key(connected_integration_id, context.chat_id),
            ExternalChatCrmChannelConfig.CONTEXT_TTL_SEC,
        )

    @classmethod
    async def _reset_notification_count(
        cls,
        connected_integration_id: str,
        context: ChatContext,
    ) -> None:
        await cls._redis_delete(
            cls._chat_notification_count_key(connected_integration_id, context.chat_id)
        )

    @staticmethod
    def _compose_chat_state_view(
        chat_revision: Any,
        notification_count: Optional[Any] = None,
    ) -> Dict[str, Any]:
        view: Dict[str, Any] = {"chat_revision": chat_revision}
        if notification_count is not None:
            view["notification_count"] = max(_parse_int(notification_count, 0) or 0, 0)
        return view

    @classmethod
    def _compose_no_context_response(
        cls,
        visitor_id: str,
        runtime: RuntimeConfig,
        *,
        include_settings: bool = False,
        include_history: bool = False,
        include_events: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "status": "ok",
            "visitor_id": visitor_id,
            **cls._compose_chat_state_view(0, 0),
            **cls._compose_ticket_view_state(runtime, None),
        }
        if include_settings:
            payload.update(
                {
                    "chat_title": runtime.chat_title,
                    "required_profile_fields": {
                        "display_name": runtime.require_display_name,
                        "phone": runtime.require_phone,
                        "email": runtime.require_email,
                    },
                }
            )
        if include_history:
            payload.update({"history_changed": True, "history": []})
        if include_events:
            payload["events"] = []
        return payload

    @classmethod
    async def _get_chat_state_view(
        cls,
        connected_integration_id: str,
        context: ChatContext,
        *,
        include_notifications: bool,
    ) -> Dict[str, Any]:
        if include_notifications:
            chat_revision, notification_count = await asyncio.gather(
                cls._get_chat_revision(connected_integration_id, str(context.chat_id)),
                cls._get_notification_count(connected_integration_id, context),
            )
            return cls._compose_chat_state_view(chat_revision, notification_count)
        chat_revision = await cls._get_chat_revision(connected_integration_id, str(context.chat_id))
        return cls._compose_chat_state_view(chat_revision)

    @classmethod
    async def _load_chat_message_by_id(
        cls,
        connected_integration_id: str,
        chat_id: str,
        message_id: str,
    ) -> Optional[Any]:
        safe_message_id = str(message_id or "").strip()
        if not safe_message_id:
            return None
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.chat.chat_message.get(
                ChatMessageGetRequest(
                    chat_id=str(chat_id),
                    ids=[safe_message_id],
                    limit=1,
                    offset=0,
                    include_staff_private=False,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @staticmethod
    def _should_increment_notification_for_message(message: Any) -> bool:
        message_payload = _result_to_dict(message)
        message_type = (
            _enum_value(message_payload.get("message_type")).strip()
            or ChatMessageTypeEnum.Regular.value
        )
        if message_type != ChatMessageTypeEnum.Regular.value:
            return False
        author_type = _enum_value(message_payload.get("author_entity_type")).strip().lower()
        if not author_type:
            return False
        return author_type != ChatEntityTypeEnum.Client.value.lower()

    @staticmethod
    def _extract_profile(data: Dict[str, Any]) -> Dict[str, Any]:
        client_params: Dict[str, Any] = {}
        for raw_key, raw_value in _iter_client_info_param_rows(data.get("client_params")):
            key = str(raw_key or "").strip().lower()
            if key and key not in client_params:
                client_params[key] = raw_value
        return {
            "display_name": _normalize_text(
                data.get("display_name")
                or data.get("name")
                or data.get("full_name")
                or client_params.get("display_name")
                or client_params.get("name")
                or client_params.get("full_name"),
                120,
            ),
            "email": _normalize_email(
                data.get("email")
                or data.get("mail")
                or client_params.get("email")
                or client_params.get("mail")
            ),
            "phone": _normalize_phone(
                data.get("phone")
                or data.get("phone_number")
                or data.get("tel")
                or client_params.get("phone")
                or client_params.get("phone_number")
                or client_params.get("tel")
            ),
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
        safe_asset_version = html.escape(ExternalChatCrmChannelConfig.UI_ASSET_VERSION, quote=True)
        safe_fontawesome_css_url = html.escape(
            _url_with_ui_asset_version(
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"
            ),
            quote=True,
        )

        if chat_css_url:
            safe_css_url = html.escape(_url_with_ui_asset_version(chat_css_url), quote=True)
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
            safe_asset_version=safe_asset_version,
            safe_fontawesome_css_url=safe_fontawesome_css_url,
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

    @staticmethod
    def _resolve_stream_ttl() -> int:
        return redis_ttl_seconds(ExternalChatCrmChannelConfig.STREAM_TTL_SEC)

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str, *, force: bool = False) -> None:
        _require_redis()
        if not force and stream_key in _STREAM_GROUP_READY:
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            ExternalChatCrmChannelConfig.STREAM_GROUP,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        _STREAM_GROUP_READY.add(stream_key)

    @classmethod
    def _serialize_stream_fields(cls, fields: Dict[str, Any]) -> Dict[str, str]:
        serialized: Dict[str, str] = {}
        for key, value in (fields or {}).items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = _json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)
        return serialized

    @classmethod
    async def _enqueue_stream(cls, stream_key: str, fields: Dict[str, Any]) -> None:
        _require_redis()
        await redis_stream_add_with_ttl(
            stream_key,
            cls._serialize_stream_fields(fields),
            maxlen=ExternalChatCrmChannelConfig.STREAM_MAXLEN,
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
        _require_redis()
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
            str(ExternalChatCrmChannelConfig.WEBHOOK_DEDUPE_TTL_SEC),
            str(ExternalChatCrmChannelConfig.STREAM_MAXLEN),
            str(stream_ttl),
            "1" if should_touch else "0",
            *field_args,
        )
        if should_touch and int(result or 0) == 1:
            _STREAM_TTL_TOUCH_TS[stream_key] = now_ts
        return int(result or 0) == 1

    @classmethod
    async def _enqueue_webhook_event(
        cls,
        connected_integration_id: str,
        webhook_action: str,
        payload: Dict[str, Any],
        event_id: Optional[str],
        event_key: str,
    ) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        await cls._ensure_stream_workers(ensure_groups=False)
        fields = {
            "connected_integration_id": ci,
            "action": webhook_action,
            "payload": payload if isinstance(payload, dict) else {},
            "event_id": event_id or "",
            "event_key": event_key,
            "attempt": "0",
            "enqueued_at": str(_now_ts()),
        }
        queued = await cls._enqueue_stream_deduped(
            stream_key=cls._stream_key(),
            dedupe_key=cls._webhook_enqueue_dedupe_key(ci, event_key),
            fields=fields,
        )
        if not queued:
            logger.debug("External chat webhook duplicate skipped: ci=%s action=%s", ci, webhook_action)
        return queued

    @classmethod
    async def _touch_stream_ttl(cls, stream_key: str, *, force: bool = False) -> None:
        _require_redis()
        await redis_expire_if_due(
            stream_key,
            cls._resolve_stream_ttl(),
            _STREAM_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def _set_worker_heartbeat(cls, worker_index: int) -> None:
        _require_redis()
        await redis_ops.setex(
            cls._worker_heartbeat_key(worker_index),
            ExternalChatCrmChannelConfig.HEARTBEAT_TTL_SEC,
            str(_now_ts()),
        )

    @classmethod
    def _stream_workers_ready(cls) -> bool:
        for index in range(ExternalChatCrmChannelConfig.STREAM_WORKERS):
            task = _STREAM_WORKER_TASKS.get(index)
            if not task or task.done():
                return False
        return True

    @classmethod
    async def _ensure_stream_workers(cls, *, ensure_groups: bool = True) -> None:
        _require_redis()
        if not ensure_groups and cls._stream_workers_ready():
            return
        stream_key = cls._stream_key()
        if ensure_groups:
            await cls._ensure_consumer_group(stream_key)
        async with _STREAM_WORKER_LOCK:
            for index in range(ExternalChatCrmChannelConfig.STREAM_WORKERS):
                task = _STREAM_WORKER_TASKS.get(index)
                if task and not task.done():
                    continue
                _STREAM_WORKER_TASKS[index] = asyncio.create_task(
                    cls._stream_worker_loop(index),
                    name=f"external_chat_stream_{index}",
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
                logger.exception("Error while stopping external chat stream worker")
        _STREAM_GROUP_READY.clear()
        _STREAM_CLAIM_TS.clear()
        _STREAM_TTL_TOUCH_TS.clear()
        _SETTINGS_LOCAL_CACHE.clear()
        async with _RUNTIME_LOCAL_LOCK:
            _RUNTIME_LOCAL_CACHE.clear()

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        _require_redis()
        await cls._ensure_stream_workers()
        return {"streams": 1, "workers": len(_STREAM_WORKER_TASKS)}

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                ExternalChatCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=ExternalChatCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=ExternalChatCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            raise
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
        consumer = f"{_INSTANCE_ID}:webhook:{worker_index}"
        semaphore = asyncio.Semaphore(ExternalChatCrmChannelConfig.EVENT_CONCURRENCY)
        logger.info("External chat stream worker started: index=%s", worker_index)
        try:
            await cls._ensure_consumer_group(stream_key)
            while True:
                try:
                    await cls._set_worker_heartbeat(worker_index)
                    await cls._touch_stream_ttl(stream_key)
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(stream_key) or 0)
                    if now_ts - last_claim_ts >= ExternalChatCrmChannelConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[stream_key] = now_ts
                        claimed = await cls._process_claimed_entries(stream_key, consumer)
                        if claimed:
                            await asyncio.gather(
                                *[
                                    cls._process_stream_entry_guarded(stream_key, entry_id, fields, semaphore)
                                    for entry_id, fields in claimed
                                ]
                            )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=ExternalChatCrmChannelConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=ExternalChatCrmChannelConfig.STREAM_BATCH_SIZE,
                            block=ExternalChatCrmChannelConfig.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(stream_key, force=True)
                            continue
                        raise

                    entries: List[Tuple[str, Dict[str, Any]]] = []
                    for _, rows in records or []:
                        entries.extend(
                            (str(entry_id), fields if isinstance(fields, dict) else {})
                            for entry_id, fields in rows or []
                        )
                    if entries:
                        await asyncio.gather(
                            *[
                                cls._process_stream_entry_guarded(stream_key, entry_id, fields, semaphore)
                                for entry_id, fields in entries
                            ]
                        )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception("External chat stream worker error: index=%s error=%s", worker_index, error)
                    await asyncio.sleep(1.0)
        finally:
            async with _STREAM_WORKER_LOCK:
                if _STREAM_WORKER_TASKS.get(worker_index) is asyncio.current_task():
                    _STREAM_WORKER_TASKS.pop(worker_index, None)

    @classmethod
    async def _process_stream_entry_guarded(
        cls,
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> None:
        async with semaphore:
            await cls._process_stream_entry(stream_key, entry_id, fields)

    @classmethod
    def _decode_stream_payload(cls, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            decoded = _json_loads(str(raw or ""))
            return decoded if isinstance(decoded, dict) else {}
        except Exception:
            return {}

    @classmethod
    async def _ack_stream_entry(cls, stream_key: str, entry_id: str) -> None:
        await redis_stream_ack_delete(stream_key, ExternalChatCrmChannelConfig.STREAM_GROUP, entry_id)

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        ci = str(fields.get("connected_integration_id") or "").strip()
        webhook_action = str(fields.get("action") or "").strip()
        event_id = str(fields.get("event_id") or "").strip() or None
        event_key = str(fields.get("event_key") or "").strip()
        payload = cls._decode_stream_payload(fields.get("payload"))
        attempt = _parse_int(fields.get("attempt"), 0) or 0
        if not ci or webhook_action not in ExternalChatCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            logger.warning("External chat stream entry skipped with invalid payload: entry_id=%s", entry_id)
            await cls._ack_stream_entry(stream_key, entry_id)
            return

        try:
            await cls._process_queued_webhook(ci, webhook_action, payload)
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.debug(
                "External chat webhook processed: ci=%s action=%s entry_id=%s event_id=%s",
                ci,
                webhook_action,
                entry_id,
                event_id,
            )
        except ConnectedIntegrationInactiveError as error:
            await cls._ack_stream_entry(stream_key, entry_id)
            await cls._redis_delete(cls._webhook_enqueue_dedupe_key(ci, event_key))
            logger.info(
                "External chat webhook skipped for inactive integration: ci=%s entry_id=%s reason=%s",
                ci,
                entry_id,
                error,
            )
        except Exception as error:
            next_attempt = attempt + 1
            if next_attempt >= ExternalChatCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(_now_ts())
                dlq_payload["error"] = str(error)
                await cls._enqueue_stream(cls._dlq_stream_key(), dlq_payload)
                await cls._redis_delete(cls._webhook_enqueue_dedupe_key(ci, event_key))
                await cls._ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "External chat webhook moved to DLQ: ci=%s action=%s entry_id=%s error=%s",
                    ci,
                    webhook_action,
                    entry_id,
                    error,
                )
                return
            retry_payload = dict(fields)
            retry_payload["attempt"] = str(next_attempt)
            retry_payload["last_error"] = str(error)
            await cls._enqueue_stream(stream_key, retry_payload)
            await cls._ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "External chat webhook requeued: ci=%s action=%s entry_id=%s attempt=%s error=%s",
                ci,
                webhook_action,
                entry_id,
                next_attempt,
                error,
            )

    @classmethod
    async def _process_queued_webhook(
        cls,
        connected_integration_id: str,
        webhook_action: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        await cls._ensure_connected_integration_active(connected_integration_id)
        lock_key = cls._webhook_processing_lock_key(
            connected_integration_id,
            webhook_action,
            payload,
        )
        lock_token = await cls._acquire_lock_wait(
            lock_key,
            ExternalChatCrmChannelConfig.PROCESSING_LOCK_TTL_SEC,
            wait_seconds=2.0,
        )
        if not lock_token:
            raise RuntimeError("webhook processing lock busy")
        try:
            if webhook_action in {
                "ChatMessageAdded",
                "ChatMessageEdited",
                "ChatMessageDeleted",
                "ChatMessageRead",
            }:
                return await cls._apply_chat_message_webhook(
                    connected_integration_id,
                    webhook_action,
                    payload,
                )
            return await cls._apply_ticket_webhook(
                connected_integration_id,
                webhook_action,
                payload,
            )
        finally:
            await cls._release_lock(lock_key, lock_token)

    async def connect(self, **_: Any) -> Any:
        _require_redis()
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        try:
            await self._ensure_connected_integration_active(ci, force_refresh=True)
        except ConnectedIntegrationInactiveError:
            return self._error_response(1001, f"ConnectedIntegration '{ci}' is inactive").dict()
        try:
            runtime = await self._load_runtime(ci)
        except Exception as error:
            return self._error_response(1002, str(error)).dict()
        await self._ensure_stream_workers()
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
        _require_redis()
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        await self._clear_settings_runtime_cache(ci)
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Any:
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Any:
        _require_redis()
        _ = settings
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id).strip()
        await self._clear_settings_runtime_cache(ci)
        return {"status": "settings updated"}

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

        message_id = str(payload.get("id") or "").strip()
        notification_count: Optional[int] = None
        if webhook_action == "ChatMessageAdded":
            context = await cls._load_cached_context_by_chat(connected_integration_id, chat_id)
            if context:
                message: Optional[Any]
                if any(
                    key in payload
                    for key in ("author_entity_type", "message_type", "author_entity_id")
                ):
                    message = payload
                else:
                    message = await cls._load_chat_message_by_id(
                        connected_integration_id,
                        chat_id,
                        message_id,
                    )
                if message and cls._should_increment_notification_for_message(message):
                    notification_count = await cls._increment_notification_count(
                        connected_integration_id,
                        context,
                    )

        revision = await cls._bump_chat_revision(connected_integration_id, chat_id)
        await cls._publish_chat_event(
            connected_integration_id,
            chat_id=chat_id,
            event_type="chat_message_changed",
            source_action=webhook_action,
            chat_revision=int(revision or 0),
            force_full=False,
            payload={
                "message_id": message_id or None,
                "notification_count": notification_count,
            },
        )
        result: Dict[str, Any] = {
            "status": "processed",
            "chat_id": chat_id,
            "chat_revision": revision,
        }
        if notification_count is not None:
            result["notification_count"] = notification_count
        return result

    @classmethod
    async def _apply_ticket_webhook(
        cls,
        connected_integration_id: str,
        webhook_action: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        ticket_id = _parse_int(
            payload.get("ticket_id")
            if payload.get("ticket_id") is not None
            else payload.get("id"),
            None,
        )
        if not ticket_id:
            return {"status": "ignored", "reason": "invalid_payload:ticket_id"}

        runtime = await cls._load_runtime(connected_integration_id)
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                ticket = await cls._load_ticket_by_id(api, int(ticket_id))
        except Exception:
            ticket = None
        if not cls._is_own_ticket(ticket, runtime):
            return {
                "status": "ignored",
                "reason": "ticket_not_external_chat",
                "ticket_id": int(ticket_id),
            }

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

        if not status_value or not chat_id:
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
        _require_redis()
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
        queued = await self._enqueue_webhook_event(
            ci,
            webhook_action,
            payload,
            event_id,
            event_key,
        )
        if not queued:
            return {
                "status": "ignored",
                "reason": "duplicate_event",
                "action": webhook_action,
                "event_id": event_id,
            }
        return {
            "status": "accepted",
            "action": webhook_action,
            "event_id": event_id,
            "queued": True,
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

        query = envelope.get("query") or {}
        version_param = ExternalChatCrmChannelConfig.UI_ASSET_VERSION_PARAM
        current_version = str(query.get(version_param) or "").strip()
        if current_version != ExternalChatCrmChannelConfig.UI_ASSET_VERSION:
            return RedirectResponse(
                url=_relative_query_with_ui_asset_version(query),
                status_code=302,
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
        if action == "events":
            action = "getupdates"
        data = body.get("data")
        data = data if isinstance(data, dict) else {}

        visitor_id = self._normalize_visitor_id(data.get("visitor_id"))
        generated_visitor_id = False
        if action == "init" and not visitor_id:
            visitor_id = self._normalize_visitor_id(uuid.uuid4().hex)
            generated_visitor_id = True
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

        if action not in ExternalChatCrmChannelConfig.SUPPORTED_EXTERNAL_ACTIONS:
            return JSONResponse(
                status_code=400,
                content={"error": 400, "description": f"Unsupported action '{action}'"},
            )

        if action in ExternalChatCrmChannelConfig.PENDING_PARAM_CAPTURE_ACTIONS:
            await self._save_pending_params(
                ci,
                visitor_id,
                data,
                clear_empty=not generated_visitor_id,
            )

        context: Optional[ChatContext] = None
        if action in ExternalChatCrmChannelConfig.EXISTING_CONTEXT_ACTIONS:
            context = await self._load_cached_context(ci, visitor_id)

        try:
            if action == "init":
                if not context:
                    return self._compose_no_context_response(
                        visitor_id,
                        runtime,
                        include_settings=True,
                        include_history=True,
                    )
                ticket_view = await self._compose_context_ticket_view_fresh(
                    ci,
                    runtime,
                    context,
                )
                chat_state, history = await asyncio.gather(
                    self._get_chat_state_view(ci, context, include_notifications=True),
                    self._read_history(
                        ci,
                        context,
                        ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT,
                    ),
                )
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "chat_title": runtime.chat_title,
                    "required_profile_fields": {
                        "display_name": runtime.require_display_name,
                        "phone": runtime.require_phone,
                        "email": runtime.require_email,
                    },
                    **chat_state,
                    "history_changed": True,
                    **ticket_view,
                    "history": history,
                })

            if action == "history":
                if not context:
                    return self._compose_no_context_response(
                        visitor_id,
                        runtime,
                        include_history=True,
                    )
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
                    chat_state = self._compose_chat_state_view(
                        chat_revision,
                        await self._get_notification_count(ci, context),
                    )
                    return await self._with_visitor_revision(ci, visitor_id, context, {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        **chat_state,
                        "history_changed": False,
                        **ticket_view,
                    })
                history, notification_count = await asyncio.gather(
                    self._read_history(
                        ci,
                        context,
                        int(limit or ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT),
                    ),
                    self._get_notification_count(ci, context),
                )
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    **self._compose_chat_state_view(chat_revision, notification_count),
                    "history_changed": True,
                    **ticket_view,
                    "history": history,
                })

            if action == "getupdates":
                if not context:
                    return self._compose_no_context_response(
                        visitor_id,
                        runtime,
                        include_events=True,
                    )
                max_events = _parse_int(
                    data.get("max_events"),
                    ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS,
                )
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                known_revision = _parse_int(data.get("known_revision"), None)
                if known_revision is None:
                    known_revision = await self._get_visitor_known_revision(
                        ci,
                        visitor_id,
                        str(context.chat_id),
                    )
                    if known_revision is None:
                        known_revision = 0
                if (
                    known_revision is not None
                    and int(chat_revision) > 0
                    and int(known_revision) != int(chat_revision)
                ):
                    ticket_view, notification_count = await asyncio.gather(
                        self._compose_context_ticket_view(
                            ci,
                            runtime,
                            context,
                        ),
                        self._get_notification_count(ci, context),
                    )
                    return await self._with_visitor_revision(ci, visitor_id, context, {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        **self._compose_chat_state_view(chat_revision, notification_count),
                        "events": [self._build_revision_sync_event(
                            chat_id=str(context.chat_id),
                            ticket_id=int(context.ticket_id),
                            chat_revision=int(chat_revision),
                            source_action="revision_sync",
                        )],
                        **ticket_view,
                    })

                events = await self._poll_chat_events(
                    ci,
                    chat_id=str(context.chat_id),
                    max_items=int(max_events or ExternalChatCrmChannelConfig.EVENT_BATCH_MAX_ITEMS),
                )
                if events:
                    chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                elif (
                    known_revision is not None
                    and int(chat_revision) > 0
                    and int(known_revision) == int(chat_revision)
                ):
                    latest_chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                    chat_revision = int(latest_chat_revision or 0)
                    if int(chat_revision) > 0 and int(known_revision) != int(chat_revision):
                        ticket_view, notification_count = await asyncio.gather(
                            self._compose_context_ticket_view(
                                ci,
                                runtime,
                                context,
                            ),
                            self._get_notification_count(ci, context),
                        )
                        return await self._with_visitor_revision(ci, visitor_id, context, {
                            "status": "ok",
                            "visitor_id": visitor_id,
                            **self._compose_chat_state_view(chat_revision, notification_count),
                            "events": [self._build_revision_sync_event(
                                chat_id=str(context.chat_id),
                                ticket_id=int(context.ticket_id),
                                chat_revision=int(chat_revision),
                                source_action="revision_sync_after_poll",
                            )],
                            **ticket_view,
                        })
                if not events:
                    return await self._with_visitor_revision(ci, visitor_id, context, {
                        "status": "ok",
                        "visitor_id": visitor_id,
                        **self._compose_chat_state_view(chat_revision),
                        "events": [],
                    })
                ticket_view, notification_count = await asyncio.gather(
                    self._compose_context_ticket_view(
                        ci,
                        runtime,
                        context,
                    ),
                    self._get_notification_count(ci, context),
                )
                response_payload = {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "events": events,
                    **self._compose_chat_state_view(chat_revision, notification_count),
                    **ticket_view,
                }
                return await self._with_visitor_revision(ci, visitor_id, context, response_payload)

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
                write_params, params_error = await self._prepare_write_params(ci, runtime, visitor_id, data)
                if params_error:
                    return params_error
                assert write_params is not None
                context = await self._ensure_chat_context(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=write_params.profile,
                    client_field_adds=write_params.client_field_adds,
                    client_field_edits=write_params.client_field_edits,
                    sync_client_info=write_params.sync_client_info,
                    sync_ticket_fields=write_params.sync_ticket_fields,
                    ticket_field_adds=write_params.ticket_field_adds,
                    ticket_field_edits=write_params.ticket_field_edits,
                    allow_create_ticket=True,
                    create_source="send_message",
                    require_writable=True,
                )
                ext_id = f"webchat:msg:{visitor_id}:{uuid.uuid4().hex[:12]}"
                context, message_id = await self._send_visitor_message_with_reopen(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=write_params.profile,
                    context=context,
                    text=text,
                    external_message_id=ext_id,
                    client_field_adds=write_params.client_field_adds,
                    client_field_edits=write_params.client_field_edits,
                    sync_client_info=write_params.sync_client_info,
                    sync_ticket_fields=write_params.sync_ticket_fields,
                    ticket_field_adds=write_params.ticket_field_adds,
                    ticket_field_edits=write_params.ticket_field_edits,
                )
                await self._delete_pending_params(ci, visitor_id)
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                ticket_view = await self._compose_context_ticket_view(ci, runtime, context)
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "message_id": message_id,
                    **self._compose_chat_state_view(chat_revision, 0),
                    **ticket_view,
                })

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
                write_params, params_error = await self._prepare_write_params(ci, runtime, visitor_id, data)
                if params_error:
                    return params_error
                assert write_params is not None
                context = await self._ensure_chat_context(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=write_params.profile,
                    client_field_adds=write_params.client_field_adds,
                    client_field_edits=write_params.client_field_edits,
                    sync_client_info=write_params.sync_client_info,
                    sync_ticket_fields=write_params.sync_ticket_fields,
                    ticket_field_adds=write_params.ticket_field_adds,
                    ticket_field_edits=write_params.ticket_field_edits,
                    allow_create_ticket=True,
                    create_source="send_file",
                    require_writable=True,
                )
                ext_id = f"webchat:file:{visitor_id}:{uuid.uuid4().hex[:12]}"
                context, message_id, file_id = await self._send_visitor_file_with_reopen(
                    connected_integration_id=ci,
                    runtime=runtime,
                    visitor_id=visitor_id,
                    profile=write_params.profile,
                    context=context,
                    text=text,
                    file_name=file_name,
                    extension=extension,
                    payload_b64=payload_b64,
                    external_message_id=ext_id,
                    client_field_adds=write_params.client_field_adds,
                    client_field_edits=write_params.client_field_edits,
                    sync_client_info=write_params.sync_client_info,
                    sync_ticket_fields=write_params.sync_ticket_fields,
                    ticket_field_adds=write_params.ticket_field_adds,
                    ticket_field_edits=write_params.ticket_field_edits,
                )
                await self._delete_pending_params(ci, visitor_id)
                await self._mark_read(ci, context)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                ticket_view = await self._compose_context_ticket_view(ci, runtime, context)
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "message_id": message_id,
                    "file_id": int(file_id),
                    "file_name": file_name,
                    "file_size": int(file_size),
                    **self._compose_chat_state_view(chat_revision, 0),
                    **ticket_view,
                })

            if action == "set_rating":
                if not context:
                    empty_view = self._compose_no_context_response(visitor_id, runtime)
                    empty_view.pop("status", None)
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": 409,
                            "description": "Ticket is not started",
                            **empty_view,
                        },
                    )
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
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "rating_saved": True,
                    "already_rated": False,
                    "chat_revision": chat_revision,
                    **saved_view,
                })

            if action == "notification_count":
                if not context:
                    return self._compose_no_context_response(visitor_id, runtime)
                chat_state = await self._get_chat_state_view(ci, context, include_notifications=True)
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    **chat_state,
                }

            if action == "mark_read":
                if not context:
                    return self._compose_no_context_response(visitor_id, runtime)
                await self._mark_read(ci, context)
                ticket_state = await self._get_ticket_write_state(ci, int(context.ticket_id))
                ticket_view = self._compose_ticket_view_state(runtime, ticket_state)
                chat_revision = await self._get_chat_revision(ci, str(context.chat_id))
                return await self._with_visitor_revision(ci, visitor_id, context, {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    **self._compose_chat_state_view(chat_revision, 0),
                    **ticket_view,
                })
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
