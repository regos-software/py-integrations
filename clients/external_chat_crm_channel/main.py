from __future__ import annotations

import asyncio
import html
import json
import re
import time
import uuid
from dataclasses import dataclass
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
    TicketSetStatusRequest,
    TicketStatusEnum,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
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
    DEFAULT_CHAT_TITLE = "Support Chat"
    DEFAULT_SUBJECT_TEMPLATE = "Web chat {visitor_id}"
    CLOSED_ENTITY_ERROR_CODE = 1220
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

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            channel_id=int(channel_id),
            ticket_subject_template=ticket_subject_template,
            default_responsible_user_id=_parse_int(
                settings_map.get("default_responsible_user_id"), None
            ),
            chat_title=chat_title,
            channel_start_message=channel_start_message,
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
            if ticket and ticket.id:
                status_value = _enum_value(getattr(ticket, "status", None)).strip()
                if status_value == TicketStatusEnum.Closed.value:
                    await api.crm.ticket.set_status(
                        TicketSetStatusRequest(
                            id=int(ticket.id),
                            status=TicketStatusEnum.Open,
                        )
                    )
                    refreshed = await api.crm.ticket.get(
                        TicketGetRequest(ids=[int(ticket.id)], limit=1, offset=0)
                    )
                    refreshed_rows = (
                        refreshed.result if refreshed.ok and isinstance(refreshed.result, list) else []
                    )
                    if refreshed_rows:
                        ticket = refreshed_rows[0]

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
                            message_type=ChatMessageTypeEnum.System,
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
            if message_type == ChatMessageTypeEnum.Private.value:
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
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
{theme_vars_css}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%);
      color: var(--text);
      font: 14px/1.45 "Segoe UI", Tahoma, sans-serif;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 16px;
    }}
    .wrap {{
      width: 100%;
      max-width: 860px;
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(16, 38, 70, 0.08);
    }}
    .head {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}
    .title {{
      font-size: 16px;
      font-weight: 600;
    }}
    .status {{
      color: var(--muted);
      font-size: 12px;
    }}
    .profile {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }}
    .profile.hidden {{
      display: none;
    }}
    .field {{
      display: grid;
      gap: 4px;
    }}
    .field.hidden {{
      display: none;
    }}
    .field label {{
      color: var(--muted);
      font-size: 11px;
    }}
    .profile input {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--text);
      background: #fff;
    }}
    .history {{
      padding: 14px 16px;
      overflow-y: auto;
      background: var(--bg);
      min-height: 360px;
      max-height: 60vh;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .msg {{
      max-width: 80%;
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid var(--line);
      white-space: pre-wrap;
      word-break: break-word;
      animation: rise .12s ease-out;
    }}
    .msg.mine {{ margin-left: auto; background: var(--mine); }}
    .msg.other {{ margin-right: auto; background: var(--other); }}
    .msg.system {{ margin: 0 auto; background: var(--system); max-width: 94%; }}
    .meta {{
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
    }}
    .composer {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      border-top: 1px solid var(--line);
      padding: 12px 16px;
      background: #fff;
    }}
    .composer textarea {{
      width: 100%;
      min-height: 42px;
      max-height: 120px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      font: inherit;
      color: var(--text);
    }}
    .composer button {{
      border: 0;
      border-radius: 8px;
      padding: 0 16px;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }}
    @keyframes rise {{
      from {{ transform: translateY(4px); opacity: .6; }}
      to {{ transform: translateY(0); opacity: 1; }}
    }}
    @media (max-width: 700px) {{
      .profile {{ grid-template-columns: 1fr; }}
      .history {{ max-height: 56vh; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="head">
      <div class="title">{safe_title}</div>
      <div class="status" id="status">connecting...</div>
    </div>
    <div class="profile" id="profile">
      <div class="field" id="display_name_wrap">
        <label for="display_name">Name</label>
        <input id="display_name" placeholder="Name">
      </div>
      <div class="field" id="email_wrap">
        <label for="email">Email</label>
        <input id="email" placeholder="Email">
      </div>
      <div class="field" id="phone_wrap">
        <label for="phone">Phone</label>
        <input id="phone" placeholder="Phone">
      </div>
    </div>
    <div class="history" id="history"></div>
    <form class="composer" id="composer">
      <textarea id="text" maxlength="{ExternalChatCrmChannelConfig.MAX_MESSAGE_LENGTH}" placeholder="Type your message"></textarea>
      <button type="submit">Send</button>
    </form>
  </div>
  <script>
    const CONFIG = {{
      ci: "{safe_ci}",
      profileKey: "webchat:profile:{safe_ci}",
      visitorKey: "webchat:visitor:{safe_ci}",
      required: {{
        display_name: {safe_require_display_name},
        phone: {safe_require_phone},
        email: {safe_require_email},
      }},
    }};
    const statusEl = document.getElementById("status");
    const profileEl = document.getElementById("profile");
    const displayNameWrapEl = document.getElementById("display_name_wrap");
    const emailWrapEl = document.getElementById("email_wrap");
    const phoneWrapEl = document.getElementById("phone_wrap");
    const historyEl = document.getElementById("history");
    const textEl = document.getElementById("text");
    const formEl = document.getElementById("composer");
    const displayNameEl = document.getElementById("display_name");
    const emailEl = document.getElementById("email");
    const phoneEl = document.getElementById("phone");

    let chatReady = false;
    let visitorId = localStorage.getItem(CONFIG.visitorKey) || "";
    if (!visitorId) {{
      visitorId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : ("v" + Date.now() + Math.random().toString(16).slice(2));
      localStorage.setItem(CONFIG.visitorKey, visitorId);
    }}

    function setupProfileRequirements() {{
      const req = CONFIG.required || {{}};
      displayNameWrapEl.classList.toggle("hidden", !req.display_name);
      emailWrapEl.classList.toggle("hidden", !req.email);
      phoneWrapEl.classList.toggle("hidden", !req.phone);

      displayNameEl.required = !!req.display_name;
      emailEl.required = !!req.email;
      phoneEl.required = !!req.phone;

      displayNameEl.placeholder = req.display_name ? "Name (required)" : "Name";
      emailEl.placeholder = req.email ? "Email (required)" : "Email";
      phoneEl.placeholder = req.phone ? "Phone (required)" : "Phone";

      const anyRequired = !!(req.display_name || req.email || req.phone);
      profileEl.classList.toggle("hidden", !anyRequired);
    }}

    function loadProfile() {{
      try {{
        const raw = localStorage.getItem(CONFIG.profileKey);
        if (!raw) return;
        const data = JSON.parse(raw);
        displayNameEl.value = data.display_name || "";
        emailEl.value = data.email || "";
        phoneEl.value = data.phone || "";
      }} catch (_) {{}}
    }}
    function saveProfile() {{
      const payload = {{
        display_name: (displayNameEl.value || "").trim(),
        email: (emailEl.value || "").trim(),
        phone: (phoneEl.value || "").trim(),
      }};
      localStorage.setItem(CONFIG.profileKey, JSON.stringify(payload));
      return payload;
    }}

    function validateRequiredProfile(showStatus = false) {{
      const profile = saveProfile();
      const req = CONFIG.required || {{}};
      const missing = [];
      if (req.display_name && !profile.display_name) missing.push("Name");
      if (req.phone && !profile.phone) missing.push("Phone");
      if (req.email && !profile.email) missing.push("Email");
      if (missing.length > 0 && showStatus) {{
        statusEl.textContent = `fill required fields: ${{missing.join(", ")}}`;
      }}
      return {{ ok: missing.length === 0, profile, missing }};
    }}

    const basePath = window.location.pathname.replace(/\\/+$/g, "").replace(/\\/+/g, "/");
    const externalUrl = `${{basePath}}/external?ci=${{encodeURIComponent(CONFIG.ci)}}`;

    async function callApi(action, data) {{
      const resp = await fetch(externalUrl, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ action, data }})
      }});
      const payload = await resp.json().catch(() => ({{}}));
      if (!resp.ok) {{
        const message = payload?.result?.description || payload?.description || `HTTP ${{resp.status}}`;
        throw new Error(message);
      }}
      return payload;
    }}

    function toTime(ts) {{
      const value = Number(ts || 0);
      if (!value) return "";
      return new Date(value * 1000).toLocaleTimeString([], {{ hour: "2-digit", minute: "2-digit" }});
    }}

    function renderHistory(items) {{
      historyEl.innerHTML = "";
      for (const item of items || []) {{
        const type = (item.message_type || "Regular");
        const box = document.createElement("div");
        box.className = "msg " + (type === "System" ? "system" : (item.mine ? "mine" : "other"));
        const text = document.createElement("div");
        text.textContent = item.text || "";
        box.appendChild(text);

        const meta = document.createElement("div");
        meta.className = "meta";
        const who = type === "System" ? "system" : (item.mine ? "you" : (item.author_name || "operator"));
        meta.textContent = `${{who}}  ${{toTime(item.created_date)}}${{item.edited ? " (edited)" : ""}}`;
        box.appendChild(meta);

        historyEl.appendChild(box);
      }}
      historyEl.scrollTop = historyEl.scrollHeight;
    }}

    async function initChat() {{
      if (chatReady) return;
      const check = validateRequiredProfile(true);
      if (!check.ok) {{
        chatReady = false;
        return;
      }}
      statusEl.textContent = "connecting...";
      const profile = check.profile;
      const result = await callApi("init", {{
        visitor_id: visitorId,
        display_name: profile.display_name,
        email: profile.email,
        phone: profile.phone
      }});
      if (result.visitor_id && result.visitor_id !== visitorId) {{
        visitorId = result.visitor_id;
        localStorage.setItem(CONFIG.visitorKey, visitorId);
      }}
      renderHistory(result.history || []);
      chatReady = true;
      statusEl.textContent = "online";
    }}

    async function refreshHistory() {{
      if (!chatReady) return;
      const check = validateRequiredProfile(false);
      if (!check.ok) {{
        chatReady = false;
        return;
      }}
      const profile = check.profile;
      const result = await callApi("history", {{
        visitor_id: visitorId,
        display_name: profile.display_name,
        email: profile.email,
        phone: profile.phone,
        limit: {ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT}
      }});
      renderHistory(result.history || []);
    }}

    formEl.addEventListener("submit", async (event) => {{
      event.preventDefault();
      const text = (textEl.value || "").trim();
      if (!text) return;
      try {{
        formEl.querySelector("button").disabled = true;
        if (!chatReady) {{
          await initChat();
        }}
        if (!chatReady) {{
          return;
        }}
        const check = validateRequiredProfile(true);
        if (!check.ok) {{
          chatReady = false;
          return;
        }}
        const profile = check.profile;
        await callApi("send_message", {{
          visitor_id: visitorId,
          text,
          display_name: profile.display_name,
          email: profile.email,
          phone: profile.phone
        }});
        textEl.value = "";
        await refreshHistory();
      }} catch (error) {{
        statusEl.textContent = `error: ${{error.message}}`;
      }} finally {{
        formEl.querySelector("button").disabled = false;
      }}
    }});

    for (const el of [displayNameEl, emailEl, phoneEl]) {{
      el.addEventListener("change", () => {{
        saveProfile();
        if (!chatReady) {{
          initChat().catch((error) => {{
            statusEl.textContent = `error: ${{error.message}}`;
          }});
        }}
      }});
    }}

    setupProfileRequirements();
    loadProfile();
    initChat().catch((error) => {{
      chatReady = false;
      statusEl.textContent = `error: ${{error.message}}`;
    }});
    setInterval(() => {{
      if (chatReady) {{
        refreshHistory().catch((error) => {{
          chatReady = false;
          statusEl.textContent = `error: ${{error.message}}`;
        }});
      }} else {{
        initChat().catch((error) => {{
          chatReady = false;
          statusEl.textContent = `error: ${{error.message}}`;
        }});
      }}
    }}, 3000);
  </script>
