from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from fastapi.responses import HTMLResponse, RedirectResponse, Response

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
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

logger = setup_logger("instagram_crm_channel")


class InstagramCrmChannelConfig:
    INTEGRATION_KEY = "instagram_crm_channel"
    REDIS_PREFIX = "clients:instagram_crm_channel:"

    GRAPH_BASE_URL = "https://graph.facebook.com/v20.0"
    OAUTH_DIALOG_URL = "https://www.facebook.com/v20.0/dialog/oauth"

    SETTINGS_TTL_SEC = max(int(app_settings.redis_cache_ttl or 60), 60)
    MAP_TTL_SEC = 30 * 24 * 60 * 60
    DEDUPE_TTL_SEC = 24 * 60 * 60
    LOCK_TTL_SEC = 30
    OAUTH_STATE_TTL_SEC = 10 * 60
    ACTIVE_CACHE_TTL_SEC = 30
    HTTP_TIMEOUT_SEC = 30

    OAUTH_SCOPES = (
        "instagram_basic",
        "instagram_manage_messages",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_metadata",
        "pages_messaging",
    )

    ACTIVE_TICKET_STATUSES = (TicketStatusEnum.Open,)

    SUPPORTED_INBOUND_WEBHOOKS = {"ChatMessageAdded"}


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    instagram_business_account_id: str
    pipeline_id: int
    channel_id: int
    default_responsible_user_id: Optional[int]
    lead_subject_template: str
    verify_token: str
    page_id: Optional[str]
    page_access_token: Optional[str]
    meta_app_id: str
    meta_app_secret: str
    meta_redirect_uri: str
    find_active_lead_by_external_id: bool


@dataclass
class LeadContext:
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
    return bool(app_settings.redis_enabled and redis_client is not None)


def _extract_connected_integration_active_flag(payload: Any) -> Optional[bool]:
    if isinstance(payload, dict):
        for key in ("is_active", "isActive"):
            if key in payload:
                return _to_bool(payload.get(key), True)
        for nested_key in ("connected_integration", "integration", "item", "data", "result"):
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


