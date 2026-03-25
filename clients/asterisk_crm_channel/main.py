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
from schemas.api.crm.lead import (
    Lead,
    LeadAddRequest,
    LeadGetRequest,
    LeadSetStatusRequest,
    LeadStatusEnum,
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
    DEFAULT_DEDUPE_TTL_SEC = 24 * 60 * 60
    DEFAULT_STATE_TTL_SEC = 24 * 60 * 60

    STREAM_GROUP = "asterisk_crm_channel_workers"
    STREAM_MAXLEN = 10000
    STREAM_BATCH_SIZE = 20
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_MAX_RETRIES = 5

    LOCK_TTL_SEC = 30
    PROCESSING_LOCK_TTL_SEC = 120
    HEARTBEAT_TTL_SEC = 30
    AMI_CONNECT_TIMEOUT_SEC = 30
    AMI_PING_INTERVAL_SEC = 20
    AMI_RECONNECT_MIN_SEC = 1
    AMI_RECONNECT_MAX_SEC = 30

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
    reconcile_lookback_min: int


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


class ChatMessageAddClosedEntityError(RuntimeError):
    def __init__(self, description: Optional[str] = None) -> None:
        self.description = str(description or "").strip() or None
        text = "ChatMessage/Add rejected for closed linked entity"
        if self.description:
            text = f"{text}: {self.description}"
        super().__init__(text)


_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[str, asyncio.Task] = {}
_AMI_TASKS: Dict[str, asyncio.Task] = {}
_INSTANCE_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None


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


def _normalize_phone(value: Any) -> Optional[str]:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits or None


def _hash_scope_key(value: str) -> str:
    return hashlib.md5(str(value or "").encode("utf-8")).hexdigest()


def _external_contact_id(asterisk_hash: str, normalized_phone: str) -> str:
    return f"ast:{asterisk_hash}:{normalized_phone}"


def _safe_subject(template: str, event: CallEvent) -> str:
    subject_template = str(template or "").strip() or "Call {direction} {from_phone}"
    try:
        return subject_template.format(
            direction=event.direction,
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
        return int(value)
    text = str(value).strip()
    if not text:
        return _now_ts()
    direct = _to_int(text, None)
    if direct is not None:
        return int(direct)
    try:
        return int(float(text))
    except (TypeError, ValueError):
        pass
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return int(parsed.timestamp())
    except Exception:
        return _now_ts()


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
        return LeadStatusEnum.WaitingClient
    if direction == "outbound" and status == "answered":
        return LeadStatusEnum.InProgress
    return None


class AsteriskCrmChannelIntegration(ClientBase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _settings_cache_key(connected_integration_id: str) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"settings:{connected_integration_id}"
        )

    @staticmethod
    def _stream_key(connected_integration_id: str) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"stream:asterisk_in:{connected_integration_id}"
        )

    @staticmethod
    def _dlq_stream_key(connected_integration_id: str) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"stream:dlq:{connected_integration_id}"
        )

    @staticmethod
    def _worker_heartbeat_key(connected_integration_id: str) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"worker:heartbeat:{connected_integration_id}:{_INSTANCE_ID}"
        )

    @staticmethod
    def _lock_create_lead_key(
        connected_integration_id: str,
        asterisk_hash: str,
        normalized_phone: str,
    ) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"lock:create_lead:{connected_integration_id}:{asterisk_hash}:{normalized_phone}"
        )

    @staticmethod
    def _dedupe_event_key(connected_integration_id: str, event_id: str) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"dedupe:event:{connected_integration_id}:{event_id}"
        )

    @staticmethod
    def _mapping_by_phone_key(
        connected_integration_id: str,
        asterisk_hash: str,
        normalized_phone: str,
    ) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"mapping:by_phone:{connected_integration_id}:{asterisk_hash}:{normalized_phone}"
        )

    @staticmethod
    def _mapping_by_call_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"mapping:by_call:{connected_integration_id}:{asterisk_hash}:{external_call_id}"
        )

    @staticmethod
    def _late_recording_state_key(
        connected_integration_id: str,
        asterisk_hash: str,
        external_call_id: str,
    ) -> str:
        return (
            f"{AsteriskCrmChannelConfig.REDIS_PREFIX}"
            f"late_recording:{connected_integration_id}:{asterisk_hash}:{external_call_id}"
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
    async def _get_http_client() -> httpx.AsyncClient:
        global _HTTP_CLIENT
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.AsyncClient(timeout=90)
        return _HTTP_CLIENT

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

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id,
                )
            )
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
    def _parse_allowed_did_set(raw: Optional[str]) -> set[str]:
        if not raw:
            return set()
        values: set[str] = set()
        for chunk in str(raw).replace(";", ",").split(","):
            normalized = _normalize_phone(chunk)
            if normalized:
                values.add(normalized)
        return values

    @staticmethod
    async def _load_runtime(connected_integration_id: str) -> RuntimeConfig:
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
                settings_map.get("asterisk_allowed_did_list")
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
            reconcile_lookback_min=max(
                _to_int(settings_map.get("reconcile_lookback_min"), 120) or 120,
                1,
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
        if not client_phone:
            return None

        if (
            direction == "inbound"
            and runtime.allowed_did_set
            and (not to_phone or to_phone not in runtime.allowed_did_set)
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
            cls._payload_pick(source, "talk_duration_sec", "billsec", "duration_sec", "duration"),
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
            client_phone=client_phone,
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
        required = (
            "event_id",
            "external_call_id",
            "asterisk_hash",
            "direction",
            "client_phone",
            "status",
            "event_ts",
        )
        for field in required:
            if payload.get(field) in (None, ""):
                return None
        status = str(payload.get("status")).strip().lower()
        if status not in AsteriskCrmChannelConfig.EVENT_STATUSES:
            return None
        return CallEvent(
            event_id=str(payload["event_id"]).strip(),
            external_call_id=str(payload["external_call_id"]).strip(),
            asterisk_hash=str(payload["asterisk_hash"]).strip(),
            direction=str(payload["direction"]).strip().lower(),
            from_phone=str(payload.get("from_phone") or "").strip(),
            to_phone=str(payload.get("to_phone") or "").strip(),
            client_phone=str(payload["client_phone"]).strip(),
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
            return "started"
        if event_type in {"dialbegin", "dialstate"}:
            return "ringing"
        if event_type == "newstate":
            return cls._normalize_status(
                cls._payload_pick(payload, "channelstatedesc", "state", "channelstate")
            )
        if event_type in {"bridgeenter", "bridgecreate", "bridge", "link"}:
            return "answered"
        if event_type in {"mixmonitorstop", "monitorstop"}:
            return "recording_ready"
        if event_type == "dialend":
            dial_status = str(cls._payload_pick(payload, "dialstatus") or "").strip().lower()
            if dial_status in {"answer", "answered"}:
                return "answered"
            if dial_status in {"noanswer", "no_answer", "cancel", "cancelled", "canceled"}:
                return "missed"
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
            if cause_text in {"noanswer", "no_answer", "no answer"} or cause in {19}:
                return "missed"
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

        caller = _normalize_phone(
            cls._payload_pick(
                payload,
                "calleridnum",
                "callerid",
                "src",
                "caller",
                "channelcalleridnum",
            )
        )
        connected = _normalize_phone(
            cls._payload_pick(
                payload,
                "connectedlinenum",
                "exten",
                "destination",
                "dnid",
                "dialstring",
                "destcalleridnum",
                "to",
            )
        )
        if runtime.allowed_did_set:
            if connected and connected in runtime.allowed_did_set:
                return "inbound"
            if caller and caller in runtime.allowed_did_set:
                return "outbound"

        context = str(
            cls._payload_pick(payload, "context", "destinationcontext", "dialcontext") or ""
        ).strip().lower()
        if any(token in context for token in {"internal", "from-internal", "outbound"}):
            return "outbound"
        if any(token in context for token in {"incoming", "from-trunk", "external", "pstn"}):
            return "inbound"

        if caller and connected:
            if len(caller) <= 5 and len(connected) >= 7:
                return "outbound"
            if len(connected) <= 5 and len(caller) >= 7:
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
        normalized["direction"] = cls._derive_direction_from_ami(runtime, source)
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
            "bridgeuniqueid",
            "uniqueid",
            "destuniqueid",
        )
        if external_call_id:
            normalized["external_call_id"] = str(external_call_id).strip()

        from_phone = _normalize_phone(
            cls._payload_pick(
                source,
                "from_phone",
                "from",
                "src",
                "calleridnum",
                "callerid",
                "caller",
                "channelcalleridnum",
            )
        )
        to_phone = _normalize_phone(
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
            )
        )
        if from_phone:
            normalized["from_phone"] = from_phone
        if to_phone:
            normalized["to_phone"] = to_phone

        talk_duration_sec = _to_int(
            cls._payload_pick(source, "talk_duration_sec", "billableseconds", "billsec", "duration"),
            None,
        )
        if talk_duration_sec is not None:
            normalized["talk_duration_sec"] = int(talk_duration_sec)

        operator_ext = _normalize_phone(
            cls._payload_pick(source, "operator_ext", "agent_ext", "extension", "connectedlinenum")
        )
        if operator_ext:
            normalized["operator_ext"] = operator_ext

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
    async def _enqueue_runtime_event(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> None:
        await cls._enqueue(
            cls._stream_key(runtime.connected_integration_id),
            {
                "connected_integration_id": runtime.connected_integration_id,
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
                    await cls._ensure_stream_worker(connected_integration_id)
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(runtime.ami_host, runtime.ami_port),
                        timeout=AsteriskCrmChannelConfig.AMI_CONNECT_TIMEOUT_SEC,
                    )
                    try:
                        await cls._ami_login(runtime, reader, writer)
                        reconnect_delay = AsteriskCrmChannelConfig.AMI_RECONNECT_MIN_SEC
                        logger.info(
                            "Asterisk AMI connected and authorized: ci=%s",
                            connected_integration_id,
                        )
                        while True:
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

        while True:
            try:
                await cls._set_worker_heartbeat(connected_integration_id)
                await cls._process_claimed_entries(
                    stream_key=stream_key,
                    consumer=consumer,
                    connected_integration_id=connected_integration_id,
                )

                try:
                    records = await redis_client.xreadgroup(
                        groupname=AsteriskCrmChannelConfig.STREAM_GROUP,
                        consumername=consumer,
                        streams={stream_key: ">"},
                        count=AsteriskCrmChannelConfig.STREAM_BATCH_SIZE,
                        block=AsteriskCrmChannelConfig.STREAM_READ_BLOCK_MS,
                    )
                except Exception as error:
                    if _is_redis_nogroup_error(error):
                        await cls._ensure_consumer_group(stream_key)
                        await asyncio.sleep(0.1)
                        continue
                    raise

                if not records:
                    continue

                for _, entries in records:
                    for message_id, fields in entries:
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
        connected_integration_id: str,
    ) -> None:
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
                return
            raise

        entries: List[Tuple[str, Dict[str, str]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []

        for message_id, fields in entries:
            await cls._process_stream_entry(
                stream_key=stream_key,
                message_id=message_id,
                fields=fields,
                connected_integration_id=connected_integration_id,
            )

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

        try:
            lead_ctx = await cls._resolve_or_create_active_lead(runtime, event)
            lead_ctx = await cls._write_event_with_1220_policy(runtime, event, lead_ctx)
            await cls._save_mapping(runtime, event, lead_ctx)
            await cls._apply_status_policy_best_effort(runtime, event, lead_ctx.lead_id)
            await cls._redis_set_with_ttl(
                dedupe_key,
                "1",
                runtime.lead_dedupe_ttl_sec,
                min_ttl_sec=60,
            )
        except Exception:
            await cls._redis_delete(dedupe_key)
            raise

    @classmethod
    async def _save_mapping(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_ctx: LeadContext,
    ) -> None:
        payload = {
            "lead_id": int(lead_ctx.lead_id),
            "chat_id": str(lead_ctx.chat_id),
            "asterisk_hash": runtime.asterisk_hash,
            "normalized_phone": event.client_phone,
            "external_call_id": event.external_call_id,
            "last_event_ts": int(event.event_ts),
        }
        await cls._redis_set_json_with_ttl(
            cls._mapping_by_phone_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.client_phone,
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
        await cls._redis_delete(
            cls._mapping_by_phone_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.client_phone,
            ),
            cls._mapping_by_call_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.external_call_id,
            ),
        )

    @classmethod
    async def _resolve_mapping(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> Optional[LeadContext]:
        keys = [
            cls._mapping_by_call_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.external_call_id,
            ),
            cls._mapping_by_phone_key(
                runtime.connected_integration_id,
                runtime.asterisk_hash,
                event.client_phone,
            ),
        ]
        for key in keys:
            payload = cls._parse_cached_json(await cls._redis_get(key))
            if not payload:
                continue
            lead_id = _to_int(payload.get("lead_id"), None)
            chat_id = str(payload.get("chat_id") or "").strip()
            if lead_id and chat_id:
                return LeadContext(lead_id=lead_id, chat_id=chat_id)
        return None

    @classmethod
    async def _find_active_lead(
        cls,
        runtime: RuntimeConfig,
        normalized_phone: str,
    ) -> Optional[Lead]:
        filters = [
            Filter(
                field="bot_id",
                operator=FilterOperator.Equal,
                value=runtime.asterisk_hash,
            ),
            Filter(
                field="external_contact_id",
                operator=FilterOperator.Equal,
                value=_external_contact_id(runtime.asterisk_hash, normalized_phone),
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
        return lead

    @classmethod
    async def _create_lead(cls, runtime: RuntimeConfig, event: CallEvent) -> Lead:
        payload = LeadAddRequest(
            channel_id=runtime.channel_id,
            pipeline_id=runtime.pipeline_id,
            responsible_user_id=runtime.default_responsible_user_id,
            subject=_safe_subject(runtime.lead_subject_template, event),
            external_contact_id=_external_contact_id(
                runtime.asterisk_hash,
                event.client_phone,
            ),
            client_phone=event.client_phone,
            external_chat_id=event.client_phone,
            bot_id=runtime.asterisk_hash,
        )
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            add_response = await api.crm.lead.add(payload)
            new_id = None
            if isinstance(add_response.result, dict):
                new_id = _to_int(add_response.result.get("new_id"), None)
            else:
                new_id = _to_int(getattr(add_response.result, "new_id", None), None)
            if not new_id:
                raise RuntimeError("Lead/Add did not return new_id")

            lead = await api.crm.lead.get_by_id(new_id)
            if not lead or not lead.id or not lead.chat_id:
                raise RuntimeError("Lead/Get did not return lead/chat pair after Lead/Add")
            return lead

    @classmethod
    async def _resolve_or_create_active_lead(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
    ) -> LeadContext:
        mapped = await cls._resolve_mapping(runtime, event)
        if mapped:
            return mapped

        recovered = await cls._find_active_lead(runtime, event.client_phone)
        if recovered and recovered.id and recovered.chat_id:
            lead_ctx = LeadContext(lead_id=int(recovered.id), chat_id=str(recovered.chat_id))
            await cls._save_mapping(runtime, event, lead_ctx)
            return lead_ctx

        lock_key = cls._lock_create_lead_key(
            runtime.connected_integration_id,
            runtime.asterisk_hash,
            event.client_phone,
        )
        lock_token = await cls._acquire_lock(lock_key, AsteriskCrmChannelConfig.LOCK_TTL_SEC)
        if not lock_token:
            await asyncio.sleep(0.25)
            mapped = await cls._resolve_mapping(runtime, event)
            if mapped:
                return mapped
            recovered = await cls._find_active_lead(runtime, event.client_phone)
            if recovered and recovered.id and recovered.chat_id:
                lead_ctx = LeadContext(lead_id=int(recovered.id), chat_id=str(recovered.chat_id))
                await cls._save_mapping(runtime, event, lead_ctx)
                return lead_ctx
            raise RuntimeError("Failed to acquire create-lead lock")

        try:
            mapped = await cls._resolve_mapping(runtime, event)
            if mapped:
                return mapped

            recovered = await cls._find_active_lead(runtime, event.client_phone)
            if recovered and recovered.id and recovered.chat_id:
                lead_ctx = LeadContext(lead_id=int(recovered.id), chat_id=str(recovered.chat_id))
                await cls._save_mapping(runtime, event, lead_ctx)
                return lead_ctx

            created = await cls._create_lead(runtime, event)
            lead_ctx = LeadContext(lead_id=int(created.id), chat_id=str(created.chat_id))
            await cls._save_mapping(runtime, event, lead_ctx)
            return lead_ctx
        finally:
            await cls._release_lock(lock_key, lock_token)

    @staticmethod
    def _event_external_message_id(event: CallEvent) -> str:
        return (
            f"astmsg:{event.asterisk_hash}:{event.external_call_id}:"
            f"{event.status}:{event.event_id}"
        )

    @staticmethod
    def _render_call_text(event: CallEvent) -> str:
        status_title = {
            "started": "started",
            "ringing": "ringing",
            "answered": "answered",
            "missed": "missed",
            "completed": "completed",
            "failed": "failed",
        }.get(event.status, event.status)
        direction_title = "inbound" if event.direction == "inbound" else "outbound"
        lines = [
            f"[Asterisk] Call {direction_title} {status_title}",
            f"Call ID: {event.external_call_id}",
            f"From: {event.from_phone or '-'}",
            f"To: {event.to_phone or '-'}",
        ]
        if event.talk_duration_sec is not None and event.talk_duration_sec >= 0:
            lines.append(f"Talk duration: {event.talk_duration_sec}s")
        if event.operator_ext:
            lines.append(f"Operator ext: {event.operator_ext}")
        return "\n".join(lines)

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
                    author_entity_type="Lead",
                    author_entity_id=lead_ctx.lead_id,
                    message_type=ChatMessageTypeEnum.Regular,
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
        file_ids: List[int] = []
        text_lines = [
            "[Asterisk] Call recording is ready",
            f"Call ID: {event.external_call_id}",
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
                text_lines.append(f"Recording: {event.recording_url}")
        else:
            text_lines.append("Recording URL is not provided")

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
                await cls._chat_message_add(
                    runtime=runtime,
                    lead_ctx=lead_ctx,
                    event=event,
                    text=cls._render_call_text(event),
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
            await cls._chat_message_add(
                runtime=runtime,
                lead_ctx=fresh,
                event=event,
                text=cls._render_call_text(event),
            )
            return fresh

    @classmethod
    async def _apply_status_policy_best_effort(
        cls,
        runtime: RuntimeConfig,
        event: CallEvent,
        lead_id: int,
    ) -> None:
        target_status = _status_from_direction_event(event.direction, event.status)
        if not target_status:
            return

        reason = f"call_{event.direction}_{event.status}"
        await cls._set_lead_status_best_effort(
            connected_integration_id=runtime.connected_integration_id,
            lead_id=lead_id,
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
        if not lead_id:
            return
        try:
            async with RegosAPI(connected_integration_id=connected_integration_id) as api:
                lead = await api.crm.lead.get_by_id(int(lead_id))
                if not lead:
                    return

                current_status: Optional[LeadStatusEnum]
                if isinstance(lead.status, LeadStatusEnum):
                    current_status = lead.status
                else:
                    try:
                        current_status = LeadStatusEnum(str(lead.status or "").strip())
                    except ValueError:
                        current_status = None

                if current_status in {LeadStatusEnum.Closed, LeadStatusEnum.Converted}:
                    return
                if (
                    current_status == LeadStatusEnum.New
                    and not getattr(lead, "responsible_user_id", None)
                ):
                    return
                if current_status == status:
                    return

                response = await api.crm.lead.set_status(
                    LeadSetStatusRequest(id=int(lead_id), status=status.value)
                )
            if response.ok:
                return
            payload = response.result if isinstance(response.result, dict) else {}
            logger.warning(
                "Lead/SetStatus rejected: ci=%s lead_id=%s status=%s reason=%s error=%s description=%s",
                connected_integration_id,
                lead_id,
                status,
                reason,
                payload.get("error"),
                payload.get("description"),
            )
        except Exception as error:
            logger.warning(
                "Lead status update failed: ci=%s lead_id=%s status=%s reason=%s error=%s",
                connected_integration_id,
                lead_id,
                status,
                reason,
                error,
            )

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

        runtime = await self._load_runtime(self.connected_integration_id)
        await self._ensure_consumer_group(self._stream_key(self.connected_integration_id))
        await self._ensure_stream_worker(self.connected_integration_id)
        await self._ensure_ami_worker(runtime)
        return {
            "status": "connected",
            "mode": "ami_with_external_fallback",
            "instance_id": _INSTANCE_ID,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
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
        await self._redis_delete(self._settings_cache_key(self.connected_integration_id))
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

        runtime = await self._load_runtime(self.connected_integration_id)

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