</body>
</html>"""

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

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        _ = data, extra
        return {"status": "ignored", "reason": "webhook_not_used", "action": action}

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
                    "history": history,
                }

            if action == "history":
                limit = _parse_int(
                    data.get("limit"),
                    ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT,
                )
                history = await self._read_history(
                    ci,
                    context,
                    int(limit or ExternalChatCrmChannelConfig.DEFAULT_HISTORY_LIMIT),
                )
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
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
                ext_id = f"webchat:msg:{visitor_id}:{uuid.uuid4().hex[:12]}"
                try:
                    message_id = await self._add_message_from_visitor(
                        connected_integration_id=ci,
                        context=context,
                        text=text,
                        external_message_id=ext_id,
                    )
                except ChatMessageAddClosedEntityError:
                    await self._redis_delete(self._context_cache_key(ci, visitor_id))
                    context = await self._ensure_chat_context(
                        connected_integration_id=ci,
                        runtime=runtime,
                        visitor_id=visitor_id,
                        profile=profile,
                    )
                    message_id = await self._add_message_from_visitor(
                        connected_integration_id=ci,
                        context=context,
                        text=text,
                        external_message_id=ext_id,
                    )
                await self._mark_read(ci, context)
                return {
                    "status": "ok",
                    "visitor_id": visitor_id,
                    "message_id": message_id,
                }

            if action == "mark_read":
                await self._mark_read(ci, context)
                return {"status": "ok", "visitor_id": visitor_id}

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