class InstagramCrmChannelIntegration(ClientBase):
    _ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
    _ACTIVE_CACHE_LOCK = asyncio.Lock()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
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

    @staticmethod
    async def _redis_get(key: str) -> Optional[str]:
        if not _redis_enabled():
            return None
        return await redis_client.get(key)

    @staticmethod
    async def _redis_set(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> None:
        if not _redis_enabled():
            return
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        await redis_client.set(key, value, ex=ttl)

    @staticmethod
    async def _redis_set_nx(key: str, value: str, ttl_sec: int, min_ttl_sec: int = 60) -> bool:
        if not _redis_enabled():
            return False
        ttl = max(_to_int(ttl_sec, min_ttl_sec) or min_ttl_sec, min_ttl_sec)
        return bool(await redis_client.set(key, value, ex=ttl, nx=True))

    @staticmethod
    async def _redis_delete(*keys: str) -> None:
        if not _redis_enabled():
            return
        rows = [str(key).strip() for key in keys if str(key or "").strip()]
        if rows:
            await redis_client.delete(*rows)

    @classmethod
    async def _fetch_settings_map(cls, connected_integration_id: str, force_refresh: bool = False) -> Dict[str, str]:
        cache_key = cls._redis_key("settings", connected_integration_id)
        if not force_refresh:
            raw = await cls._redis_get(cache_key)
            if raw:
                try:
                    cached = _json_loads(raw)
                    if isinstance(cached, dict):
                        return {str(k): str(v or "") for k, v in cached.items()}
                except Exception:
                    pass

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=connected_integration_id)
            )

        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            key = str(getattr(row, "key", "") or "").strip()
            if key:
                settings_map[key] = str(getattr(row, "value", "") or "").strip()

        await cls._redis_set(cache_key, _json_dumps(settings_map), InstagramCrmChannelConfig.SETTINGS_TTL_SEC)
        return settings_map

    @classmethod
    async def _edit_settings(cls, connected_integration_id: str, patch: Dict[str, str]) -> None:
        rows = [
            ConnectedIntegrationSettingEditItem(
                connected_integration_id=connected_integration_id,
                key=str(key),
                value=str(value or ""),
            )
            for key, value in patch.items()
        ]
        if not rows:
            return
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            await api.integrations.connected_integration_setting.edit(ConnectedIntegrationSettingEditRequest(rows))
        await cls._redis_delete(cls._redis_key("settings", connected_integration_id))

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

        detected: Optional[bool] = None
        for payload in ({}, {"connected_integration_id": ci, "limit": 1, "offset": 0}):
            try:
                async with RegosAPI(connected_integration_id=ci) as api:
                    response = await api.call("ConnectedIntegration/Get", payload, APIBaseResponse[Any])
                if response.ok:
                    detected = _extract_connected_integration_active_flag(response.result)
                    if detected is not None:
                        break
            except Exception:
                continue
        if detected is None:
            detected = True

        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (bool(detected), now + InstagramCrmChannelConfig.ACTIVE_CACHE_TTL_SEC)
        return bool(detected)

    @classmethod
    async def _load_runtime(cls, connected_integration_id: str, require_page_token: bool) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(connected_integration_id)

        business_id = str(settings_map.get("instagram_business_account_id") or "").strip()
        pipeline_id = _to_int(settings_map.get("instagram_pipeline_id"), None)
        channel_id = _to_int(settings_map.get("instagram_channel_id"), None)
        if not business_id:
            raise ValueError("instagram_business_account_id is required")
        if not pipeline_id or pipeline_id <= 0:
            raise ValueError("instagram_pipeline_id must be > 0")
        if not channel_id or channel_id <= 0:
            raise ValueError("instagram_channel_id must be > 0")

        app_id = (
            str(settings_map.get("instagram_meta_app_id") or "").strip()
            or str(os.getenv("INSTAGRAM_META_APP_ID") or "").strip()
            or str(os.getenv("META_APP_ID") or "").strip()
        )
        app_secret = (
            str(settings_map.get("instagram_meta_app_secret") or "").strip()
            or str(os.getenv("INSTAGRAM_META_APP_SECRET") or "").strip()
            or str(os.getenv("META_APP_SECRET") or "").strip()
        )
        redirect_uri = (
            str(settings_map.get("instagram_meta_redirect_uri") or "").strip()
            or str(os.getenv("INSTAGRAM_META_REDIRECT_URI") or "").strip()
            or str(os.getenv("META_REDIRECT_URI") or "").strip()
        )
        if not app_id or not app_secret or not redirect_uri:
            raise ValueError("instagram_meta_app_id/secret/redirect_uri are required")

        page_id = str(settings_map.get("instagram_page_id") or "").strip() or None
        page_access_token = str(settings_map.get("instagram_page_access_token") or "").strip() or None
        if require_page_token and (not page_id or not page_access_token):
            raise ValueError("Instagram authorization required: instagram_page_id and instagram_page_access_token")

        verify_token = str(settings_map.get("instagram_verify_token") or "").strip()
        if not verify_token:
            verify_token = hashlib.md5(f"ig-verify:{connected_integration_id}".encode("utf-8")).hexdigest()

        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            instagram_business_account_id=business_id,
            pipeline_id=int(pipeline_id),
            channel_id=int(channel_id),
            default_responsible_user_id=_to_int(settings_map.get("instagram_default_responsible_user_id"), None),
            lead_subject_template=str(settings_map.get("instagram_lead_subject_template") or "").strip() or "Instagram {client_id}",
            verify_token=verify_token,
            page_id=page_id,
            page_access_token=page_access_token,
            meta_app_id=app_id,
            meta_app_secret=app_secret,
            meta_redirect_uri=redirect_uri,
            find_active_lead_by_external_id=_to_bool(settings_map.get("instagram_find_active_lead_by_external_user"), True),
        )

    @classmethod
    async def _sync_reverse_indexes(cls, runtime: RuntimeConfig) -> None:
        await cls._redis_set(
            cls._redis_key("map", "business_ci", runtime.instagram_business_account_id),
            runtime.connected_integration_id,
            InstagramCrmChannelConfig.MAP_TTL_SEC,
        )
        await cls._redis_set(
            cls._redis_key("map", "verify_ci", hashlib.md5(runtime.verify_token.encode("utf-8")).hexdigest()),
            runtime.connected_integration_id,
            InstagramCrmChannelConfig.MAP_TTL_SEC,
        )

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
        return f"ig:{runtime.instagram_business_account_id}:{external_user_id}"

    @classmethod
    def _extract_external_user_from_client_external_id(
        cls, runtime: RuntimeConfig, external_id: Optional[str]
    ) -> Optional[str]:
        value = str(external_id or "").strip()
        prefix = f"ig:{runtime.instagram_business_account_id}:"
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
                value=external_user_id,
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
                # Legacy key for backward compatibility with old cache entries.
                "lead_id": int(ticket_id),
                "chat_id": str(chat_id),
            }
        )
        await cls._redis_set(cls._redis_key("map", "by_user", runtime.connected_integration_id, external_user_id), payload, InstagramCrmChannelConfig.MAP_TTL_SEC)
        await cls._redis_set(cls._redis_key("map", "by_chat", runtime.connected_integration_id, chat_id), payload, InstagramCrmChannelConfig.MAP_TTL_SEC)

    @classmethod
    async def _resolve_mapping_by_user(cls, runtime: RuntimeConfig, external_user_id: str) -> Optional[LeadContext]:
        raw = await cls._redis_get(cls._redis_key("map", "by_user", runtime.connected_integration_id, external_user_id))
        if raw:
            try:
                data = _json_loads(raw)
            except Exception:
                data = {}
            client_id = _to_int(data.get("client_id"), None) if isinstance(data, dict) else None
            ticket_id = _to_int(data.get("ticket_id"), None) if isinstance(data, dict) else None
            if not ticket_id:
                ticket_id = _to_int(data.get("lead_id"), None) if isinstance(data, dict) else None
            chat_id = str(data.get("chat_id") or "").strip() if isinstance(data, dict) else ""
            if ticket_id and chat_id:
                ticket = await cls._get_ticket_by_id(runtime, int(ticket_id))
                if ticket and ticket.status in InstagramCrmChannelConfig.ACTIVE_TICKET_STATUSES and str(ticket.chat_id or "") == chat_id:
                    resolved_client_id = _to_int(client_id, None) or _to_int(ticket.client_id, None)
                    if resolved_client_id:
                        return LeadContext(
                            client_id=int(resolved_client_id),
                            ticket_id=int(ticket_id),
                            chat_id=chat_id,
                        )

        client = await cls._find_client_by_instagram_id(runtime, external_user_id)
        if (not client or not client.id) and runtime.find_active_lead_by_external_id:
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
                return LeadContext(
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
            chat_response = await api.call("Chat/Get", {"ids": [chat_id], "limit": 1, "offset": 0}, APIBaseResponse[Any])
        if not chat_response.ok or not isinstance(chat_response.result, list) or not chat_response.result:
            return None

        row = chat_response.result[0] if isinstance(chat_response.result[0], dict) else {}
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
            external_user_id_from_ticket = str(ticket.external_dialog_id or "").strip()
            if (
                ticket_channel_id
                and int(ticket_channel_id) == int(runtime.channel_id)
                and external_user_id_from_ticket
            ):
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
    def _render_lead_subject(cls, runtime: RuntimeConfig, external_user_id: str) -> str:
        template = str(runtime.lead_subject_template or "").strip() or "Instagram {client_id}"
        try:
            subject = template.format(client_id=external_user_id, external_user_id=external_user_id)
        except Exception:
            subject = template
        return str(subject or "").strip() or f"Instagram {external_user_id}"

    @classmethod
    async def _create_ticket_context(
        cls, runtime: RuntimeConfig, external_user_id: str
    ) -> LeadContext:
        client = await cls._resolve_or_create_client(runtime, external_user_id)
        if not client.id:
            raise RuntimeError("Client id is empty after resolve/create")
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.crm.ticket.add(
                TicketAddRequest(
                    client_id=int(client.id),
                    channel_id=int(runtime.channel_id),
                    direction=TicketDirectionEnum.Inbound,
                    external_dialog_id=external_user_id,
                    responsible_user_id=runtime.default_responsible_user_id,
                    subject=cls._render_lead_subject(runtime, external_user_id),
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
        return LeadContext(
            client_id=int(client.id),
            ticket_id=int(ticket_id),
            chat_id=str(ticket.chat_id),
        )

    @classmethod
    async def _resolve_or_create_lead(cls, runtime: RuntimeConfig, external_user_id: str) -> LeadContext:
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
    async def _post_chat_message(cls, runtime: RuntimeConfig, lead_ctx: LeadContext, external_user_id: str, text: str, message_id: str) -> None:
        external_message_id = cls._inbound_external_message_id(runtime, external_user_id, message_id)
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/Add",
                ChatMessageAddRequest(
                    chat_id=lead_ctx.chat_id,
                    author_entity_type="Client",
                    author_entity_id=lead_ctx.client_id,
                    message_type=ChatMessageTypeEnum.Regular,
                    text=text,
                    external_message_id=external_message_id,
                ),
                APIBaseResponse[Dict[str, Any]],
            )
        if not response.ok:
            payload = response.result if isinstance(response.result, dict) else {}
            raise RuntimeError(f"ChatMessage/Add rejected: error={payload.get('error')} description={payload.get('description')}")

    @classmethod
    def _extract_messaging_events(cls, body: Any, runtime: RuntimeConfig) -> List[Dict[str, Any]]:
        if not isinstance(body, dict):
            return []
        obj = str(body.get("object") or "").strip().lower()
        if obj and obj not in {"instagram", "page"}:
            return []

        events: List[Dict[str, Any]] = []
        for entry in body.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or "").strip()
            if entry_id and entry_id != runtime.instagram_business_account_id:
                continue
            for event in entry.get("messaging") or []:
                if isinstance(event, dict):
                    events.append(event)
        return events

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
        if _redis_enabled() and not await cls._redis_set_nx(dedupe_key, "1", InstagramCrmChannelConfig.DEDUPE_TTL_SEC):
            return "ignored_duplicate"

        text = cls._extract_message_text(event)
        if not text:
            return "ignored_empty"

        lead_ctx = await cls._resolve_or_create_lead(runtime, external_user_id)
        await cls._post_chat_message(runtime, lead_ctx, external_user_id, text, message_id)
        return "accepted"

    async def _meta_exchange_code(self, runtime: RuntimeConfig, code: str) -> str:
        response = await self.http_client.get(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/oauth/access_token",
            params={
                "client_id": runtime.meta_app_id,
                "client_secret": runtime.meta_app_secret,
                "redirect_uri": runtime.meta_redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        token = str(response.json().get("access_token") or "").strip()
        if not token:
            raise RuntimeError("Meta OAuth token exchange did not return access_token")
        return token

    async def _meta_exchange_long_lived(self, runtime: RuntimeConfig, short_token: str) -> str:
        response = await self.http_client.get(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": runtime.meta_app_id,
                "client_secret": runtime.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        response.raise_for_status()
        token = str(response.json().get("access_token") or "").strip()
        if not token:
            raise RuntimeError("Meta long-lived token exchange did not return access_token")
        return token

    async def _meta_resolve_page_for_instagram(self, runtime: RuntimeConfig, user_access_token: str) -> Tuple[str, str]:
        response = await self.http_client.get(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/me/accounts",
            params={
                "access_token": user_access_token,
                "fields": "id,name,access_token,instagram_business_account{id,username}",
            },
        )
        response.raise_for_status()

        rows = response.json().get("data") or []
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            ig = row.get("instagram_business_account") or {}
            if not isinstance(ig, dict):
                continue
            if str(ig.get("id") or "").strip() != runtime.instagram_business_account_id:
                continue
            page_id = str(row.get("id") or "").strip()
            page_access_token = str(row.get("access_token") or "").strip()
            if page_id and page_access_token:
                return page_id, page_access_token

        raise RuntimeError("No page found for configured instagram_business_account_id")

    async def _meta_send_text_message(self, runtime: RuntimeConfig, external_user_id: str, text: str) -> Optional[str]:
        if not runtime.page_id or not runtime.page_access_token:
            raise RuntimeError("Instagram page authorization is missing")

        response = await self.http_client.post(
            f"{InstagramCrmChannelConfig.GRAPH_BASE_URL}/{runtime.page_id}/messages",
            params={"access_token": runtime.page_access_token},
            json={
                "recipient": {"id": external_user_id},
                "message": {"text": text},
                "messaging_type": "RESPONSE",
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
            response = await api.call(
                "ChatMessage/Get",
                ChatMessageGetRequest(chat_id=chat_id, ids=[message_id], limit=1, offset=0, include_staff_private=True),
                APIBaseResponse[Any],
            )
        if not response.ok or not isinstance(response.result, list) or not response.result:
            return None
        try:
            return ChatMessage.model_validate(response.result[0])
        except Exception:
            return None

    @classmethod
    async def _mark_chat_message_sent(cls, connected_integration_id: str, message_id: str, external_message_id: str) -> None:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.call(
                "ChatMessage/MarkSent",
                ChatMessageMarkSentRequest(id=message_id, external_message_id=external_message_id),
                APIBaseResponse[Any],
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

            remote_message_id = await self._meta_send_text_message(runtime, external_user_id, text)
            external_message_id = self._outbound_external_message_id(runtime, external_user_id, remote_message_id or message_id)
            await self._mark_chat_message_sent(runtime.connected_integration_id, message_id, external_message_id)
            return {"status": "accepted", "chat_id": chat_id, "message_id": message_id}
        except Exception:
            if _redis_enabled():
                await self._redis_delete(dedupe_key)
            raise

    def _resolve_ci_from_envelope(self, envelope: Dict[str, Any]) -> Optional[str]:
        if self.connected_integration_id:
            return str(self.connected_integration_id).strip()

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
    async def _resolve_ci_by_verify_token(cls, verify_token: str) -> Optional[str]:
        key = cls._redis_key("map", "verify_ci", hashlib.md5(str(verify_token or "").encode("utf-8")).hexdigest())
        value = await cls._redis_get(key)
        return str(value or "").strip() or None

    @classmethod
    async def _resolve_ci_by_business_id(cls, business_id: str) -> Optional[str]:
        value = await cls._redis_get(cls._redis_key("map", "business_ci", business_id))
        return str(value or "").strip() or None

    @staticmethod
    def _html_page(title: str, text: str) -> str:
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>"
            + str(title)
            + "</title><style>body{font-family:Arial,sans-serif;margin:40px;line-height:1.5;}</style></head><body><h1>"
            + str(title)
            + "</h1><p>"
            + str(text)
            + "</p></body></html>"
        )

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id)
        if not await self._is_connected_integration_active(ci, force_refresh=True):
            return self._error_response(1004, f"ConnectedIntegration '{ci}' is inactive").dict()

        try:
            runtime = await self._load_runtime(ci, require_page_token=False)
            await self._sync_reverse_indexes(runtime)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        return {
            "status": "connected",
            "authorized": bool(runtime.page_id and runtime.page_access_token),
            "instagram_business_account_id": runtime.instagram_business_account_id,
            "verify_token": runtime.verify_token,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        try:
            runtime = await self._load_runtime(str(self.connected_integration_id), require_page_token=False)
            await self._redis_delete(
                self._redis_key("map", "business_ci", runtime.instagram_business_account_id),
                self._redis_key("map", "verify_ci", hashlib.md5(runtime.verify_token.encode("utf-8")).hexdigest()),
            )
        except Exception:
            pass
        await self._redis_delete(self._redis_key("settings", self.connected_integration_id))
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
        await self._redis_delete(self._redis_key("settings", self.connected_integration_id))
        return {"status": "settings updated", "reconnect": await self.reconnect()}

    async def handle_ui(self, envelope: Dict[str, Any]) -> Any:
        if str(envelope.get("method") or "").upper() != "GET":
            return Response(status_code=405, content="Method not allowed")

        query = envelope.get("query") or {}
        ci = self._resolve_ci_from_envelope(envelope)

        state = _query_get(query, "state")
        state_ci, state_nonce = self._decode_oauth_state(state or "") if state else (None, None)
        if not ci and state_ci:
            ci = state_ci
        if not ci:
            return HTMLResponse(self._html_page("Instagram CRM Channel", "connected_integration_id is required"), status_code=400)

        if not await self._is_connected_integration_active(ci):
            return HTMLResponse(self._html_page("Instagram CRM Channel", f"ConnectedIntegration '{ci}' is inactive"), status_code=403)

        try:
            runtime = await self._load_runtime(ci, require_page_token=False)
            await self._sync_reverse_indexes(runtime)
        except Exception as error:
            return HTMLResponse(self._html_page("Instagram CRM Channel", str(error)), status_code=400)

        oauth_error = _query_get(query, "error")
        if oauth_error:
            return HTMLResponse(self._html_page("Instagram OAuth Error", _query_get(query, "error_description") or oauth_error), status_code=400)

        oauth_code = _query_get(query, "code")
        if oauth_code:
            if not state_ci or not state_nonce or state_ci != ci:
                return HTMLResponse(self._html_page("Instagram OAuth Error", "Invalid OAuth state"), status_code=400)

            if _redis_enabled():
                cached_ci = await self._consume_oauth_state(state_nonce)
                if cached_ci != ci:
                    return HTMLResponse(self._html_page("Instagram OAuth Error", "OAuth state expired or invalid"), status_code=400)

            try:
                short_token = await self._meta_exchange_code(runtime, oauth_code)
                long_token = await self._meta_exchange_long_lived(runtime, short_token)
                page_id, page_access_token = await self._meta_resolve_page_for_instagram(runtime, long_token)
                await self._edit_settings(ci, {
                    "instagram_page_id": page_id,
                    "instagram_page_access_token": page_access_token,
                    "instagram_verify_token": runtime.verify_token,
                })
                runtime = await self._load_runtime(ci, require_page_token=True)
                await self._sync_reverse_indexes(runtime)
                return HTMLResponse(self._html_page("Instagram Connected", f"Business account: {runtime.instagram_business_account_id}"), status_code=200)
            except Exception as error:
                logger.exception("Instagram OAuth callback failed: ci=%s", ci)
                return HTMLResponse(self._html_page("Instagram OAuth Error", str(error)), status_code=500)

        nonce = uuid.uuid4().hex
        await self._store_oauth_state(ci, nonce)
        oauth_url = f"{InstagramCrmChannelConfig.OAUTH_DIALOG_URL}?{urlencode({
            'client_id': runtime.meta_app_id,
            'redirect_uri': runtime.meta_redirect_uri,
            'response_type': 'code',
            'scope': ','.join(InstagramCrmChannelConfig.OAUTH_SCOPES),
            'state': self._encode_oauth_state(ci, nonce),
        })}"
        return RedirectResponse(url=oauth_url, status_code=302)

    async def handle_external(self, envelope: Dict[str, Any]) -> Any:
        method = str(envelope.get("method") or "").upper()
        query = envelope.get("query") or {}
        body = envelope.get("body")

        ci = self._resolve_ci_from_envelope(envelope)

        if method == "GET":
            verify_token = _query_get(query, "hub.verify_token") or _query_get(query, "verify_token")
            mode = _query_get(query, "hub.mode") or _query_get(query, "mode")
            challenge = _query_get(query, "hub.challenge") or _query_get(query, "challenge")

            if not ci and verify_token:
                ci = await self._resolve_ci_by_verify_token(verify_token)
            if not ci:
                return Response(status_code=403, content="Missing connected_integration_id")
            if not await self._is_connected_integration_active(ci):
                return Response(status_code=200, content="ignored")

            try:
                runtime = await self._load_runtime(ci, require_page_token=False)
            except Exception as error:
                return Response(status_code=400, content=str(error))

            if mode == "subscribe" and verify_token == runtime.verify_token:
                await self._sync_reverse_indexes(runtime)
                return Response(status_code=200, content=str(challenge or ""), media_type="text/plain")
            return Response(status_code=403, content="Forbidden")

        if method != "POST":
            return Response(status_code=405, content="Method not allowed")
        if not isinstance(body, dict):
            return self._error_response(400, "Invalid webhook payload").dict()

        if not ci:
            candidates: List[str] = []
            for entry in body.get("entry") or []:
                if not isinstance(entry, dict):
                    continue
                business_id = str(entry.get("id") or "").strip()
                if not business_id:
                    continue
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
            runtime = await self._load_runtime(ci, require_page_token=False)
            await self._sync_reverse_indexes(runtime)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        events = self._extract_messaging_events(body, runtime)
        if not events:
            return {"status": "ignored", "reason": "no_supported_events"}

        accepted = 0
        ignored = 0
        reasons: Dict[str, int] = {}
        for event in events:
            try:
                decision = await self._process_inbound_event(runtime, event)
                if decision == "accepted":
                    accepted += 1
                else:
                    ignored += 1
                    reasons[decision] = reasons.get(decision, 0) + 1
            except Exception as error:
                ignored += 1
                key = f"error:{type(error).__name__}"
                reasons[key] = reasons.get(key, 0) + 1
                logger.exception("Inbound Instagram event failed: ci=%s", ci)

        return {"status": "accepted" if accepted else "ignored", "accepted": accepted, "ignored": ignored, "ignored_reasons": reasons}

    async def handle_webhook(self, action: Optional[str] = None, data: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()

        ci = str(self.connected_integration_id)
        if not await self._is_connected_integration_active(ci):
            return {"status": "ignored", "reason": "connected_integration_inactive"}

        normalized_action, payload, event_id = self._normalize_regos_webhook_payload(action, data, extra)
        if normalized_action not in InstagramCrmChannelConfig.SUPPORTED_INBOUND_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{normalized_action}"}

        try:
            runtime = await self._load_runtime(ci, require_page_token=True)
            await self._sync_reverse_indexes(runtime)
            return await self._process_regos_chat_message_added(runtime, payload, event_id)
        except Exception as error:
            logger.exception("REGOS webhook processing failed: ci=%s action=%s", ci, normalized_action)
            return self._error_response(1002, str(error)).dict()
