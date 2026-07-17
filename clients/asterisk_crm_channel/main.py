from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import socket
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from starlette.responses import JSONResponse

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_ops,
    redis_error_contains,
    redis_expire_if_due,
    redis_sadd_with_ttl,
    redis_stream_add_with_ttl,
    redis_stream_ack_delete,
    redis_stream_group_create_with_ttl,
    redis_ttl_seconds,
)
from schemas.api.chat.chat_message import (
    ChatMessageAddRequest,
    ChatMessageTypeEnum,
)
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.client import ClientAddRequest, ClientGetRequest
from schemas.api.crm.ticket import (
    TicketAddRequest,
    TicketCloseRequest,
    TicketDirectionEnum,
    TicketGetRequest,
    TicketSetResponsibleRequest,
    TicketSetStatusRequest,
    TicketStatusEnum,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.rbac.user import UserGetRequest
from schemas.api.rbac.work_attendance import WorkAttendanceStatusRequest
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("asterisk_crm_channel")


class AsteriskCrmChannelConfig:
    INTEGRATION_KEY = "asterisk_crm_channel"
    REDIS_PREFIX = "acc:"
    STREAM_REDIS_PREFIX = "acc"
    DEFAULT_AMI_PORT = 5038

    SETTINGS_TTL = max(int(app_settings.redis_cache_ttl or 60), 60)
    SETTINGS_STALE_TTL = max(SETTINGS_TTL * 10, 10 * 60)
    SETTINGS_LOCAL_TTL = min(30, max(5, SETTINGS_TTL // 4))
    SETTINGS_LOCAL_MAX = 10000
    SETTINGS_LOCK_TTL_SEC = 10
    SETTINGS_LOCK_WAIT_SEC = 2.0
    RUNTIME_LOCAL_TTL = min(30, max(5, SETTINGS_TTL // 4))
    CI_ACTIVE_MEMORY_TTL_SEC = 5
    DEFAULT_DEDUPE_TTL_SEC = 60 * 60
    DEFAULT_STATE_TTL_SEC = 6 * 60 * 60
    STREAM_TTL_SEC = 24 * 60 * 60
    ACTIVE_CI_IDS_TTL_SEC = 30 * 24 * 60 * 60
    # Short on purpose: only collapses repeated User/Get within one call's events. A longer
    # negative cache would keep a freshly-configured operator unresolved (and unassigned).
    OPERATOR_NOT_FOUND_CACHE_TTL_SEC = 60
    STORE_DECISION_TRACE = bool(getattr(app_settings, "debug", False))

    STREAM_GROUP = "accw"
    STREAM_MAXLEN = max(int(app_settings.asterisk_crm_channel_stream_maxlen or 0), 10000)
    STREAM_BATCH_SIZE = max(int(app_settings.asterisk_crm_channel_stream_batch_size or 0), 1)
    STREAM_WORKERS = max(int(app_settings.asterisk_crm_channel_stream_workers or 0), 1)
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30
    STREAM_MAX_RETRIES = max(int(app_settings.asterisk_crm_channel_stream_retry_limit or 0), 1)
    EVENT_CONCURRENCY = max(int(app_settings.asterisk_crm_channel_event_concurrency or 0), 1)

    LOCK_TTL_SEC = 30
    PROCESSING_LOCK_TTL_SEC = 120
    # Wait for the in-flight same-call event to finish before processing the next stage.
    # Must comfortably exceed one create/assign/close CRM round-trip held under the lock;
    # on timeout the event is soft-retried (re-enqueued) without counting toward the DLQ.
    CALL_LOCK_WAIT_SEC = 6.0
    HEARTBEAT_TTL_SEC = 30
    AMI_CONNECT_TIMEOUT_SEC = 30
    AMI_PING_INTERVAL_SEC = 20
    AMI_RECONNECT_MIN_SEC = 1
    AMI_RECONNECT_MAX_SEC = 30
    AMI_OWNER_LOCK_TTL_SEC = 30
    AMI_OWNER_LOCK_REFRESH_SEC = 10
    AMI_OWNER_WAIT_SEC = 2

    CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR = 1220

    CALL_STATE_STATUSES = {
        "started",
        "ringing",
        "answered",
        "missed",
        "completed",
        "failed",
    }
    EVENT_STATUSES = CALL_STATE_STATUSES | {"recording_ready"}
    CLOSE_ON_CALL_END_STATUSES = {"completed"}
    CLIENT_PHONE_OPTIONAL_STATUSES = {"answered", "recording_ready"}


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    asterisk_hash: str
    ami_host: str
    ami_port: int
    ami_user: str
    ami_password: str
    channel_id: int
    default_responsible_user_id: Optional[int]
    subject_template: str
    allowed_did_set: set[str]
    recording_base_url: Optional[str]
    state_ttl_sec: int
    default_country_code: str
    assign_responsible_by_operator_ext: bool
    message_language: str
    close_ticket_on_call_end: bool
    min_external_digits: int
    create_ticket_on_call_start: bool
    assign_responsible_requires_attendance: bool
    post_status_messages: bool
    log_ami_events: bool


@dataclass
class CallEvent:
    event_id: str
    external_call_id: str
    asterisk_hash: str
    direction: str
    from_phone: str
    to_phone: str
    client_phone: str
    status: str
    event_ts: int
    talk_duration_sec: Optional[int]
    recording_url: Optional[str]
    operator_ext: Optional[str]
    raw_payload: Dict[str, Any]


@dataclass
class LeadContext:
    ticket_id: int
    chat_id: str
    client_id: Optional[int] = None

    @property
    def lead_id(self) -> int:
        # Keep backward-compatible attribute name for legacy logs/telemetry payloads.
        return int(self.ticket_id)


class ChatMessageAddClosedEntityError(RuntimeError):
    def __init__(self, description: Optional[str] = None) -> None:
        self.description = str(description or "").strip() or None
        text = "ChatMessage/Add rejected for closed linked entity"
        if self.description:
            text = f"{text}: {self.description}"
        super().__init__(text)


class ConnectedIntegrationInactiveError(RuntimeError):
    pass


class NonRetryableCallEventError(RuntimeError):
    pass


class CallLockBusyError(RuntimeError):
    """Per-call lock is held by another in-flight event. Soft-retried (no DLQ count)."""

    pass


_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[int, asyncio.Task] = {}
_AMI_TASKS: Dict[str, asyncio.Task] = {}
_INSTANCE_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
_CI_ACTIVE_MEMORY_CACHE: Dict[str, Tuple[bool, int]] = {}
_CI_ACTIVE_LOCKS: Dict[str, asyncio.Lock] = {}
_REDIS_TTL_TOUCH_TS: Dict[str, int] = {}
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


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_ops)


def _require_redis() -> None:
    if not _redis_enabled():
        raise RuntimeError("Redis is required for asterisk_crm_channel")


def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return bool(default)
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _normalize_unix_ts_seconds(value: int) -> int:
    ts = int(value)
    abs_ts = abs(ts)
    # 13 digits+ are almost always ms/us/ns in modern telephony events.
    if abs_ts >= 10**18:  # ns
        return int(ts / 1_000_000_000)
    if abs_ts >= 10**15:  # us
        return int(ts / 1_000_000)
    if abs_ts >= 10**11:  # ms
        return int(ts / 1_000)
    return ts


def _normalize_phone(value: Any) -> Optional[str]:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    # Some AMI fields may contain duplicated number tokens concatenated together.
    if len(digits) >= 10:
        for parts in (2, 3, 4):
            if len(digits) % parts != 0:
                continue
            chunk_len = len(digits) // parts
            if chunk_len < 5:
                continue
            chunk = digits[:chunk_len]
            if chunk and chunk * parts == digits:
                digits = chunk
                break
    return digits or None


def _normalize_country_code(value: Any, default: str = "998") -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits or default


def _normalize_message_language(value: Any, default: str = "ru") -> str:
    text = str(value or "").strip().lower()
    if not text:
        return default
    aliases = {
        "ru": "ru",
        "rus": "ru",
        "russian": "ru",
        "рус": "ru",
        "русский": "ru",
        "uz": "uz",
        "uzb": "uz",
        "uzbek": "uz",
        "uzbekcha": "uz",
        "o'zbek": "uz",
        "ozbek": "uz",
        "уз": "uz",
        "узбек": "uz",
        "en": "en",
        "eng": "en",
        "english": "en",
        "анг": "en",
        "английский": "en",
    }
    return aliases.get(text, default)


def _is_internal_extension(value: Optional[str]) -> bool:
    digits = _normalize_phone(value)
    return bool(digits and 2 <= len(digits) <= 6)


def _to_international_phone(value: Any, country_code: str) -> Optional[str]:
    digits = _normalize_phone(value)
    if not digits:
        return None
    if _is_internal_extension(digits):
        return digits

    cc = _normalize_country_code(country_code)
    if digits.startswith("00") and len(digits) > 2:
        digits = digits[2:]
    # Normalize common local formats first, even if the local number
    # accidentally starts with country-code digits (e.g. 998668988).
    if len(digits) == 10 and digits.startswith("0"):
        return f"{cc}{digits[1:]}"
    if len(digits) == 9:
        return f"{cc}{digits}"
    if digits.startswith(cc):
        return digits
    return digits


def _extract_internal_extension_candidate(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    for chunk in re.split(r"[,\s]+", text):
        token = str(chunk or "").strip()
        if not token:
            continue
        match = re.search(r"/(\d{2,6})(?:[@;:/\-]|$)", token)
        if not match:
            match = re.search(r"^(\d{2,6})(?:[@;:/\-]|$)", token)
        if not match:
            continue
        candidate = _normalize_phone(match.group(1))
        if candidate and _is_internal_extension(candidate):
            return candidate
    return None


def _hash_scope_key(value: str) -> str:
    return hashlib.md5(str(value or "").encode("utf-8")).hexdigest()


def _external_id(connected_integration_id: str, normalized_phone: str) -> str:
    return f"ci:{connected_integration_id}:asterisk:{normalized_phone}"


def _phone_filter_candidates(
    normalized_phone: str,
    country_code: str,
) -> List[str]:
    phone = _normalize_phone(normalized_phone)
    if not phone:
        return []

    cc = _normalize_country_code(country_code)
    candidates: List[str] = [phone]

    if cc and phone.startswith(cc):
        local = phone[len(cc) :]
        if local:
            candidates.append(local)
    elif cc and len(phone) == 9:
        candidates.append(f"{cc}{phone}")

    # Preserve order and remove duplicates.
    unique: List[str] = []
    seen = set()
    for item in candidates:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _translate_direction(direction: str, language: str) -> str:
    normalized_language = _normalize_message_language(language, "ru")
    normalized_direction = str(direction or "").strip().lower()
    translations: Dict[str, Dict[str, str]] = {
        "ru": {
            "inbound": "входящий",
            "outbound": "исходящий",
            "unknown": "звонок",
        },
        "uz": {
            "inbound": "kiruvchi",
            "outbound": "chiquvchi",
            "unknown": "qo'ng'iroq",
        },
        "en": {
            "inbound": "inbound",
            "outbound": "outbound",
            "unknown": "call",
        },
    }
    language_map = translations.get(normalized_language, translations["ru"])
    if not normalized_direction:
        return language_map.get("unknown", "call")
    return language_map.get(normalized_direction, normalized_direction)


def _safe_subject(template: str, event: CallEvent, language: str = "ru") -> str:
    subject_template = str(template or "").strip() or "Call {direction} {client_phone}"
    translated_direction = _translate_direction(event.direction, language)
    try:
        return subject_template.format(
            direction=translated_direction,
            direction_raw=event.direction,
            from_phone=event.from_phone or "",
            to_phone=event.to_phone or "",
            client_phone=event.client_phone or "",
            external_call_id=event.external_call_id or "",
            status=event.status or "",
        ).strip() or subject_template
    except Exception:
        return subject_template


def _parse_event_ts(value: Any) -> int:
    if value is None:
        return _now_ts()
    if isinstance(value, (int, float)):
        return _normalize_unix_ts_seconds(int(value))
    text = str(value).strip()
    if not text:
        return _now_ts()
    direct = _to_int(text, None)
    if direct is not None:
        return _normalize_unix_ts_seconds(int(direct))
    try:
        return _normalize_unix_ts_seconds(int(float(text)))
    except (TypeError, ValueError):
        pass
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return _normalize_unix_ts_seconds(int(parsed.timestamp()))
    except Exception:
        return _now_ts()


def _format_duration_hms(total_seconds: int) -> str:
    seconds = max(int(total_seconds), 0)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    tail_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{tail_seconds:02d}"


def _resolve_recording_url(base_url: Optional[str], raw_url: Optional[str]) -> Optional[str]:
    url = str(raw_url or "").strip().replace("\\", "/")
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url

    path = url
    lower_path = path.lower()
    for prefix in (
        "/var/spool/asterisk/monitor/",
        "var/spool/asterisk/monitor/",
    ):
        prefix_index = lower_path.find(prefix)
        if prefix_index >= 0:
            path = path[prefix_index + len(prefix):]
            break

    path = path.lstrip("/")
    if "/" not in path:
        freepbx_date = re.search(
            r"(?:^|[-_])(?P<year>20\d{2})(?P<month>0[1-9]|1[0-2])(?P<day>0[1-9]|[12]\d|3[01])(?:[-_])",
            path,
        )
        if freepbx_date:
            path = (
                f"{freepbx_date.group('year')}/"
                f"{freepbx_date.group('month')}/"
                f"{freepbx_date.group('day')}/"
                f"{path}"
            )

    base = str(base_url or "").strip()
    if not base:
        return path or url
    return urljoin(base.rstrip("/") + "/", path)


def _parse_ami_host_port(raw_host: Any, raw_port: Any) -> Tuple[str, int]:
    host_raw = str(raw_host or "").strip()
    if not host_raw:
        raise ValueError("asterisk_ami_host is required")
    parsed = urlparse(host_raw if "://" in host_raw else f"tcp://{host_raw}")
    host = str(parsed.hostname or "").strip()
    if not host:
        raise ValueError("asterisk_ami_host is invalid")
    port = _to_int(raw_port, parsed.port or AsteriskCrmChannelConfig.DEFAULT_AMI_PORT)
    if not port or port <= 0 or port > 65535:
        raise ValueError("asterisk_ami_port must be in range 1..65535")
    return host, int(port)


class AsteriskCrmChannelIntegration(ClientBase):
    MESSAGE_TEXTS: Dict[str, Dict[str, str]] = {
        "ru": {
            "inbound_started": "**Телефония | Входящий звонок**\nКлиент: {client_phone}",
            "inbound_missed": "**Телефония | Пропущенный звонок**",
            "inbound_answered_with_operator": "**Телефония | Звонок принят**\nОператор: {operator_name}",
            "inbound_answered": "**Телефония | Звонок принят**",
            "inbound_completed_with_duration": "**Телефония | Звонок завершен**\nДлительность: {talk_duration}",
            "inbound_completed": "**Телефония | Звонок завершен**",
            "outbound_started": "**Телефония | Исходящий звонок**\nКлиент: {client_phone}",
            "outbound_failed": "**Телефония | Исходящий звонок не состоялся**",
            "outbound_answered": "**Телефония | Клиент ответил**",
            "outbound_completed_with_duration": "**Телефония | Исходящий звонок завершен**\nДлительность: {talk_duration}",
            "outbound_completed": "**Телефония | Исходящий звонок завершен**",
            "generic_event": "**Телефония | Событие звонка**",
            "recording_ready_title": "**Телефония | Запись разговора готова**",
            "call_id_label": "ID звонка: {external_call_id}",
            "recording_link": "Ссылка на запись: {recording_url}",
            "recording_url_missing": "Ссылка на запись: не передана",
        },
        "uz": {
            "inbound_started": "**Aloqa | Kiruvchi qo'ng'iroq**\nMijoz: {client_phone}",
            "inbound_missed": "**Aloqa | O'tkazib yuborilgan qo'ng'iroq**",
            "inbound_answered_with_operator": "**Aloqa | Qo'ng'iroq qabul qilindi**\nOperator: {operator_name}",
            "inbound_answered": "**Aloqa | Qo'ng'iroq qabul qilindi**",
            "inbound_completed_with_duration": "**Aloqa | Qo'ng'iroq yakunlandi**\nDavomiyligi: {talk_duration}",
            "inbound_completed": "**Aloqa | Qo'ng'iroq yakunlandi**",
            "outbound_started": "**Aloqa | Chiquvchi qo'ng'iroq**\nMijoz: {client_phone}",
            "outbound_failed": "**Aloqa | Chiquvchi qo'ng'iroq amalga oshmadi**",
            "outbound_answered": "**Aloqa | Mijoz javob berdi**",
            "outbound_completed_with_duration": "**Aloqa | Chiquvchi qo'ng'iroq yakunlandi**\nDavomiyligi: {talk_duration}",
            "outbound_completed": "**Aloqa | Chiquvchi qo'ng'iroq yakunlandi**",
            "generic_event": "**Aloqa | Qo'ng'iroq hodisasi**",
            "recording_ready_title": "**Aloqa | Qo'ng'iroq yozuvi tayyor**",
            "call_id_label": "Qo'ng'iroq ID: {external_call_id}",
            "recording_link": "Yozuv havolasi: {recording_url}",
            "recording_url_missing": "Yozuv havolasi: yuborilmadi",
        },
        "en": {
            "inbound_started": "**Telephony | Inbound call**\nCustomer: {client_phone}",
            "inbound_missed": "**Telephony | Missed call**",
            "inbound_answered_with_operator": "**Telephony | Call answered**\nOperator: {operator_name}",
            "inbound_answered": "**Telephony | Call answered**",
            "inbound_completed_with_duration": "**Telephony | Call completed**\nDuration: {talk_duration}",
            "inbound_completed": "**Telephony | Call completed**",
            "outbound_started": "**Telephony | Outbound call**\nCustomer: {client_phone}",
            "outbound_failed": "**Telephony | Outbound call failed**",
            "outbound_answered": "**Telephony | Customer answered**",
            "outbound_completed_with_duration": "**Telephony | Outbound call completed**\nDuration: {talk_duration}",
            "outbound_completed": "**Telephony | Outbound call completed**",
            "generic_event": "**Telephony | Call event**",
            "recording_ready_title": "**Telephony | Call recording ready**",
            "call_id_label": "Call ID: {external_call_id}",
            "recording_link": "Recording link: {recording_url}",
            "recording_url_missing": "Recording link: not provided",
        },
    }

    def __init__(self):
        super().__init__()

    @classmethod
    def _text(cls, language: str, key: str, **kwargs: Any) -> str:
        lang = _normalize_message_language(language, "ru")
        text = (
            cls.MESSAGE_TEXTS.get(lang, {}).get(key)
            or cls.MESSAGE_TEXTS["ru"].get(key)
            or key
        )
        try:
            return text.format(**kwargs)
        except Exception:
            return text

    @staticmethod
    def _redis_key(*parts: Any) -> str:
        normalized_parts: List[str] = []
        for part in parts:
            if part is None:
                continue
            text = str(part).strip()
            if not text:
                continue
            normalized_parts.append(text.strip(":"))
        prefix = AsteriskCrmChannelConfig.REDIS_PREFIX.rstrip(":")
        return f"{prefix}:{':'.join(normalized_parts)}" if normalized_parts else f"{prefix}:"

    @staticmethod
    def _stream_redis_key(*parts: Any) -> str:
        normalized_parts: List[str] = []
        for part in parts:
            if part is None:
                continue
            text = str(part).strip()
            if text:
                normalized_parts.append(text.strip(":"))
        if not normalized_parts:
            return AsteriskCrmChannelConfig.STREAM_REDIS_PREFIX
        return f"{AsteriskCrmChannelConfig.STREAM_REDIS_PREFIX}:{':'.join(normalized_parts)}"

    @staticmethod
    def _settings_cache_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key("settings", connected_integration_id)

    @staticmethod
    def _settings_stale_cache_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "settings_stale",
            connected_integration_id,
        )

    @staticmethod
    def _settings_fetch_lock_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._stream_redis_key(
            "stl",
            connected_integration_id,
        )

    @staticmethod
    def _ci_active_cache_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key("ci_active", connected_integration_id)

    @staticmethod
    def _ci_active_lock(connected_integration_id: str) -> asyncio.Lock:
        ci = str(connected_integration_id or "").strip()
        lock = _CI_ACTIVE_LOCKS.get(ci)
        if lock is None:
            lock = asyncio.Lock()
            _CI_ACTIVE_LOCKS[ci] = lock
        return lock

    @staticmethod
    def _ci_active_memory_cache_get(connected_integration_id: str) -> Optional[bool]:
        ci = str(connected_integration_id or "").strip()
        cached = _CI_ACTIVE_MEMORY_CACHE.get(ci)
        if not cached:
            return None
        value, expires_at = cached
        if int(expires_at) <= _now_ts():
            _CI_ACTIVE_MEMORY_CACHE.pop(ci, None)
            return None
        return bool(value)

    @staticmethod
    def _ci_active_memory_cache_set(connected_integration_id: str, is_active: bool) -> None:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        ttl = max(
            1,
            min(
                AsteriskCrmChannelConfig.CI_ACTIVE_MEMORY_TTL_SEC,
                AsteriskCrmChannelConfig.SETTINGS_TTL,
            ),
        )
        _CI_ACTIVE_MEMORY_CACHE[ci] = (bool(is_active), _now_ts() + ttl)

    @staticmethod
    def _active_ci_ids_key() -> str:
        return AsteriskCrmChannelIntegration._redis_key("active_ci_ids")

    @staticmethod
    def _active_ci_ids_ttl() -> int:
        return redis_ttl_seconds(AsteriskCrmChannelConfig.ACTIVE_CI_IDS_TTL_SEC)

    @classmethod
    async def _touch_active_ci_ids_ttl(cls, *, force: bool = False) -> None:
        _require_redis()
        await redis_expire_if_due(
            cls._active_ci_ids_key(),
            cls._active_ci_ids_ttl(),
            _REDIS_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=60,
            force=force,
        )

    @staticmethod
    def _stream_key(connected_integration_id: Optional[str] = None) -> str:
        return AsteriskCrmChannelIntegration._stream_redis_key("s", "e")

    @staticmethod
    def _dlq_stream_key(connected_integration_id: Optional[str] = None) -> str:
        return AsteriskCrmChannelIntegration._stream_redis_key("s", "dlq")

    @staticmethod
    def _worker_heartbeat_key(worker_index: int) -> str:
        return AsteriskCrmChannelIntegration._stream_redis_key(
            "w",
            worker_index,
            _INSTANCE_ID,
        )

    @staticmethod
    def _ami_owner_lock_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lock",
            "ami_owner",
            connected_integration_id,
        )

    @staticmethod
    def _connect_lock_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._stream_redis_key(
            "cl",
            connected_integration_id,
        )

    @staticmethod
    def _lock_create_ticket_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lock",
            "create_ticket",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _dedupe_event_key(connected_integration_id: str, event_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "dedupe",
            "event",
            connected_integration_id,
            event_id,
        )

    @staticmethod
    def _enqueue_dedupe_event_key(connected_integration_id: str, event_id: str) -> str:
        event_hash = hashlib.sha256(str(event_id or "").encode("utf-8")).hexdigest()[:20]
        return AsteriskCrmChannelIntegration._stream_redis_key(
            "d",
            connected_integration_id,
            event_hash,
        )

    @staticmethod
    def _mapping_by_call_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "mapping",
            "by_call",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _call_alias_key(
        connected_integration_id: str,
        asterisk_hash: str,
        raw_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "call_alias",
            connected_integration_id,
            asterisk_hash,
            raw_call_id,
        )

    @staticmethod
    def _lock_call_process_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lock",
            "call_process",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _late_closed_event_state_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "late_closed_event",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _call_progress_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "call_progress",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _recording_file_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "recording_file",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _operator_user_cache_key(
        connected_integration_id: str,
        asterisk_hash: str,
        operator_ext: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "operator_user",
            connected_integration_id,
            asterisk_hash,
            operator_ext,
        )

    @staticmethod
    def _operator_name_cache_key(
        connected_integration_id: str,
        asterisk_hash: str,
        operator_ext: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "operator_name",
            connected_integration_id,
            asterisk_hash,
            operator_ext,
        )

    @staticmethod
    def _call_responsible_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "call_responsible",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _call_responsible_name_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "call_responsible_name",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _call_close_pending_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        # Set when a call's terminal event arrives before a responsible was bound, so the
        # assign path can perform the parked close once it answers (order-independent).
        return AsteriskCrmChannelIntegration._redis_key(
            "call_close_pending",
            connected_integration_id,
            asterisk_hash,
            external_call_id,
        )

    @staticmethod
    def _user_name_cache_key(
        connected_integration_id: str,
        asterisk_hash: str,
        user_id: int,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "user_name",
            connected_integration_id,
            asterisk_hash,
            int(user_id),
        )

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        _require_redis()
        return await redis_ops.get(key)

    @staticmethod
    async def _redis_set_with_ttl(
        key: str,
        value: str,
        ttl_sec: int,
        *,
        min_ttl_sec: int,
    ) -> None:
        _require_redis()
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        await redis_ops.set(key, value, ex=ttl)

    @classmethod
    async def _redis_set_json_with_ttl(
        cls,
        key: str,
        payload: Dict[str, Any],
        ttl_sec: int,
        *,
        min_ttl_sec: int,
    ) -> None:
        await cls._redis_set_with_ttl(
            key=key,
            value=_json_dumps(payload),
            ttl_sec=ttl_sec,
            min_ttl_sec=min_ttl_sec,
        )

    @staticmethod
    async def _redis_set_nx_with_ttl(
        key: str,
        value: str,
        ttl_sec: int,
        *,
        min_ttl_sec: int,
    ) -> bool:
        _require_redis()
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        result = await redis_ops.set(key, value, ex=ttl, nx=True)
        return bool(result)

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        _require_redis()
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if not rows:
            return
        await redis_ops.delete(*rows)

    @classmethod
    async def _mark_ci_active(cls, connected_integration_id: str) -> None:
        _require_redis()
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        ttl = cls._active_ci_ids_ttl()
        await redis_sadd_with_ttl(cls._active_ci_ids_key(), ci, ttl)
        _REDIS_TTL_TOUCH_TS[cls._active_ci_ids_key()] = _now_ts()

    @classmethod
    async def _mark_ci_inactive(cls, connected_integration_id: str) -> None:
        _require_redis()
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        await redis_ops.srem(cls._active_ci_ids_key(), ci)
        _CI_ACTIVE_MEMORY_CACHE.pop(ci, None)
        async with _RUNTIME_LOCAL_LOCK:
            _RUNTIME_LOCAL_CACHE.pop(ci, None)

    @classmethod
    async def _acquire_lock(cls, lock_key: str, ttl_sec: int) -> Optional[str]:
        token = uuid.uuid4().hex
        ok = await cls._redis_set_nx_with_ttl(
            lock_key,
            token,
            ttl_sec,
            min_ttl_sec=AsteriskCrmChannelConfig.LOCK_TTL_SEC,
        )
        return token if ok else None

    @classmethod
    async def _acquire_lock_wait(
        cls,
        lock_key: str,
        ttl_sec: int,
        *,
        wait_seconds: float = 0.0,
    ) -> Optional[str]:
        token = uuid.uuid4().hex
        deadline = asyncio.get_running_loop().time() + max(float(wait_seconds or 0.0), 0.0)
        while True:
            ok = await cls._redis_set_nx_with_ttl(
                lock_key,
                token,
                ttl_sec,
                min_ttl_sec=AsteriskCrmChannelConfig.LOCK_TTL_SEC,
            )
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
        script = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""
        try:
            await redis_ops.eval(script, 1, lock_key, token)
        except Exception:
            current = await redis_ops.get(lock_key)
            if current == token:
                await redis_ops.delete(lock_key)

    @classmethod
    async def _refresh_lock(cls, lock_key: str, token: Optional[str], ttl_sec: int) -> bool:
        if not lock_key or not token:
            return False
        _require_redis()
        ttl = max(
            _to_int(ttl_sec, AsteriskCrmChannelConfig.LOCK_TTL_SEC)
            or AsteriskCrmChannelConfig.LOCK_TTL_SEC,
            AsteriskCrmChannelConfig.LOCK_TTL_SEC,
        )
        script = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return 0
"""
        try:
            result = await redis_ops.eval(script, 1, lock_key, token, str(ttl))
            return bool(int(result or 0))
        except Exception:
            try:
                current = await redis_ops.get(lock_key)
                if current != token:
                    return False
                return bool(await redis_ops.expire(lock_key, ttl))
            except Exception:
                return False

    @staticmethod
    def _parse_cached_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        try:
            parsed = _json_loads(raw)
        except Exception:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

    @classmethod
    async def _is_connected_integration_active(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")

        _require_redis()
        cache_key = cls._ci_active_cache_key(ci)
        if not force_refresh:
            memory_cached = cls._ci_active_memory_cache_get(ci)
            if memory_cached is not None:
                return memory_cached
            cached = str(await redis_ops.get(cache_key) or "").strip().lower()
            if cached in {"1", "0"}:
                detected = cached == "1"
                cls._ci_active_memory_cache_set(ci, detected)
                return detected

        active_lock = cls._ci_active_lock(ci)
        async with active_lock:
            if not force_refresh:
                memory_cached = cls._ci_active_memory_cache_get(ci)
                if memory_cached is not None:
                    return memory_cached
                cached = str(await redis_ops.get(cache_key) or "").strip().lower()
                if cached in {"1", "0"}:
                    detected = cached == "1"
                    cls._ci_active_memory_cache_set(ci, detected)
                    return detected

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

            await redis_ops.set(
                cache_key,
                "1" if detected else "0",
                ex=AsteriskCrmChannelConfig.SETTINGS_TTL,
            )
            cls._ci_active_memory_cache_set(ci, bool(detected))
            return bool(detected)

    @classmethod
    async def _ensure_connected_integration_active(
        cls,
        connected_integration_id: str,
        *,
        force_refresh: bool = False,
    ) -> None:
        is_active = await cls._is_connected_integration_active(
            connected_integration_id,
            force_refresh=force_refresh,
        )
        if is_active:
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
        if len(_SETTINGS_LOCAL_CACHE) >= AsteriskCrmChannelConfig.SETTINGS_LOCAL_MAX:
            for key, (expires_at, _) in list(_SETTINGS_LOCAL_CACHE.items()):
                if expires_at <= now_ts:
                    _SETTINGS_LOCAL_CACHE.pop(key, None)
            while len(_SETTINGS_LOCAL_CACHE) >= AsteriskCrmChannelConfig.SETTINGS_LOCAL_MAX:
                _SETTINGS_LOCAL_CACHE.pop(next(iter(_SETTINGS_LOCAL_CACHE)), None)
        _SETTINGS_LOCAL_CACHE[cache_key] = (
            now_ts + AsteriskCrmChannelConfig.SETTINGS_LOCAL_TTL,
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
            cached = await redis_ops.get(stale_key)
            if not cached:
                return None
            settings_map = cls._normalize_settings_map(_json_loads(cached))
            cls._write_local_settings_cache(stale_key, settings_map)
            return settings_map
        except Exception:
            return None

    @classmethod
    async def _fetch_settings_map(cls, connected_integration_id: str) -> Dict[str, str]:
        _require_redis()
        cache_key = AsteriskCrmChannelIntegration._settings_cache_key(
            connected_integration_id
        )
        local = cls._read_local_settings_cache(cache_key)
        if local is not None:
            return local
        cached = await redis_ops.get(cache_key)
        if cached:
            try:
                loaded = _json_loads(cached)
                if isinstance(loaded, dict):
                    settings_map = cls._normalize_settings_map(loaded)
                    cls._write_local_settings_cache(cache_key, settings_map)
                    return settings_map
            except Exception:
                pass

        lock_token = await cls._acquire_lock_wait(
            cls._settings_fetch_lock_key(connected_integration_id),
            AsteriskCrmChannelConfig.SETTINGS_LOCK_TTL_SEC,
            wait_seconds=AsteriskCrmChannelConfig.SETTINGS_LOCK_WAIT_SEC,
        )
        if not lock_token:
            stale = await cls._read_settings_stale_cache(connected_integration_id)
            if stale is not None:
                return stale
            raise TimeoutError(
                f"Timed out waiting for Asterisk settings refresh for ID {connected_integration_id}"
            )

        try:
            cached = await redis_ops.get(cache_key)
            if cached:
                loaded = _json_loads(cached)
                if isinstance(loaded, dict):
                    settings_map = cls._normalize_settings_map(loaded)
                    cls._write_local_settings_cache(cache_key, settings_map)
                    return settings_map
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(
                        connected_integration_id=connected_integration_id,
                    )
                )
            settings_map = cls._normalize_settings_map(
                {
                    str(item.key or "").strip().lower(): str(item.value or "")
                    for item in (response.result or [])
                    if item and item.key
                }
            )
            payload = _json_dumps(settings_map)
            stale_key = cls._settings_stale_cache_key(connected_integration_id)
            cls._write_local_settings_cache(cache_key, settings_map)
            cls._write_local_settings_cache(stale_key, settings_map)
            async with redis_ops.pipeline(transaction=True) as pipe:
                await pipe.set(cache_key, payload, ex=AsteriskCrmChannelConfig.SETTINGS_TTL)
                await pipe.set(
                    stale_key,
                    payload,
                    ex=AsteriskCrmChannelConfig.SETTINGS_STALE_TTL,
                )
                await pipe.execute()
            return settings_map
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code in {401, 403, 404}:
                is_active = await cls._is_connected_integration_active(
                    connected_integration_id,
                    force_refresh=True,
                )
                if not is_active or status_code in {401, 403}:
                    raise ConnectedIntegrationInactiveError(
                        f"ConnectedIntegration {connected_integration_id} is inactive "
                        f"(settings unavailable, status={status_code})"
                    ) from error
            stale = await cls._read_settings_stale_cache(connected_integration_id)
            if stale is not None:
                return stale
            raise
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

    @staticmethod
    def _parse_allowed_did_set(raw: Optional[str], country_code: str) -> set[str]:
        if not raw:
            return set()
        values: set[str] = set()
        for chunk in str(raw).replace(";", ",").split(","):
            normalized = _to_international_phone(chunk, country_code)
            if normalized:
                values.add(normalized)
        return values

    @staticmethod
    async def _load_runtime(connected_integration_id: str) -> RuntimeConfig:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        await AsteriskCrmChannelIntegration._ensure_connected_integration_active(
            ci
        )
        now_ts = _now_ts()
        async with _RUNTIME_LOCAL_LOCK:
            cached = _RUNTIME_LOCAL_CACHE.get(ci)
            if cached and cached[0] > now_ts:
                return cached[1]
            if cached:
                _RUNTIME_LOCAL_CACHE.pop(ci, None)

        settings_map = await AsteriskCrmChannelIntegration._fetch_settings_map(
            ci
        )

        ami_host, ami_port = _parse_ami_host_port(
            settings_map.get("asterisk_ami_host"),
            settings_map.get("asterisk_ami_port"),
        )
        ami_user = (
            str(settings_map.get("asterisk_ami_user") or "").strip()
            or str(settings_map.get("asterisk_ami_username") or "").strip()
        )
        ami_password = (
            str(settings_map.get("asterisk_ami_password") or "").strip()
            or str(settings_map.get("asterisk_ami_secret") or "").strip()
        )
        default_country_code = _normalize_country_code(
            settings_map.get("asterisk_default_country_code"), "998"
        )

        channel_id = _to_int(settings_map.get("asterisk_channel_id"), None)
        if not ami_user:
            raise ValueError("asterisk_ami_user is required")
        if not ami_password:
            raise ValueError("asterisk_ami_password is required")
        if not channel_id or channel_id <= 0:
            raise ValueError("asterisk_channel_id must be > 0")

        default_responsible_user_id = _to_int(
            settings_map.get("asterisk_default_responsible_user_id"),
            None,
        )
        if default_responsible_user_id is not None and default_responsible_user_id <= 0:
            raise ValueError("asterisk_default_responsible_user_id must be > 0")

        runtime = RuntimeConfig(
            connected_integration_id=ci,
            asterisk_hash=_hash_scope_key(ci),
            ami_host=ami_host,
            ami_port=ami_port,
            ami_user=ami_user,
            ami_password=ami_password,
            channel_id=channel_id,
            default_responsible_user_id=default_responsible_user_id,
            subject_template=(
                str(settings_map.get("asterisk_lead_subject_template") or "").strip()
                or "Call {direction} {client_phone}"
            ),
            allowed_did_set=AsteriskCrmChannelIntegration._parse_allowed_did_set(
                settings_map.get("asterisk_allowed_did_list"),
                default_country_code,
            ),
            recording_base_url=(
                str(settings_map.get("asterisk_recording_base_url") or "").strip() or None
            ),
            state_ttl_sec=AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
            default_country_code=default_country_code,
            assign_responsible_by_operator_ext=_to_bool(
                settings_map.get("asterisk_assign_responsible_by_operator_ext"),
                True,
            ),
            message_language=_normalize_message_language(
                settings_map.get("asterisk_message_language"),
                "ru",
            ),
            close_ticket_on_call_end=_to_bool(
                settings_map.get("asterisk_close_ticket_on_call_end"),
                True,
            ),
            min_external_digits=max(
                _to_int(settings_map.get("asterisk_min_external_digits"), 4) or 4,
                2,
            ),
            create_ticket_on_call_start=_to_bool(
                settings_map.get("asterisk_create_ticket_on_call_start"),
                True,
            ),
            assign_responsible_requires_attendance=_to_bool(
                settings_map.get("asterisk_assign_responsible_requires_attendance"),
                False,
            ),
            post_status_messages=_to_bool(
                settings_map.get("asterisk_post_status_messages"),
                True,
            ),
            log_ami_events=_to_bool(
                settings_map.get("asterisk_log_ami_events"),
                False,
            ),
        )
        async with _RUNTIME_LOCAL_LOCK:
            _RUNTIME_LOCAL_CACHE[ci] = (
                _now_ts() + AsteriskCrmChannelConfig.RUNTIME_LOCAL_TTL,
                runtime,
            )
        return runtime

    @staticmethod
    def _payload_get(payload: Dict[str, Any], path: str) -> Any:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _normalize_call_id(value: Any) -> Optional[str]:
        if isinstance(value, (dict, list, tuple, set)):
            return None
        text = str(value or "").strip()
        return text or None

    @classmethod
    def _ticket_external_dialog_id(cls, runtime: RuntimeConfig, external_call_id: str) -> Optional[str]:
        normalized_call_id = cls._normalize_call_id(external_call_id)
        if not normalized_call_id:
            return None
        return f"ci:{runtime.connected_integration_id}:asterisk:{normalized_call_id}"

    @classmethod
    def _payload_pick(cls, payload: Dict[str, Any], *paths: str) -> Any:
        for path in paths:
            value = cls._payload_get(payload, path)
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            return value
        return None

    @staticmethod
    def _normalize_direction(raw: Any, payload: Dict[str, Any]) -> str:
        value = str(raw or "").strip().lower()
        if value in {"inbound", "incoming", "in"}:
            return "inbound"
        if value in {"outbound", "outgoing", "out"}:
            return "outbound"
        inbound_flag = payload.get("is_inbound")
        if isinstance(inbound_flag, bool):
            return "inbound" if inbound_flag else "outbound"
        return "inbound"

    @staticmethod
    def _normalize_status(raw: Any) -> Optional[str]:
        value = str(raw or "").strip().lower()
        if not value:
            return None
        mapping = {
            "stasisstart": "started",
            "channelcreated": "started",
            "started": "started",
            "start": "started",
            "ringing": "ringing",
            "ring": "ringing",
            "dialing": "ringing",
            "answered": "answered",
            "up": "answered",
            "connected": "answered",
            "missed": "missed",
            "no_answer": "missed",
            "noanswer": "missed",
            "completed": "completed",
            "ended": "completed",
            "failed": "failed",
            "busy": "failed",
            "congestion": "failed",
            "cancelled": "failed",
            "recording_ready": "recording_ready",
            "recordingready": "recording_ready",
        }
        normalized = mapping.get(value, value)
        if normalized in AsteriskCrmChannelConfig.EVENT_STATUSES:
            return normalized
        return None

    @classmethod
    def _raw_event_type(cls, payload: Dict[str, Any]) -> str:
        return str(
            cls._payload_pick(payload or {}, "event", "event_name", "type") or ""
        ).strip().lower()

    @classmethod
    def _recording_value_from_payload(cls, payload: Dict[str, Any]) -> Any:
        return cls._payload_pick(
            payload or {},
            "recording_url",
            "recording.url",
            "recording.file",
            "file_url",
            "recordingfile",
            "recording_file",
            "mixmonitorfilename",
            "mixmonitor_filename",
            "monitorfilename",
            "filename",
            "file",
        )

    @classmethod
    def _extract_internal_extension_from_payload(
        cls,
        payload: Dict[str, Any],
        *paths: str,
    ) -> Optional[str]:
        for path in paths:
            candidate = _extract_internal_extension_candidate(
                cls._payload_get(payload or {}, path)
            )
            if candidate:
                return candidate
        return None

    @classmethod
    def _is_allowed_did_phone(cls, runtime: RuntimeConfig, value: Any) -> bool:
        if not runtime.allowed_did_set:
            return False
        normalized = _to_international_phone(value, runtime.default_country_code)
        if normalized and normalized in runtime.allowed_did_set:
            return True
        raw = _normalize_phone(value)
        return bool(raw and raw in runtime.allowed_did_set)

    @classmethod
    def _operator_candidate_is_usable(
        cls,
        runtime: RuntimeConfig,
        candidate: Any,
        client_phone: Optional[str],
    ) -> bool:
        normalized = _normalize_phone(candidate)
        if not normalized:
            return False
        if client_phone and normalized == _normalize_phone(client_phone):
            return False
        if cls._is_allowed_did_phone(runtime, normalized):
            return False
        return True

    @classmethod
    def _autodetected_client_phone_is_usable(
        cls,
        runtime: RuntimeConfig,
        candidate: Any,
    ) -> bool:
        normalized = _normalize_phone(candidate)
        if not normalized:
            return False
        if _is_internal_extension(normalized):
            return False
        if cls._is_allowed_did_phone(runtime, normalized):
            return False
        return True

    @classmethod
    def _should_ignore_external_congestion_noise(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
        *,
        direction: str,
        client_candidate: Optional[str],
    ) -> bool:
        if direction != "inbound":
            return False

        context_values = [
            cls._payload_pick(payload, "context"),
            cls._payload_pick(payload, "destinationcontext", "destination_context"),
            cls._payload_pick(payload, "dialcontext", "dcontext", "dstcontext"),
            cls._payload_pick(payload, "destination", "dst", "exten", "lastdata"),
        ]
        if not any(
            "from-sip-external" in str(value or "").strip().lower()
            for value in context_values
        ):
            return False

        app = str(
            cls._payload_pick(
                payload,
                "app",
                "application",
                "lastapplication",
                "last_application",
            )
            or ""
        ).strip().lower()
        if app != "congestion":
            return False

        did = cls._payload_pick(
            payload,
            "did",
            "dnid",
            "did_number",
            "didnum",
            "did_num",
            "did_phone",
        )
        if did:
            if runtime.allowed_did_set and cls._is_allowed_did_phone(runtime, did):
                return False
            if not runtime.allowed_did_set and not _is_internal_extension(did):
                return False

        return _is_internal_extension(client_candidate)

    @classmethod
    def _context_values(cls, payload: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        for value in (
            cls._payload_pick(payload, "context", "channelcontext", "chancontext"),
            cls._payload_pick(payload, "destinationcontext", "destination_context"),
            cls._payload_pick(payload, "dialcontext", "dcontext", "dstcontext"),
        ):
            text = str(value or "").strip().lower()
            if text:
                values.append(text)
        return values

    @classmethod
    def _is_scanner_context(cls, payload: Dict[str, Any]) -> bool:
        # Scanner/fraud SIP probes land in the "from-sip-external" context. The whole
        # linked call must be ignored, so any leg showing this context flags the call.
        return any(
            value.startswith("from-sip-external") for value in cls._context_values(payload)
        )

    @staticmethod
    def _is_root_channel(payload: Dict[str, Any]) -> bool:
        # Root channel of a call has Uniqueid == Linkedid. When Linkedid is absent
        # (older Asterisk), the single channel is its own root.
        uniqueid = str(
            AsteriskCrmChannelIntegration._payload_pick(payload, "uniqueid", "channel.uniqueid")
            or ""
        ).strip()
        linkedid = str(
            AsteriskCrmChannelIntegration._payload_pick(payload, "linkedid", "linked_id", "channel.linkedid")
            or ""
        ).strip()
        if not linkedid:
            return True
        if not uniqueid:
            return True
        return uniqueid == linkedid

    @classmethod
    def _cdr_disposition(cls, payload: Dict[str, Any]) -> str:
        raw = str(cls._payload_pick(payload or {}, "disposition") or "").strip().lower()
        return re.sub(r"[\s_-]+", "", raw)

    @classmethod
    def _ami_completed_is_strong(cls, payload: Dict[str, Any]) -> bool:
        event_type = cls._raw_event_type(payload)
        if event_type == "agentcomplete":
            talk_time = _to_int(
                cls._payload_pick(payload, "talktime", "talk_time", "talk_duration_sec"),
                0,
            ) or 0
            return talk_time > 0
        if event_type == "cdr":
            billsec = _to_int(
                cls._payload_pick(payload, "billableseconds", "billsec", "talk_duration_sec"),
                0,
            ) or 0
            return cls._cdr_disposition(payload) in {"answer", "answered"} and billsec > 0
        return False

    @classmethod
    def _normalize_external_event(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Optional[CallEvent]:
        source = payload
        if isinstance(payload.get("data"), dict):
            nested = payload.get("data")
            if isinstance(nested, dict):
                source = nested
        if isinstance(payload.get("event"), dict):
            nested = payload.get("event")
            if isinstance(nested, dict):
                source = nested

        status_raw = cls._payload_pick(
            source,
            "status",
            "event_status",
            "call_status",
            "type",
            "event_name",
        )
        status = cls._normalize_status(status_raw)
        if not status:
            # Some event sources put call state into nested payload fields.
            status = cls._normalize_status(
                cls._payload_pick(source, "channel.state", "state")
            )
        if not status:
            return None

        external_call_id = str(
            cls._payload_pick(
                source,
                "external_call_id",
                "linkedid",
                "linked_id",
                "call_id",
                "uniqueid",
                "channel.linkedid",
                "channel.id",
            )
            or ""
        ).strip()
        if not external_call_id:
            return None

        direction = cls._normalize_direction(
            cls._payload_pick(source, "direction", "call_direction"), source
        )

        from_phone = _normalize_phone(
            cls._payload_pick(
                source,
                "from_phone",
                "from",
                "src",
                "caller_number",
                "caller",
                "caller.number",
                "channel.caller.number",
            )
        )
        to_phone = _normalize_phone(
            cls._payload_pick(
                source,
                "to_phone",
                "to",
                "dst",
                "destination_number",
                "destination",
                "connected.number",
                "channel.connected.number",
                "channel.dialplan.exten",
                "dialplan.exten",
            )
        )
        client_phone = _normalize_phone(
            cls._payload_pick(source, "client_phone", "customer_phone")
        )
        fallback_client_phone = None
        if not client_phone:
            fallback_client_phone = from_phone if direction == "inbound" else to_phone
            if cls._autodetected_client_phone_is_usable(runtime, fallback_client_phone):
                client_phone = fallback_client_phone

        if cls._should_ignore_external_congestion_noise(
            runtime,
            source,
            direction=direction,
            client_candidate=client_phone or fallback_client_phone or from_phone,
        ):
            return None

        if (
            not client_phone
            and status not in AsteriskCrmChannelConfig.CLIENT_PHONE_OPTIONAL_STATUSES
        ):
            return None

        event_ts = _parse_event_ts(
            cls._payload_pick(source, "event_ts", "timestamp", "ts")
        )
        event_id_raw = str(cls._payload_pick(source, "event_id") or "").strip()
        event_id = event_id_raw or hashlib.md5(
            f"{external_call_id}:{status}:{event_ts}".encode("utf-8")
        ).hexdigest()

        talk_duration_sec = _to_int(
            cls._payload_pick(
                source,
                "talk_duration_sec",
                "billableseconds",
                "billsec",
                "answered_duration_sec",
                "conversation_duration_sec",
                "duration_sec",
            ),
            None,
        )
        recording_url = _resolve_recording_url(
            runtime.recording_base_url,
            cls._recording_value_from_payload(source),
        )
        operator_ext = _normalize_phone(
            cls._payload_pick(source, "operator_ext", "agent_ext", "extension")
        )

        return CallEvent(
            event_id=event_id,
            external_call_id=external_call_id,
            asterisk_hash=runtime.asterisk_hash,
            direction=direction,
            from_phone=from_phone or "",
            to_phone=to_phone or "",
            client_phone=client_phone or "",
            status=status,
            event_ts=event_ts,
            talk_duration_sec=talk_duration_sec,
            recording_url=recording_url,
            operator_ext=operator_ext,
            raw_payload=source,
        )

    @staticmethod
    def _event_to_dict(event: CallEvent) -> Dict[str, Any]:
        return {
            "event_id": event.event_id,
            "external_call_id": event.external_call_id,
            "asterisk_hash": event.asterisk_hash,
            "direction": event.direction,
            "from_phone": event.from_phone,
            "to_phone": event.to_phone,
            "client_phone": event.client_phone,
            "status": event.status,
            "event_ts": event.event_ts,
            "talk_duration_sec": event.talk_duration_sec,
            "recording_url": event.recording_url,
            "operator_ext": event.operator_ext,
            "raw_payload": AsteriskCrmChannelIntegration._compact_raw_payload_for_stream(
                event.raw_payload
            ),
        }

    @classmethod
    def _compact_raw_payload_for_stream(cls, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        compact: Dict[str, Any] = {}
        for key in (
            "event",
            "event_name",
            "type",
            "scanner",
            "direction_confident",
            "linkedid",
            "linked_id",
            "external_call_id",
            "call_id",
            "uniqueid",
            "destuniqueid",
            "bridgeuniqueid",
            "dialstatus",
            "disposition",
            "billableseconds",
            "billsec",
            "talktime",
            "talk_time",
            "talk_duration_sec",
            "cause",
            "cause-txt",
            "cause_txt",
            "causetxt",
            "recording_url",
            "recordingfile",
            "recording_file",
            "mixmonitorfilename",
            "mixmonitor_filename",
            "monitorfilename",
            "filename",
            "file",
        ):
            value = payload.get(key)
            if value not in (None, ""):
                compact[key] = value

        for key, fields in (
            ("channel", ("linkedid", "uniqueid", "id")),
            ("destchannel", ("uniqueid", "id")),
        ):
            source = payload.get(key)
            if not isinstance(source, dict):
                continue
            nested: Dict[str, Any] = {}
            for field in fields:
                value = source.get(field)
                if value not in (None, ""):
                    nested[field] = value
            if nested:
                compact[key] = nested

        return compact

    @staticmethod
    def _event_from_dict(payload: Dict[str, Any]) -> Optional[CallEvent]:
        status = str(payload.get("status") or "").strip().lower()
        if status not in AsteriskCrmChannelConfig.EVENT_STATUSES:
            return None

        required = (
            "event_id",
            "external_call_id",
            "asterisk_hash",
            "direction",
            "event_ts",
        )
        for field in required:
            if payload.get(field) in (None, ""):
                return None
        client_phone = _normalize_phone(payload.get("client_phone"))
        if (
            status not in AsteriskCrmChannelConfig.CLIENT_PHONE_OPTIONAL_STATUSES
            and not client_phone
        ):
            return None

        return CallEvent(
            event_id=str(payload["event_id"]).strip(),
            external_call_id=str(payload["external_call_id"]).strip(),
            asterisk_hash=str(payload["asterisk_hash"]).strip(),
            direction=str(payload["direction"]).strip().lower(),
            from_phone=str(payload.get("from_phone") or "").strip(),
            to_phone=str(payload.get("to_phone") or "").strip(),
            client_phone=client_phone or "",
            status=status,
            event_ts=_to_int(payload.get("event_ts"), _now_ts()) or _now_ts(),
            talk_duration_sec=_to_int(payload.get("talk_duration_sec"), None),
            recording_url=str(payload.get("recording_url") or "").strip() or None,
            operator_ext=str(payload.get("operator_ext") or "").strip() or None,
            raw_payload=payload.get("raw_payload")
            if isinstance(payload.get("raw_payload"), dict)
            else {},
        )

    @staticmethod
    def _normalize_ami_packet(payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in (payload or {}).items():
            key_text = str(key or "").strip().lower()
            if not key_text:
                continue
            normalized[key_text] = value
            key_alt = key_text.replace("-", "_")
            if key_alt != key_text:
                normalized[key_alt] = value
        return normalized

    @classmethod
    def _format_ami_event_for_log(cls, packet: Dict[str, Any]) -> str:
        """One-line summary of a raw AMI packet for opt-in diagnostics."""
        fields = [
            ("event", cls._raw_event_type(packet) or "?"),
            ("channel", cls._payload_pick(packet, "channel")),
            ("destchannel", cls._payload_pick(packet, "destchannel", "destinationchannel")),
            ("calleridnum", cls._payload_pick(packet, "calleridnum")),
            ("connectedlinenum", cls._payload_pick(packet, "connectedlinenum")),
            ("exten", cls._payload_pick(packet, "exten")),
            ("context", cls._payload_pick(packet, "context")),
            ("state", cls._payload_pick(packet, "channelstatedesc", "channelstate", "state")),
            ("uniqueid", cls._payload_pick(packet, "uniqueid")),
            ("linkedid", cls._payload_pick(packet, "linkedid", "linked_id")),
            ("dialstatus", cls._payload_pick(packet, "dialstatus")),
            ("disposition", cls._payload_pick(packet, "disposition")),
        ]
        return " ".join(
            f"{name}={value}"
            for name, value in fields
            if value not in (None, "")
        )

    @classmethod
    def _derive_status_from_ami(cls, payload: Dict[str, Any]) -> Optional[str]:
        event_type = cls._raw_event_type(payload)
        if not event_type:
            return None

        if event_type == "newchannel":
            # Root channel (Uniqueid == Linkedid) seeds the per-call metadata at call
            # start; non-root legs are dropped in _normalize_ami_payload_to_external.
            return "started"
        if event_type in {"newcallerid", "newexten"}:
            # Too noisy for CRM chat; keep only meaningful call stages.
            return None
        if event_type in {"dialbegin", "dialstate", "agentcalled"}:
            # Ring / queue fan-out (one event per dialed member). Never a CRM action — the
            # ticket is created at Newchannel and the answer arrives via AgentConnect/
            # BridgeEnter. Dropping these keeps the per-call event stream small so the real
            # answer is not stuck behind dozens of ring legs in the serialized worker.
            return None
        if event_type == "agentconnect":
            return "answered"
        if event_type == "agentcomplete":
            return "completed" if cls._ami_completed_is_strong(payload) else None
        if event_type == "newstate":
            normalized = cls._normalize_status(
                cls._payload_pick(payload, "channelstatedesc", "state", "channelstate")
            )
            if normalized == "answered":
                # "Up" alone is noisy (every channel goes Up). Treat it as the answer only
                # when a NON-root local-extension channel goes Up — i.e. an operator picked
                # up a call routed to them (inbound). The root channel going Up is the
                # originator (outbound) or the trunk leg, not an operator answer. Inbound
                # dedups to one answered via posted_statuses.
                channel_ext = _extract_internal_extension_candidate(
                    cls._payload_pick(payload, "channel")
                )
                if channel_ext and not cls._is_root_channel(payload):
                    return "answered"
                return None
            # Other channel states (Ring/Ringing/Dialing/...) are ring noise.
            return None
        if event_type in {"bridgeenter", "bridge", "link"}:
            return "answered"
        if event_type == "bridgecreate":
            # Bridge creation alone is not enough to prove that an operator joined.
            return None
        if event_type in {"mixmonitorstop", "monitorstop"}:
            return "recording_ready"
        if event_type == "dialend":
            # Only an actual answer matters. Per-leg noanswer/cancel/busy/congestion is
            # queue fan-out noise (the call is answered by another member, or ends via the
            # root Hangup) — never a CRM action.
            dial_status = str(cls._payload_pick(payload, "dialstatus") or "").strip().lower()
            if dial_status in {"answer", "answered"}:
                return "answered"
            return None
        if event_type in {"hangup", "hanguprequest", "softhanguprequest"}:
            # A channel hangup ends the call. The master-record gate keeps only the root
            # channel (Uniqueid == Linkedid), so this is the call finishing. Map it to a
            # terminal "completed"; whether the ticket closes is decided by the presence of
            # a responsible (answered -> close) vs none (missed -> left open).
            return "completed"
        if event_type in {"unlink", "bridgeleave"}:
            # Per-leg bridge events are not the call end.
            return None
        if event_type == "cdr":
            # Redundant terminal: the root Hangup already drives the close. CDR carries no
            # Linkedid (so it cannot be master-gated) and fans out one record per leg, so
            # forwarding it only floods the serialized worker with duplicate terminals.
            return None
        return cls._normalize_status(event_type)

    @classmethod
    def _direction_from_context(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Optional[str]:
        """Classify direction from the dialplan Context (spec-preferred signal).

        from-trunk/from-pstn/from-did -> inbound; from-internal with an
        external-length dialed number -> outbound. Returns None when the context
        is unknown or an internal/feature dial, so phone heuristics can decide.
        """
        for context in cls._context_values(payload):
            if context.startswith("from-sip-external"):
                # Scanner traffic; ignored elsewhere, never a real direction here.
                continue
            if (
                context.startswith("from-trunk")
                or context.startswith("from-pstn")
                or context.startswith("from-did")
                or context.startswith("from-external")
                or context.startswith("from-pubpeer")
                or "incoming" in context
            ):
                return "inbound"
            if context.startswith("from-internal") or context.startswith("from-office"):
                dialed_digits = _normalize_phone(
                    cls._payload_pick(
                        payload,
                        "exten",
                        "dnid",
                        "destination",
                        "dst",
                        "connectedlinenum",
                    )
                )
                if (
                    dialed_digits
                    and not _is_internal_extension(dialed_digits)
                    and len(dialed_digits) >= runtime.min_external_digits
                ):
                    return "outbound"
                # Short/feature codes or ext-to-ext: let phone heuristics decide.
                return None
        return None

    @classmethod
    def _derive_direction_from_ami(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> str:
        explicit = cls._payload_pick(payload, "direction", "call_direction")
        if explicit is not None:
            return cls._normalize_direction(explicit, payload)

        context_direction = cls._direction_from_context(runtime, payload)
        if context_direction:
            return context_direction

        caller = _to_international_phone(
            cls._payload_pick(
                payload,
                "calleridnum",
                "callerid",
                "src",
                "source",
                "source_number",
                "source_num",
                "caller",
                "channelcalleridnum",
            ),
            runtime.default_country_code,
        )
        connected = _to_international_phone(
            cls._payload_pick(
                payload,
                "connectedlinenum",
                "exten",
                "destination",
                "dst",
                "dnid",
                "did",
                "did_number",
                "dialstring",
                "destcalleridnum",
                "to",
            ),
            runtime.default_country_code,
        )
        caller_is_ext = _is_internal_extension(caller)
        connected_is_ext = _is_internal_extension(connected)
        if caller and connected:
            if caller_is_ext and not connected_is_ext:
                return "outbound"
            if connected_is_ext and not caller_is_ext:
                return "inbound"

        if runtime.allowed_did_set:
            if connected and connected in runtime.allowed_did_set:
                return "inbound"
            if caller and caller in runtime.allowed_did_set:
                return "outbound"

        context = str(
            cls._payload_pick(
                payload,
                "context",
                "destinationcontext",
                "dialcontext",
                "dcontext",
            )
            or ""
        ).strip().lower()
        if any(token in context for token in {"internal", "from-internal", "outbound"}):
            return "outbound"
        if any(token in context for token in {"incoming", "from-trunk", "external", "pstn"}):
            return "inbound"

        if caller and connected:
            if caller_is_ext and len(connected) >= runtime.min_external_digits:
                return "outbound"
            if connected_is_ext and len(caller) >= runtime.min_external_digits:
                return "inbound"
        return "inbound"

    @classmethod
    def _normalize_ami_payload_to_external(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return None

        source = cls._normalize_ami_packet(payload)
        status = cls._derive_status_from_ami(source)
        if not status:
            return None

        event_type = cls._raw_event_type(source)
        is_root = cls._is_root_channel(source)

        # Only the root channel (Uniqueid == Linkedid) seeds the call at start; queue
        # and member-leg Newchannel events are dropped so one call is seeded once.
        if status == "started" and not is_root:
            return None

        # Forward only the master hangup/CDR record (UniqueID == Linkedid). Queue and
        # ring-group fan-out emit many per-leg records; non-root terminals are leg noise.
        if (
            not is_root
            and status in {"completed", "missed", "failed"}
            and event_type in {"cdr", "hangup", "hanguprequest", "softhanguprequest"}
        ):
            return None

        normalized = dict(source)
        normalized["status"] = status
        if cls._is_scanner_context(source):
            # Mark the whole linked call ignored; enforced once in the worker.
            normalized["scanner"] = "1"
        direction = cls._derive_direction_from_ami(runtime, source)
        normalized["direction"] = direction
        normalized.setdefault(
            "event_ts",
            cls._payload_pick(source, "timestamp", "eventtv", "eventtime", "event_ts", "ts"),
        )

        external_call_id = cls._payload_pick(
            source,
            "external_call_id",
            "linkedid",
            "linked_id",
            "call_id",
            "uniqueid",
            "destuniqueid",
            "bridgeuniqueid",
        )
        if external_call_id:
            normalized["external_call_id"] = str(external_call_id).strip()

        from_phone = _to_international_phone(
            cls._payload_pick(
                source,
                "from_phone",
                "from",
                "src",
                "calleridnum",
                "callerid",
                "caller",
                "channelcalleridnum",
            ),
            runtime.default_country_code,
        )
        to_phone = _to_international_phone(
            cls._payload_pick(
                source,
                "to_phone",
                "to",
                "dst",
                "connectedlinenum",
                "exten",
                "destination",
                "dnid",
                "dialstring",
                "destcalleridnum",
            ),
            runtime.default_country_code,
        )
        from_is_ext = _is_internal_extension(from_phone)
        to_is_ext = _is_internal_extension(to_phone)

        # Re-evaluate direction using resolved endpoints. This helps for CDR/Hangup
        # packets where explicit direction fields are absent.
        if from_phone and to_phone:
            if from_is_ext and not to_is_ext:
                direction = "outbound"
            elif to_is_ext and not from_is_ext:
                direction = "inbound"
        # Decide the call direction at the ORIGINATOR (root channel) and LOCK it
        # (direction_confident) so later leg events — whose own CallerIDNum is the operator
        # ext — cannot flip the call. Robust to FreePBX CallerID rewriting (outbound calls
        # get the trunk CID), in priority order:
        #   1) a recognized dialplan context (from-trunk/pstn -> inbound, from-internal +
        #      external dialed -> outbound);
        #   2) the root channel NAME — an extension device (SIP/2012) originates an outbound
        #      call, a trunk channel (SIP/trunk-...) is inbound;
        #   3) the caller's nature (internal ext -> outbound, external -> inbound).
        if is_root:
            ctx_dir = cls._direction_from_context(runtime, source)
            root_channel_ext = _extract_internal_extension_candidate(
                cls._payload_pick(source, "channel")
            )
            if ctx_dir:
                direction = ctx_dir
            elif root_channel_ext:
                direction = "outbound"
            elif from_phone:
                direction = "outbound" if from_is_ext else "inbound"
            normalized["direction_confident"] = "1"
        normalized["direction"] = direction

        did_phone = _to_international_phone(
            cls._payload_pick(
                source,
                "did_phone",
                "did",
                "dnid",
                "did_number",
                "didnum",
                "did_num",
            ),
            runtime.default_country_code,
        )
        if did_phone and not _is_internal_extension(did_phone):
            normalized["did_phone"] = did_phone

        explicit_client_phone = _to_international_phone(
            cls._payload_pick(source, "client_phone", "customer_phone"),
            runtime.default_country_code,
        )
        client_phone = (
            explicit_client_phone if explicit_client_phone and not _is_internal_extension(explicit_client_phone) else None
        )
        if not client_phone:
            if direction == "inbound":
                if from_phone and not from_is_ext:
                    client_phone = from_phone
                elif to_phone and not to_is_ext:
                    client_phone = to_phone
            else:
                if to_phone and not to_is_ext:
                    client_phone = to_phone
                elif from_phone and not from_is_ext:
                    client_phone = from_phone
        if client_phone:
            normalized["client_phone"] = client_phone

        channel_operator_ext = cls._extract_internal_extension_from_payload(
            source,
            "operator_ext",
            "agent_ext",
            "agent",
            "interface",
            "member",
            "membername",
            "channel",
            "sourcechannel",
            "srcchannel",
            "destchannel",
            "destinationchannel",
            "peer",
            "peerchannel",
        )
        field_operator_ext = cls._extract_internal_extension_from_payload(
            source,
            "sourceextension",
            "destinationextension",
            "extension",
            "connectedlinenum",
            "destcalleridnum",
            "exten",
        )
        operator_candidates = [
            _to_international_phone(
                cls._payload_pick(source, "operator_ext", "agent_ext", "agent"), runtime.default_country_code
            ),
            _to_international_phone(channel_operator_ext, runtime.default_country_code),
            _to_international_phone(field_operator_ext, runtime.default_country_code),
        ]
        operator_ext: Optional[str] = None
        for candidate in operator_candidates:
            if not cls._operator_candidate_is_usable(runtime, candidate, client_phone):
                continue
            operator_ext = candidate
            if _is_internal_extension(candidate):
                break

        if not operator_ext:
            if direction == "inbound":
                if cls._operator_candidate_is_usable(runtime, to_phone, client_phone):
                    operator_ext = to_phone
                elif cls._operator_candidate_is_usable(runtime, from_phone, client_phone):
                    operator_ext = from_phone
            else:
                if cls._operator_candidate_is_usable(runtime, from_phone, client_phone):
                    operator_ext = from_phone
                elif cls._operator_candidate_is_usable(runtime, to_phone, client_phone):
                    operator_ext = to_phone
        if operator_ext:
            normalized["operator_ext"] = operator_ext

        # Render participants in stable semantic order.
        if direction == "inbound":
            normalized["from_phone"] = client_phone or from_phone or ""
            normalized["to_phone"] = operator_ext or to_phone or ""
        else:
            normalized["from_phone"] = operator_ext or from_phone or ""
            normalized["to_phone"] = client_phone or to_phone or ""

        talk_duration_sec = _to_int(
            cls._payload_pick(
                source,
                "talk_duration_sec",
                "billableseconds",
                "billsec",
                "answered_duration_sec",
                "conversation_duration_sec",
                "talktime",
                "talk_time",
            ),
            None,
        )
        if talk_duration_sec is not None:
            normalized["talk_duration_sec"] = int(talk_duration_sec)

        recording_value = cls._recording_value_from_payload(source)
        if recording_value:
            normalized["recording_url"] = _resolve_recording_url(
                runtime.recording_base_url,
                str(recording_value),
            )

        if not cls._payload_pick(normalized, "event_id"):
            try:
                source_dump = _json_dumps(source)
            except Exception:
                source_dump = str(source)
            normalized["event_id"] = hashlib.md5(
                f"ami:{source_dump}".encode("utf-8")
            ).hexdigest()

        return normalized

    @classmethod
    def _normalize_ami_event(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Optional[CallEvent]:
        external_payload = cls._normalize_ami_payload_to_external(runtime, payload)
        if not external_payload:
            return None
        return cls._normalize_external_event(runtime, external_payload)

    @classmethod
    async def _maybe_capture_recording_filename(
        cls,
        runtime: RuntimeConfig,
        packet: Dict[str, Any],
    ) -> None:
        """Stash the MixMonitor recording filename from a VarSet event, keyed by linkedid.

        Asterisk reports the recording path on a VarSet (Variable=MIXMONITOR_FILENAME
        or CDR(recordingfile)) during the call; the later stop/CDR packet may not carry
        it. Caching it lets recording_ready build the URL from the recording base URL.
        """
        if cls._raw_event_type(packet) != "varset":
            return
        variable = str(cls._payload_pick(packet, "variable", "var") or "").strip().lower()
        if variable not in {"mixmonitor_filename", "cdr(recordingfile)"}:
            return
        value = str(cls._payload_pick(packet, "value", "val") or "").strip()
        if not value:
            return
        call_id = cls._normalize_call_id(
            cls._payload_pick(packet, "linkedid", "linked_id", "uniqueid")
        )
        if not call_id:
            return
        try:
            await cls._redis_set_with_ttl(
                cls._recording_file_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    call_id,
                ),
                value,
                runtime.state_ttl_sec,
                min_ttl_sec=300,
            )
        except Exception:
            logger.debug(
                "Failed to cache recording filename: ci=%s call_id=%s",
                runtime.connected_integration_id,
                call_id,
            )

    @classmethod
    def _collect_call_id_candidates_from_event(cls, event: CallEvent) -> List[str]:
        candidates: List[str] = []

        def _add(value: Any) -> None:
            normalized = cls._normalize_call_id(value)
            if normalized and normalized not in candidates:
                candidates.append(normalized)

        raw_payload = event.raw_payload if isinstance(event.raw_payload, dict) else {}
        for path in ("linkedid", "linked_id", "channel.linkedid"):
            _add(cls._payload_get(raw_payload, path))
        _add(event.external_call_id)
        for path in (
            "external_call_id",
            "call_id",
            "uniqueid",
            "destuniqueid",
            "bridgeuniqueid",
            "channel.uniqueid",
            "channel.id",
            "destchannel.uniqueid",
        ):
            _add(cls._payload_get(raw_payload, path))
        return candidates

    @classmethod
    async def _resolve_canonical_call_id_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[str]:
        candidates = cls._collect_call_id_candidates_from_event(event)
        if not candidates:
            return None

        raw_payload = event.raw_payload if isinstance(event.raw_payload, dict) else {}
        preferred_linked = cls._normalize_call_id(
            cls._payload_pick(raw_payload, "linkedid", "linked_id", "channel.linkedid")
        )

        resolved_aliases: List[str] = []
        canonical: Optional[str] = None
        alias_keys: List[str] = [
            cls._call_alias_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                candidate,
            )
            for candidate in candidates
        ]
        _require_redis()
        aliases_raw = await redis_ops.mget(*alias_keys)
        for alias_raw in aliases_raw:
            alias = cls._normalize_call_id(alias_raw)
            if alias:
                resolved_aliases.append(alias)

        if preferred_linked:
            canonical = preferred_linked
        elif resolved_aliases:
            canonical = resolved_aliases[0]
        else:
            canonical = candidates[0]

        aliases_to_write = {canonical, *candidates, *resolved_aliases}
        ttl = max(_to_int(runtime.state_ttl_sec, 300) or 300, 300)
        pipeline = redis_ops.pipeline()
        for candidate in aliases_to_write:
            alias_key = cls._call_alias_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                candidate,
            )
            pipeline.set(alias_key, canonical, ex=ttl)
        await pipeline.execute()
        return canonical

    @classmethod
    async def _canonicalize_event_call_id_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> CallEvent:
        canonical = await cls._resolve_canonical_call_id_best_effort(runtime, event)
        if canonical:
            event.external_call_id = canonical
        return event

    @classmethod
    async def _enqueue_runtime_event(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> bool:
        return await cls._enqueue_event(
            runtime.connected_integration_id,
            event,
            {
                "connected_integration_id": runtime.connected_integration_id,
                "event_ts": str(_to_int(event.event_ts, _now_ts()) or _now_ts()),
                "state_ttl_sec": str(runtime.state_ttl_sec),
                "event": cls._event_to_dict(event),
                "attempt": "0",
                "enqueued_at": str(_now_ts()),
            },
        )

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str, *, force: bool = False) -> None:
        _require_redis()
        if not force and stream_key in _STREAM_GROUP_READY:
            return
        await redis_stream_group_create_with_ttl(
            stream_key,
            AsteriskCrmChannelConfig.STREAM_GROUP,
            ttl_sec=cls._resolve_stream_ttl(),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        _STREAM_GROUP_READY.add(stream_key)

    @classmethod
    def _serialize_stream_fields(cls, fields: Dict[str, Any]) -> Dict[str, str]:
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[key] = _json_dumps(value)
            elif value is None:
                serialized[key] = ""
            else:
                serialized[key] = str(value)
        return serialized

    @classmethod
    async def _enqueue(
        cls,
        stream_key: str,
        fields: Dict[str, Any],
        stream_ttl_sec: Optional[int] = None,
    ) -> None:
        _require_redis()
        await redis_stream_add_with_ttl(
            stream_key,
            cls._serialize_stream_fields(fields),
            maxlen=AsteriskCrmChannelConfig.STREAM_MAXLEN,
            ttl_sec=cls._resolve_stream_ttl(stream_ttl_sec),
            touch_ts_by_key=_REDIS_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )

    @classmethod
    async def _enqueue_deduped(
        cls,
        stream_key: str,
        dedupe_key: str,
        fields: Dict[str, Any],
        stream_ttl_sec: Optional[int] = None,
    ) -> bool:
        _require_redis()
        now_ts = _now_ts()
        stream_ttl = cls._resolve_stream_ttl(stream_ttl_sec)
        should_touch = (
            now_ts - int(_REDIS_TTL_TOUCH_TS.get(stream_key) or 0)
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
            str(AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC),
            str(AsteriskCrmChannelConfig.STREAM_MAXLEN),
            str(stream_ttl),
            "1" if should_touch else "0",
            *field_args,
        )
        if should_touch and int(result or 0) == 1:
            _REDIS_TTL_TOUCH_TS[stream_key] = now_ts
        return int(result or 0) == 1

    @classmethod
    async def _enqueue_event(
        cls,
        connected_integration_id: str,
        event: CallEvent,
        fields: Dict[str, Any],
    ) -> bool:
        ci = str(connected_integration_id or "").strip()
        if not ci:
            raise ValueError("connected_integration_id is required")
        await cls._ensure_stream_workers(ensure_groups=False)
        stream_key = cls._stream_key()
        dedupe_key = cls._enqueue_dedupe_event_key(ci, event.event_id)
        return await cls._enqueue_deduped(
            stream_key,
            dedupe_key,
            fields,
            stream_ttl_sec=fields.get("state_ttl_sec"),
        )

    @staticmethod
    def _resolve_stream_ttl(stream_ttl_sec: Optional[int] = None) -> int:
        ttl = (
            stream_ttl_sec
            if stream_ttl_sec is not None
            else AsteriskCrmChannelConfig.STREAM_TTL_SEC
        )
        return redis_ttl_seconds(ttl)

    @classmethod
    async def _touch_stream_ttl(
        cls,
        stream_key: str,
        stream_ttl_sec: Optional[int] = None,
        *,
        force: bool = False,
    ) -> None:
        _require_redis()
        await redis_expire_if_due(
            stream_key,
            cls._resolve_stream_ttl(stream_ttl_sec),
            _REDIS_TTL_TOUCH_TS,
            _now_ts(),
            min_refresh_sec=10,
            force=force,
        )

    @classmethod
    async def _set_worker_heartbeat(cls, worker_index: int) -> None:
        _require_redis()
        await redis_ops.setex(
            cls._worker_heartbeat_key(worker_index),
            AsteriskCrmChannelConfig.HEARTBEAT_TTL_SEC,
            str(_now_ts()),
        )
        await cls._touch_active_ci_ids_ttl()

    @classmethod
    async def _ensure_stream_workers(
        cls,
        connected_integration_id: Optional[str] = None,
        *,
        ensure_groups: bool = True,
    ) -> None:
        _require_redis()
        async with _MANAGER_LOCK:
            stream_key = cls._stream_key()
            if ensure_groups:
                await cls._ensure_consumer_group(stream_key)
            for index in range(AsteriskCrmChannelConfig.STREAM_WORKERS):
                task = _WORKER_TASKS.get(index)
                if task and not task.done():
                    continue
                _WORKER_TASKS[index] = asyncio.create_task(
                    cls._stream_worker_loop(index),
                    name=f"asterisk_crm_stream_{index}",
                )

    @classmethod
    async def _ensure_ami_worker(cls, runtime: RuntimeConfig) -> None:
        connected_integration_id = runtime.connected_integration_id
        async with _MANAGER_LOCK:
            task = _AMI_TASKS.get(connected_integration_id)
            if task and not task.done():
                return
            _AMI_TASKS[connected_integration_id] = asyncio.create_task(
                cls._ami_listener_loop(runtime),
                name=f"asterisk_crm_ami_{connected_integration_id}",
            )

    @classmethod
    async def shutdown_all(cls) -> None:
        async with _MANAGER_LOCK:
            worker_tasks = list(_WORKER_TASKS.values())
            _WORKER_TASKS.clear()
            ami_tasks = list(_AMI_TASKS.values())
            _AMI_TASKS.clear()

        for task in worker_tasks + ami_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping Asterisk background task")

        _STREAM_GROUP_READY.clear()
        _STREAM_CLAIM_TS.clear()
        _SETTINGS_LOCAL_CACHE.clear()
        _CI_ACTIVE_MEMORY_CACHE.clear()
        async with _RUNTIME_LOCAL_LOCK:
            _RUNTIME_LOCAL_CACHE.clear()

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not _redis_enabled():
            return {"total": 0, "restored": 0, "failed": 0}
        await cls._ensure_stream_workers()

        try:
            raw_ids = await redis_ops.smembers(cls._active_ci_ids_key())
        except Exception as error:
            logger.warning("Failed to read active Asterisk integrations set: %s", error)
            return {"total": 0, "restored": 0, "failed": 0}

        ci_ids = sorted(
            str(value or "").strip()
            for value in (raw_ids or set())
            if str(value or "").strip()
        )
        if not ci_ids:
            logger.info("Asterisk auto-restore: no active integrations found")
            return {
                "total": 0,
                "restored": 0,
                "failed": 0,
                "stream_workers": len(_WORKER_TASKS),
            }
        await cls._touch_active_ci_ids_ttl(force=True)

        restored = 0
        failed = 0
        for connected_integration_id in ci_ids:
            try:
                runtime = await cls._load_runtime(connected_integration_id)
                await cls._ensure_ami_worker(runtime)
                restored += 1
            except ConnectedIntegrationInactiveError:
                failed += 1
                await cls._mark_ci_inactive(connected_integration_id)
                logger.info(
                    "Asterisk auto-restore skipped inactive integration: ci=%s",
                    connected_integration_id,
                )
            except Exception as error:
                failed += 1
                logger.exception(
                    "Asterisk auto-restore failed: ci=%s error=%s",
                    connected_integration_id,
                    error,
                )

        logger.info(
            "Asterisk auto-restore completed: total=%s restored=%s failed=%s",
            len(ci_ids),
            restored,
            failed,
        )
        return {
            "total": len(ci_ids),
            "restored": restored,
            "failed": failed,
            "stream_workers": len(_WORKER_TASKS),
        }

    @classmethod
    async def _stop_stream_worker(cls, connected_integration_id: Optional[str] = None) -> None:
        if connected_integration_id:
            return
        async with _MANAGER_LOCK:
            tasks = list(_WORKER_TASKS.values())
            _WORKER_TASKS.clear()
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping stream worker")

    @classmethod
    async def _stop_ami_worker(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            task = _AMI_TASKS.pop(connected_integration_id, None)
        if not task:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error while stopping AMI worker: ci=%s", connected_integration_id)

    @classmethod
    async def _ami_send_action(
        cls,
        writer: asyncio.StreamWriter,
        action: str,
        **fields: Any,
    ) -> str:
        action_id = str(fields.pop("ActionID", "")).strip() or uuid.uuid4().hex
        lines = [f"Action: {str(action).strip()}", f"ActionID: {action_id}"]
        for key, value in fields.items():
            if value is None:
                continue
            lines.append(f"{str(key)}: {str(value)}")
        writer.write(("\r\n".join(lines) + "\r\n\r\n").encode("utf-8"))
        await writer.drain()
        return action_id

    @staticmethod
    async def _ami_read_packet(reader: asyncio.StreamReader) -> Optional[Dict[str, Any]]:
        lines: List[str] = []
        while True:
            raw_line = await reader.readline()
            if raw_line == b"":
                if not lines:
                    return None
                break
            line = raw_line.decode("utf-8", errors="ignore").rstrip("\r\n")
            if not line:
                if lines:
                    break
                continue
            lines.append(line)

        payload: Dict[str, Any] = {}
        for line in lines:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if not key:
                continue
            payload[key] = value.lstrip()
        return payload

    @classmethod
    async def _ami_login(
        cls,
        runtime: RuntimeConfig,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        login_action_id = await cls._ami_send_action(
            writer,
            "Login",
            Username=runtime.ami_user,
            Secret=runtime.ami_password,
            Events="on",
        )
        deadline = time.monotonic() + AsteriskCrmChannelConfig.AMI_CONNECT_TIMEOUT_SEC
        while True:
            timeout_left = deadline - time.monotonic()
            if timeout_left <= 0:
                raise RuntimeError("AMI login timeout")
            packet = await asyncio.wait_for(cls._ami_read_packet(reader), timeout_left)
            if packet is None:
                raise RuntimeError("AMI socket closed during login")
            if not packet:
                continue
            normalized = cls._normalize_ami_packet(packet)
            response = str(normalized.get("response") or "").strip().lower()
            if not response:
                continue
            response_action_id = str(normalized.get("actionid") or "").strip()
            if response_action_id and response_action_id != login_action_id:
                continue
            if response == "success":
                return
            message = str(normalized.get("message") or "").strip()
            raise RuntimeError(f"AMI login rejected: {message or response or 'unknown'}")

    @classmethod
    async def _ami_listener_loop(cls, runtime: RuntimeConfig) -> None:
        connected_integration_id = runtime.connected_integration_id
        owner_lock_key = cls._ami_owner_lock_key(connected_integration_id)
        owner_lock_token: Optional[str] = None
        owner_refresh_every = max(
            AsteriskCrmChannelConfig.AMI_OWNER_LOCK_REFRESH_SEC,
            1,
        )
        reconnect_delay = AsteriskCrmChannelConfig.AMI_RECONNECT_MIN_SEC
        logger.info(
            "Asterisk AMI listener started: ci=%s host=%s port=%s",
            connected_integration_id,
            runtime.ami_host,
            runtime.ami_port,
        )
        try:
            while True:
                try:
                    if not await cls._is_connected_integration_active(connected_integration_id):
                        raise ConnectedIntegrationInactiveError(
                            f"ConnectedIntegration {connected_integration_id} is inactive"
                        )
                    if not owner_lock_token:
                        owner_lock_token = await cls._acquire_lock(
                            owner_lock_key,
                            AsteriskCrmChannelConfig.AMI_OWNER_LOCK_TTL_SEC,
                        )
                        if not owner_lock_token:
                            await asyncio.sleep(AsteriskCrmChannelConfig.AMI_OWNER_WAIT_SEC)
                            continue
                        reconnect_delay = AsteriskCrmChannelConfig.AMI_RECONNECT_MIN_SEC
                        logger.info(
                            "Asterisk AMI ownership acquired: ci=%s instance=%s",
                            connected_integration_id,
                            _INSTANCE_ID,
                        )

                    await cls._ensure_stream_workers()
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(runtime.ami_host, runtime.ami_port),
                        timeout=AsteriskCrmChannelConfig.AMI_CONNECT_TIMEOUT_SEC,
                    )
                    try:
                        await cls._ami_login(runtime, reader, writer)
                        reconnect_delay = AsteriskCrmChannelConfig.AMI_RECONNECT_MIN_SEC
                        last_owner_refresh = time.monotonic()
                        last_active_check = time.monotonic()
                        logger.info(
                            "Asterisk AMI connected and authorized: ci=%s",
                            connected_integration_id,
                        )
                        while True:
                            if time.monotonic() - last_owner_refresh >= owner_refresh_every:
                                lock_refreshed = await cls._refresh_lock(
                                    owner_lock_key,
                                    owner_lock_token,
                                    AsteriskCrmChannelConfig.AMI_OWNER_LOCK_TTL_SEC,
                                )
                                if not lock_refreshed:
                                    raise RuntimeError("Asterisk AMI owner lock lost")
                                last_owner_refresh = time.monotonic()
                            if (
                                time.monotonic() - last_active_check
                                >= AsteriskCrmChannelConfig.AMI_PING_INTERVAL_SEC
                            ):
                                if not await cls._is_connected_integration_active(
                                    connected_integration_id
                                ):
                                    raise ConnectedIntegrationInactiveError(
                                        f"ConnectedIntegration {connected_integration_id} is inactive"
                                    )
                                last_active_check = time.monotonic()

                            try:
                                packet = await asyncio.wait_for(
                                    cls._ami_read_packet(reader),
                                    timeout=AsteriskCrmChannelConfig.AMI_PING_INTERVAL_SEC,
                                )
                            except asyncio.TimeoutError:
                                await cls._ami_send_action(writer, "Ping")
                                continue
                            if packet is None:
                                raise RuntimeError("AMI socket closed by remote host")
                            if not packet:
                                continue
                            normalized_packet = cls._normalize_ami_packet(packet)
                            if not normalized_packet.get("event"):
                                continue

                            if runtime.log_ami_events:
                                logger.info(
                                    "AMI event: ci=%s %s",
                                    connected_integration_id,
                                    cls._format_ami_event_for_log(normalized_packet),
                                )
                            await cls._maybe_capture_recording_filename(
                                runtime, normalized_packet
                            )
                            event = cls._normalize_ami_event(runtime, normalized_packet)
                            if not event:
                                continue
                            try:
                                await cls._enqueue_runtime_event(runtime, event)
                                await cls._ensure_stream_workers()
                            except Exception as enqueue_error:
                                logger.exception(
                                    "AMI event enqueue failed: ci=%s event_id=%s error=%s",
                                    connected_integration_id,
                                    event.event_id,
                                    enqueue_error,
                                )
                    finally:
                        writer.close()
                        try:
                            await writer.wait_closed()
                        except Exception:
                            pass
                except asyncio.CancelledError:
                    raise
                except ConnectedIntegrationInactiveError as error:
                    logger.info(
                        "Asterisk AMI listener stopped for inactive integration: ci=%s reason=%s",
                        connected_integration_id,
                        error,
                    )
                    await cls._mark_ci_inactive(connected_integration_id)
                    break
                except Exception as error:
                    logger.warning(
                        "Asterisk AMI listener error: ci=%s reconnect_in=%ss error=%s",
                        connected_integration_id,
                        reconnect_delay,
                        error,
                    )
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(
                        reconnect_delay * 2,
                        AsteriskCrmChannelConfig.AMI_RECONNECT_MAX_SEC,
                    )
                finally:
                    if owner_lock_token:
                        await cls._release_lock(owner_lock_key, owner_lock_token)
                        owner_lock_token = None
        finally:
            current_task = asyncio.current_task()
            async with _MANAGER_LOCK:
                active = _AMI_TASKS.get(connected_integration_id)
                if active is current_task:
                    _AMI_TASKS.pop(connected_integration_id, None)

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        stream_key = cls._stream_key()
        consumer = f"{_INSTANCE_ID}:asterisk:{worker_index}"
        await cls._ensure_consumer_group(stream_key)
        logger.info("Asterisk stream worker started: index=%s", worker_index)
        pending_entries: List[Tuple[str, Dict[str, str]]] = []
        semaphore = asyncio.Semaphore(AsteriskCrmChannelConfig.EVENT_CONCURRENCY)

        try:
            while True:
                try:
                    await cls._set_worker_heartbeat(worker_index)
                    await cls._touch_stream_ttl(stream_key)
                    claim_key = f"{stream_key}:{worker_index}"
                    now_ts = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(claim_key) or 0)
                    if now_ts - last_claim_ts >= AsteriskCrmChannelConfig.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[claim_key] = now_ts
                        claimed_entries = await cls._process_claimed_entries(
                            stream_key=stream_key,
                            consumer=consumer,
                        )
                        if claimed_entries:
                            pending_entries.extend(claimed_entries)

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=AsteriskCrmChannelConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=AsteriskCrmChannelConfig.STREAM_BATCH_SIZE,
                            block=AsteriskCrmChannelConfig.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(stream_key, force=True)
                            await asyncio.sleep(0.1)
                            continue
                        raise

                    if records:
                        for _, entries in records:
                            pending_entries.extend(
                                (str(message_id), fields if isinstance(fields, dict) else {})
                                for message_id, fields in entries
                            )

                    if not pending_entries:
                        continue

                    ready_entries, pending_entries = cls._select_ready_stream_entries(pending_entries)
                    if not ready_entries:
                        continue

                    async def guarded_process(entry: Tuple[str, Dict[str, str]]) -> None:
                        async with semaphore:
                            message_id, fields = entry
                            await cls._process_stream_entry(
                                stream_key=stream_key,
                                message_id=message_id,
                                fields=fields,
                            )

                    await asyncio.gather(*(guarded_process(entry) for entry in ready_entries))
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception(
                        "Asterisk stream worker error: index=%s error=%s",
                        worker_index,
                        error,
                    )
                    await asyncio.sleep(1.0)
        finally:
            current_task = asyncio.current_task()
            async with _MANAGER_LOCK:
                if _WORKER_TASKS.get(worker_index) is current_task:
                    _WORKER_TASKS.pop(worker_index, None)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, str]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=AsteriskCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=AsteriskCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(stream_key, force=True)
                return []
            raise

        entries: List[Tuple[str, Dict[str, str]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return entries

    @classmethod
    def _sort_stream_entries_by_event_ts(
        cls,
        entries: List[Tuple[str, Dict[str, str]]],
    ) -> List[Tuple[str, Dict[str, str]]]:
        def _sort_key(item: Tuple[str, Dict[str, str]]) -> Tuple[int, int, str]:
            message_id, fields = item
            event_ts = cls._stream_entry_event_ts(fields)
            if event_ts is not None:
                return (0, int(event_ts), str(message_id))
            fallback_ts = _to_int(fields.get("enqueued_at"), None)
            if fallback_ts is not None:
                return (1, int(fallback_ts), str(message_id))
            return (2, 0, str(message_id))

        return sorted(entries, key=_sort_key)

    @classmethod
    def _stream_entry_event_ts(cls, fields: Dict[str, str]) -> Optional[int]:
        direct_ts = _to_int(fields.get("event_ts"), None)
        if direct_ts is not None:
            return _normalize_unix_ts_seconds(int(direct_ts))
        raw_event = fields.get("event")
        if not raw_event:
            return None
        try:
            payload = _json_loads(raw_event)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        payload_ts = _to_int(payload.get("event_ts"), None)
        if payload_ts is None:
            return None
        return _normalize_unix_ts_seconds(int(payload_ts))

    @classmethod
    def _select_ready_stream_entries(
        cls,
        entries: List[Tuple[str, Dict[str, str]]],
    ) -> Tuple[List[Tuple[str, Dict[str, str]]], List[Tuple[str, Dict[str, str]]]]:
        # No reorder/defer hold: AMI is a single ordered socket, so the enqueue order is
        # already the call order. Events process as they arrive; the per-call lock plus
        # idempotent create/assign/close cover any residual cross-worker reordering. Sort
        # by event_ts only to keep within-batch ordering stable.
        return cls._sort_stream_entries_by_event_ts(entries), []

    @classmethod
    async def _clear_enqueue_dedupe_for_fields(
        cls,
        connected_integration_id: str,
        fields: Dict[str, str],
    ) -> None:
        raw_event = fields.get("event")
        if not raw_event:
            return
        try:
            event_payload = _json_loads(raw_event)
        except Exception:
            return
        if not isinstance(event_payload, dict):
            return
        event_id = str(event_payload.get("event_id") or "").strip()
        if not event_id:
            return
        await cls._redis_delete(
            cls._enqueue_dedupe_event_key(connected_integration_id, event_id)
        )

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        message_id: str,
        fields: Dict[str, str],
    ) -> None:
        connected_integration_id = str(fields.get("connected_integration_id") or "").strip()
        if not connected_integration_id:
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
            logger.warning(
                "Asterisk stream entry skipped without connected_integration_id: message_id=%s",
                message_id,
            )
            return
        attempts = _to_int(fields.get("attempt"), 0) or 0
        state_ttl_sec = (
            _to_int(fields.get("state_ttl_sec"), None)
            or AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC
        )
        try:
            raw_event = fields.get("event")
            if not raw_event:
                raise RuntimeError("stream payload has no event")
            event_payload = _json_loads(raw_event)
            if not isinstance(event_payload, dict):
                raise RuntimeError("stream event payload is not a dict")

            await cls._process_queued_event(connected_integration_id, event_payload)
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
        except CallLockBusyError:
            # Transient per-call contention: re-enqueue the same entry WITHOUT incrementing
            # the attempt counter so it never reaches the DLQ. The lock-holder finishes its
            # CRM round-trip and this stage runs on the next read.
            await cls._enqueue(stream_key, dict(fields), stream_ttl_sec=state_ttl_sec)
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
            return
        except ConnectedIntegrationInactiveError as error:
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
            await cls._mark_ci_inactive(connected_integration_id)
            logger.info(
                "Asterisk event skipped for inactive integration: ci=%s message_id=%s reason=%s",
                connected_integration_id,
                message_id,
                error,
            )
            return
        except NonRetryableCallEventError as error:
            dlq_payload = dict(fields)
            dlq_payload["attempt"] = str(max(attempts, 0) + 1)
            dlq_payload["error"] = str(error)
            dlq_payload["source_stream"] = stream_key
            dlq_payload["source_message_id"] = message_id
            await cls._enqueue(
                cls._dlq_stream_key(connected_integration_id),
                dlq_payload,
                stream_ttl_sec=state_ttl_sec,
            )
            await cls._clear_enqueue_dedupe_for_fields(connected_integration_id, fields)
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
            logger.error(
                "Asterisk event moved to DLQ (non-retryable): ci=%s message_id=%s error=%s",
                connected_integration_id,
                message_id,
                error,
            )
            return
        except Exception as error:
            attempts += 1
            if attempts >= AsteriskCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(attempts)
                dlq_payload["error"] = str(error)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_message_id"] = message_id
                await cls._enqueue(
                    cls._dlq_stream_key(connected_integration_id),
                    dlq_payload,
                    stream_ttl_sec=state_ttl_sec,
                )
                await cls._clear_enqueue_dedupe_for_fields(connected_integration_id, fields)
                await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
                logger.error(
                    "Asterisk event moved to DLQ: ci=%s message_id=%s error=%s",
                    connected_integration_id,
                    message_id,
                    error,
                )
                return

            retry_payload = dict(fields)
            retry_payload["attempt"] = str(attempts)
            retry_payload["last_error"] = str(error)
            await cls._enqueue(
                stream_key,
                retry_payload,
                stream_ttl_sec=state_ttl_sec,
            )
            await redis_stream_ack_delete(stream_key, AsteriskCrmChannelConfig.STREAM_GROUP, message_id)
            logger.warning(
                "Asterisk event requeued: ci=%s attempt=%s message_id=%s error=%s",
                connected_integration_id,
                attempts,
                message_id,
                error,
            )

    @classmethod
    async def _process_queued_event(
        cls,
        connected_integration_id: str,
        event_payload: Dict[str, Any],
    ) -> None:
        runtime = await cls._load_runtime(connected_integration_id)

        event = cls._event_from_dict(event_payload)
        if not event:
            return

        dedupe_key = cls._dedupe_event_key(connected_integration_id, event.event_id)
        locked = await cls._redis_set_nx_with_ttl(
            dedupe_key,
            _INSTANCE_ID,
            AsteriskCrmChannelConfig.PROCESSING_LOCK_TTL_SEC,
            min_ttl_sec=AsteriskCrmChannelConfig.LOCK_TTL_SEC,
        )
        if not locked:
            return

        emitted_event: Optional[CallEvent] = None
        call_lock_key: Optional[str] = None
        call_lock_token: Optional[str] = None
        try:
            event = await cls._canonicalize_event_call_id_best_effort(runtime, event)
            finalize_call_id = event.external_call_id
            if event.external_call_id:
                call_lock_key = cls._lock_call_process_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    event.external_call_id,
                )
                # Serialize same-call events by briefly waiting for the in-flight event to
                # finish — no re-enqueue churn. Events arrive ordered, so a short wait keeps
                # create -> assign -> close in order.
                call_lock_token = await cls._acquire_lock_wait(
                    call_lock_key,
                    AsteriskCrmChannelConfig.PROCESSING_LOCK_TTL_SEC,
                    wait_seconds=AsteriskCrmChannelConfig.CALL_LOCK_WAIT_SEC,
                )
                if not call_lock_token:
                    # Another stage of the same call is still in flight. Soft-retry without
                    # counting toward the DLQ (transient contention is not a failure).
                    raise CallLockBusyError("call-process lock contended")

            event = await cls._dedupe_and_stabilize_call_event(runtime, event)
            if not event:
                # Even when this event is deduped/suppressed, retry any close a terminal
                # parked but could not apply yet (transient failure, or close-before-assign
                # race). This makes the close self-healing across the call's later events.
                await cls._finalize_pending_close_best_effort(runtime, finalize_call_id)
                await cls._redis_set_with_ttl(
                    dedupe_key,
                    "1",
                    AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                    min_ttl_sec=60,
                )
                return
            emitted_event = event
            lead_ctx: Optional[LeadContext] = None
            if event.status == "recording_ready" and not _normalize_phone(event.client_phone):
                lead_ctx = await cls._resolve_mapping(runtime, event)
                if not lead_ctx:
                    logger.info(
                        "Asterisk recording event skipped: no client_phone and no mapping: ci=%s call_id=%s event_id=%s",
                        runtime.connected_integration_id,
                        event.external_call_id,
                        event.event_id,
                    )
                    await cls._redis_set_with_ttl(
                        dedupe_key,
                        "1",
                        AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                        min_ttl_sec=60,
                    )
                    return
            if not lead_ctx:
                lead_ctx = await cls._resolve_or_create_active_ticket(runtime, event)
            await cls._maybe_assign_responsible_from_operator_best_effort(
                runtime=runtime,
                event=event,
                lead_ctx=lead_ctx,
            )
            lead_ctx, _ = await cls._write_event_with_1220_policy(
                runtime,
                event,
                lead_ctx,
            )
            await cls._save_mapping(runtime, event, lead_ctx)
            await cls._post_recording_sidecar_event_best_effort(
                runtime=runtime,
                event=event,
                lead_ctx=lead_ctx,
            )
            await cls._apply_status_policy_best_effort(runtime, event, lead_ctx)
            await cls._redis_set_with_ttl(
                dedupe_key,
                "1",
                AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                min_ttl_sec=60,
            )
        except Exception as error:
            if emitted_event:
                try:
                    await cls._rollback_call_progress_after_failure(runtime, emitted_event)
                except Exception as rollback_error:
                    logger.warning(
                        "Asterisk call_progress rollback failed: ci=%s call_id=%s event_id=%s error=%s rollback_error=%s",
                        runtime.connected_integration_id,
                        emitted_event.external_call_id,
                        emitted_event.event_id,
                        error,
                        rollback_error,
                    )
            await cls._redis_delete(dedupe_key)
            raise
        finally:
            if call_lock_key and call_lock_token:
                await cls._release_lock(call_lock_key, call_lock_token)

    @staticmethod
    def _status_rank(status: str) -> int:
        return {
            "inbound_started": 20,
            "outbound_started": 20,
            "inbound_answered": 30,
            "outbound_answered": 30,
            "inbound_missed": 40,
            "outbound_failed": 40,
            # Completed with talk duration is a stronger terminal state than missed/failed.
            "inbound_completed": 45,
            "outbound_completed": 45,
            "recording_ready": 50,
        }.get(str(status or "").strip().lower(), 0)

    @staticmethod
    def _chat_event_code(event: CallEvent) -> str:
        direction = event.direction if event.direction in {"inbound", "outbound"} else "unknown"
        status = str(event.status or "").strip().lower()
        if status == "recording_ready":
            return "recording_ready"

        if direction == "inbound":
            if status in {"started", "ringing"}:
                return "inbound_started"
            if status == "answered":
                return "inbound_answered"
            if status in {"missed", "failed"}:
                return "inbound_missed"
            if status == "completed":
                return "inbound_completed"
            return f"inbound_{status or 'unknown'}"

        if direction == "outbound":
            if status in {"started", "ringing"}:
                return "outbound_started"
            if status == "answered":
                return "outbound_answered"
            if status in {"missed", "failed"}:
                return "outbound_failed"
            if status == "completed":
                return "outbound_completed"
            return f"outbound_{status or 'unknown'}"

        return f"{direction}_{status or 'unknown'}"

    @classmethod
    def _should_suppress_noise_event(cls, event: CallEvent) -> bool:
        status = str(event.status or "").strip().lower()
        if not status:
            return True

        talk_duration = _to_int(event.talk_duration_sec, 0) or 0
        to_phone = _normalize_phone(event.to_phone)
        operator_phone = cls._operator_phone_from_event(event) or _normalize_phone(
            event.operator_ext
        )

        # For outbound, ringing without operator endpoint is too noisy.
        if event.direction == "outbound" and status == "ringing" and not operator_phone:
            return True

        # Suppress queue leg noise for inbound ringing/starting to internal extensions.
        if (
            event.direction == "inbound"
            and status in {"started", "ringing"}
            and to_phone
            and _is_internal_extension(to_phone)
        ):
            return True

        # Queue fan-out emits many "missed/failed" legs per extension.
        # Suppress per-extension zero-talk legs to keep only meaningful call result.
        if (
            event.direction == "inbound"
            and status in {"missed", "failed"}
            and talk_duration <= 0
            and to_phone
            and _is_internal_extension(to_phone)
        ):
            return True

        # Some PBX variants emit intermediate inbound no-answer legs without endpoint details.
        # These events are usually noise and should not become CRM statuses.
        if (
            event.direction == "inbound"
            and status in {"missed", "failed"}
            and talk_duration <= 0
            and not to_phone
            and not operator_phone
        ):
            return True

        # Per-leg dial/hangup events can report inbound missed even when another
        # operator accepted the same call later (queue fan-out noise).
        if event.direction == "inbound" and status in {"missed", "failed"} and talk_duration <= 0:
            raw_event_type = cls._raw_event_type(event.raw_payload or {})
            if raw_event_type in {
                "dialend",
                "hangup",
                "hanguprequest",
                "softhanguprequest",
                "unlink",
                "bridgeleave",
            }:
                return True

        return False

    @classmethod
    async def _dedupe_and_stabilize_call_event(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[CallEvent]:
        if not event.external_call_id:
            return event

        progress_key = cls._call_progress_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        cached = cls._parse_cached_json(await cls._redis_get(progress_key)) or {}

        # Scanner/fraud calls (from-sip-external) are ignored for the whole linked call:
        # the first leg flags the linkedid, every later leg short-circuits here.
        if cached.get("ignored"):
            return None
        if _to_bool((event.raw_payload or {}).get("scanner"), False):
            await cls._redis_set_json_with_ttl(
                progress_key,
                {**cached, "ignored": True, "updated_at": _now_ts()},
                runtime.state_ttl_sec,
                min_ttl_sec=300,
            )
            return None

        decision_reasons: List[str] = []
        suppress_untrusted_answered = False

        stable_direction = str(cached.get("direction") or "").strip().lower()
        direction_locked = bool(cached.get("direction_locked"))
        # Apply the cached direction only once a meaningful stage has locked it. The
        # root Newchannel seed is low-information (endpoints may not be populated yet),
        # so it must not pin the direction — a later stage (ringing/answered/CDR) with
        # real endpoints can still correct a weak initial guess.
        if stable_direction in {"inbound", "outbound"} and direction_locked:
            event.direction = stable_direction

        stable_client_phone = _normalize_phone(cached.get("client_phone"))
        if stable_client_phone and not _normalize_phone(event.client_phone):
            event.client_phone = stable_client_phone
        stable_operator_ext = _normalize_phone(cached.get("operator_ext"))
        locked_operator_ext = _normalize_phone(cached.get("locked_operator_ext"))
        if locked_operator_ext:
            event.operator_ext = locked_operator_ext
        if stable_operator_ext and not _normalize_phone(event.operator_ext):
            event.operator_ext = stable_operator_ext
        stable_from_phone = _normalize_phone(cached.get("from_phone"))
        if stable_from_phone and not _normalize_phone(event.from_phone):
            event.from_phone = stable_from_phone
        stable_to_phone = _normalize_phone(cached.get("to_phone"))
        if stable_to_phone and not _normalize_phone(event.to_phone):
            event.to_phone = stable_to_phone
        event_ts = _to_int(event.event_ts, _now_ts()) or _now_ts()
        event.event_ts = int(event_ts)
        answered_at = _to_int(cached.get("answered_at"), None)
        raw_event_type = cls._raw_event_type(event.raw_payload or {})
        raw_operator_phone = cls._operator_phone_from_event_for_runtime(runtime, event)
        operator_phone = locked_operator_ext or raw_operator_phone
        if locked_operator_ext:
            event.operator_ext = locked_operator_ext
        # Inbound "answered" is the bridge leg whose channel name parses to a real local
        # extension (the human pickup). Trust it on the extension alone — mapping that ext
        # to a CRM user happens (and is logged) in the assign step, so a not-yet-mapped
        # operator no longer silently swallows the answer. Trunk/Local legs (no internal
        # ext) are the only ones suppressed.
        inbound_answered_operator_trusted = False
        if event.status == "answered" and event.direction == "inbound":
            if operator_phone and _is_internal_extension(operator_phone):
                inbound_answered_operator_trusted = True
                decision_reasons.append("operator_ext_for_answered")
            else:
                suppress_untrusted_answered = True
                decision_reasons.append("operator_missing_for_answered")
                logger.info(
                    "Asterisk inbound answered with no operator extension (suppressed leg): "
                    "ci=%s call_id=%s raw_event=%s operator=%s from=%s to=%s",
                    runtime.connected_integration_id,
                    event.external_call_id,
                    raw_event_type or None,
                    operator_phone or None,
                    event.from_phone or None,
                    event.to_phone or None,
                )
        trusted_answered_event = (
            event.status == "answered"
            and not suppress_untrusted_answered
            and (
                event.direction == "outbound"
                or inbound_answered_operator_trusted
            )
        )
        if trusted_answered_event:
            decision_reasons.append("trusted_answered")
            if (
                not locked_operator_ext
                and operator_phone
                and _is_internal_extension(operator_phone)
            ):
                locked_operator_ext = operator_phone
                event.operator_ext = locked_operator_ext
                decision_reasons.append("operator_locked_on_answered")
            if answered_at is None or event_ts < answered_at:
                answered_at = event_ts
        if event.status == "completed" and answered_at is not None and event_ts >= answered_at:
            duration_from_answer = max(event_ts - answered_at, 0)
            reported_duration = _to_int(event.talk_duration_sec, None)
            if reported_duration is None or reported_duration <= 0:
                event.talk_duration_sec = duration_from_answer
            elif duration_from_answer > 0:
                # Keep only the segment after operator answer (exclude IVR/queue time).
                event.talk_duration_sec = min(reported_duration, duration_from_answer)
        if event.status == "completed" and event.direction == "inbound" and answered_at is None:
            # No operator pickup recorded. If the endpoint maps to a real operator we can
            # still infer the answer (out-of-order BridgeEnter); otherwise the call was
            # never answered by an agent — it stays "completed" but the ticket has no
            # responsible, so the close step leaves it OPEN (the missed-call case).
            talk_duration = _to_int(event.talk_duration_sec, 0) or 0
            if (
                talk_duration > 0
                and operator_phone
                and _is_internal_extension(operator_phone)
                and raw_event_type in {"cdr", "agentcomplete", ""}
            ):
                resolved_operator_user_id = await cls._resolve_user_id_by_operator_ext_best_effort(
                    runtime,
                    operator_phone,
                )
                if resolved_operator_user_id:
                    answered_at = max(event_ts - talk_duration, 0)
                    decision_reasons.append("inferred_answered_from_completed")
                else:
                    decision_reasons.append("operator_unresolved_for_completed")

        posted_statuses = {
            str(item).strip().lower()
            for item in (cached.get("posted_statuses") or [])
            if str(item).strip()
        }
        last_rank = _to_int(cached.get("last_rank"), 0) or 0
        stage_code = cls._chat_event_code(event)
        current_rank = cls._status_rank(stage_code)
        status = stage_code

        suppressed_as_noise = cls._should_suppress_noise_event(event)
        if suppressed_as_noise:
            decision_reasons.append("suppressed_as_leg_noise")
        should_emit = not suppressed_as_noise and not suppress_untrusted_answered
        # The root Newchannel always seeds call metadata (direction/client) below, but
        # only emits a call_initiated ticket/message when explicitly enabled. By default
        # the ticket is created on the first meaningful stage (ringing/answered/hangup).
        if (
            should_emit
            and status in {"inbound_started", "outbound_started"}
            and not runtime.create_ticket_on_call_start
        ):
            should_emit = False
            decision_reasons.append("seed_only_call_start")
        completed_with_talk = (
            status in {"inbound_completed", "outbound_completed"}
            and (_to_int(event.talk_duration_sec, 0) or 0) > 0
        )
        if should_emit:
            if status == "recording_ready":
                should_emit = not bool(cached.get("recording_posted"))
                if not should_emit:
                    decision_reasons.append("suppressed_recording_duplicate")
            else:
                if status in posted_statuses:
                    should_emit = False
                    decision_reasons.append("suppressed_duplicate_stage")
                elif status == "inbound_missed" and (
                    "inbound_answered" in posted_statuses
                    or "inbound_completed" in posted_statuses
                ):
                    should_emit = False
                    decision_reasons.append("suppressed_missed_after_answered")
                elif last_rank >= 40 and current_rank <= 40 and not completed_with_talk:
                    should_emit = False
                    decision_reasons.append("suppressed_regression_by_rank")
                elif current_rank and current_rank < last_rank and not completed_with_talk:
                    should_emit = False
                    decision_reasons.append("suppressed_stage_rank_regression")

        stable_direction = (
            event.direction if event.direction in {"inbound", "outbound"} else stable_direction
        )
        # Lock the direction once it is confidently classified. The root Newchannel locks
        # immediately via the originator's caller nature (direction_confident), so later leg
        # events can't flip the call; any non-seed packet also locks. Only a low-information
        # seed stays unlocked so a later packet can still correct it.
        direction_confident = _to_bool(
            (event.raw_payload or {}).get("direction_confident"), False
        )
        direction_locked = direction_locked or (
            event.direction in {"inbound", "outbound"}
            and (raw_event_type != "newchannel" or direction_confident)
        )
        stable_client_phone = _normalize_phone(event.client_phone) or stable_client_phone
        stable_operator_ext = (
            locked_operator_ext
            or _normalize_phone(event.operator_ext)
            or stable_operator_ext
        )
        stable_from_phone = _normalize_phone(event.from_phone) or stable_from_phone
        stable_to_phone = _normalize_phone(event.to_phone) or stable_to_phone
        effective_rank = current_rank
        next_last_rank = max(last_rank, effective_rank)
        if should_emit and status and status != "recording_ready":
            posted_statuses.add(status)
        recording_posted = bool(cached.get("recording_posted")) or status == "recording_ready"
        decision_trace: List[Dict[str, Any]] = []
        store_decision_trace = bool(AsteriskCrmChannelConfig.STORE_DECISION_TRACE)
        if store_decision_trace:
            cached_trace = cached.get("decision_trace")
            if isinstance(cached_trace, list):
                for row in cached_trace[-19:]:
                    if isinstance(row, dict):
                        decision_trace.append(dict(row))
        if not decision_reasons:
            decision_reasons.append("emitted" if should_emit else "suppressed")
        trace_entry = {
            "at": _now_ts(),
            "event_ts": int(event.event_ts),
            "status": str(event.status or "").strip().lower(),
            "stage": status,
            "emit": bool(should_emit),
            "reasons": decision_reasons,
            "raw_event_type": raw_event_type or None,
        }
        if store_decision_trace:
            decision_trace.append(trace_entry)
            decision_trace = decision_trace[-20:]

        progress_payload: Dict[str, Any] = {
            "direction": stable_direction or "",
            "direction_locked": bool(direction_locked),
            "client_phone": stable_client_phone or "",
            "operator_ext": stable_operator_ext or "",
            "locked_operator_ext": locked_operator_ext or "",
            "from_phone": stable_from_phone or "",
            "to_phone": stable_to_phone or "",
            "posted_statuses": sorted(posted_statuses),
            "last_rank": int(next_last_rank),
            "recording_posted": recording_posted,
            "answered_at": int(answered_at) if answered_at is not None else None,
            "last_decision": trace_entry,
            "updated_at": _now_ts(),
        }
        if store_decision_trace:
            progress_payload["decision_trace"] = decision_trace

        await cls._redis_set_json_with_ttl(
            progress_key,
            progress_payload,
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )

        if not should_emit:
            return None
        return event

    @classmethod
    async def _rollback_call_progress_after_failure(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> None:
        if not event.external_call_id:
            return

        progress_key = cls._call_progress_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        cached = cls._parse_cached_json(await cls._redis_get(progress_key)) or {}
        if not isinstance(cached, dict) or not cached:
            return

        stage = cls._chat_event_code(event)
        posted_statuses = {
            str(item).strip().lower()
            for item in (cached.get("posted_statuses") or [])
            if str(item).strip()
        }

        changed = False
        if stage == "recording_ready":
            if bool(cached.get("recording_posted")):
                cached["recording_posted"] = False
                changed = True
        elif stage and stage in posted_statuses:
            posted_statuses.remove(stage)
            changed = True

        recalculated_rank = 0
        for posted_stage in posted_statuses:
            recalculated_rank = max(recalculated_rank, cls._status_rank(posted_stage))
        current_rank = _to_int(cached.get("last_rank"), 0) or 0
        if current_rank != recalculated_rank:
            changed = True

        if not changed:
            return

        raw_event_type = cls._raw_event_type(event.raw_payload or {})
        rollback_entry = {
            "at": _now_ts(),
            "event_ts": int(event.event_ts),
            "status": str(event.status or "").strip().lower(),
            "stage": stage,
            "emit": False,
            "deferred": False,
            "reasons": ["rolled_back_after_processing_error"],
            "raw_event_type": raw_event_type or None,
        }

        decision_trace: List[Dict[str, Any]] = []
        store_decision_trace = bool(AsteriskCrmChannelConfig.STORE_DECISION_TRACE)
        if store_decision_trace:
            cached_trace = cached.get("decision_trace")
            if isinstance(cached_trace, list):
                for row in cached_trace[-19:]:
                    if isinstance(row, dict):
                        decision_trace.append(dict(row))
            decision_trace.append(rollback_entry)
            decision_trace = decision_trace[-20:]

        cached["posted_statuses"] = sorted(posted_statuses)
        cached["last_rank"] = int(recalculated_rank)
        cached["last_decision"] = rollback_entry
        if store_decision_trace:
            cached["decision_trace"] = decision_trace
        else:
            cached.pop("decision_trace", None)
        cached["updated_at"] = _now_ts()
        await cls._redis_set_json_with_ttl(
            progress_key,
            cached,
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )

    @staticmethod
    def _extract_digit_tokens(value: Any) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, dict):
            tokens: set[str] = set()
            for nested in value.values():
                tokens.update(AsteriskCrmChannelIntegration._extract_digit_tokens(nested))
            return tokens
        if isinstance(value, (list, tuple, set)):
            tokens: set[str] = set()
            for nested in value:
                tokens.update(AsteriskCrmChannelIntegration._extract_digit_tokens(nested))
            return tokens
        text = str(value or "")
        return {
            token
            for token in (_normalize_phone(raw) for raw in re.findall(r"\d{2,20}", text))
            if token
        }

    @staticmethod
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

    @classmethod
    def _rows_to_dict_list(cls, rows: Any) -> List[Dict[str, Any]]:
        if not isinstance(rows, list):
            return []
        parsed: List[Dict[str, Any]] = []
        for row in rows:
            row_dict = cls._row_to_dict(row)
            if row_dict:
                parsed.append(row_dict)
        return parsed

    @classmethod
    def _user_matches_operator_ext(
        cls,
        user_payload: Dict[str, Any],
        operator_ext: str,
    ) -> bool:
        if not operator_ext:
            return False
        candidate_paths = (
            "internal_number",
            "internal_phone",
            "internal_ext",
            "extension",
            "ext",
            "operator_ext",
            "short_number",
            "phone",
            "main_phone",
            "phones",
            "sip",
            "sip_number",
            "sip_extension",
            "telephony.extension",
            "telephony.internal_number",
            "telephony.internal_ext",
            "pbx.extension",
        )
        for path in candidate_paths:
            value = cls._payload_get(user_payload, path)
            if value is None:
                continue
            tokens = cls._extract_digit_tokens(value)
            if operator_ext in tokens:
                return True
        return False

    @staticmethod
    def _extract_user_display_name(user_payload: Dict[str, Any]) -> Optional[str]:
        if not isinstance(user_payload, dict):
            return None

        full_name = str(user_payload.get("full_name") or "").strip()
        if full_name:
            return full_name

        parts = [
            str(user_payload.get("first_name") or "").strip(),
            str(user_payload.get("middle_name") or "").strip(),
            str(user_payload.get("last_name") or "").strip(),
        ]
        composed = " ".join(part for part in parts if part).strip()
        if composed:
            return composed

        for field in ("login", "email"):
            value = str(user_payload.get(field) or "").strip()
            if value:
                return value
        return None

    @classmethod
    async def _resolve_user_id_by_operator_ext_best_effort(
        cls,
        runtime: RuntimeConfig,
        operator_ext: str,
    ) -> Optional[int]:
        normalized_ext = _normalize_phone(operator_ext)
        if not normalized_ext:
            return None

        cache_key = cls._operator_user_cache_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            normalized_ext,
        )
        name_cache_key = cls._operator_name_cache_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            normalized_ext,
        )
        cached_user_id = _to_int(await cls._redis_get(cache_key), None)
        if cached_user_id is not None:
            if cached_user_id > 0:
                return cached_user_id
            return None

        def _resolve_from_rows(
            rows: List[Dict[str, Any]],
            *,
            allow_single_fallback: bool,
        ) -> Tuple[Optional[int], Optional[str]]:
            if not rows:
                return None, None

            matched_user_ids: List[int] = []
            matched_by_id: Dict[int, Dict[str, Any]] = {}
            fallback_row: Optional[Dict[str, Any]] = None
            if allow_single_fallback and len(rows) == 1 and isinstance(rows[0], dict):
                fallback_row = rows[0]

            for row in rows:
                if not isinstance(row, dict):
                    continue
                user_id = _to_int(row.get("id"), None)
                if not user_id:
                    continue
                if cls._user_matches_operator_ext(row, normalized_ext):
                    matched_user_ids.append(user_id)
                    matched_by_id[user_id] = row

            unique_matches = sorted(set(matched_user_ids))
            if len(unique_matches) == 1:
                user_id = unique_matches[0]
                return user_id, cls._extract_user_display_name(matched_by_id.get(user_id) or {})
            if len(unique_matches) > 1:
                logger.warning(
                    "Operator extension matched multiple users: ci=%s operator_ext=%s users=%s",
                    runtime.connected_integration_id,
                    normalized_ext,
                    unique_matches,
                )
                return None, None
            fallback_user_id = (
                _to_int(fallback_row.get("id"), None) if isinstance(fallback_row, dict) else None
            )
            fallback_name = (
                cls._extract_user_display_name(fallback_row) if isinstance(fallback_row, dict) else None
            )
            return fallback_user_id, fallback_name

        # Primary lookup by internal extension, according to User/Get docs.
        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.rbac.user.get(
                    UserGetRequest(
                        active=True,
                        internal_phone=normalized_ext,
                        limit=50,
                        offset=0,
                    )
                )
        except Exception as error:
            logger.warning(
                "User/Get failed for operator extension match: ci=%s operator_ext=%s error=%s",
                runtime.connected_integration_id,
                normalized_ext,
                error,
            )
            response = None

        if response is not None and not response.ok:
            logger.warning(
                "User/Get rejected for internal extension match: ci=%s operator_ext=%s payload=%s",
                runtime.connected_integration_id,
                normalized_ext,
                response.result,
            )
            response = None

        resolved_user_id: Optional[int] = None
        resolved_user_name: Optional[str] = None
        lookup_successful = False
        if response and response.ok:
            lookup_successful = True
            internal_rows = cls._rows_to_dict_list(response.result)
            resolved_user_id, resolved_user_name = _resolve_from_rows(
                internal_rows,
                allow_single_fallback=True,
            )
            if resolved_user_id:
                await cls._redis_set_with_ttl(
                    cache_key,
                    str(resolved_user_id),
                    runtime.state_ttl_sec,
                    min_ttl_sec=300,
                )
                if resolved_user_name:
                    await cls._redis_set_with_ttl(
                        cls._user_name_cache_key(
                            runtime.connected_integration_id,
                            runtime.asterisk_hash,
                            int(resolved_user_id),
                        ),
                        resolved_user_name,
                        runtime.state_ttl_sec,
                        min_ttl_sec=300,
                    )
                if resolved_user_name:
                    await cls._redis_set_with_ttl(
                        name_cache_key,
                        resolved_user_name,
                        runtime.state_ttl_sec,
                        min_ttl_sec=300,
                    )
                return resolved_user_id
        if lookup_successful:
            await cls._redis_set_with_ttl(
                cache_key,
                "0",
                AsteriskCrmChannelConfig.OPERATOR_NOT_FOUND_CACHE_TTL_SEC,
                min_ttl_sec=60,
            )
        return None

    @classmethod
    async def _resolve_operator_name_by_operator_ext_best_effort(
        cls,
        runtime: RuntimeConfig,
        operator_ext: str,
    ) -> Optional[str]:
        normalized_ext = _normalize_phone(operator_ext)
        if not normalized_ext:
            return None

        name_cache_key = cls._operator_name_cache_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            normalized_ext,
        )
        cached_name = str(await cls._redis_get(name_cache_key) or "").strip()
        if cached_name:
            return cached_name

        user_id = await cls._resolve_user_id_by_operator_ext_best_effort(runtime, normalized_ext)
        if not user_id:
            return None

        user_name_cache_key = cls._user_name_cache_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            user_id,
        )
        cached_user_name = str(await cls._redis_get(user_name_cache_key) or "").strip()
        if cached_user_name:
            await cls._redis_set_with_ttl(
                name_cache_key,
                cached_user_name,
                runtime.state_ttl_sec,
                min_ttl_sec=300,
            )
            return cached_user_name

        cached_name = str(await cls._redis_get(name_cache_key) or "").strip()
        if cached_name:
            return cached_name

        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.rbac.user.get(
                    UserGetRequest(
                        ids=[user_id],
                        active=True,
                        limit=1,
                        offset=0,
                    )
                )
        except Exception as error:
            logger.warning(
                "User/Get by id failed for operator name resolve: ci=%s operator_ext=%s user_id=%s error=%s",
                runtime.connected_integration_id,
                normalized_ext,
                user_id,
                error,
            )
            return None

        if not response.ok:
            logger.warning(
                "User/Get by id rejected for operator name resolve: ci=%s operator_ext=%s user_id=%s payload=%s",
                runtime.connected_integration_id,
                normalized_ext,
                user_id,
                response.result,
            )
            return None

        rows = cls._rows_to_dict_list(response.result)
        if not rows or not isinstance(rows[0], dict):
            return None

        name = cls._extract_user_display_name(rows[0])
        if not name:
            return None

        await cls._redis_set_with_ttl(
            name_cache_key,
            name,
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )
        await cls._redis_set_with_ttl(
            user_name_cache_key,
            name,
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )
        return name

    @classmethod
    async def _resolve_operator_display_name_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[str]:
        operator_ext = cls._operator_phone_from_event_for_runtime(runtime, event)
        if not event.external_call_id:
            if not operator_ext:
                return None
            return await cls._resolve_operator_name_by_operator_ext_best_effort(
                runtime,
                operator_ext,
            )

        call_responsible_name_key = cls._call_responsible_name_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        cached_call_name = str(await cls._redis_get(call_responsible_name_key) or "").strip()
        if cached_call_name:
            return cached_call_name

        call_responsible_id = _to_int(
            await cls._redis_get(
                cls._call_responsible_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    event.external_call_id,
                )
            ),
            None,
        )
        if call_responsible_id and call_responsible_id > 0:
            cached_user_name = str(
                await cls._redis_get(
                    cls._user_name_cache_key(
                        runtime.connected_integration_id,
                        runtime.asterisk_hash,
                        int(call_responsible_id),
                    )
                )
                or ""
            ).strip()
            if cached_user_name:
                await cls._redis_set_with_ttl(
                    call_responsible_name_key,
                    cached_user_name,
                    runtime.state_ttl_sec,
                    min_ttl_sec=300,
                )
                return cached_user_name
            if operator_ext:
                return operator_ext
            return None

        if not operator_ext:
            return None
        return await cls._resolve_operator_name_by_operator_ext_best_effort(
            runtime,
            operator_ext,
        )

    @classmethod
    async def _maybe_assign_responsible_from_operator_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        if not runtime.assign_responsible_by_operator_ext:
            return
        if event.status not in {"answered", "completed"}:
            return
        operator_ext = cls._operator_phone_from_event_for_runtime(runtime, event)
        if not operator_ext:
            logger.info(
                "Asterisk assign skipped (no operator extension on event): ci=%s call_id=%s status=%s raw_event=%s",
                runtime.connected_integration_id,
                event.external_call_id,
                event.status,
                cls._raw_event_type(event.raw_payload or {}) or None,
            )
            return

        call_key = cls._call_responsible_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        already_bound = _to_int(await cls._redis_get(call_key), None)
        if already_bound and already_bound > 0:
            return

        target_user_id = await cls._resolve_user_id_by_operator_ext_best_effort(
            runtime,
            operator_ext,
        )
        if not target_user_id:
            # The operator answered but their extension is not mapped to a CRM user — most
            # often the agent's User.internal_phone is empty or differs from the dialplan
            # extension. Surface it so the operator can be configured.
            logger.warning(
                "Asterisk responsible NOT assigned: operator extension %s is not mapped to "
                "any CRM user (set User.internal_phone = %s). ci=%s call_id=%s ticket_id=%s",
                operator_ext,
                operator_ext,
                runtime.connected_integration_id,
                event.external_call_id,
                lead_ctx.ticket_id,
            )
            return

        # Single-source the attendance policy: when on-shift is required and the
        # operator is off-shift, do NOT bind them here either — otherwise this path
        # would silently overwrite the gated responsible chosen at ticket creation.
        if runtime.assign_responsible_requires_attendance and not await cls._user_is_available_best_effort(
            runtime, target_user_id
        ):
            return

        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.crm.ticket.set_responsible(
                    TicketSetResponsibleRequest(
                        id=int(lead_ctx.ticket_id),
                        responsible_user_id=target_user_id,
                    )
                )
            if not response.ok:
                logger.warning(
                    "Ticket/SetResponsible rejected while binding responsible by operator extension: ci=%s ticket_id=%s operator_ext=%s user_id=%s payload=%s",
                    runtime.connected_integration_id,
                    lead_ctx.ticket_id,
                    operator_ext,
                    target_user_id,
                    response.result,
                )
                return
            await cls._redis_set_with_ttl(
                call_key,
                str(target_user_id),
                runtime.state_ttl_sec,
                min_ttl_sec=300,
            )
            logger.info(
                "Asterisk responsible assigned: ci=%s call_id=%s ticket_id=%s operator_ext=%s user_id=%s",
                runtime.connected_integration_id,
                event.external_call_id,
                lead_ctx.ticket_id,
                operator_ext,
                target_user_id,
            )
            resolved_user_name = str(
                await cls._redis_get(
                    cls._operator_name_cache_key(
                        runtime.connected_integration_id,
                        runtime.asterisk_hash,
                        operator_ext,
                    )
                )
                or ""
            ).strip()
            if resolved_user_name:
                await cls._redis_set_with_ttl(
                    cls._call_responsible_name_key(
                        runtime.connected_integration_id,
                        runtime.asterisk_hash,
                        event.external_call_id,
                    ),
                    resolved_user_name,
                    runtime.state_ttl_sec,
                    min_ttl_sec=300,
                )
            # Move the ticket to WaitingClient right after the responsible is bound — must
            # run BEFORE the close finalizer below so it can never reopen a just-closed
            # ticket in the close-before-assign race. Self-gates on inbound answered.
            await cls._apply_answered_status_policy_best_effort(
                runtime=runtime,
                event=event,
                lead_ctx=lead_ctx,
            )
            # If the call already finished (terminal won the lock before this answered
            # event), apply the parked close now that a responsible is bound. Later events
            # keep retrying via the same finalizer, so a transient failure can't orphan it.
            await cls._finalize_pending_close_best_effort(runtime, event.external_call_id)
        except Exception as error:
            logger.warning(
                "Failed to bind responsible by operator extension: ci=%s ticket_id=%s operator_ext=%s user_id=%s error=%s",
                runtime.connected_integration_id,
                lead_ctx.ticket_id,
                operator_ext,
                target_user_id,
                error,
            )

    @classmethod
    async def _save_mapping(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        ticket_id = _to_int(lead_ctx.ticket_id, None)
        if not ticket_id:
            raise RuntimeError("Cannot save mapping without ticket_id")
        payload = {
            "ticket_id": int(ticket_id),
            "client_id": _to_int(lead_ctx.client_id, None),
            "chat_id": str(lead_ctx.chat_id),
            "asterisk_hash": runtime.asterisk_hash,
            "external_call_id": event.external_call_id,
            "last_event_ts": int(event.event_ts),
        }
        await cls._redis_set_json_with_ttl(
            cls._mapping_by_call_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.external_call_id,
            ),
            payload,
            runtime.state_ttl_sec,
            min_ttl_sec=60,
        )

    @classmethod
    async def _resolve_mapping(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[LeadContext]:
        call_id = cls._normalize_call_id(event.external_call_id)
        if not call_id:
            return None
        payload = cls._parse_cached_json(
            await cls._redis_get(
                cls._mapping_by_call_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    call_id,
                )
            )
        )
        if not payload:
            return None
        ticket_id = _to_int(payload.get("ticket_id"), None)
        if not ticket_id:
            return None
        client_id = _to_int(payload.get("client_id"), None)
        chat_id = str(payload.get("chat_id") or "").strip()
        if not chat_id:
            return None
        return LeadContext(
            ticket_id=int(ticket_id),
            chat_id=chat_id,
            client_id=client_id,
        )

    @classmethod
    async def _resolve_existing_ticket_context(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[LeadContext]:
        mapped_ctx = await cls._resolve_mapping(runtime, event)
        if mapped_ctx:
            return mapped_ctx

        normalized_call_id = cls._normalize_call_id(event.external_call_id)
        if normalized_call_id:
            by_external_call = await cls._find_ticket_by_external_call(
                runtime,
                normalized_call_id,
            )
            if by_external_call:
                await cls._save_mapping(runtime, event, by_external_call)
                return by_external_call
        return None

    @classmethod
    async def _resolve_or_create_client_by_phone(
        cls,
        runtime: RuntimeConfig,
        phone: str,
    ) -> int:
        normalized_phone = _normalize_phone(phone)
        if not normalized_phone:
            raise NonRetryableCallEventError("Client phone is required for Ticket/Add")

        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            get_response = await api.crm.client.get(
                ClientGetRequest(phones=[normalized_phone], limit=1, offset=0)
            )
            rows = (
                get_response.result
                if get_response.ok and isinstance(get_response.result, list)
                else []
            )
            if rows and rows[0] and rows[0].id:
                return int(rows[0].id)

            add_response = await api.crm.client.add(
                ClientAddRequest(
                    phone=normalized_phone,
                    name=normalized_phone,
                    external_id=_external_id(
                        runtime.connected_integration_id,
                        normalized_phone,
                    ),
                )
            )
            add_result = cls._row_to_dict(add_response.result)
            if not add_response.ok:
                error_code = add_result.get("error")
                description = add_result.get("description")
                raise NonRetryableCallEventError(
                    f"Client/Add rejected: error={error_code} description={description}"
                )
            new_id = _to_int(add_result.get("new_id"), None)
            if not new_id:
                raise RuntimeError("Client/Add did not return new_id")
            return int(new_id)

    @classmethod
    async def _find_ticket_by_external_call(
        cls,
        runtime: RuntimeConfig,
        external_call_id: str,
    ) -> Optional[LeadContext]:
        normalized_call_id = cls._normalize_call_id(external_call_id)
        if not normalized_call_id:
            return None
        external_dialog_id = cls._ticket_external_dialog_id(runtime, normalized_call_id)
        if not external_dialog_id:
            return None
        filters = [
            Filter(
                field="external_dialog_id",
                operator=FilterOperator.Equal,
                value=external_dialog_id,
            ),
        ]
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.get(
                TicketGetRequest(
                    channel_ids=[runtime.channel_id],
                    filters=filters,
                    limit=20,
                    offset=0,
                )
            )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        valid = [
            row
            for row in rows
            if row and row.id and row.chat_id and _to_int(row.client_id, None)
        ]
        if not valid:
            return None
        ticket = max(valid, key=lambda row: int(row.id or 0))
        return LeadContext(
            ticket_id=int(ticket.id),
            chat_id=str(ticket.chat_id),
            client_id=int(ticket.client_id),
        )

    @classmethod
    async def _resolve_create_responsible_user_id(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[int]:
        """Pick the responsible user for a freshly created ticket.

        Inbound tickets start with NO responsible — they are assigned only when an
        agent actually answers (call_answered), which keeps "no responsible at hangup
        == missed" meaningful. Outbound is originated by an agent, so the responsible
        is resolved from the originating extension (optionally gated on work shift).
        """
        if event.direction != "outbound":
            return None

        operator_phone = cls._operator_phone_from_event_for_runtime(runtime, event)
        if not (
            runtime.assign_responsible_by_operator_ext
            and operator_phone
            and _is_internal_extension(operator_phone)
        ):
            return runtime.default_responsible_user_id

        user_id = await cls._resolve_user_id_by_operator_ext_best_effort(
            runtime, operator_phone
        )
        if not user_id:
            return runtime.default_responsible_user_id

        if runtime.assign_responsible_requires_attendance and not await cls._user_is_available_best_effort(
            runtime, user_id
        ):
            # Off-shift agent: fall back to the default responsible (spec behaviour).
            return runtime.default_responsible_user_id
        return int(user_id)

    @classmethod
    async def _user_is_available_best_effort(
        cls,
        runtime: RuntimeConfig,
        user_id: int,
    ) -> bool:
        """Return True when the user is checked in, within shift and not on a break.

        Best-effort: an attendance-lookup failure or an empty result does NOT block
        assignment (returns True), so a missing/disabled WorkAttendance module never
        silently strips responsibles.
        """
        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.rbac.work_attendance.status(
                    WorkAttendanceStatusRequest(user_id=int(user_id))
                )
        except Exception as error:
            logger.warning(
                "WorkAttendance/Status failed, treating user as available: ci=%s user=%s error=%s",
                runtime.connected_integration_id,
                user_id,
                error,
            )
            return True

        availability = response.result if response and response.ok else None
        if availability is None:
            return True
        checked_in = availability.is_checked_in
        in_shift = availability.is_in_shift
        on_break = availability.is_on_break
        if checked_in is None and in_shift is None and on_break is None:
            return True
        return bool(checked_in) and bool(in_shift) and not bool(on_break)

    @classmethod
    async def _create_ticket(cls, runtime: RuntimeConfig, event: CallEvent) -> LeadContext:
        normalized_call_id = cls._normalize_call_id(event.external_call_id)
        if not normalized_call_id:
            raise NonRetryableCallEventError("external_call_id is required for Ticket flow")
        external_dialog_id = cls._ticket_external_dialog_id(runtime, normalized_call_id)
        if not external_dialog_id:
            raise NonRetryableCallEventError("external_call_id is required for Ticket flow")
        reused = await cls._find_ticket_by_external_call(
            runtime,
            normalized_call_id,
        )
        if reused:
            return reused

        client_id = await cls._resolve_or_create_client_by_phone(runtime, event.client_phone)

        responsible_user_id = await cls._resolve_create_responsible_user_id(runtime, event)

        payload = TicketAddRequest(
            client_id=client_id,
            channel_id=runtime.channel_id,
            direction=(
                TicketDirectionEnum.Outbound
                if event.direction == "outbound"
                else TicketDirectionEnum.Inbound
            ),
            external_dialog_id=external_dialog_id,
            responsible_user_id=responsible_user_id,
            subject=_safe_subject(
                runtime.subject_template,
                event,
                language=runtime.message_language,
            ),
            description=None,
        )
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            add_response = await api.crm.ticket.add(payload)
            add_result = cls._row_to_dict(add_response.result)
            if not add_response.ok:
                error_code = add_result.get("error")
                description = add_result.get("description")
                raise NonRetryableCallEventError(
                    f"Ticket/Add rejected: error={error_code} description={description}"
                )
            ticket_id = _to_int(add_result.get("new_id"), None)
            if not ticket_id:
                raise RuntimeError("Ticket/Add did not return new_id")

            ticket_response = await api.crm.ticket.get(
                TicketGetRequest(ids=[int(ticket_id)], limit=1, offset=0)
            )
            ticket_rows = (
                ticket_response.result
                if ticket_response.ok and isinstance(ticket_response.result, list)
                else []
            )
            ticket = ticket_rows[0] if ticket_rows else None
            if not ticket or not ticket.id or not ticket.chat_id:
                raise RuntimeError("Ticket/Get did not return ticket/chat pair after Ticket/Add")

            resolved_client_id = _to_int(ticket.client_id, client_id) or client_id
            return LeadContext(
                ticket_id=int(ticket.id),
                chat_id=str(ticket.chat_id),
                client_id=int(resolved_client_id),
            )

    @classmethod
    async def _resolve_or_create_active_ticket(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> LeadContext:
        normalized_call_id = cls._normalize_call_id(event.external_call_id)
        if not normalized_call_id:
            raise RuntimeError("Cannot resolve or create ticket: external_call_id is empty")
        event.external_call_id = normalized_call_id

        normalized_client_phone = _normalize_phone(event.client_phone)
        if not normalized_client_phone:
            raise RuntimeError(
                "Cannot resolve or create ticket: client_phone is empty and mapping is missing"
            )
        event.client_phone = normalized_client_phone

        lead_ctx = await cls._resolve_existing_ticket_context(runtime, event)
        if lead_ctx:
            return lead_ctx

        lock_key = cls._lock_create_ticket_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        lock_token = await cls._acquire_lock(lock_key, AsteriskCrmChannelConfig.LOCK_TTL_SEC)
        if not lock_token:
            await asyncio.sleep(0.25)
            lead_ctx = await cls._resolve_existing_ticket_context(runtime, event)
            if lead_ctx:
                return lead_ctx
            raise RuntimeError("Failed to acquire create-ticket lock")

        try:
            lead_ctx = await cls._resolve_existing_ticket_context(runtime, event)
            if lead_ctx:
                return lead_ctx

            lead_ctx = await cls._create_ticket(runtime, event)
            await cls._save_mapping(runtime, event, lead_ctx)
            return lead_ctx
        finally:
            await cls._release_lock(lock_key, lock_token)

    @classmethod
    def _event_external_message_id(cls, event: CallEvent) -> str:
        # Stable id makes ChatMessage/Add idempotent for repeated AMI events.
        return f"astmsg:{event.asterisk_hash}:{event.external_call_id}:{cls._chat_event_code(event)}"

    @staticmethod
    def _operator_phone_from_event(
        event: CallEvent,
        *,
        excluded_phones: Optional[Set[str]] = None,
    ) -> Optional[str]:
        client_phone = _normalize_phone(event.client_phone)
        excluded = {_normalize_phone(item) for item in (excluded_phones or set())}
        excluded.discard(None)
        preferred: List[Optional[str]]
        if event.direction == "inbound":
            preferred = [event.to_phone, event.from_phone]
        else:
            preferred = [event.from_phone, event.to_phone]

        for candidate in preferred:
            normalized = _normalize_phone(candidate)
            if not normalized:
                continue
            if client_phone and normalized == client_phone:
                continue
            if normalized in excluded:
                continue
            return normalized
        return None

    @classmethod
    def _operator_phone_from_event_for_runtime(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[str]:
        operator_ext = _normalize_phone(event.operator_ext)
        if operator_ext and not cls._is_allowed_did_phone(runtime, operator_ext):
            return operator_ext
        return cls._operator_phone_from_event(
            event,
            excluded_phones=runtime.allowed_did_set,
        )

    @classmethod
    def _render_call_text(
        cls,
        event: CallEvent,
        language: str,
        *,
        operator_name: Optional[str] = None,
        operator_phone: Optional[str] = None,
    ) -> str:
        code = cls._chat_event_code(event)
        client_phone = event.client_phone or "-"
        operator_phone = operator_phone or cls._operator_phone_from_event(event)
        talk_duration = _to_int(event.talk_duration_sec, None)

        if code == "inbound_started":
            return cls._text(language, "inbound_started", client_phone=client_phone)
        if code == "inbound_missed":
            return cls._text(language, "inbound_missed")
        if code == "inbound_answered":
            resolved_operator_name = str(operator_name or "").strip()
            resolved_operator_ext = str(operator_phone or "").strip()
            if resolved_operator_ext and resolved_operator_name:
                resolved_operator_name = f"{resolved_operator_ext} | {resolved_operator_name}"
            elif resolved_operator_ext:
                resolved_operator_name = resolved_operator_ext
            return (
                cls._text(
                    language,
                    "inbound_answered_with_operator",
                    operator_name=resolved_operator_name,
                )
                if resolved_operator_name
                else cls._text(language, "inbound_answered")
            )
        if code == "inbound_completed":
            if talk_duration is not None and talk_duration >= 0:
                talk_duration_hms = _format_duration_hms(talk_duration)
                return cls._text(
                    language,
                    "inbound_completed_with_duration",
                    talk_duration=talk_duration_hms,
                )
            return cls._text(language, "inbound_completed")

        if code == "outbound_started":
            return cls._text(language, "outbound_started", client_phone=client_phone)
        if code == "outbound_failed":
            return cls._text(language, "outbound_failed")
        if code == "outbound_answered":
            return cls._text(language, "outbound_answered")
        if code == "outbound_completed":
            if talk_duration is not None and talk_duration >= 0:
                talk_duration_hms = _format_duration_hms(talk_duration)
                return cls._text(
                    language,
                    "outbound_completed_with_duration",
                    talk_duration=talk_duration_hms,
                )
            return cls._text(language, "outbound_completed")

        return cls._text(language, "generic_event")

    @classmethod
    async def _chat_message_add(
        cls,
        runtime: RuntimeConfig,
        lead_ctx: LeadContext,
        event: CallEvent,
        *,
        text: Optional[str],
        file_ids: Optional[List[int]] = None,
    ) -> str:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=lead_ctx.chat_id,
                    message_type=ChatMessageTypeEnum.System,
                    text=text,
                    file_ids=file_ids or None,
                    external_message_id=cls._event_external_message_id(event),
                ),
            )

        if not response.ok:
            payload = cls._row_to_dict(response.result)
            error_code = _to_int(payload.get("error"), None)
            error_description = str(payload.get("description") or "").strip() or None
            if error_code == AsteriskCrmChannelConfig.CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR:
                raise ChatMessageAddClosedEntityError(error_description)
            raise RuntimeError(
                "ChatMessage/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        result_payload = cls._row_to_dict(response.result)
        message_uuid = str(result_payload.get("new_uuid") or "").strip()
        if not message_uuid:
            message_uuid = str(getattr(response.result, "new_uuid", "") or "").strip()
        if not message_uuid:
            raise RuntimeError("ChatMessage/Add did not return new_uuid")
        return message_uuid

    @classmethod
    async def _post_recording_event(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        language = runtime.message_language
        # Fall back to the recording filename captured from VarSet (MIXMONITOR_FILENAME)
        # when the stop/CDR event itself does not carry the path.
        recording_url = event.recording_url or await cls._resolve_captured_recording_url_best_effort(
            runtime, event
        )
        text_lines = [
            cls._text(language, "recording_ready_title"),
            cls._text(language, "call_id_label", external_call_id=event.external_call_id),
        ]

        if recording_url:
            text_lines.append(
                cls._text(language, "recording_link", recording_url=recording_url)
            )
        else:
            text_lines.append(cls._text(language, "recording_url_missing"))

        await cls._chat_message_add(
            runtime=runtime,
            lead_ctx=lead_ctx,
            event=event,
            text="\n".join(text_lines),
        )

    @classmethod
    async def _resolve_captured_recording_url_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[str]:
        if not event.external_call_id:
            return None
        try:
            filename = await cls._redis_get(
                cls._recording_file_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    event.external_call_id,
                )
            )
        except Exception:
            return None
        return _resolve_recording_url(runtime.recording_base_url, filename)

    @classmethod
    async def _post_recording_sidecar_event_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        if event.status == "recording_ready":
            return
        if not event.external_call_id:
            return

        progress_key = cls._call_progress_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        cached = cls._parse_cached_json(await cls._redis_get(progress_key)) or {}
        if bool(cached.get("recording_posted")):
            return

        recording_url = event.recording_url
        event_status = str(event.status or "").strip().lower()
        if (
            not recording_url
            and event_status in AsteriskCrmChannelConfig.CLOSE_ON_CALL_END_STATUSES
        ):
            recording_url = await cls._resolve_captured_recording_url_best_effort(
                runtime, event
            )
        if not recording_url:
            return

        raw_payload = dict(event.raw_payload or {})
        raw_payload["recording_source_event"] = cls._raw_event_type(raw_payload) or None
        raw_payload["recording_source"] = (
            "event_payload" if event.recording_url else "captured_filename_on_call_end"
        )
        recording_event = CallEvent(
            event_id=hashlib.md5(
                f"{event.event_id}:recording_ready".encode("utf-8")
            ).hexdigest(),
            external_call_id=event.external_call_id,
            asterisk_hash=event.asterisk_hash,
            direction=event.direction,
            from_phone=event.from_phone,
            to_phone=event.to_phone,
            client_phone=event.client_phone,
            status="recording_ready",
            event_ts=event.event_ts,
            talk_duration_sec=event.talk_duration_sec,
            recording_url=recording_url,
            operator_ext=event.operator_ext,
            raw_payload=raw_payload,
        )

        try:
            await cls._post_recording_event(runtime, recording_event, lead_ctx)
        except ChatMessageAddClosedEntityError as error:
            await cls._store_late_closed_event_state(
                runtime=runtime,
                event=recording_event,
                lead_ctx=lead_ctx,
                reason=error.description,
            )
            return
        except Exception as error:
            logger.warning(
                "Asterisk recording sidecar post failed: ci=%s call_id=%s event_id=%s error=%s",
                runtime.connected_integration_id,
                event.external_call_id,
                event.event_id,
                error,
            )
            return

        cached["recording_posted"] = True
        cached["updated_at"] = _now_ts()
        await cls._redis_set_json_with_ttl(
            progress_key,
            cached,
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )

    @classmethod
    async def _store_late_closed_event_state(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
        reason: Optional[str],
    ) -> None:
        payload = {
            "status": "late_event_closed_ticket",
            "connected_integration_id": runtime.connected_integration_id,
            "asterisk_hash": runtime.asterisk_hash,
            "external_call_id": event.external_call_id,
            "event_id": event.event_id,
            "event_status": event.status,
            "recording_url": event.recording_url,
            "event_ts": event.event_ts,
            "lead_id": lead_ctx.lead_id,
            "chat_id": lead_ctx.chat_id,
            "reason": reason,
            "stored_at": _now_ts(),
            "raw_payload": event.raw_payload,
        }
        await cls._redis_set_json_with_ttl(
            cls._late_closed_event_state_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.external_call_id,
            ),
            payload,
            runtime.state_ttl_sec,
            min_ttl_sec=60,
        )

    @classmethod
    async def _write_event_with_1220_policy(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> Tuple[LeadContext, bool]:
        try:
            if event.status == "recording_ready":
                await cls._post_recording_event(runtime, event, lead_ctx)
            elif runtime.post_status_messages:
                operator_name: Optional[str] = None
                if cls._chat_event_code(event) == "inbound_answered":
                    operator_name = await cls._resolve_operator_display_name_best_effort(
                        runtime,
                        event,
                    )
                await cls._chat_message_add(
                    runtime=runtime,
                    lead_ctx=lead_ctx,
                    event=event,
                    text=cls._render_call_text(
                        event,
                        runtime.message_language,
                        operator_name=operator_name,
                        operator_phone=cls._operator_phone_from_event_for_runtime(
                            runtime,
                            event,
                        ),
                    ),
                )
            else:
                # Minimal mode: only the CRM actions (create/assign/close) and the recording
                # are surfaced; per-stage status messages are suppressed. Returning False
                # keeps the answered WaitingClient transition off as well.
                return lead_ctx, False
            return lead_ctx, True
        except ChatMessageAddClosedEntityError as error:
            # Keep 1 call = 1 ticket. If ticket is already closed, never reopen/create new.
            await cls._store_late_closed_event_state(
                runtime=runtime,
                event=event,
                lead_ctx=lead_ctx,
                reason=error.description,
            )
            return lead_ctx, False

    @classmethod
    async def _apply_answered_status_policy_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        if lead_ctx.ticket_id <= 0:
            return
        if str(event.status or "").strip().lower() != "answered":
            return
        if cls._chat_event_code(event) != "inbound_answered":
            return

        try:
            async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
                response = await api.crm.ticket.set_status(
                    TicketSetStatusRequest(
                        id=int(lead_ctx.ticket_id),
                        status=TicketStatusEnum.WaitingClient,
                    )
                )
            if response.ok:
                return
            payload = cls._row_to_dict(response.result)
            logger.warning(
                "Ticket/SetStatus WaitingClient rejected after answered call: ci=%s ticket_id=%s call_id=%s error=%s description=%s",
                runtime.connected_integration_id,
                lead_ctx.ticket_id,
                event.external_call_id,
                payload.get("error"),
                payload.get("description"),
            )
        except Exception as error:
            logger.warning(
                "Ticket/SetStatus WaitingClient failed after answered call: ci=%s ticket_id=%s call_id=%s error=%s",
                runtime.connected_integration_id,
                lead_ctx.ticket_id,
                event.external_call_id,
                error,
            )

    @classmethod
    async def _close_ticket_best_effort(
        cls,
        runtime: RuntimeConfig,
        ticket_id: int,
        resolved_date: Optional[int],
    ) -> bool:
        if int(ticket_id or 0) <= 0:
            return False
        try:
            async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
                response = await api.crm.ticket.close(
                    TicketCloseRequest(
                        id=int(ticket_id),
                        resolved_date=resolved_date,
                    )
                )
            if response.ok:
                return True
            payload = cls._row_to_dict(response.result)
            logger.warning(
                "Ticket/Close rejected: ci=%s ticket_id=%s error=%s description=%s",
                runtime.connected_integration_id,
                ticket_id,
                payload.get("error"),
                payload.get("description"),
            )
        except Exception as error:
            logger.warning(
                "Ticket close failed: ci=%s ticket_id=%s error=%s",
                runtime.connected_integration_id,
                ticket_id,
                error,
            )
        return False

    @classmethod
    async def _finalize_pending_close_best_effort(
        cls,
        runtime: RuntimeConfig,
        external_call_id: Optional[str],
    ) -> None:
        """Apply a close that a terminal parked but could not yet perform.

        Safe to call for EVERY event of a call (including deduped/suppressed ones): it
        no-ops unless a close is pending AND a responsible is now bound. This is the
        self-healing retry for the close-before-assign race — a single transient close
        failure can no longer orphan a genuinely answered ticket, because the call's later
        events keep retrying until the close succeeds.
        """
        if not runtime.close_ticket_on_call_end:
            return
        call_id = cls._normalize_call_id(external_call_id)
        if not call_id:
            return
        pending_key = cls._call_close_pending_key(
            runtime.connected_integration_id, runtime.asterisk_hash, call_id
        )
        pending = await cls._redis_get(pending_key)
        if pending is None:
            return
        responsible = _to_int(
            await cls._redis_get(
                cls._call_responsible_key(
                    runtime.connected_integration_id, runtime.asterisk_hash, call_id
                )
            ),
            None,
        )
        if not (responsible and responsible > 0):
            # Not answered yet — leave the close parked (missed inbound stays OPEN).
            return
        mapping = cls._parse_cached_json(
            await cls._redis_get(
                cls._mapping_by_call_key(
                    runtime.connected_integration_id, runtime.asterisk_hash, call_id
                )
            )
        )
        ticket_id = _to_int(mapping.get("ticket_id"), None) if mapping else None
        if not ticket_id:
            return
        closed = await cls._close_ticket_best_effort(
            runtime, int(ticket_id), _to_int(pending, None)
        )
        if closed:
            await cls._redis_delete(pending_key)

    @classmethod
    async def _apply_status_policy_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        if not runtime.close_ticket_on_call_end:
            return
        if lead_ctx.ticket_id <= 0:
            return
        status = str(event.status or "").strip().lower()
        if status not in AsteriskCrmChannelConfig.CLOSE_ON_CALL_END_STATUSES:
            return
        resolved_date = int(event.event_ts) if int(event.event_ts or 0) > 0 else None
        # Close only answered calls: a ticket with no responsible was never picked up by an
        # agent (missed inbound) and must stay OPEN for callback.
        has_responsible = await cls._ticket_has_responsible_before_close(
            runtime=runtime,
            ticket_id=int(lead_ctx.ticket_id),
        )
        if not has_responsible:
            # The terminal can win the per-call lock before the answered/assign event under
            # cross-worker concurrency. Park the close so the assign path performs it once a
            # responsible is bound; a genuinely missed call never binds one, so the key just
            # expires and the ticket stays OPEN.
            if event.external_call_id:
                await cls._redis_set_with_ttl(
                    cls._call_close_pending_key(
                        runtime.connected_integration_id,
                        runtime.asterisk_hash,
                        event.external_call_id,
                    ),
                    str(resolved_date if resolved_date is not None else _now_ts()),
                    runtime.state_ttl_sec,
                    min_ttl_sec=300,
                )
            return

        await cls._close_ticket_best_effort(runtime, int(lead_ctx.ticket_id), resolved_date)
        if event.external_call_id:
            await cls._redis_delete(
                cls._call_close_pending_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    event.external_call_id,
                )
            )

    @classmethod
    async def _ticket_has_responsible_before_close(
        cls,
        runtime: RuntimeConfig,
        ticket_id: int,
    ) -> bool:
        if ticket_id <= 0:
            return False
        try:
            async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
                response = await api.crm.ticket.get(
                    TicketGetRequest(
                        ids=[int(ticket_id)],
                        limit=1,
                        offset=0,
                    )
                )
            rows = response.result if response.ok and isinstance(response.result, list) else []
            ticket = rows[0] if rows else None
            if not ticket:
                return False
            return bool(_to_int(getattr(ticket, "responsible_user_id", None), None))
        except Exception as error:
            logger.warning(
                "Ticket/Get failed while checking responsible before close: ci=%s ticket_id=%s error=%s",
                runtime.connected_integration_id,
                ticket_id,
                error,
            )
            return False

    @staticmethod
    def _extract_events_from_body(body: Any) -> List[Dict[str, Any]]:
        if isinstance(body, list):
            return [row for row in body if isinstance(row, dict)]
        if isinstance(body, dict):
            if isinstance(body.get("events"), list):
                return [row for row in body.get("events", []) if isinstance(row, dict)]
            if isinstance(body.get("event"), dict):
                return [body.get("event")]
            return [body]
        return []

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        lock_key = self._connect_lock_key(self.connected_integration_id)
        lock_token = await self._acquire_lock_wait(lock_key, AsteriskCrmChannelConfig.LOCK_TTL_SEC)
        if not lock_token:
            return self._error_response(1002, "connect is already running").dict()
        try:
            try:
                await self._ensure_connected_integration_active(
                    self.connected_integration_id,
                    force_refresh=True,
                )
                runtime = await self._load_runtime(self.connected_integration_id)
            except ConnectedIntegrationInactiveError as error:
                return self._error_response(1004, str(error)).dict()
            await self._mark_ci_active(self.connected_integration_id)
            await self._ensure_stream_workers()
            await self._ensure_ami_worker(runtime)
            return {
                "status": "connected",
                "mode": "ami_with_external_fallback",
                "instance_id": _INSTANCE_ID,
            }
        except Exception:
            await self._mark_ci_inactive(self.connected_integration_id)
            raise
        finally:
            await self._release_lock(lock_key, lock_token)

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._mark_ci_inactive(self.connected_integration_id)
        await self._stop_ami_worker(self.connected_integration_id)
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        lock_key = self._settings_fetch_lock_key(self.connected_integration_id)
        lock_token = await self._acquire_lock_wait(
            lock_key,
            AsteriskCrmChannelConfig.SETTINGS_LOCK_TTL_SEC,
            wait_seconds=AsteriskCrmChannelConfig.SETTINGS_LOCK_WAIT_SEC,
        )
        if not lock_token:
            return self._error_response(1002, "settings update is already running").dict()
        try:
            await self._redis_delete(
                self._settings_cache_key(self.connected_integration_id),
                self._settings_stale_cache_key(self.connected_integration_id),
                self._ci_active_cache_key(self.connected_integration_id),
            )
            _CI_ACTIVE_MEMORY_CACHE.pop(str(self.connected_integration_id or "").strip(), None)
            _SETTINGS_LOCAL_CACHE.pop(self._settings_cache_key(self.connected_integration_id), None)
            _SETTINGS_LOCAL_CACHE.pop(self._settings_stale_cache_key(self.connected_integration_id), None)
            async with _RUNTIME_LOCAL_LOCK:
                _RUNTIME_LOCAL_CACHE.pop(str(self.connected_integration_id or "").strip(), None)
        finally:
            await self._release_lock(lock_key, lock_token)
        return {"status": "settings updated"}

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        # Events are consumed via AMI worker and/or /external endpoint; webhook endpoint is unused.
        return {"status": "ignored", "action": action, "has_data": bool(data)}

    async def handle_external(self, envelope: Dict[str, Any]) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not _redis_enabled():
            return JSONResponse(
                status_code=503,
                content=self._error_response(
                    1001, "Redis is required for this integration"
                ).dict(),
            )

        try:
            runtime = await self._load_runtime(self.connected_integration_id)
        except ConnectedIntegrationInactiveError:
            return {"status": "ignored", "reason": "connected_integration_inactive"}

        raw_events = self._extract_events_from_body(envelope.get("body"))
        if not raw_events:
            return self._error_response(400, "Invalid Asterisk payload").dict()

        accepted = 0
        ignored = 0
        for raw_event in raw_events:
            normalized = self._normalize_external_event(runtime, raw_event)
            if not normalized:
                ignored += 1
                continue

            queued = await self._enqueue_runtime_event(runtime, normalized)
            if queued:
                accepted += 1
            else:
                ignored += 1

        await self._ensure_stream_workers()
        return {
            "status": "accepted" if accepted else "ignored",
            "accepted": accepted,
            "ignored": ignored,
        }
