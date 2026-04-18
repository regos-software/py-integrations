from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import re
import socket
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from redis.exceptions import ResponseError
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
    ChatMessageTypeEnum,
)
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.client import ClientAddRequest, ClientGetRequest
from schemas.api.crm.lead import (
    Lead,
    LeadGetRequest,
    LeadSetResponsibleRequest,
    LeadStatusEnum,
)
from schemas.api.crm.ticket import (
    TicketAddRequest,
    TicketDirectionEnum,
    TicketGetRequest,
    TicketSetResponsibleRequest,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("asterisk_crm_channel")


class AsteriskCrmChannelConfig:
    INTEGRATION_KEY = "asterisk_crm_channel"
    REDIS_PREFIX = "clients:asterisk_crm_channel:"
    DEFAULT_AMI_PORT = 5038

    SETTINGS_TTL = max(int(app_settings.redis_cache_ttl or 60), 60)
    CI_ACTIVE_MEMORY_TTL_SEC = 5
    DEFAULT_DEDUPE_TTL_SEC = 6 * 60 * 60
    DEFAULT_STATE_TTL_SEC = 6 * 60 * 60
    LEAD_STATE_CACHE_TTL_SEC = 5 * 60
    LEAD_LOOKUP_MISS_TTL_SEC = 30

    STREAM_GROUP = "asterisk_crm_channel_workers"
    STREAM_MAXLEN = 10000
    STREAM_BATCH_SIZE = 20
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_MAX_RETRIES = 5
    STREAM_EVENT_REORDER_WINDOW_SEC = 3
    STREAM_MAX_FUTURE_SKEW_SEC = 30

    LOCK_TTL_SEC = 30
    PROCESSING_LOCK_TTL_SEC = 120
    HEARTBEAT_TTL_SEC = 30
    AMI_CONNECT_TIMEOUT_SEC = 30
    AMI_PING_INTERVAL_SEC = 20
    AMI_RECONNECT_MIN_SEC = 1
    AMI_RECONNECT_MAX_SEC = 30
    AMI_OWNER_LOCK_TTL_SEC = 30
    AMI_OWNER_LOCK_REFRESH_SEC = 10
    AMI_OWNER_WAIT_SEC = 2
    INBOUND_FINALIZE_DELAY_SEC = 7

    CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR = 1220

    ACTIVE_LEAD_STATUSES = (
        LeadStatusEnum.New,
        LeadStatusEnum.InProgress,
        LeadStatusEnum.WaitingClient,
    )
    CALL_STATE_STATUSES = {
        "started",
        "ringing",
        "answered",
        "missed",
        "completed",
        "failed",
    }
    EVENT_STATUSES = CALL_STATE_STATUSES | {"recording_ready"}


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    asterisk_hash: str
    ami_host: str
    ami_port: int
    ami_user: str
    ami_password: str
    pipeline_id: int
    channel_id: int
    default_responsible_user_id: Optional[int]
    lead_subject_template: str
    allowed_did_set: set[str]
    recording_base_url: Optional[str]
    lead_dedupe_ttl_sec: int
    state_ttl_sec: int
    default_country_code: str
    assign_responsible_by_operator_ext: bool
    find_active_lead_by_phone: bool
    message_language: str


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
    lead_id: int
    chat_id: str
    client_id: Optional[int] = None
    ticket_id: Optional[int] = None


class ChatMessageAddClosedEntityError(RuntimeError):
    def __init__(self, description: Optional[str] = None) -> None:
        self.description = str(description or "").strip() or None
        text = "ChatMessage/Add rejected for closed linked entity"
        if self.description:
            text = f"{text}: {self.description}"
        super().__init__(text)


class ConnectedIntegrationInactiveError(RuntimeError):
    pass


class DeferredCallEvent(RuntimeError):
    def __init__(self, reason: str, delay_sec: int = 1) -> None:
        self.reason = str(reason or "").strip() or "deferred"
        self.delay_sec = max(int(delay_sec), 1)
        super().__init__(f"Deferred call event: {self.reason} (delay={self.delay_sec}s)")


class NonRetryableCallEventError(RuntimeError):
    pass


_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[str, asyncio.Task] = {}
_AMI_TASKS: Dict[str, asyncio.Task] = {}
_INSTANCE_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
_CACHE_UNSET = object()
_CI_ACTIVE_MEMORY_CACHE: Dict[str, Tuple[bool, int]] = {}
_CI_ACTIVE_LOCKS: Dict[str, asyncio.Lock] = {}


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> Any:
    return json.loads(raw)


def _redis_enabled() -> bool:
    return bool(app_settings.redis_enabled and redis_client is not None)


def _is_redis_nogroup_error(error: Exception) -> bool:
    if isinstance(error, ResponseError):
        return "NOGROUP" in str(error).upper()
    return "NOGROUP" in str(error or "").upper()


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


def _external_id(asterisk_hash: str, normalized_phone: str) -> str:
    return f"ast:{asterisk_hash}:{normalized_phone}"


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
    subject_template = str(template or "").strip() or "Call {direction} {from_phone}"
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


def _recording_name_from_url(url: str, external_call_id: str) -> Tuple[str, str]:
    parsed = urlparse(url)
    file_name = os.path.basename(parsed.path or "").strip()
    if not file_name:
        file_name = f"recording_{external_call_id}.mp3"
    if "." not in file_name:
        file_name = f"{file_name}.mp3"
    file_name = file_name[:200]
    extension = file_name.rsplit(".", 1)[-1].strip().lower()[:10] or "mp3"
    return file_name, extension


def _resolve_recording_url(base_url: Optional[str], raw_url: Optional[str]) -> Optional[str]:
    url = str(raw_url or "").strip()
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    base = str(base_url or "").strip()
    if not base:
        return url
    return urljoin(base.rstrip("/") + "/", url.lstrip("/"))


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

def _status_from_direction_event(direction: str, status: str) -> Optional[LeadStatusEnum]:
    if direction == "inbound" and status in {"started", "ringing", "answered"}:
        return LeadStatusEnum.InProgress
    if direction == "outbound" and status in {"started", "ringing"}:
        return LeadStatusEnum.InProgress
    if direction == "outbound" and status == "answered":
        return LeadStatusEnum.InProgress
    return None


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
    def _settings_cache_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key("settings", connected_integration_id)

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
    def _stream_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "stream",
            "asterisk_in",
            connected_integration_id,
        )

    @staticmethod
    def _dlq_stream_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key("stream", "dlq", connected_integration_id)

    @staticmethod
    def _worker_heartbeat_key(connected_integration_id: str) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "worker",
            "heartbeat",
            connected_integration_id,
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
    def _lock_create_lead_key(
        connected_integration_id: str,
        asterisk_hash: str,
        normalized_phone: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lock",
            "create_lead",
            connected_integration_id,
            asterisk_hash,
            normalized_phone,
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
    def _mapping_by_phone_key(
        connected_integration_id: str,
        asterisk_hash: str,
        normalized_phone: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "mapping",
            "by_phone",
            connected_integration_id,
            asterisk_hash,
            normalized_phone,
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
    def _late_recording_state_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "late_recording",
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
    def _lead_state_cache_key(
        connected_integration_id: str,
        lead_id: int,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lead_state",
            connected_integration_id,
            int(lead_id),
        )

    @staticmethod
    def _lead_lookup_miss_phone_key(
        connected_integration_id: str,
        asterisk_hash: str,
        normalized_phone: str,
    ) -> str:
        return AsteriskCrmChannelIntegration._redis_key(
            "lead_lookup_miss",
            "phone",
            connected_integration_id,
            asterisk_hash,
            normalized_phone,
        )

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set_with_ttl(
        key: str,
        value: str,
        ttl_sec: int,
        *,
        min_ttl_sec: int,
    ) -> None:
        if not _redis_enabled():
            return
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        await redis_client.set(key, value, ex=ttl)

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
        if not _redis_enabled():
            return False
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        result = await redis_client.set(key, value, ex=ttl, nx=True)
        return bool(result)

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if not rows:
            return
        await redis_client.delete(*rows)

    @classmethod
    async def _mark_ci_active(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        await redis_client.sadd(cls._active_ci_ids_key(), ci)

    @classmethod
    async def _mark_ci_inactive(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        ci = str(connected_integration_id or "").strip()
        if not ci:
            return
        await redis_client.srem(cls._active_ci_ids_key(), ci)

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

    @staticmethod
    async def _release_lock(lock_key: str, token: Optional[str]) -> None:
        if not _redis_enabled():
            return
        if not lock_key or not token:
            return
        script = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""
        try:
            await redis_client.eval(script, 1, lock_key, token)
        except Exception:
            current = await redis_client.get(lock_key)
            if current == token:
                await redis_client.delete(lock_key)

    @classmethod
    async def _refresh_lock(cls, lock_key: str, token: Optional[str], ttl_sec: int) -> bool:
        if not _redis_enabled():
            return False
        if not lock_key or not token:
            return False
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
            result = await redis_client.eval(script, 1, lock_key, token, str(ttl))
            return bool(int(result or 0))
        except Exception:
            try:
                current = await redis_client.get(lock_key)
                if current != token:
                    return False
                return bool(await redis_client.expire(lock_key, ttl))
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

    @staticmethod
    def _normalize_lead_status(value: Any) -> Optional[LeadStatusEnum]:
        if isinstance(value, LeadStatusEnum):
            return value
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return LeadStatusEnum(text)
        except ValueError:
            return None

    @classmethod
    async def _get_lead_state_cache(
        cls,
        connected_integration_id: str,
        lead_id: Optional[int],
    ) -> Dict[str, Any]:
        resolved_lead_id = _to_int(lead_id, None)
        if not resolved_lead_id:
            return {}
        payload = cls._parse_cached_json(
            await cls._redis_get(
                cls._lead_state_cache_key(connected_integration_id, int(resolved_lead_id))
            )
        )
        return payload or {}

    @classmethod
    async def _update_lead_state_cache(
        cls,
        connected_integration_id: str,
        lead_id: Optional[int],
        *,
        status: Any = _CACHE_UNSET,
        responsible_user_id: Any = _CACHE_UNSET,
    ) -> None:
        resolved_lead_id = _to_int(lead_id, None)
        if not resolved_lead_id:
            return
        key = cls._lead_state_cache_key(connected_integration_id, int(resolved_lead_id))
        cached = cls._parse_cached_json(await cls._redis_get(key)) or {}

        if status is not _CACHE_UNSET:
            normalized_status = cls._normalize_lead_status(status)
            if normalized_status is not None:
                cached["status"] = normalized_status.value
            else:
                raw_status = str(status or "").strip()
                cached["status"] = raw_status or None

        if responsible_user_id is not _CACHE_UNSET:
            resolved_user_id = _to_int(responsible_user_id, None)
            cached["responsible_user_id"] = (
                int(resolved_user_id) if resolved_user_id and resolved_user_id > 0 else None
            )

        cached["updated_at"] = _now_ts()
        await cls._redis_set_json_with_ttl(
            key,
            cached,
            AsteriskCrmChannelConfig.LEAD_STATE_CACHE_TTL_SEC,
            min_ttl_sec=60,
        )

    @classmethod
    async def _cache_lead_snapshot(
        cls,
        connected_integration_id: str,
        lead: Optional[Lead],
    ) -> None:
        if not lead or not getattr(lead, "id", None):
            return
        await cls._update_lead_state_cache(
            connected_integration_id=connected_integration_id,
            lead_id=_to_int(getattr(lead, "id", None), None),
            status=getattr(lead, "status", None),
            responsible_user_id=getattr(lead, "responsible_user_id", None),
        )

    @staticmethod
    async def _get_http_client() -> httpx.AsyncClient:
        global _HTTP_CLIENT
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.AsyncClient(timeout=90)
        return _HTTP_CLIENT

    @staticmethod
    def _extract_ci_active_flag(payload: Any) -> Optional[bool]:
        if isinstance(payload, dict):
            for key in ("is_active", "isActive"):
                if key in payload:
                    return _to_bool(payload.get(key), True)
            for nested_key in ("connected_integration", "integration", "item", "data", "result"):
                nested = payload.get(nested_key)
                if nested is None:
                    continue
                nested_value = AsteriskCrmChannelIntegration._extract_ci_active_flag(nested)
                if nested_value is not None:
                    return nested_value
            return None
        if isinstance(payload, list):
            for row in payload:
                nested_value = AsteriskCrmChannelIntegration._extract_ci_active_flag(row)
                if nested_value is not None:
                    return nested_value
            return None
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

        cache_key = cls._ci_active_cache_key(ci)
        if not force_refresh:
            memory_cached = cls._ci_active_memory_cache_get(ci)
            if memory_cached is not None:
                return memory_cached
            if _redis_enabled():
                cached = str(await redis_client.get(cache_key) or "").strip().lower()
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
                if _redis_enabled():
                    cached = str(await redis_client.get(cache_key) or "").strip().lower()
                    if cached in {"1", "0"}:
                        detected = cached == "1"
                        cls._ci_active_memory_cache_set(ci, detected)
                        return detected

            request_payloads: Tuple[Dict[str, Any], ...] = (
                {},
                {"connected_integration_id": ci, "limit": 1, "offset": 0},
            )
            detected: Optional[bool] = None
            last_error: Optional[Exception] = None
            for payload in request_payloads:
                try:
                    async with RegosAPI(connected_integration_id=ci) as api:
                        response = await api.call(
                            "ConnectedIntegration/Get",
                            payload,
                            APIBaseResponse[Any],
                        )
                    if not response.ok:
                        continue
                    detected = cls._extract_ci_active_flag(response.result)
                    if detected is not None:
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
                        break
                except Exception as error:
                    last_error = error

            if detected is None:
                if last_error is not None:
                    logger.warning(
                        "ConnectedIntegration/Get failed for active check, fallback active=true: ci=%s error=%s",
                        ci,
                        last_error,
                    )
                detected = True

            if _redis_enabled():
                await redis_client.set(
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
    async def _fetch_settings_map(connected_integration_id: str) -> Dict[str, str]:
        cache_key = AsteriskCrmChannelIntegration._settings_cache_key(
            connected_integration_id
        )
        if _redis_enabled():
            cached = await redis_client.get(cache_key)
            if cached:
                try:
                    loaded = _json_loads(cached)
                    if isinstance(loaded, dict):
                        return {str(k).lower(): str(v or "") for k, v in loaded.items()}
                except Exception:
                    pass

        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                response = await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(
                        connected_integration_id=connected_integration_id,
                    )
                )
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code in {401, 403, 404}:
                is_active = await AsteriskCrmChannelIntegration._is_connected_integration_active(
                    connected_integration_id,
                    force_refresh=True,
                )
                if not is_active or status_code in {401, 403}:
                    raise ConnectedIntegrationInactiveError(
                        f"ConnectedIntegration {connected_integration_id} is inactive "
                        f"(settings unavailable, status={status_code})"
                    ) from error
            raise
        settings_map = {
            str(item.key or "").strip().lower(): str(item.value or "")
            for item in (response.result or [])
            if item and item.key
        }

        if _redis_enabled():
            await redis_client.set(
                cache_key,
                _json_dumps(settings_map),
                ex=AsteriskCrmChannelConfig.SETTINGS_TTL,
            )
        return settings_map

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
        await AsteriskCrmChannelIntegration._ensure_connected_integration_active(
            connected_integration_id
        )
        settings_map = await AsteriskCrmChannelIntegration._fetch_settings_map(
            connected_integration_id
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

        pipeline_id = _to_int(settings_map.get("asterisk_pipeline_id"), None)
        channel_id = _to_int(settings_map.get("asterisk_channel_id"), None)
        if not ami_user:
            raise ValueError("asterisk_ami_user is required")
        if not ami_password:
            raise ValueError("asterisk_ami_password is required")
        if not pipeline_id or pipeline_id <= 0:
            raise ValueError("asterisk_pipeline_id must be > 0")
        if not channel_id or channel_id <= 0:
            raise ValueError("asterisk_channel_id must be > 0")

        default_responsible_user_id = _to_int(
            settings_map.get("asterisk_default_responsible_user_id"),
            None,
        )
        if default_responsible_user_id is not None and default_responsible_user_id <= 0:
            raise ValueError("asterisk_default_responsible_user_id must be > 0")
        find_active_lead_by_phone_raw = settings_map.get("asterisk_find_active_lead_by_phone")
        if find_active_lead_by_phone_raw is None:
            find_active_lead_by_phone_raw = settings_map.get(
                "asterisk_search_active_lead_by_phone"
            )

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            asterisk_hash=_hash_scope_key(connected_integration_id),
            ami_host=ami_host,
            ami_port=ami_port,
            ami_user=ami_user,
            ami_password=ami_password,
            pipeline_id=pipeline_id,
            channel_id=channel_id,
            default_responsible_user_id=default_responsible_user_id,
            lead_subject_template=(
                str(settings_map.get("asterisk_lead_subject_template") or "").strip()
                or "Call {direction} {from_phone}"
            ),
            allowed_did_set=AsteriskCrmChannelIntegration._parse_allowed_did_set(
                settings_map.get("asterisk_allowed_did_list"),
                default_country_code,
            ),
            recording_base_url=(
                str(settings_map.get("asterisk_recording_base_url") or "").strip() or None
            ),
            lead_dedupe_ttl_sec=max(
                _to_int(
                    settings_map.get("lead_dedupe_ttl_sec"),
                    AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                )
                or AsteriskCrmChannelConfig.DEFAULT_DEDUPE_TTL_SEC,
                60,
            ),
            state_ttl_sec=max(
                _to_int(
                    settings_map.get("state_ttl_sec"),
                    AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                )
                or AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
                60,
            ),
            default_country_code=default_country_code,
            assign_responsible_by_operator_ext=_to_bool(
                settings_map.get("asterisk_assign_responsible_by_operator_ext"),
                True,
            ),
            find_active_lead_by_phone=_to_bool(
                find_active_lead_by_phone_raw,
                True,
            ),
            message_language=_normalize_message_language(
                settings_map.get("asterisk_message_language"),
                "ru",
            ),
        )

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
            "hangup": "completed",
            "stasisend": "completed",
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
        if not client_phone:
            client_phone = from_phone if direction == "inbound" else to_phone
        if not client_phone and status != "recording_ready":
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
            cls._payload_pick(
                source,
                "recording_url",
                "recording.url",
                "recording.file",
                "file_url",
                "recordingfile",
                "recording_file",
                "mixmonitorfilename",
                "filename",
                "file",
            ),
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
            "raw_payload": event.raw_payload,
        }

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
        if status != "recording_ready" and not client_phone:
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
    def _derive_status_from_ami(cls, payload: Dict[str, Any]) -> Optional[str]:
        event_type = str(payload.get("event") or payload.get("event_name") or "").strip().lower()
        if not event_type:
            return None

        if event_type in {"newchannel", "newcallerid", "newexten"}:
            # Too noisy for CRM chat; keep only meaningful call stages.
            return None
        if event_type in {"dialbegin", "dialstate"}:
            return "ringing"
        if event_type == "agentcalled":
            return "ringing"
        if event_type == "agentconnect":
            return "answered"
        if event_type == "agentcomplete":
            return "completed"
        if event_type == "newstate":
            normalized = cls._normalize_status(
                cls._payload_pick(payload, "channelstatedesc", "state", "channelstate")
            )
            # "Up" in Newstate is frequently emitted by local/queue legs and can be noisy.
            if normalized == "answered":
                return None
            return normalized
        if event_type in {"bridgeenter", "bridgecreate", "bridge", "link"}:
            # Bridge lifecycle events are too noisy for reliable "answered" signal.
            return None
        if event_type in {"mixmonitorstop", "monitorstop"}:
            return "recording_ready"
        if event_type == "dialend":
            dial_status = str(cls._payload_pick(payload, "dialstatus") or "").strip().lower()
            if dial_status in {"answer", "answered"}:
                return "answered"
            # Per-leg DialEnd noanswer/cancel frequently appears in queue fan-out
            # while the same linked call is later answered by another operator.
            # Treat it as non-final noise to avoid false "missed" in CRM.
            if dial_status in {"noanswer", "no_answer", "cancel", "cancelled", "canceled"}:
                return None
            if dial_status in {
                "busy",
                "congestion",
                "chanunavail",
                "failed",
                "invalidargs",
            }:
                return "failed"
            return "completed"
        if event_type in {"hangup", "hanguprequest", "softhanguprequest", "unlink", "bridgeleave"}:
            cause_text = str(
                cls._payload_pick(payload, "cause_txt", "cause-txt", "causetxt") or ""
            ).strip().lower()
            cause = _to_int(cls._payload_pick(payload, "cause"), None)
            # Same reason as DialEnd: per-leg noanswer hangups are not final call result.
            if cause_text in {"noanswer", "no_answer", "no answer"} or cause in {19}:
                return None
            if cause_text in {"busy", "congestion", "cancelled", "canceled", "failed"} or cause in {
                17,
                34,
                38,
                41,
                42,
                44,
                47,
                58,
            }:
                return "failed"
            return "completed"
        if event_type == "cdr":
            recording_value = cls._payload_pick(
                payload,
                "recording_url",
                "recordingfile",
                "recording_file",
                "mixmonitorfilename",
                "mixmonitor_filename",
                "monitorfilename",
                "filename",
                "file",
            )
            if str(recording_value or "").strip():
                # Many PBX setups publish recording path in CDR instead of MixMonitorStop.
                return "recording_ready"
            disposition = str(cls._payload_pick(payload, "disposition") or "").strip().lower()
            billsec = _to_int(cls._payload_pick(payload, "billableseconds", "billsec"), 0) or 0
            if billsec > 0 or disposition in {"answer", "answered"}:
                return "completed"
            if disposition in {"noanswer", "no_answer", "no answer"}:
                return "missed"
            if disposition in {"busy", "failed", "congestion"}:
                return "failed"
            return "completed"
        return cls._normalize_status(event_type)

    @classmethod
    def _derive_direction_from_ami(
        cls,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> str:
        explicit = cls._payload_pick(payload, "direction", "call_direction")
        if explicit is not None:
            return cls._normalize_direction(explicit, payload)

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
            if caller_is_ext and len(connected) >= 7:
                return "outbound"
            if connected_is_ext and len(caller) >= 7:
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

        normalized = dict(source)
        normalized["status"] = status
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

        queue_operator_ext = _extract_internal_extension_candidate(
            cls._payload_pick(
                source,
                "interface",
                "member",
                "membername",
                "destchannel",
                "destinationchannel",
                "peer",
                "peerchannel",
                "channel",
            )
        )
        operator_candidates = [
            _to_international_phone(
                cls._payload_pick(source, "operator_ext", "agent_ext", "agent"), runtime.default_country_code
            ),
            _to_international_phone(queue_operator_ext, runtime.default_country_code),
            _to_international_phone(
                cls._payload_pick(
                    source,
                    "extension",
                    "sourceextension",
                    "destinationextension",
                    "connectedlinenum",
                    "destcalleridnum",
                    "exten",
                ),
                runtime.default_country_code,
            ),
        ]
        operator_ext: Optional[str] = None
        for candidate in operator_candidates:
            if not candidate:
                continue
            if client_phone and candidate == client_phone:
                continue
            operator_ext = candidate
            if _is_internal_extension(candidate):
                break

        if not operator_ext:
            if direction == "inbound":
                if to_phone and to_phone != client_phone:
                    operator_ext = to_phone
                elif from_phone and from_phone != client_phone:
                    operator_ext = from_phone
            else:
                if from_phone and from_phone != client_phone:
                    operator_ext = from_phone
                elif to_phone and to_phone != client_phone:
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

        if status == "recording_ready":
            recording_value = cls._payload_pick(
                source,
                "recording_url",
                "recordingfile",
                "recording_file",
                "mixmonitorfilename",
                "filename",
                "file",
            )
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
        for candidate in candidates:
            alias_key = cls._call_alias_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                candidate,
            )
            alias = cls._normalize_call_id(await cls._redis_get(alias_key))
            if alias:
                resolved_aliases.append(alias)

        if preferred_linked:
            canonical = preferred_linked
        elif resolved_aliases:
            canonical = resolved_aliases[0]
        else:
            canonical = candidates[0]

        for candidate in {canonical, *candidates, *resolved_aliases}:
            alias_key = cls._call_alias_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                candidate,
            )
            await cls._redis_set_with_ttl(
                alias_key,
                canonical,
                runtime.state_ttl_sec,
                min_ttl_sec=300,
            )
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
    ) -> None:
        await cls._enqueue(
            cls._stream_key(runtime.connected_integration_id),
            {
                "connected_integration_id": runtime.connected_integration_id,
                "event_ts": str(_to_int(event.event_ts, _now_ts()) or _now_ts()),
                "event": cls._event_to_dict(event),
                "attempt": "0",
                "enqueued_at": str(_now_ts()),
                "state_ttl_sec": str(runtime.state_ttl_sec),
            },
            stream_ttl_sec=runtime.state_ttl_sec,
        )

    @classmethod
    async def _ensure_consumer_group(cls, stream_key: str) -> None:
        if not _redis_enabled():
            return
        try:
            await redis_client.xgroup_create(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                id="0-0",
                mkstream=True,
            )
        except Exception as error:
            if "BUSYGROUP" not in str(error):
                raise

    @classmethod
    async def _enqueue(
        cls,
        stream_key: str,
        fields: Dict[str, Any],
        stream_ttl_sec: int,
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
            maxlen=AsteriskCrmChannelConfig.STREAM_MAXLEN,
            approximate=True,
        )
        ttl = max(_to_int(stream_ttl_sec, 60) or 60, 60)
        await redis_client.expire(stream_key, ttl)

    @classmethod
    async def _set_worker_heartbeat(cls, connected_integration_id: str) -> None:
        if not _redis_enabled():
            return
        await redis_client.setex(
            cls._worker_heartbeat_key(connected_integration_id),
            AsteriskCrmChannelConfig.HEARTBEAT_TTL_SEC,
            str(_now_ts()),
        )

    @classmethod
    async def _ensure_stream_worker(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            task = _WORKER_TASKS.get(connected_integration_id)
            if task and not task.done():
                return
            _WORKER_TASKS[connected_integration_id] = asyncio.create_task(
                cls._stream_worker_loop(connected_integration_id),
                name=f"asterisk_crm_stream_{connected_integration_id}",
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

        global _HTTP_CLIENT
        http_client = _HTTP_CLIENT
        _HTTP_CLIENT = None
        if http_client is not None:
            try:
                await http_client.aclose()
            except Exception:
                logger.exception("Error while closing Asterisk shared http client")

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not _redis_enabled():
            return {"total": 0, "restored": 0, "failed": 0}

        try:
            raw_ids = await redis_client.smembers(cls._active_ci_ids_key())
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
            return {"total": 0, "restored": 0, "failed": 0}

        restored = 0
        failed = 0
        for connected_integration_id in ci_ids:
            try:
                runtime = await cls._load_runtime(connected_integration_id)
                await cls._ensure_consumer_group(cls._stream_key(connected_integration_id))
                await cls._ensure_stream_worker(connected_integration_id)
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
        return {"total": len(ci_ids), "restored": restored, "failed": failed}

    @classmethod
    async def _stop_stream_worker(cls, connected_integration_id: str) -> None:
        async with _MANAGER_LOCK:
            task = _WORKER_TASKS.pop(connected_integration_id, None)
        if not task:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error while stopping stream worker: ci=%s", connected_integration_id)

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

                    await cls._ensure_stream_worker(connected_integration_id)
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

                            event = cls._normalize_ami_event(runtime, normalized_packet)
                            if not event:
                                continue
                            try:
                                await cls._enqueue_runtime_event(runtime, event)
                                await cls._ensure_stream_worker(connected_integration_id)
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
                    await cls._stop_stream_worker(connected_integration_id)
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
    async def _stream_worker_loop(cls, connected_integration_id: str) -> None:
        stream_key = cls._stream_key(connected_integration_id)
        consumer = f"{_INSTANCE_ID}:asterisk"
        await cls._ensure_consumer_group(stream_key)
        logger.info("Asterisk stream worker started: ci=%s", connected_integration_id)
        pending_entries: List[Tuple[str, Dict[str, str]]] = []

        while True:
            try:
                await cls._set_worker_heartbeat(connected_integration_id)
                claimed_entries = await cls._process_claimed_entries(
                    stream_key=stream_key,
                    consumer=consumer,
                )
                if claimed_entries:
                    pending_entries.extend(claimed_entries)

                try:
                    block_ms = AsteriskCrmChannelConfig.STREAM_READ_BLOCK_MS
                    if pending_entries:
                        block_ms = min(block_ms, 500)
                    records = await redis_client.xreadgroup(
                        groupname=AsteriskCrmChannelConfig.STREAM_GROUP,
                        consumername=consumer,
                        streams={stream_key: ">"},
                        count=AsteriskCrmChannelConfig.STREAM_BATCH_SIZE,
                        block=block_ms,
                    )
                except Exception as error:
                    if _is_redis_nogroup_error(error):
                        await cls._ensure_consumer_group(stream_key)
                        await asyncio.sleep(0.1)
                        continue
                    raise

                if records:
                    for _, entries in records:
                        pending_entries.extend(entries)

                if not pending_entries:
                    continue

                ready_entries, pending_entries = cls._select_ready_stream_entries(pending_entries)
                if not ready_entries:
                    continue

                for message_id, fields in ready_entries:
                    await cls._process_stream_entry(
                        stream_key=stream_key,
                        message_id=message_id,
                        fields=fields,
                        connected_integration_id=connected_integration_id,
                    )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.exception(
                    "Asterisk stream worker error: ci=%s error=%s",
                    connected_integration_id,
                    error,
                )
                await asyncio.sleep(1.0)

    @classmethod
    async def _process_claimed_entries(
        cls,
        stream_key: str,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, str]]]:
        try:
            claimed_raw = await redis_client.xautoclaim(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                consumer,
                min_idle_time=AsteriskCrmChannelConfig.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=AsteriskCrmChannelConfig.STREAM_BATCH_SIZE,
            )
        except Exception as error:
            if _is_redis_nogroup_error(error):
                await cls._ensure_consumer_group(stream_key)
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

    @staticmethod
    def _stream_entry_defer_until_ts(fields: Dict[str, str]) -> Optional[int]:
        return _to_int(fields.get("defer_until_ts"), None)

    @classmethod
    def _select_ready_stream_entries(
        cls,
        entries: List[Tuple[str, Dict[str, str]]],
    ) -> Tuple[List[Tuple[str, Dict[str, str]]], List[Tuple[str, Dict[str, str]]]]:
        now_ts = _now_ts()
        reorder_window_sec = max(AsteriskCrmChannelConfig.STREAM_EVENT_REORDER_WINDOW_SEC, 0)
        max_future_skew_sec = max(AsteriskCrmChannelConfig.STREAM_MAX_FUTURE_SKEW_SEC, 0)
        safe_event_ts = now_ts - reorder_window_sec
        sorted_entries = cls._sort_stream_entries_by_event_ts(entries)
        ready_entries: List[Tuple[str, Dict[str, str]]] = []
        pending_entries: List[Tuple[str, Dict[str, str]]] = []
        for message_id, fields in sorted_entries:
            defer_until_ts = cls._stream_entry_defer_until_ts(fields)
            if defer_until_ts is not None and defer_until_ts > now_ts:
                pending_entries.append((message_id, fields))
                continue
            event_ts = cls._stream_entry_event_ts(fields)
            if event_ts is not None and reorder_window_sec > 0 and event_ts > safe_event_ts:
                if max_future_skew_sec > 0 and event_ts > now_ts + max_future_skew_sec:
                    # Guard against clock skew / wrong timestamp units.
                    ready_entries.append((message_id, fields))
                    continue
                pending_entries.append((message_id, fields))
                continue
            ready_entries.append((message_id, fields))

        if (
            not ready_entries
            and pending_entries
            and len(pending_entries) >= AsteriskCrmChannelConfig.STREAM_BATCH_SIZE * 3
        ):
            ready_entries.append(pending_entries.pop(0))
        return ready_entries, pending_entries

    @classmethod
    async def _process_stream_entry(
        cls,
        stream_key: str,
        message_id: str,
        fields: Dict[str, str],
        connected_integration_id: str,
    ) -> None:
        attempts = _to_int(fields.get("attempt"), 0) or 0
        state_ttl_sec = max(
            _to_int(fields.get("state_ttl_sec"), AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC)
            or AsteriskCrmChannelConfig.DEFAULT_STATE_TTL_SEC,
            60,
        )
        try:
            raw_event = fields.get("event")
            if not raw_event:
                raise RuntimeError("stream payload has no event")
            event_payload = _json_loads(raw_event)
            if not isinstance(event_payload, dict):
                raise RuntimeError("stream event payload is not a dict")

            await cls._process_queued_event(connected_integration_id, event_payload)
            await redis_client.xack(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                message_id,
            )
        except DeferredCallEvent as deferred:
            defer_payload = dict(fields)
            defer_payload["defer_until_ts"] = str(_now_ts() + deferred.delay_sec)
            defer_payload["defer_reason"] = deferred.reason
            defer_payload.pop("error", None)
            defer_payload.pop("last_error", None)
            await cls._enqueue(
                stream_key,
                defer_payload,
                stream_ttl_sec=state_ttl_sec,
            )
            await redis_client.xack(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                message_id,
            )
            return
        except ConnectedIntegrationInactiveError as error:
            await redis_client.xack(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                message_id,
            )
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
            await redis_client.xack(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                message_id,
            )
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
                await redis_client.xack(
                    stream_key,
                    AsteriskCrmChannelConfig.STREAM_GROUP,
                    message_id,
                )
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
            await redis_client.xack(
                stream_key,
                AsteriskCrmChannelConfig.STREAM_GROUP,
                message_id,
            )
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
            if event.external_call_id:
                call_lock_key = cls._lock_call_process_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    event.external_call_id,
                )
                call_lock_token = await cls._acquire_lock(
                    call_lock_key,
                    AsteriskCrmChannelConfig.PROCESSING_LOCK_TTL_SEC,
                )
                if not call_lock_token:
                    raise DeferredCallEvent("call_lock_busy", delay_sec=1)

            event = await cls._dedupe_and_stabilize_call_event(runtime, event)
            if not event:
                await cls._redis_set_with_ttl(
                    dedupe_key,
                    "1",
                    runtime.lead_dedupe_ttl_sec,
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
                        runtime.lead_dedupe_ttl_sec,
                        min_ttl_sec=60,
                    )
                    return
            if not lead_ctx:
                lead_ctx = await cls._resolve_or_create_active_lead(runtime, event)
            await cls._maybe_assign_responsible_from_operator_best_effort(
                runtime=runtime,
                event=event,
                lead_ctx=lead_ctx,
            )
            lead_ctx = await cls._write_event_with_1220_policy(runtime, event, lead_ctx)
            await cls._save_mapping(runtime, event, lead_ctx)
            await cls._apply_status_policy_best_effort(runtime, event, lead_ctx)
            await cls._redis_set_with_ttl(
                dedupe_key,
                "1",
                runtime.lead_dedupe_ttl_sec,
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
            raw_event_type = str(
                cls._payload_get(event.raw_payload or {}, "event") or ""
            ).strip().lower()
            if raw_event_type in {
                "dialend",
                "hangup",
                "hanguprequest",
                "softhanguprequest",
                "unlink",
                "bridgeleave",
            }:
                return True

        # Early per-leg hangup events may emit "completed" before CDR with billsec.
        # Suppress these interim zero-talk completions and wait for final call result.
        if status == "completed" and talk_duration <= 0:
            raw_event_type = str(
                cls._payload_get(event.raw_payload or {}, "event") or ""
            ).strip().lower()
            if raw_event_type in {
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
        decision_reasons: List[str] = []
        finalize_defer_sec = 0
        converted_to_missed_by_timeout = False
        pending_inbound_completed_at = _to_int(cached.get("pending_inbound_completed_at"), None)

        stable_direction = str(cached.get("direction") or "").strip().lower()
        if stable_direction in {"inbound", "outbound"}:
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
        raw_event_type = str(
            cls._payload_get(event.raw_payload or {}, "event") or ""
        ).strip().lower()
        raw_operator_phone = cls._operator_phone_from_event(event) or _normalize_phone(
            event.operator_ext
        )
        operator_phone = locked_operator_ext or raw_operator_phone
        if locked_operator_ext:
            event.operator_ext = locked_operator_ext
        trusted_answered_event = (
            event.status == "answered"
            and (
                event.direction == "outbound"
                or (
                    event.direction == "inbound"
                    and bool(operator_phone)
                    and _is_internal_extension(operator_phone)
                )
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
            pending_inbound_completed_at = None
        if event.status == "completed" and answered_at is not None and event_ts >= answered_at:
            duration_from_answer = max(event_ts - answered_at, 0)
            reported_duration = _to_int(event.talk_duration_sec, None)
            if reported_duration is None or reported_duration <= 0:
                event.talk_duration_sec = duration_from_answer
            elif duration_from_answer > 0:
                # Keep only the segment after operator answer (exclude IVR/queue time).
                event.talk_duration_sec = min(reported_duration, duration_from_answer)
        if event.status == "completed" and event.direction == "inbound" and answered_at is None:
            talk_duration = _to_int(event.talk_duration_sec, 0) or 0
            can_infer_answered_from_completed = False
            if (
                talk_duration > 0
                and operator_phone
                and _is_internal_extension(operator_phone)
                and raw_event_type in {"cdr", ""}
            ):
                resolved_operator_user_id = await cls._resolve_user_id_by_operator_ext_best_effort(
                    runtime,
                    operator_phone,
                )
                if resolved_operator_user_id:
                    can_infer_answered_from_completed = True
                    decision_reasons.append("operator_resolved_for_completed")
                else:
                    decision_reasons.append("operator_unresolved_for_completed")

            if can_infer_answered_from_completed:
                # Infer answered only when we can map endpoint to a real operator.
                # This prevents IVR-only calls from being treated as operator-answered.
                answered_at = max(event_ts - talk_duration, 0)
                pending_inbound_completed_at = None
                decision_reasons.append("trusted_answered")
                decision_reasons.append("inferred_answered_from_completed")
            else:
                # Wait a short grace window for out-of-order AMI events before
                # converting inbound completed-without-operator into missed.
                now_ts = _now_ts()
                if pending_inbound_completed_at is None:
                    pending_inbound_completed_at = now_ts
                elapsed = max(now_ts - pending_inbound_completed_at, 0)
                wait_sec = max(AsteriskCrmChannelConfig.INBOUND_FINALIZE_DELAY_SEC, 1)
                if elapsed < wait_sec:
                    finalize_defer_sec = min(2, max(wait_sec - elapsed, 1))
                    decision_reasons.append("await_inbound_final_state")
                else:
                    # IVR/queue can answer the call before any operator picks it up.
                    # Treat such calls as missed from CRM perspective.
                    event.status = "missed"
                    event.talk_duration_sec = None
                    pending_inbound_completed_at = None
                    converted_to_missed_by_timeout = True
                    decision_reasons.append("converted_to_missed")

        if event.status in {"answered", "missed", "failed", "recording_ready"}:
            pending_inbound_completed_at = None

        posted_statuses = {
            str(item).strip().lower()
            for item in (cached.get("posted_statuses") or [])
            if str(item).strip()
        }
        last_rank = _to_int(cached.get("last_rank"), 0) or 0
        stage_code = cls._chat_event_code(event)
        current_rank = cls._status_rank(stage_code)
        status = stage_code

        suppressed_as_noise = (
            False if converted_to_missed_by_timeout else cls._should_suppress_noise_event(event)
        )
        if suppressed_as_noise:
            decision_reasons.append("suppressed_as_leg_noise")
        should_emit = not suppressed_as_noise and finalize_defer_sec <= 0
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
        stable_client_phone = _normalize_phone(event.client_phone) or stable_client_phone
        stable_operator_ext = (
            locked_operator_ext
            or _normalize_phone(event.operator_ext)
            or stable_operator_ext
        )
        stable_from_phone = _normalize_phone(event.from_phone) or stable_from_phone
        stable_to_phone = _normalize_phone(event.to_phone) or stable_to_phone
        effective_rank = current_rank if finalize_defer_sec <= 0 else 0
        next_last_rank = max(last_rank, effective_rank)
        if should_emit and status and status != "recording_ready":
            posted_statuses.add(status)
        recording_posted = bool(cached.get("recording_posted")) or status == "recording_ready"
        cached_trace = cached.get("decision_trace")
        decision_trace: List[Dict[str, Any]] = []
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
            "deferred": bool(finalize_defer_sec > 0),
            "reasons": decision_reasons,
            "raw_event_type": raw_event_type or None,
        }
        decision_trace.append(trace_entry)
        decision_trace = decision_trace[-20:]

        await cls._redis_set_json_with_ttl(
            progress_key,
            {
                "direction": stable_direction or "",
                "client_phone": stable_client_phone or "",
                "operator_ext": stable_operator_ext or "",
                "locked_operator_ext": locked_operator_ext or "",
                "from_phone": stable_from_phone or "",
                "to_phone": stable_to_phone or "",
                "posted_statuses": sorted(posted_statuses),
                "last_rank": int(next_last_rank),
                "recording_posted": recording_posted,
                "answered_at": int(answered_at) if answered_at is not None else None,
                "pending_inbound_completed_at": (
                    int(pending_inbound_completed_at)
                    if pending_inbound_completed_at is not None
                    else None
                ),
                "last_decision": trace_entry,
                "decision_trace": decision_trace,
                "updated_at": _now_ts(),
            },
            runtime.state_ttl_sec,
            min_ttl_sec=300,
        )

        if finalize_defer_sec > 0:
            raise DeferredCallEvent("await_inbound_final_state", delay_sec=finalize_defer_sec)
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

        raw_event_type = str(
            cls._payload_get(event.raw_payload or {}, "event") or ""
        ).strip().lower()
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

        cached_trace = cached.get("decision_trace")
        decision_trace: List[Dict[str, Any]] = []
        if isinstance(cached_trace, list):
            for row in cached_trace[-19:]:
                if isinstance(row, dict):
                    decision_trace.append(dict(row))
        decision_trace.append(rollback_entry)
        decision_trace = decision_trace[-20:]

        cached["posted_statuses"] = sorted(posted_statuses)
        cached["last_rank"] = int(recalculated_rank)
        cached["last_decision"] = rollback_entry
        cached["decision_trace"] = decision_trace
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
        if cached_user_id and cached_user_id > 0:
            return cached_user_id

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
                response = await api.call(
                    "User/Get",
                    {
                        "active": True,
                        "internal_phone": normalized_ext,
                        "limit": 50,
                        "offset": 0,
                    },
                    APIBaseResponse[List[Dict[str, Any]]],
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
        if response and response.ok:
            internal_rows = response.result if isinstance(response.result, list) else []
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
                        name_cache_key,
                        resolved_user_name,
                        runtime.state_ttl_sec,
                        min_ttl_sec=300,
                    )
                return resolved_user_id

        # Backward-compatible fallback for old environments where `internal_phone`
        # may be unavailable in User/Get.
        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.call(
                    "User/Get",
                    {
                        "active": True,
                        "search": normalized_ext,
                        "limit": 50,
                        "offset": 0,
                    },
                    APIBaseResponse[List[Dict[str, Any]]],
                )
        except Exception as error:
            logger.warning(
                "User/Get fallback search failed for operator extension match: ci=%s operator_ext=%s error=%s",
                runtime.connected_integration_id,
                normalized_ext,
                error,
            )
            return None

        if not response.ok:
            logger.warning(
                "User/Get fallback search rejected for operator extension match: ci=%s operator_ext=%s payload=%s",
                runtime.connected_integration_id,
                normalized_ext,
                response.result,
            )
            return None

        rows = response.result if isinstance(response.result, list) else []
        resolved_user_id, resolved_user_name = _resolve_from_rows(
            rows,
            allow_single_fallback=False,
        )

        if not resolved_user_id:
            return None

        await cls._redis_set_with_ttl(
            cache_key,
            str(resolved_user_id),
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

        cached_name = str(await cls._redis_get(name_cache_key) or "").strip()
        if cached_name:
            return cached_name

        try:
            async with RegosAPI(
                connected_integration_id=runtime.connected_integration_id
            ) as api:
                response = await api.call(
                    "User/Get",
                    {
                        "ids": [user_id],
                        "active": True,
                        "limit": 1,
                        "offset": 0,
                    },
                    APIBaseResponse[List[Dict[str, Any]]],
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

        rows = response.result if isinstance(response.result, list) else []
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
        return name

    @classmethod
    async def _resolve_operator_display_name_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[str]:
        operator_ext = _normalize_phone(event.operator_ext) or cls._operator_phone_from_event(event)
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
        talked = (_to_int(event.talk_duration_sec, 0) or 0) > 0
        should_move_to_in_progress = event.status == "answered" or (
            event.status == "completed" and talked
        )
        operator_ext = _normalize_phone(event.operator_ext) or cls._operator_phone_from_event(
            event
        )
        if not operator_ext:
            return

        target_user_id = await cls._resolve_user_id_by_operator_ext_best_effort(
            runtime,
            operator_ext,
        )
        if not target_user_id:
            return

        call_key = cls._call_responsible_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.external_call_id,
        )
        already_bound = _to_int(await cls._redis_get(call_key), None)
        if already_bound and already_bound == target_user_id:
            if not lead_ctx.ticket_id:
                await cls._update_lead_state_cache(
                    connected_integration_id=runtime.connected_integration_id,
                    lead_id=lead_ctx.lead_id,
                    responsible_user_id=target_user_id,
                )
                if should_move_to_in_progress:
                    await cls._set_lead_status_best_effort(
                        connected_integration_id=runtime.connected_integration_id,
                        lead_id=lead_ctx.lead_id,
                        status=LeadStatusEnum.InProgress,
                        reason="responsible_already_bound_by_operator_ext",
                    )
            return
        if already_bound and already_bound != target_user_id:
            return

        try:
            if lead_ctx.ticket_id:
                async with RegosAPI(
                    connected_integration_id=runtime.connected_integration_id
                ) as api:
                    response = await api.crm.ticket.set_responsible(
                        TicketSetResponsibleRequest(
                            id=int(lead_ctx.ticket_id),
                            responsible_user_id=target_user_id,
                        )
                    )
            else:
                async with RegosAPI(
                    connected_integration_id=runtime.connected_integration_id
                ) as api:
                    response = await api.crm.lead.set_responsible(
                        LeadSetResponsibleRequest(
                            id=lead_ctx.lead_id, responsible_user_id=target_user_id
                        )
                    )
            if not response.ok:
                if lead_ctx.ticket_id:
                    logger.warning(
                        "Ticket/SetResponsible rejected while binding responsible by operator extension: ci=%s ticket_id=%s operator_ext=%s user_id=%s payload=%s",
                        runtime.connected_integration_id,
                        lead_ctx.ticket_id,
                        operator_ext,
                        target_user_id,
                        response.result,
                    )
                else:
                    logger.warning(
                        "Lead/SetResponsible rejected while binding responsible by operator extension: ci=%s lead_id=%s operator_ext=%s user_id=%s payload=%s",
                        runtime.connected_integration_id,
                        lead_ctx.lead_id,
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
            if not lead_ctx.ticket_id:
                await cls._update_lead_state_cache(
                    connected_integration_id=runtime.connected_integration_id,
                    lead_id=lead_ctx.lead_id,
                    responsible_user_id=target_user_id,
                )
                if should_move_to_in_progress:
                    await cls._set_lead_status_best_effort(
                        connected_integration_id=runtime.connected_integration_id,
                        lead_id=lead_ctx.lead_id,
                        status=LeadStatusEnum.InProgress,
                        reason="responsible_bound_by_operator_ext",
                    )
        except Exception as error:
            if lead_ctx.ticket_id:
                logger.warning(
                    "Failed to bind responsible by operator extension: ci=%s ticket_id=%s operator_ext=%s user_id=%s error=%s",
                    runtime.connected_integration_id,
                    lead_ctx.ticket_id,
                    operator_ext,
                    target_user_id,
                    error,
                )
            else:
                logger.warning(
                    "Failed to bind responsible by operator extension: ci=%s lead_id=%s operator_ext=%s user_id=%s error=%s",
                    runtime.connected_integration_id,
                    lead_ctx.lead_id,
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
        normalized_phone = _normalize_phone(event.client_phone) or ""
        payload = {
            "lead_id": int(lead_ctx.lead_id),
            "ticket_id": int(lead_ctx.ticket_id or lead_ctx.lead_id),
            "client_id": _to_int(lead_ctx.client_id, None),
            "chat_id": str(lead_ctx.chat_id),
            "asterisk_hash": runtime.asterisk_hash,
            "normalized_phone": normalized_phone,
            "external_call_id": event.external_call_id,
            "last_event_ts": int(event.event_ts),
        }
        if normalized_phone:
            await cls._redis_set_json_with_ttl(
                cls._mapping_by_phone_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    normalized_phone,
                ),
                payload,
                runtime.state_ttl_sec,
                min_ttl_sec=60,
            )
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
    async def _clear_mapping(cls, runtime: RuntimeConfig, event: CallEvent) -> None:
        keys = [
            cls._mapping_by_call_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.external_call_id,
            )
        ]
        normalized_phone = _normalize_phone(event.client_phone)
        if normalized_phone:
            phone_key = cls._mapping_by_phone_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                normalized_phone,
            )
            payload = cls._parse_cached_json(await cls._redis_get(phone_key))
            mapped_call_id = cls._normalize_call_id(
                payload.get("external_call_id") if isinstance(payload, dict) else None
            )
            current_call_id = cls._normalize_call_id(event.external_call_id)
            if not mapped_call_id or not current_call_id or mapped_call_id == current_call_id:
                keys.append(phone_key)
        await cls._redis_delete(*keys)

    @classmethod
    async def _resolve_mapping(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[LeadContext]:
        call_id = cls._normalize_call_id(event.external_call_id)
        if call_id:
            payload = cls._parse_cached_json(
                await cls._redis_get(
                    cls._mapping_by_call_key(
                        runtime.connected_integration_id,
                        runtime.asterisk_hash,
                        call_id,
                    )
                )
            )
            if payload:
                lead_id = _to_int(payload.get("lead_id"), None)
                ticket_id = _to_int(payload.get("ticket_id"), None)
                client_id = _to_int(payload.get("client_id"), None)
                chat_id = str(payload.get("chat_id") or "").strip()
                if lead_id and chat_id:
                    return LeadContext(
                        lead_id=lead_id,
                        chat_id=chat_id,
                        client_id=client_id,
                        ticket_id=ticket_id,
                    )

        normalized_phone = _normalize_phone(event.client_phone)
        if not normalized_phone:
            return None
        payload = cls._parse_cached_json(
            await cls._redis_get(
                cls._mapping_by_phone_key(
                    runtime.connected_integration_id,
                    runtime.asterisk_hash,
                    normalized_phone,
                )
            )
        )
        if not payload:
            return None
        mapped_call_id = cls._normalize_call_id(payload.get("external_call_id"))
        if call_id and mapped_call_id and mapped_call_id != call_id:
            # Protect against cross-call collisions when same client has parallel calls.
            return None
        lead_id = _to_int(payload.get("lead_id"), None)
        ticket_id = _to_int(payload.get("ticket_id"), None)
        client_id = _to_int(payload.get("client_id"), None)
        chat_id = str(payload.get("chat_id") or "").strip()
        if lead_id and chat_id:
            return LeadContext(
                lead_id=lead_id,
                chat_id=chat_id,
                client_id=client_id,
                ticket_id=ticket_id,
            )
        return None

    @classmethod
    async def _find_active_lead_by_external(
        cls,
        runtime: RuntimeConfig,
        normalized_phone: str,
    ) -> Optional[Lead]:
        filters = [
            Filter(
                field="external_id",
                operator=FilterOperator.Equal,
                value=_external_id(runtime.asterisk_hash, normalized_phone),
            ),
        ]
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.lead.get(
                LeadGetRequest(
                    filters=filters,
                    statuses=list(AsteriskCrmChannelConfig.ACTIVE_LEAD_STATUSES),
                    limit=1,
                    offset=0,
                )
            )
        if not response.result:
            return None
        lead = response.result[0]
        if not lead or not lead.id or not lead.chat_id:
            return None
        await cls._cache_lead_snapshot(runtime.connected_integration_id, lead)
        return lead

    @staticmethod
    def _pick_latest_active_lead(leads: List[Lead]) -> Optional[Lead]:
        valid = [
            row
            for row in (leads or [])
            if row and getattr(row, "id", None) and getattr(row, "chat_id", None)
        ]
        if not valid:
            return None
        return max(valid, key=lambda row: int(row.id or 0))

    @classmethod
    async def _find_active_lead_by_phone(
        cls,
        runtime: RuntimeConfig,
        normalized_phone: str,
    ) -> Optional[Lead]:
        candidates = _phone_filter_candidates(
            normalized_phone,
            runtime.default_country_code,
        )
        if not candidates:
            return None

        for phone in candidates:
            miss_key = cls._lead_lookup_miss_phone_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                phone,
            )
            if str(await cls._redis_get(miss_key) or "").strip() == "1":
                continue
            filters = [
                Filter(
                    field="client_phone",
                    operator=FilterOperator.Equal,
                    value=phone,
                ),
            ]
            try:
                async with RegosAPI(
                    connected_integration_id=runtime.connected_integration_id
                ) as api:
                    response = await api.crm.lead.get(
                        LeadGetRequest(
                            filters=filters,
                            statuses=list(AsteriskCrmChannelConfig.ACTIVE_LEAD_STATUSES),
                            limit=50,
                            offset=0,
                        )
                    )
            except Exception as error:
                logger.warning(
                    "Lead/Get by client_phone failed: ci=%s phone=%s error=%s",
                    runtime.connected_integration_id,
                    phone,
                    error,
                )
                return None
            rows = response.result or []
            lead = cls._pick_latest_active_lead(rows)
            if not lead:
                await cls._redis_set_with_ttl(
                    miss_key,
                    "1",
                    AsteriskCrmChannelConfig.LEAD_LOOKUP_MISS_TTL_SEC,
                    min_ttl_sec=10,
                )
                continue
            await cls._redis_delete(miss_key)
            await cls._cache_lead_snapshot(runtime.connected_integration_id, lead)
            if len(rows) > 1:
                lead_ids = sorted(
                    int(row.id)
                    for row in rows
                    if row and getattr(row, "id", None)
                )
                logger.info(
                    "Multiple active leads matched by client_phone, picked latest: ci=%s phone=%s lead_ids=%s selected=%s",
                    runtime.connected_integration_id,
                    phone,
                    lead_ids,
                    lead.id,
                )
            return lead
        return None

    @classmethod
    async def _find_active_lead(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[Lead]:
        if not _normalize_phone(event.client_phone):
            return None
        if not runtime.find_active_lead_by_phone:
            return None
        # For both inbound and outbound calls we first try to reuse an active lead
        # by customer phone/external id (for example, an existing chat lead).
        lead_by_phone = await cls._find_active_lead_by_phone(
            runtime,
            event.client_phone,
        )
        if lead_by_phone:
            return lead_by_phone

        lead_by_external = await cls._find_active_lead_by_external(
            runtime,
            event.client_phone,
        )
        if lead_by_external:
            return lead_by_external

        return None

    @classmethod
    async def _resolve_existing_lead_context(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[LeadContext]:
        mapped_ctx = await cls._resolve_mapping(runtime, event)
        if mapped_ctx:
            return mapped_ctx

        active_lead = await cls._find_active_lead(runtime, event)
        if not active_lead or not active_lead.id or not active_lead.chat_id:
            return None

        lead_ctx = LeadContext(lead_id=int(active_lead.id), chat_id=str(active_lead.chat_id))
        await cls._save_mapping(runtime, event, lead_ctx)
        return lead_ctx

    @classmethod
    async def _resolve_or_create_client_by_phone(
        cls,
        runtime: RuntimeConfig,
        phone: str,
    ) -> int:
        candidates = _phone_filter_candidates(phone, runtime.default_country_code)
        if not candidates:
            candidates = [phone]

        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            for candidate in candidates:
                response = await api.crm.client.get(
                    ClientGetRequest(phones=[candidate], limit=1, offset=0)
                )
                rows = response.result if response.ok and isinstance(response.result, list) else []
                if rows and rows[0] and rows[0].id:
                    return int(rows[0].id)

            add_response = await api.crm.client.add(
                ClientAddRequest(
                    phone=phone,
                    name=phone,
                    external_id=_external_id(runtime.asterisk_hash, phone),
                )
            )
            add_result = add_response.result if isinstance(add_response.result, dict) else {}
            if not add_response.ok:
                # In race conditions client can be created concurrently: retry lookup.
                for candidate in candidates:
                    response = await api.crm.client.get(
                        ClientGetRequest(phones=[candidate], limit=1, offset=0)
                    )
                    rows = (
                        response.result
                        if response.ok and isinstance(response.result, list)
                        else []
                    )
                    if rows and rows[0] and rows[0].id:
                        return int(rows[0].id)
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
    async def _find_open_ticket_by_external_call(
        cls,
        runtime: RuntimeConfig,
        external_call_id: str,
    ) -> Optional[LeadContext]:
        filters = [
            Filter(
                field="external_dialog_id",
                operator=FilterOperator.Equal,
                value=external_call_id,
            ),
        ]
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.get(
                TicketGetRequest(
                    channel_ids=[runtime.channel_id],
                    filters=filters,
                    limit=10,
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
            lead_id=int(ticket.id),
            chat_id=str(ticket.chat_id),
            client_id=int(ticket.client_id),
            ticket_id=int(ticket.id),
        )

    @classmethod
    async def _create_lead(cls, runtime: RuntimeConfig, event: CallEvent) -> LeadContext:
        reused = await cls._find_open_ticket_by_external_call(
            runtime,
            event.external_call_id,
        )
        if reused:
            return reused

        client_id = await cls._resolve_or_create_client_by_phone(runtime, event.client_phone)
        payload = TicketAddRequest(
            client_id=client_id,
            channel_id=runtime.channel_id,
            direction=(
                TicketDirectionEnum.Outbound
                if event.direction == "outbound"
                else TicketDirectionEnum.Inbound
            ),
            external_dialog_id=event.external_call_id,
            responsible_user_id=runtime.default_responsible_user_id,
            subject=_safe_subject(
                runtime.lead_subject_template,
                event,
                language=runtime.message_language,
            ),
            description=None,
        )
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            add_response = await api.crm.ticket.add(payload)
            add_result = add_response.result if isinstance(add_response.result, dict) else {}
            if not add_response.ok:
                error_code = add_result.get("error")
                description = add_result.get("description")
                raise NonRetryableCallEventError(
                    f"Ticket/Add rejected: error={error_code} description={description}"
                )
            new_id = _to_int(add_result.get("new_id"), None)
            if not new_id:
                raise RuntimeError("Ticket/Add did not return new_id")

            ticket_response = await api.crm.ticket.get(
                TicketGetRequest(ids=[int(new_id)], limit=1, offset=0)
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
                lead_id=int(ticket.id),
                chat_id=str(ticket.chat_id),
                client_id=int(resolved_client_id),
                ticket_id=int(ticket.id),
            )

    @classmethod
    async def _resolve_or_create_active_lead(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> LeadContext:
        normalized_client_phone = _normalize_phone(event.client_phone)
        if not normalized_client_phone:
            raise RuntimeError(
                "Cannot resolve or create lead: client_phone is empty and mapping is missing"
            )
        event.client_phone = normalized_client_phone

        lead_ctx = await cls._resolve_existing_lead_context(runtime, event)
        if lead_ctx:
            return lead_ctx

        lock_key = cls._lock_create_lead_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.client_phone,
        )
        lock_token = await cls._acquire_lock(lock_key, AsteriskCrmChannelConfig.LOCK_TTL_SEC)
        if not lock_token:
            await asyncio.sleep(0.25)
            lead_ctx = await cls._resolve_existing_lead_context(runtime, event)
            if lead_ctx:
                return lead_ctx
            raise RuntimeError("Failed to acquire create-lead lock")

        try:
            lead_ctx = await cls._resolve_existing_lead_context(runtime, event)
            if lead_ctx:
                return lead_ctx

            lead_ctx = await cls._create_lead(runtime, event)
            await cls._save_mapping(runtime, event, lead_ctx)
            return lead_ctx
        finally:
            await cls._release_lock(lock_key, lock_token)

    @classmethod
    def _event_external_message_id(cls, event: CallEvent) -> str:
        # Stable id makes ChatMessage/Add idempotent for repeated AMI events.
        return f"astmsg:{event.asterisk_hash}:{event.external_call_id}:{cls._chat_event_code(event)}"

    @staticmethod
    def _operator_phone_from_event(event: CallEvent) -> Optional[str]:
        client_phone = _normalize_phone(event.client_phone)
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
            return normalized
        return None

    @classmethod
    def _render_call_text(
        cls,
        event: CallEvent,
        language: str,
        *,
        operator_name: Optional[str] = None,
    ) -> str:
        code = cls._chat_event_code(event)
        client_phone = event.client_phone or "-"
        operator_phone = cls._operator_phone_from_event(event)
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
            response = await api.call(
                "ChatMessage/Add",
                ChatMessageAddRequest(
                    chat_id=lead_ctx.chat_id,
                    message_type=ChatMessageTypeEnum.System,
                    text=text,
                    file_ids=file_ids or None,
                    external_message_id=cls._event_external_message_id(event),
                ),
                APIBaseResponse[Dict[str, Any]],
            )

        if not response.ok:
            payload = response.result if isinstance(response.result, dict) else {}
            error_code = _to_int(payload.get("error"), None)
            error_description = str(payload.get("description") or "").strip() or None
            if error_code == AsteriskCrmChannelConfig.CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR:
                raise ChatMessageAddClosedEntityError(error_description)
            raise RuntimeError(
                "ChatMessage/Add rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        result_payload = response.result if isinstance(response.result, dict) else {}
        message_uuid = str(result_payload.get("new_uuid") or "").strip()
        if not message_uuid:
            message_uuid = str(getattr(response.result, "new_uuid", "") or "").strip()
        if not message_uuid:
            raise RuntimeError("ChatMessage/Add did not return new_uuid")
        return message_uuid

    @classmethod
    async def _chat_message_add_file(
        cls,
        runtime: RuntimeConfig,
        chat_id: str,
        file_name: str,
        extension: str,
        payload_b64: str,
    ) -> int:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/AddFile",
                ChatMessageAddFileRequest(
                    chat_id=chat_id,
                    name=file_name,
                    extension=extension,
                    data=payload_b64,
                ),
                APIBaseResponse[Dict[str, Any]],
            )

        if not response.ok:
            payload = response.result if isinstance(response.result, dict) else {}
            error_code = _to_int(payload.get("error"), None)
            error_description = str(payload.get("description") or "").strip() or None
            if error_code == AsteriskCrmChannelConfig.CHAT_MESSAGE_ADD_CLOSED_ENTITY_ERROR:
                raise ChatMessageAddClosedEntityError(error_description)
            raise RuntimeError(
                "ChatMessage/AddFile rejected: "
                f"error={payload.get('error')} description={payload.get('description')}"
            )

        payload = response.result if isinstance(response.result, dict) else {}
        file_id = _to_int(payload.get("file_id"), None)
        if not file_id:
            file_id = _to_int(getattr(response.result, "file_id", None), None)
        if not file_id:
            raise RuntimeError("ChatMessage/AddFile did not return file_id")
        return int(file_id)

    @classmethod
    async def _download_recording_bytes(cls, recording_url: str) -> bytes:
        client = await cls._get_http_client()
        response = await client.get(recording_url)
        response.raise_for_status()
        return response.content

    @classmethod
    async def _post_recording_event(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        language = runtime.message_language
        file_ids: List[int] = []
        text_lines = [
            cls._text(language, "recording_ready_title"),
            cls._text(language, "call_id_label", external_call_id=event.external_call_id),
        ]

        if event.recording_url:
            file_name, extension = _recording_name_from_url(
                event.recording_url,
                event.external_call_id,
            )
            try:
                file_bytes = await cls._download_recording_bytes(event.recording_url)
                file_id = await cls._chat_message_add_file(
                    runtime=runtime,
                    chat_id=lead_ctx.chat_id,
                    file_name=file_name,
                    extension=extension,
                    payload_b64=base64.b64encode(file_bytes).decode("ascii"),
                )
                file_ids = [file_id]
            except ChatMessageAddClosedEntityError:
                raise
            except Exception as error:
                logger.warning(
                    "Recording attach failed, fallback to link: ci=%s call_id=%s error=%s",
                    runtime.connected_integration_id,
                    event.external_call_id,
                    error,
                )
                text_lines.append(
                    cls._text(language, "recording_link", recording_url=event.recording_url)
                )
        else:
            text_lines.append(cls._text(language, "recording_url_missing"))

        await cls._chat_message_add(
            runtime=runtime,
            lead_ctx=lead_ctx,
            event=event,
            text="\n".join(text_lines),
            file_ids=file_ids,
        )

    @classmethod
    async def _store_late_recording_state(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
        reason: Optional[str],
    ) -> None:
        payload = {
            "status": "late_recording_closed_lead",
            "connected_integration_id": runtime.connected_integration_id,
            "asterisk_hash": runtime.asterisk_hash,
            "external_call_id": event.external_call_id,
            "event_id": event.event_id,
            "recording_url": event.recording_url,
            "event_ts": event.event_ts,
            "lead_id": lead_ctx.lead_id,
            "chat_id": lead_ctx.chat_id,
            "reason": reason,
            "stored_at": _now_ts(),
            "raw_payload": event.raw_payload,
        }
        await cls._redis_set_json_with_ttl(
            cls._late_recording_state_key(
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
    ) -> LeadContext:
        try:
            if event.status == "recording_ready":
                await cls._post_recording_event(runtime, event, lead_ctx)
            else:
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
                    ),
                )
            return lead_ctx
        except ChatMessageAddClosedEntityError as error:
            if event.status == "recording_ready":
                # Recording arrived after close/convert: keep audit state, do not reopen.
                await cls._store_late_recording_state(
                    runtime=runtime,
                    event=event,
                    lead_ctx=lead_ctx,
                    reason=error.description,
                )
                return lead_ctx

            # Call-state event for closed lead: rebuild mapping and retry once.
            await cls._clear_mapping(runtime, event)
            fresh = await cls._resolve_or_create_active_lead(runtime, event)
            operator_name: Optional[str] = None
            if cls._chat_event_code(event) == "inbound_answered":
                operator_name = await cls._resolve_operator_display_name_best_effort(
                    runtime,
                    event,
                )
            await cls._chat_message_add(
                runtime=runtime,
                lead_ctx=fresh,
                event=event,
                text=cls._render_call_text(
                    event,
                    runtime.message_language,
                    operator_name=operator_name,
                ),
            )
            return fresh

    @classmethod
    async def _apply_status_policy_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        # New CRM flow is Client + Ticket; telephony does not transition ticket status here.
        # Leave ticket open and avoid legacy Lead/SetStatus for ticket ids.
        if lead_ctx.ticket_id:
            return

        target_status = _status_from_direction_event(event.direction, event.status)
        if not target_status:
            return

        reason = f"call_{event.direction}_{event.status}"
        await cls._set_lead_status_best_effort(
            connected_integration_id=runtime.connected_integration_id,
            lead_id=lead_ctx.lead_id,
            status=target_status,
            reason=reason,
        )

    @classmethod
    async def _set_lead_status_best_effort(
        cls,
        connected_integration_id: str,
        lead_id: Optional[int],
        status: LeadStatusEnum,
        *,
        reason: str,
    ) -> None:
        _ = (connected_integration_id, lead_id, status, reason)
        # Lead/SetStatus is deprecated in the new CRM API flow.
        return

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

        try:
            await self._ensure_connected_integration_active(
                self.connected_integration_id,
                force_refresh=True,
            )
            runtime = await self._load_runtime(self.connected_integration_id)
        except ConnectedIntegrationInactiveError as error:
            return self._error_response(1004, str(error)).dict()
        await self._mark_ci_active(self.connected_integration_id)
        try:
            await self._ensure_consumer_group(self._stream_key(self.connected_integration_id))
            await self._ensure_stream_worker(self.connected_integration_id)
            await self._ensure_ami_worker(runtime)
        except Exception:
            await self._mark_ci_inactive(self.connected_integration_id)
            raise
        return {
            "status": "connected",
            "mode": "ami_with_external_fallback",
            "instance_id": _INSTANCE_ID,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._mark_ci_inactive(self.connected_integration_id)
        await self._stop_ami_worker(self.connected_integration_id)
        await self._stop_stream_worker(self.connected_integration_id)
        return {"status": "disconnected"}

    async def reconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self.disconnect()
        return await self.connect()

    async def update_settings(self, settings: Optional[dict] = None, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        await self._redis_delete(
            self._settings_cache_key(self.connected_integration_id),
            self._ci_active_cache_key(self.connected_integration_id),
        )
        reconnect_result = await self.reconnect()
        return {"status": "settings updated", "reconnect": reconnect_result}

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

            await self._enqueue_runtime_event(runtime, normalized)
            accepted += 1

        await self._ensure_stream_worker(self.connected_integration_id)
        return {
            "status": "accepted" if accepted else "ignored",
            "accepted": accepted,
            "ignored": ignored,
        }
