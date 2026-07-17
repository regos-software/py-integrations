from __future__ import annotations

import asyncio
from dataclasses import replace
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import httpx
from fastapi.responses import HTMLResponse, Response

from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_ops, redis_error_contains
from schemas.api.integrations.connected_integration import (
    ConnectedIntegrationGetRequest,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import IntegrationErrorModel, IntegrationErrorResponse

from .config import MetaLeadgenCrmChannelConfig
from .crm_sync import MetaLeadgenCrmSync
from .meta_api import MetaLeadgenApi, headers_ci
from .models import (
    MetaLeadEvent,
    RuntimeConfig,
    normalize_text,
    now_ts,
    parse_field_mapping,
    parse_int_list,
    to_int,
)
from .redis_state import MetaLeadgenRedisState, redis_enabled
from .storage import (
    PageMapConflictError,
    active_connected_integration_ids,
    ensure_schema as ensure_meta_leadgen_db_schema,
    mark_page_map_inactive,
    reassign_page_map,
    resolve_ci_by_page_id as resolve_ci_by_page_id_db,
    upsert_page_map,
)
from .ui import (
    MetaLeadgenUiContext,
    normalize_locale,
    render_meta_leadgen_ui,
    resolve_locale,
)

logger = setup_logger("meta_leadgen_crm_channel")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_MANAGER_LOCK = asyncio.Lock()
_WORKER_TASKS: Dict[str, asyncio.Task] = {}


def _query_get(query: Dict[str, Any], key: str) -> Optional[str]:
    value = query.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    return normalize_text(value)


class MetaLeadgenCrmChannelIntegration(ClientBase):
    _ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
    _ACTIVE_CACHE_LOCK = asyncio.Lock()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.connected_integration_id: Optional[str] = None
        self.http_client = httpx.AsyncClient(
            timeout=MetaLeadgenCrmChannelConfig.HTTP_TIMEOUT_SEC
        )
        self.meta_api = MetaLeadgenApi(self.http_client)

    async def __aenter__(self) -> "MetaLeadgenCrmChannelIntegration":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.http_client.aclose()

    @staticmethod
    def _error_response(code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _normalize_settings_map(settings_map: Optional[Dict[Any, Any]]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key_raw, value_raw in (settings_map or {}).items():
            key = MetaLeadgenCrmChannelIntegration._normalize_setting_key(key_raw)
            if key:
                normalized[key] = str(value_raw or "").strip()
        return normalized

    @staticmethod
    def _normalize_setting_key(value: Any) -> Optional[str]:
        key = normalize_text(value, max_len=128)
        return key.lower() if key else None

    @classmethod
    async def _fetch_setting_key_aliases(
        cls,
        connected_integration_id: str,
    ) -> Dict[str, str]:
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id
                )
            )

        aliases: Dict[str, str] = {}
        for row in response.result or []:
            raw_key = normalize_text(getattr(row, "key", None), max_len=128)
            key = cls._normalize_setting_key(raw_key)
            if not key or not raw_key:
                continue
            if key not in aliases or raw_key != key:
                aliases[key] = raw_key
        return aliases

    @classmethod
    def _store_setting_value(
        cls,
        settings_map: Dict[str, str],
        raw_key: Any,
        value: Any,
    ) -> None:
        key = cls._normalize_setting_key(raw_key)
        if not key:
            return
        raw = normalize_text(raw_key, max_len=128) or key
        current = settings_map.get(key)
        if current is None or raw != key or not current:
            settings_map[key] = str(value or "").strip()

    @staticmethod
    def _setting_truthy(value: Any) -> bool:
        return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}

    @classmethod
    async def _cache_settings_map(
        cls,
        connected_integration_id: str,
        settings_map: Dict[Any, Any],
    ) -> None:
        await MetaLeadgenRedisState.set_json(
            MetaLeadgenRedisState.settings_cache_key(connected_integration_id),
            cls._normalize_settings_map(settings_map),
            MetaLeadgenCrmChannelConfig.SETTINGS_TTL_SEC,
        )

    @classmethod
    async def _fetch_settings_map(
        cls,
        connected_integration_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        cache_key = MetaLeadgenRedisState.settings_cache_key(connected_integration_id)
        cached_settings = cls._normalize_settings_map(
            await MetaLeadgenRedisState.get_json(cache_key)
        )
        if cached_settings and not force_refresh:
            return cached_settings

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id
                )
            )
        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            cls._store_setting_value(
                settings_map,
                getattr(row, "key", None),
                getattr(row, "value", ""),
            )

        await cls._cache_settings_map(connected_integration_id, settings_map)
        return settings_map

    @classmethod
    async def _edit_settings(
        cls,
        connected_integration_id: str,
        patch: Dict[str, str],
        *,
        settings_map: Optional[Dict[Any, Any]] = None,
    ) -> None:
        normalized_patch = cls._normalize_settings_map(patch)
        if not normalized_patch:
            return
        aliases = await cls._fetch_setting_key_aliases(connected_integration_id)
        rows = []
        for normalized_key, value in normalized_patch.items():
            rows.append(
                ConnectedIntegrationSettingEditItem(
                    connected_integration_id=connected_integration_id,
                    key=aliases.get(normalized_key, normalized_key),
                    value=str(value or ""),
                )
            )
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.edit(
                ConnectedIntegrationSettingEditRequest(rows)
            )
        if not response.ok:
            raise RuntimeError(f"ConnectedIntegrationSetting/Edit rejected: {response.result}")
        if settings_map is not None:
            updated_settings = cls._normalize_settings_map(settings_map)
            updated_settings.update(normalized_patch)
            await cls._cache_settings_map(connected_integration_id, updated_settings)
            return
        await MetaLeadgenRedisState.delete(
            MetaLeadgenRedisState.settings_cache_key(connected_integration_id)
        )

    @classmethod
    async def _is_connected_integration_active(
        cls,
        connected_integration_id: str,
        force_refresh: bool = False,
    ) -> bool:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci:
            return True

        now = time.monotonic()
        if not force_refresh:
            async with cls._ACTIVE_CACHE_LOCK:
                cached = cls._ACTIVE_CACHE.get(ci)
            if cached and cached[1] > now:
                return cached[0]

            cached_raw = await MetaLeadgenRedisState.get(
                MetaLeadgenRedisState.ci_active_cache_key(ci)
            )
            if cached_raw in {"0", "1"}:
                active = cached_raw == "1"
                async with cls._ACTIVE_CACHE_LOCK:
                    cls._ACTIVE_CACHE[ci] = (
                        active,
                        now + MetaLeadgenCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
                    )
                return active

        active = False
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
                    row_ci = normalize_text(getattr(row, "connected_integration_id", None))
                    if row_ci and row_ci != ci:
                        continue
                    row_active = getattr(row, "is_active", None)
                    active = bool(row_active)
                    break
        except httpx.HTTPStatusError as error:
            status_code = (
                int(error.response.status_code)
                if error.response is not None
                else None
            )
            if status_code not in {401, 403, 404}:
                raise
            logger.info(
                "Meta Leadgen active check treated integration as inactive: ci=%s status=%s",
                ci,
                status_code,
            )

        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (
                active,
                now + MetaLeadgenCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
            )
        await MetaLeadgenRedisState.set(
            MetaLeadgenRedisState.ci_active_cache_key(ci),
            "1" if active else "0",
            MetaLeadgenCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
        )
        return active

    @classmethod
    async def _mark_ci_active(cls, connected_integration_id: str) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci:
            return
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE[ci] = (
                True,
                time.monotonic() + MetaLeadgenCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
            )
        await MetaLeadgenRedisState.set(
            MetaLeadgenRedisState.ci_active_cache_key(ci),
            "1",
            MetaLeadgenCrmChannelConfig.ACTIVE_CACHE_TTL_SEC,
        )
        await MetaLeadgenRedisState.mark_ci_active(ci)

    @classmethod
    async def _mark_ci_inactive(cls, connected_integration_id: str) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci:
            return
        async with cls._ACTIVE_CACHE_LOCK:
            cls._ACTIVE_CACHE.pop(ci, None)
        await MetaLeadgenRedisState.delete(MetaLeadgenRedisState.ci_active_cache_key(ci))
        await MetaLeadgenRedisState.mark_ci_inactive(ci)

    @classmethod
    async def _load_runtime(
        cls,
        connected_integration_id: str,
        *,
        require_access_token: bool,
        require_page_id: bool,
        force_refresh: bool = False,
    ) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(
            connected_integration_id,
            force_refresh=force_refresh,
        )
        MetaLeadgenApi.app_config()
        webhook_verify_token = MetaLeadgenApi.webhook_verify_token()

        page_id = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID),
            max_len=128,
        )
        page_access_token = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN)
        )
        page_name = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME),
            max_len=250,
        )
        access_token_expires_at = to_int(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT),
            None,
        )
        if require_page_id and not page_id:
            raise ValueError("meta_page_id is required")
        if require_access_token and (not page_id or not page_access_token):
            raise ValueError("Meta authorization required: meta_page_id and meta_page_access_token")

        title_template = (
            normalize_text(settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_TITLE_TEMPLATE), max_len=250)
            or MetaLeadgenCrmChannelConfig.DEFAULT_TITLE_TEMPLATE
        )
        return RuntimeConfig(
            connected_integration_id=connected_integration_id,
            page_id=page_id,
            page_name=page_name,
            page_access_token=page_access_token,
            access_token_expires_at=access_token_expires_at,
            pipeline_id=to_int(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PIPELINE_ID),
                None,
            ),
            stage_id=to_int(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_STAGE_ID),
                None,
            ),
            responsible_user_id=to_int(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_RESPONSIBLE_USER_ID),
                None,
            ),
            participant_user_ids=parse_int_list(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PARTICIPANT_USER_IDS)
            ),
            title_template=title_template,
            webhook_verify_token=webhook_verify_token,
            client_field_mapping=parse_field_mapping(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_CLIENT_FIELD_MAPPING)
            ),
            lead_field_mapping=parse_field_mapping(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_LEAD_FIELD_MAPPING)
            ),
        )

    @staticmethod
    def _is_runtime_authorized(runtime: RuntimeConfig) -> bool:
        return bool(runtime.page_id and runtime.page_access_token)

    @classmethod
    def _authorization_settings_patch(
        cls,
        *,
        authorized: bool,
        authorization_url: str = "",
        generated_at: Optional[int] = None,
    ) -> Dict[str, str]:
        if authorized:
            return {
                MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZED: "true",
                MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_STATUS: "authorized",
                MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL: "",
                MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL_GENERATED_AT: "",
            }
        return {
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZED: "false",
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_STATUS: "authorization_required",
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL: str(authorization_url or "").strip(),
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL_GENERATED_AT: str(generated_at or ""),
        }

    @classmethod
    def _authorization_url_settings_patch(
        cls,
        *,
        authorization_url: str,
        generated_at: int,
    ) -> Dict[str, str]:
        return {
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL: str(
                authorization_url or ""
            ).strip(),
            MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL_GENERATED_AT: str(
                generated_at or ""
            ),
        }

    @classmethod
    async def _save_authorization_state(
        cls,
        connected_integration_id: str,
        *,
        authorized: bool,
        authorization_url: str = "",
        generated_at: Optional[int] = None,
    ) -> None:
        await cls._edit_settings(
            connected_integration_id,
            cls._authorization_settings_patch(
                authorized=authorized,
                authorization_url=authorization_url,
                generated_at=generated_at,
            ),
        )

    @staticmethod
    def _authorization_url_has_current_scopes(authorization_url: str) -> bool:
        try:
            parsed = urlparse(str(authorization_url or ""))
            query = parse_qs(parsed.query)
        except Exception:
            return False
        scopes = query.get("scope") or []
        scope_value = str(scopes[0] if scopes else "").strip()
        return scope_value == ",".join(MetaLeadgenCrmChannelConfig.OAUTH_SCOPES)

    @staticmethod
    def _authorization_url_has_locale(authorization_url: str, locale: str) -> bool:
        expected = normalize_locale(locale)
        if not expected:
            return True
        try:
            parsed = urlparse(str(authorization_url or ""))
            query = parse_qs(parsed.query)
        except Exception:
            return False
        states = query.get("state") or []
        _, _, state_locale = MetaLeadgenApi.decode_oauth_state(str(states[0] if states else ""))
        return normalize_locale(state_locale) == expected

    @classmethod
    def _authorization_url_is_fresh(
        cls,
        settings_map: Dict[str, str],
        authorization_url: str,
        locale: str = "",
    ) -> bool:
        generated_at = to_int(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL_GENERATED_AT),
            None,
        )
        if not generated_at:
            return False
        if not cls._authorization_url_has_current_scopes(authorization_url):
            return False
        if locale and not cls._authorization_url_has_locale(authorization_url, locale):
            return False
        return now_ts() < int(generated_at) + MetaLeadgenCrmChannelConfig.OAUTH_STATE_TTL_SEC - 60

    @classmethod
    async def _get_or_refresh_authorization_url(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        settings_map: Dict[str, str],
        locale: str = "",
    ) -> str:
        if cls._is_runtime_authorized(runtime):
            if (
                not cls._setting_truthy(settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZED))
                or settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_STATUS) != "authorized"
                or settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL)
            ):
                await cls._save_authorization_state(connected_integration_id, authorized=True)
            return ""

        existing_url = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL)
        )
        if existing_url and cls._authorization_url_is_fresh(settings_map, existing_url, locale):
            return existing_url

        generated_at = now_ts()
        authorization_url = await MetaLeadgenApi.build_oauth_url(connected_integration_id, locale)
        await cls._edit_settings(
            connected_integration_id,
            cls._authorization_url_settings_patch(
                authorization_url=authorization_url,
                generated_at=generated_at,
            ),
            settings_map=settings_map,
        )
        return authorization_url

    @classmethod
    async def _write_page_mapping(
        cls,
        *,
        connected_integration_id: str,
        page_id: str,
        require_persistent_map: bool,
    ) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        page = normalize_text(page_id, max_len=128)
        if not ci:
            if require_persistent_map:
                raise RuntimeError("connected_integration_id is required for persistent mapping")
            return
        if not page:
            if require_persistent_map:
                raise RuntimeError("meta_page_id is required for persistent mapping")
            return

        try:
            stored = await upsert_page_map(
                connected_integration_id=ci,
                page_id=page,
                is_active=True,
            )
        except PageMapConflictError:
            raise
        except Exception:
            if require_persistent_map:
                raise
            return
        if require_persistent_map and not stored:
            raise RuntimeError("Meta page mapping was not stored")
        if stored:
            await MetaLeadgenRedisState.sync_page_index(ci, page)

    @classmethod
    async def _clear_meta_page_binding(
        cls,
        connected_integration_id: str,
        *,
        expected_page_id: Optional[str] = None,
    ) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        expected = normalize_text(expected_page_id, max_len=128)
        if not ci:
            return

        should_clear_settings = True
        if expected:
            try:
                settings_map = await cls._fetch_settings_map(ci, force_refresh=True)
                current_page = normalize_text(
                    settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID),
                    max_len=128,
                )
                should_clear_settings = not current_page or current_page == expected
            except Exception as error:
                logger.warning(
                    "Failed to read previous Meta Leadgen settings before unlink: ci=%s page_id=%s error=%s",
                    ci,
                    expected,
                    error,
                )
                should_clear_settings = True

        if not should_clear_settings:
            return

        try:
            await cls._edit_settings(
                ci,
                {
                    MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID: "",
                    MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME: "",
                    MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN: "",
                    MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT: "",
                    **cls._authorization_settings_patch(authorized=False),
                },
            )
        except Exception as error:
            logger.warning(
                "Failed to clear previous Meta Leadgen integration settings: ci=%s page_id=%s error=%s",
                ci,
                expected,
                error,
            )

        await cls._mark_ci_inactive(ci)
        await cls._stop_stream_worker(ci)
        keys = [
            MetaLeadgenRedisState.settings_cache_key(ci),
            MetaLeadgenRedisState.ci_active_cache_key(ci),
            MetaLeadgenRedisState.field_ready_key(ci),
        ]
        if expected:
            keys.append(MetaLeadgenRedisState.page_ci_key(expected))
        await MetaLeadgenRedisState.delete(*keys)

    @classmethod
    async def _move_page_mapping_to_integration(
        cls,
        *,
        connected_integration_id: str,
        page_id: str,
    ) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        page = normalize_text(page_id, max_len=128)
        if not ci:
            raise RuntimeError("connected_integration_id is required for persistent mapping")
        if not page:
            raise RuntimeError("meta_page_id is required for persistent mapping")

        previous_ci = await reassign_page_map(
            connected_integration_id=ci,
            page_id=page,
        )
        if previous_ci and previous_ci != ci:
            await cls._clear_meta_page_binding(
                previous_ci,
                expected_page_id=page,
            )
        await MetaLeadgenRedisState.sync_page_index(ci, page)

    @classmethod
    async def _sync_reverse_indexes(
        cls,
        runtime: RuntimeConfig,
        *,
        persist_page_map: bool = False,
        require_persistent_map: bool = False,
    ) -> None:
        page_id = normalize_text(runtime.page_id, max_len=128)
        if not page_id:
            if require_persistent_map:
                raise RuntimeError("meta_page_id is required for persistent mapping")
            return

        if persist_page_map or require_persistent_map:
            await cls._write_page_mapping(
                connected_integration_id=runtime.connected_integration_id,
                page_id=page_id,
                require_persistent_map=require_persistent_map,
            )
            return

        await MetaLeadgenRedisState.sync_page_index(
            runtime.connected_integration_id,
            page_id,
        )

    @classmethod
    async def _load_runtime_for_page_event(
        cls,
        connected_integration_id: str,
        event_page_id: str,
    ) -> RuntimeConfig:
        page = normalize_text(event_page_id, max_len=128)
        runtime = await cls._load_runtime(
            connected_integration_id,
            require_access_token=False,
            require_page_id=False,
        )
        if not runtime.page_id or not runtime.page_access_token or (page and runtime.page_id != page):
            runtime = await cls._load_runtime(
                connected_integration_id,
                require_access_token=False,
                require_page_id=False,
                force_refresh=True,
            )

        if page and not runtime.page_id:
            runtime = replace(runtime, page_id=page)

        if not runtime.page_id or not runtime.page_access_token:
            raise ValueError("Meta authorization required: meta_page_id and meta_page_access_token")
        return runtime

    def _resolve_ci_from_envelope(self, envelope: Dict[str, Any]) -> Optional[str]:
        instance_ci = str(getattr(self, "connected_integration_id", "") or "").strip()
        if instance_ci:
            return instance_ci

        headers = envelope.get("headers") or {}
        query = envelope.get("query") or {}
        ci = headers_ci(headers, "Connected-Integration-Id")
        if ci:
            return ci
        for key in ("connected_integration_id", "ci"):
            ci = _query_get(query, key)
            if ci:
                return ci

        body = envelope.get("body")
        if isinstance(body, dict):
            ci = normalize_text(body.get("connected_integration_id"), max_len=128)
            if ci:
                return ci
        return None

    @classmethod
    async def _resolve_ci_by_page_id(cls, page_id: str) -> Optional[str]:
        page = normalize_text(page_id, max_len=128)
        if not page:
            return None

        resolved = await MetaLeadgenRedisState.resolve_ci_by_page_id(page)
        if resolved:
            return resolved

        try:
            resolved = await resolve_ci_by_page_id_db(page)
        except Exception:
            logger.exception("Failed to resolve Meta Leadgen page mapping: page_id=%s", page)
            raise
        if resolved:
            await MetaLeadgenRedisState.sync_page_index(resolved, page)
            return resolved
        return None

    @staticmethod
    def _extract_lead_events(body: Any) -> List[MetaLeadEvent]:
        if not isinstance(body, dict):
            return []
        obj = normalize_text(body.get("object"), max_len=32)
        if obj and obj.lower() != "page":
            return []

        events: List[MetaLeadEvent] = []
        for entry in body.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            entry_page_id = normalize_text(entry.get("id"), max_len=128)
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                if str(change.get("field") or "").strip().lower() != "leadgen":
                    continue
                value = change.get("value")
                if not isinstance(value, dict):
                    continue
                page_id = normalize_text(value.get("page_id"), max_len=128) or entry_page_id
                leadgen_id = normalize_text(value.get("leadgen_id"), max_len=128)
                if not page_id or not leadgen_id:
                    continue
                events.append(
                    MetaLeadEvent(
                        page_id=page_id,
                        leadgen_id=leadgen_id,
                        form_id=normalize_text(value.get("form_id"), max_len=128),
                        created_time=to_int(value.get("created_time"), None),
                        ad_id=normalize_text(value.get("ad_id"), max_len=128),
                        raw_value=value,
                    )
                )
        return events

    @classmethod
    async def _enqueue_event(
        cls,
        connected_integration_id: str,
        *,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        attempt: int = 0,
        last_error: Optional[str] = None,
    ) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci:
            raise ValueError("connected_integration_id is required")
        await cls._ensure_stream_worker(ci)
        await cls._mark_ci_active(ci)
        await MetaLeadgenRedisState.enqueue(
            MetaLeadgenRedisState.stream_key(ci),
            {
                "connected_integration_id": ci,
                "kind": "meta_lead",
                "payload": payload,
                "event_id": event_id or "",
                "attempt": str(max(int(attempt), 0)),
                "last_error": last_error or "",
                "enqueued_at": str(now_ts()),
            },
        )

    @classmethod
    async def _ensure_stream_worker(cls, connected_integration_id: str) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci or not redis_enabled():
            return
        async with _MANAGER_LOCK:
            task = _WORKER_TASKS.get(ci)
            if task and not task.done():
                return
            _WORKER_TASKS[ci] = asyncio.create_task(
                cls._stream_worker_loop(ci),
                name=f"meta_leadgen_crm_channel_stream_{ci}",
            )

    @classmethod
    async def _stop_stream_worker(cls, connected_integration_id: str) -> None:
        ci = normalize_text(connected_integration_id, max_len=128)
        if not ci:
            return
        async with _MANAGER_LOCK:
            task = _WORKER_TASKS.pop(ci, None)
        if not task:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error while stopping Meta Leadgen stream worker: ci=%s", ci)

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
                logger.exception("Error while stopping Meta Leadgen background task")

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not redis_enabled():
            return {"total": 0, "restored": 0, "failed": 0}

        try:
            ci_ids = await active_connected_integration_ids()
        except Exception as error:
            logger.exception("Meta Leadgen auto-restore failed to read MariaDB mappings: %s", error)
            return {"total": 0, "restored": 0, "failed": 1}

        if not ci_ids:
            logger.info("Meta Leadgen auto-restore: no active integrations found")
            return {"total": 0, "restored": 0, "failed": 0}

        restored = 0
        failed = 0
        for ci in ci_ids:
            try:
                if not await cls._is_connected_integration_active(ci, force_refresh=True):
                    await cls._mark_ci_inactive(ci)
                    failed += 1
                    continue
                runtime = await cls._load_runtime(
                    ci,
                    require_access_token=False,
                    require_page_id=False,
                )
                await cls._sync_reverse_indexes(runtime, persist_page_map=True)
                await MetaLeadgenRedisState.ensure_consumer_group(
                    MetaLeadgenRedisState.stream_key(ci)
                )
                await cls._ensure_stream_worker(ci)
                await cls._mark_ci_active(ci)
                restored += 1
            except Exception as error:
                failed += 1
                logger.exception("Meta Leadgen auto-restore failed: ci=%s error=%s", ci, error)
        return {"total": len(ci_ids), "restored": restored, "failed": failed}

    @classmethod
    async def _stream_worker_loop(cls, connected_integration_id: str) -> None:
        ci = normalize_text(connected_integration_id, max_len=128) or ""
        stream_key = MetaLeadgenRedisState.stream_key(ci)
        consumer = f"{_INSTANCE_ID}:{ci[:8]}"
        worker = cls()
        worker.connected_integration_id = ci
        logger.info("Meta Leadgen stream worker started: ci=%s", ci)
        try:
            await MetaLeadgenRedisState.ensure_consumer_group(stream_key)
            while True:
                try:
                    if not await cls._is_connected_integration_active(ci):
                        await cls._mark_ci_inactive(ci)
                        logger.info("Meta Leadgen stream worker stopped for inactive integration: ci=%s", ci)
                        break
                    await MetaLeadgenRedisState.set_worker_heartbeat(ci)
                    await MetaLeadgenRedisState.touch_stream_ttl(stream_key)

                    for entry_id, fields in await MetaLeadgenRedisState.process_claimed_entries(stream_key, consumer):
                        await cls._process_stream_entry(
                            worker=worker,
                            stream_key=stream_key,
                            entry_id=entry_id,
                            fields=fields,
                        )

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=MetaLeadgenCrmChannelConfig.STREAM_GROUP,
                            consumername=consumer,
                            streams={stream_key: ">"},
                            count=MetaLeadgenCrmChannelConfig.STREAM_BATCH_SIZE,
                            block=MetaLeadgenCrmChannelConfig.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await MetaLeadgenRedisState.ensure_consumer_group(stream_key)
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
                    logger.exception("Meta Leadgen stream worker error: ci=%s error=%s", ci, error)
                    await asyncio.sleep(2)
        finally:
            try:
                await worker.http_client.aclose()
            except Exception:
                logger.exception("Error while closing Meta Leadgen worker HTTP client")
            async with _MANAGER_LOCK:
                current = _WORKER_TASKS.get(ci)
                if current is asyncio.current_task():
                    _WORKER_TASKS.pop(ci, None)

    @classmethod
    async def _process_stream_entry(
        cls,
        *,
        worker: "MetaLeadgenCrmChannelIntegration",
        stream_key: str,
        entry_id: str,
        fields: Dict[str, Any],
    ) -> None:
        ci = normalize_text(fields.get("connected_integration_id") or worker.connected_integration_id, max_len=128)
        kind = normalize_text(fields.get("kind"), max_len=32)
        payload = MetaLeadgenRedisState.decode_stream_payload(fields.get("payload"))
        event = MetaLeadEvent.from_payload(payload)
        if not ci or kind != "meta_lead" or not event:
            logger.warning("Meta Leadgen stream entry has invalid payload: entry_id=%s fields=%s", entry_id, fields)
            await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
            return

        attempt = MetaLeadgenRedisState.stream_entry_attempt(fields)
        dedupe_key = MetaLeadgenRedisState.dedupe_key(ci, event.event_id)
        dedupe_acquired = await MetaLeadgenRedisState.set_nx(
            dedupe_key,
            "1",
            MetaLeadgenCrmChannelConfig.DEDUPE_TTL_SEC,
        )
        if redis_enabled() and not dedupe_acquired:
            await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
            return

        try:
            runtime = await cls._load_runtime_for_page_event(ci, event.page_id)
            if runtime.page_id != event.page_id:
                logger.warning(
                    "Meta Leadgen stream entry page mismatch: ci=%s runtime_page_id=%s event_page_id=%s",
                    ci,
                    runtime.page_id,
                    event.page_id,
                )
                if dedupe_acquired:
                    await MetaLeadgenRedisState.delete(dedupe_key)
                await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
                return
            await cls._sync_reverse_indexes(runtime)
            result = await MetaLeadgenCrmSync.process_meta_lead(
                runtime,
                event,
                worker.meta_api,
            )
            logger.info(
                "Meta Leadgen stream job processed: ci=%s leadgen_id=%s status=%s",
                ci,
                event.leadgen_id,
                result.get("status") if isinstance(result, dict) else result,
            )
            await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
        except Exception as error:
            if dedupe_acquired:
                await MetaLeadgenRedisState.delete(dedupe_key)
            next_attempt = attempt + 1
            if next_attempt >= MetaLeadgenCrmChannelConfig.STREAM_MAX_RETRIES:
                dlq_payload = dict(fields)
                dlq_payload["attempt"] = str(next_attempt)
                dlq_payload["source_stream"] = stream_key
                dlq_payload["source_entry_id"] = entry_id
                dlq_payload["failed_at"] = str(now_ts())
                dlq_payload["error"] = str(error)
                await MetaLeadgenRedisState.enqueue(
                    MetaLeadgenRedisState.dlq_stream_key(ci),
                    dlq_payload,
                )
                await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
                logger.error(
                    "Meta Leadgen stream job moved to DLQ: ci=%s entry_id=%s error=%s",
                    ci,
                    entry_id,
                    error,
                )
                return

            await cls._enqueue_event(
                ci,
                payload=event.to_payload(),
                event_id=event.event_id,
                attempt=next_attempt,
                last_error=str(error),
            )
            await MetaLeadgenRedisState.ack_stream_entry(stream_key, entry_id)
            logger.warning(
                "Meta Leadgen stream job requeued: ci=%s entry_id=%s attempt=%s error=%s",
                ci,
                entry_id,
                next_attempt,
                error,
            )

    @classmethod
    def _ui_settings_error_key(cls, error: Exception) -> str:
        text = str(error or "")
        if "Service Meta Leadgen app config" in text or "Service Meta Leadgen webhook verify token" in text:
            return "notice_service_unavailable"
        if "Meta authorization required" in text:
            return "notice_authorization_required"
        if "meta_page_id" in text:
            return "notice_settings_required"
        if "field mapping" in text.lower() or "pipeline" in text.lower() or "stage" in text.lower():
            return "notice_settings_required"
        return "notice_error"

    @staticmethod
    def _ui_response(
        *,
        connected_integration_id: str,
        locale: str,
        mode: str,
        authorization_url: str = "",
        page_name: Optional[str] = None,
        message_key: str = "",
        message: str = "",
        disconnect_token: str = "",
        status_code: int = 200,
    ) -> HTMLResponse:
        return HTMLResponse(
            render_meta_leadgen_ui(
                MetaLeadgenUiContext(
                    connected_integration_id=connected_integration_id,
                    locale=locale,
                    mode=mode,
                    authorization_url=authorization_url,
                    page_name=page_name,
                    message_key=message_key,
                    message=message,
                    disconnect_token=disconnect_token,
                )
            ),
            status_code=status_code,
        )

    @classmethod
    async def _store_ui_action_token(cls, connected_integration_id: str, action: str) -> str:
        token = uuid.uuid4().hex
        await MetaLeadgenRedisState.set(
            MetaLeadgenRedisState.key("ui_action", action, connected_integration_id, token),
            "1",
            MetaLeadgenCrmChannelConfig.OAUTH_STATE_TTL_SEC,
            min_ttl_sec=30,
        )
        return token

    @classmethod
    async def _consume_ui_action_token(cls, connected_integration_id: str, action: str, token: str) -> bool:
        normalized_token = str(token or "").strip()
        if not normalized_token:
            return False
        key = MetaLeadgenRedisState.key("ui_action", action, connected_integration_id, normalized_token)
        value = await MetaLeadgenRedisState.get(key)
        await MetaLeadgenRedisState.delete(key)
        return value == "1"

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        ci = str(self.connected_integration_id)
        if not await self._is_connected_integration_active(ci, force_refresh=True):
            return self._error_response(1004, f"ConnectedIntegration '{ci}' is inactive").dict()

        try:
            await ensure_meta_leadgen_db_schema()
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            field_result = await MetaLeadgenCrmSync.ensure_required_fields(ci, force=True)
            mapping_result = await MetaLeadgenCrmSync.validate_mapping_fields(runtime, force=True)
            authorized = self._is_runtime_authorized(runtime)
            subscribe_result: Dict[str, Any] = {"status": "skipped"}
            if authorized:
                await self._sync_reverse_indexes(
                    runtime,
                    persist_page_map=True,
                    require_persistent_map=True,
                )
                subscribe_result = await self.meta_api.subscribe_page(
                    str(runtime.page_id),
                    str(runtime.page_access_token),
                )
                authorization_url = ""
                await self._save_authorization_state(ci, authorized=True)
            else:
                generated_at = now_ts()
                authorization_url = await MetaLeadgenApi.build_oauth_url(ci)
                await self._edit_settings(
                    ci,
                    self._authorization_url_settings_patch(
                        authorization_url=authorization_url,
                        generated_at=generated_at,
                    ),
                )
            await self._mark_ci_active(ci)
            await MetaLeadgenRedisState.ensure_consumer_group(
                MetaLeadgenRedisState.stream_key(ci)
            )
            await self._ensure_stream_worker(ci)
        except PageMapConflictError as error:
            logger.warning(
                "Meta Leadgen connect found page moved to another integration: ci=%s page_id=%s owner_ci=%s",
                ci,
                error.page_id,
                error.connected_integration_id,
            )
            await self._clear_meta_page_binding(
                ci,
                expected_page_id=error.page_id,
            )
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            field_result = {"status": "skipped"}
            mapping_result = {"status": "skipped"}
            subscribe_result = {"status": "skipped"}
            authorized = False
            authorization_url = await MetaLeadgenApi.build_oauth_url(ci)
            await self._mark_ci_active(ci)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        return {
            "status": "connected",
            "authorized": authorized,
            "meta_page_id": runtime.page_id,
            "queue_enabled": True,
            "authorization_url": authorization_url,
            "page_subscription": subscribe_result,
            "required_fields": field_result,
            "mapping_fields": mapping_result,
        }

    async def disconnect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        ci = str(self.connected_integration_id)
        keys = [
            MetaLeadgenRedisState.settings_cache_key(ci),
            MetaLeadgenRedisState.ci_active_cache_key(ci),
            MetaLeadgenRedisState.field_ready_key(ci),
        ]
        runtime: Optional[RuntimeConfig] = None
        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
        except Exception:
            runtime = None

        try:
            if runtime and runtime.page_id:
                keys.append(MetaLeadgenRedisState.page_ci_key(runtime.page_id))
                await mark_page_map_inactive(
                    connected_integration_id=ci,
                    page_id=runtime.page_id or None,
                )
            else:
                await mark_page_map_inactive(connected_integration_id=ci)
        except Exception as error:
            logger.exception(
                "Failed to mark Meta Leadgen page mapping inactive during disconnect: ci=%s error=%s",
                ci,
                error,
            )
            return self._error_response(1001, str(error)).dict()

        await self._edit_settings(
            ci,
            {
                MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID: "",
                MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME: "",
                MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN: "",
                MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT: "",
                **self._authorization_settings_patch(authorized=False),
            },
        )
        await self._mark_ci_inactive(ci)
        await self._stop_stream_worker(ci)
        await MetaLeadgenRedisState.delete(*keys)
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
        await MetaLeadgenRedisState.delete(
            MetaLeadgenRedisState.settings_cache_key(str(self.connected_integration_id))
        )
        return {"status": "settings updated"}

    async def handle_ui(self, envelope: Dict[str, Any]) -> Any:
        locale = resolve_locale(envelope)
        if str(envelope.get("method") or "").upper() != "GET":
            return self._ui_response(
                connected_integration_id=self._resolve_ci_from_envelope(envelope) or "",
                locale=locale,
                mode="unavailable",
                status_code=405,
            )
        if not redis_enabled():
            return self._ui_response(
                connected_integration_id=self._resolve_ci_from_envelope(envelope) or "",
                locale=locale,
                mode="unavailable",
                status_code=503,
            )

        query = envelope.get("query") or {}
        ci = self._resolve_ci_from_envelope(envelope)

        state = _query_get(query, "state")
        state_ci, state_nonce, state_lang = MetaLeadgenApi.decode_oauth_state(state or "") if state else (None, None, None)
        has_query_lang = any(_query_get(query, key) for key in ("lang", "locale", "language", "hl"))
        if state_lang and not has_query_lang:
            locale = normalize_locale(state_lang)
        if not ci and state_ci:
            ci = state_ci
        if not ci:
            return self._ui_response(
                connected_integration_id="",
                locale=locale,
                mode="missing_context",
                status_code=400,
            )

        if not await self._is_connected_integration_active(ci):
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="inactive",
                status_code=403,
            )

        action = _query_get(query, "action")
        if action == "confirm_disconnect":
            token = await self._store_ui_action_token(ci, "disconnect")
            try:
                runtime = await self._load_runtime(
                    ci,
                    require_access_token=False,
                    require_page_id=False,
                )
                page_name = runtime.page_name
            except Exception:
                page_name = None
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="confirm_disconnect",
                page_name=page_name,
                disconnect_token=token,
                status_code=200,
            )

        if action == "disconnect":
            token = _query_get(query, "token") or ""
            if not await self._consume_ui_action_token(ci, "disconnect", token):
                try:
                    runtime = await self._load_runtime(
                        ci,
                        require_access_token=False,
                        require_page_id=False,
                    )
                    settings_map = await self._fetch_settings_map(ci)
                    authorization_url = await self._get_or_refresh_authorization_url(
                        ci,
                        runtime,
                        settings_map,
                        locale,
                    )
                    page_name = runtime.page_name
                except Exception:
                    authorization_url = ""
                    page_name = None
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="error",
                    authorization_url=authorization_url,
                    page_name=page_name,
                    message_key="notice_invalid_disconnect",
                    status_code=400,
                )

            self.connected_integration_id = ci
            result = await self.disconnect()
            if isinstance(result, dict) and "result" in result:
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="error",
                    message_key="notice_disconnect_failed",
                    status_code=500,
                )
            try:
                runtime = await self._load_runtime(
                    ci,
                    require_access_token=False,
                    require_page_id=False,
                )
                settings_map = await self._fetch_settings_map(ci)
                authorization_url = await self._get_or_refresh_authorization_url(
                    ci,
                    runtime,
                    settings_map,
                    locale,
                )
            except Exception:
                authorization_url = ""
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="disconnected_success",
                authorization_url=authorization_url,
                page_name=None,
                status_code=200,
            )

        try:
            await ensure_meta_leadgen_db_schema()
            settings_map = await self._fetch_settings_map(ci, force_refresh=True)
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            authorized_runtime = self._is_runtime_authorized(runtime)
            await self._sync_reverse_indexes(
                runtime,
                persist_page_map=authorized_runtime,
                require_persistent_map=authorized_runtime,
            )
        except PageMapConflictError as error:
            await self._clear_meta_page_binding(
                ci,
                expected_page_id=error.page_id,
            )
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            settings_map = await self._fetch_settings_map(ci, force_refresh=True)
            authorization_url = await self._get_or_refresh_authorization_url(
                ci,
                runtime,
                settings_map,
                locale,
            )
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="disconnected",
                authorization_url=authorization_url,
                page_name=None,
                status_code=200,
            )
        except Exception as error:
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="error",
                message_key=self._ui_settings_error_key(error),
                status_code=400,
            )

        oauth_error = _query_get(query, "error")
        if oauth_error:
            authorization_url = await MetaLeadgenApi.build_oauth_url(ci, locale)
            return self._ui_response(
                connected_integration_id=ci,
                locale=locale,
                mode="oauth_error",
                authorization_url=authorization_url,
                page_name=runtime.page_name,
                status_code=400,
            )

        oauth_code = _query_get(query, "code")
        if oauth_code:
            if not state_ci or not state_nonce or state_ci != ci:
                authorization_url = await MetaLeadgenApi.build_oauth_url(ci, locale)
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="session_expired",
                    authorization_url=authorization_url,
                    page_name=runtime.page_name,
                    status_code=400,
                )
            cached_ci = await MetaLeadgenApi.consume_oauth_state(state_nonce)
            if cached_ci != ci:
                authorization_url = await MetaLeadgenApi.build_oauth_url(ci, locale)
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="session_expired",
                    authorization_url=authorization_url,
                    page_name=runtime.page_name,
                    status_code=400,
                )

            try:
                short_token, short_expires_at = await self.meta_api.exchange_code(oauth_code)
                long_token, long_expires_at = await self.meta_api.exchange_long_lived(short_token)
                page_id, page_name, page_token = await self.meta_api.resolve_page(runtime, long_token)
                await self.meta_api.subscribe_page(page_id, page_token)
                await self._move_page_mapping_to_integration(
                    connected_integration_id=ci,
                    page_id=page_id,
                )
                await self._edit_settings(
                    ci,
                    {
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID: page_id,
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME: page_name or "",
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN: page_token,
                        MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT: str(
                            long_expires_at or short_expires_at or ""
                        ),
                        **self._authorization_settings_patch(authorized=True),
                    },
                    settings_map=settings_map,
                )
                runtime = replace(
                    runtime,
                    page_id=page_id,
                    page_name=page_name,
                    page_access_token=page_token,
                    access_token_expires_at=to_int(
                        long_expires_at or short_expires_at,
                        None,
                    ),
                )
                await MetaLeadgenCrmSync.ensure_required_fields(ci, force=True)
                await MetaLeadgenCrmSync.validate_mapping_fields(runtime, force=True)
                await self._mark_ci_active(ci)
                await MetaLeadgenRedisState.ensure_consumer_group(
                    MetaLeadgenRedisState.stream_key(ci)
                )
                await self._ensure_stream_worker(ci)
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="connected_success",
                    page_name=runtime.page_name,
                    status_code=200,
                )
            except Exception as error:
                logger.exception("Meta OAuth callback failed: ci=%s", ci)
                authorization_url = ""
                try:
                    authorization_url = await MetaLeadgenApi.build_oauth_url(ci, locale)
                except Exception:
                    pass
                return self._ui_response(
                    connected_integration_id=ci,
                    locale=locale,
                    mode="error",
                    authorization_url=authorization_url,
                    page_name=runtime.page_name,
                    message_key=self._ui_settings_error_key(error),
                    status_code=500,
                )

        authorization_url = await self._get_or_refresh_authorization_url(ci, runtime, settings_map, locale)
        authorized = self._is_runtime_authorized(runtime)
        return self._ui_response(
            connected_integration_id=ci,
            locale=locale,
            mode="connected" if authorized else "disconnected",
            authorization_url=authorization_url,
            page_name=runtime.page_name,
            status_code=200,
        )

    async def handle_external(self, envelope: Dict[str, Any]) -> Any:
        method = str(envelope.get("method") or "").upper()
        query = envelope.get("query") or {}
        body = envelope.get("body")
        raw_body = envelope.get("raw_body")
        headers = envelope.get("headers") or {}

        if method == "GET":
            verify_token = _query_get(query, "hub.verify_token") or _query_get(query, "verify_token")
            mode = _query_get(query, "hub.mode") or _query_get(query, "mode")
            challenge = _query_get(query, "hub.challenge") or _query_get(query, "challenge")
            try:
                expected_verify_token = MetaLeadgenApi.webhook_verify_token()
            except Exception as error:
                return Response(status_code=400, content=str(error))
            if mode == "subscribe" and verify_token == expected_verify_token:
                return Response(status_code=200, content=str(challenge or ""), media_type="text/plain")
            return Response(status_code=403, content="Forbidden")

        if method != "POST":
            return Response(status_code=405, content="Method not allowed")
        if not redis_enabled():
            return Response(status_code=503, content="Redis is required for this integration")
        if not isinstance(body, dict):
            return self._error_response(400, "Invalid webhook payload").dict()

        _, app_secret, _ = MetaLeadgenApi.app_config()
        if not MetaLeadgenApi.verify_signature(headers, raw_body, app_secret):
            return Response(status_code=403, content="Invalid signature")

        events = self._extract_lead_events(body)
        if not events:
            return {"status": "ignored", "reason": "no_supported_events"}

        explicit_ci = self._resolve_ci_from_envelope(envelope)
        accepted = 0
        ignored = 0
        reasons: Dict[str, int] = {}
        for event in events:
            ci = await self._resolve_ci_by_page_id(event.page_id) or explicit_ci
            if not ci:
                ignored += 1
                reason = "connected_integration_id_not_resolved"
                reasons[reason] = reasons.get(reason, 0) + 1
                continue
            if not await self._is_connected_integration_active(ci):
                ignored += 1
                reason = "connected_integration_inactive"
                reasons[reason] = reasons.get(reason, 0) + 1
                continue
            try:
                runtime = await self._load_runtime_for_page_event(ci, event.page_id)
                if runtime.page_id != event.page_id:
                    ignored += 1
                    reason = "page_id_mismatch"
                    reasons[reason] = reasons.get(reason, 0) + 1
                    continue
                await self._sync_reverse_indexes(
                    runtime,
                    persist_page_map=True,
                    require_persistent_map=True,
                )
                await self._enqueue_event(
                    ci,
                    payload=event.to_payload(),
                    event_id=event.event_id,
                )
                accepted += 1
            except Exception as error:
                logger.exception(
                    "Failed to enqueue Meta lead webhook: ci=%s page_id=%s leadgen_id=%s",
                    ci,
                    event.page_id,
                    event.leadgen_id,
                )
                ignored += 1
                reason = f"enqueue_failed:{type(error).__name__}"
                reasons[reason] = reasons.get(reason, 0) + 1

        return {
            "status": "accepted" if accepted else "ignored",
            "queued": accepted,
            "ignored": ignored,
            "ignored_reasons": reasons,
        }

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        _ = action, data, extra
        return {"status": "ignored", "reason": "crm_webhooks_not_supported"}
