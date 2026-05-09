from __future__ import annotations

import asyncio
import html
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

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

    @classmethod
    async def _fetch_settings_map(
        cls,
        connected_integration_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        cache_key = MetaLeadgenRedisState.settings_cache_key(connected_integration_id)
        if not force_refresh:
            cached = await MetaLeadgenRedisState.get_json(cache_key)
            if cached is not None:
                return {str(k): str(v or "") for k, v in cached.items()}

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(
                    connected_integration_id=connected_integration_id
                )
            )
        settings_map: Dict[str, str] = {}
        for row in response.result or []:
            key = normalize_text(getattr(row, "key", None))
            if key:
                settings_map[key] = str(getattr(row, "value", "") or "").strip()

        await MetaLeadgenRedisState.set_json(
            cache_key,
            settings_map,
            MetaLeadgenCrmChannelConfig.SETTINGS_TTL_SEC,
        )
        return settings_map

    @classmethod
    async def _edit_settings(
        cls,
        connected_integration_id: str,
        patch: Dict[str, str],
    ) -> None:
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
            response = await api.integrations.connected_integration_setting.edit(
                ConnectedIntegrationSettingEditRequest(rows)
            )
        if not response.ok:
            raise RuntimeError(f"ConnectedIntegrationSetting/Edit rejected: {response.result}")
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

        async with RegosAPI(connected_integration_id=ci) as api:
            response = await api.integrations.connected_integration.get(
                ConnectedIntegrationGetRequest(
                    connected_integration_ids=[ci],
                    include_name=False,
                    include_schedule=False,
                )
            )
        active = False
        if response.ok and isinstance(response.result, list):
            for row in response.result:
                row_ci = normalize_text(getattr(row, "connected_integration_id", None))
                if row_ci and row_ci != ci:
                    continue
                row_active = getattr(row, "is_active", None)
                active = bool(row_active)
                break

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
    async def _load_runtime(
        cls,
        connected_integration_id: str,
        *,
        require_access_token: bool,
        require_page_id: bool,
    ) -> RuntimeConfig:
        settings_map = await cls._fetch_settings_map(connected_integration_id)
        MetaLeadgenApi.app_config()
        webhook_verify_token = MetaLeadgenApi.webhook_verify_token()

        page_id = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID),
            max_len=128,
        )
        page_access_token = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN)
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
            page_name=normalize_text(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME),
                max_len=250,
            ),
            page_access_token=page_access_token,
            access_token_expires_at=to_int(
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT),
                None,
            ),
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
    def _authorization_url_is_fresh(settings_map: Dict[str, str]) -> bool:
        generated_at = to_int(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL_GENERATED_AT),
            None,
        )
        if not generated_at:
            return False
        return now_ts() < int(generated_at) + MetaLeadgenCrmChannelConfig.OAUTH_STATE_TTL_SEC - 60

    @classmethod
    async def _get_or_refresh_authorization_url(
        cls,
        connected_integration_id: str,
        runtime: RuntimeConfig,
        settings_map: Dict[str, str],
    ) -> str:
        if cls._is_runtime_authorized(runtime):
            if (
                settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZED) != "true"
                or settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_STATUS) != "authorized"
                or settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL)
            ):
                await cls._save_authorization_state(connected_integration_id, authorized=True)
            return ""

        existing_url = normalize_text(
            settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_URL)
        )
        if existing_url and cls._authorization_url_is_fresh(settings_map):
            return existing_url

        generated_at = now_ts()
        authorization_url = await MetaLeadgenApi.build_oauth_url(connected_integration_id)
        await cls._save_authorization_state(
            connected_integration_id,
            authorized=False,
            authorization_url=authorization_url,
            generated_at=generated_at,
        )
        return authorization_url

    @classmethod
    async def _sync_reverse_indexes(cls, runtime: RuntimeConfig) -> None:
        await MetaLeadgenRedisState.sync_page_index(
            runtime.connected_integration_id,
            runtime.page_id,
        )

    def _resolve_ci_from_envelope(self, envelope: Dict[str, Any]) -> Optional[str]:
        if self.connected_integration_id:
            return normalize_text(self.connected_integration_id, max_len=128)

        headers = envelope.get("headers") or {}
        query = envelope.get("query") or {}
        ci = headers_ci(headers, "Connected-Integration-Id") or headers_ci(
            headers,
            "connected-integration-id",
        )
        if ci:
            return ci
        for key in ("connected_integration_id", "ci"):
            ci = _query_get(query, key)
            if ci:
                return ci
        body = envelope.get("body")
        if isinstance(body, dict):
            return normalize_text(body.get("connected_integration_id"), max_len=128)
        return None

    @classmethod
    async def _resolve_ci_by_page_id(cls, page_id: str) -> Optional[str]:
        resolved = await MetaLeadgenRedisState.resolve_ci_by_page_id(page_id)
        if resolved:
            return resolved

        expected = normalize_text(page_id, max_len=128)
        if not expected or not redis_enabled():
            return None
        for ci in await MetaLeadgenRedisState.active_ci_ids():
            runtime = await cls._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            await cls._sync_reverse_indexes(runtime)
            if runtime.page_id == expected:
                return ci
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
        await MetaLeadgenRedisState.mark_ci_active(ci)
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

        ci_ids = await MetaLeadgenRedisState.active_ci_ids()
        if not ci_ids:
            logger.info("Meta Leadgen auto-restore: no active integrations found")
            return {"total": 0, "restored": 0, "failed": 0}
        await MetaLeadgenRedisState.touch_active_ci_ids_ttl(force=True)

        restored = 0
        failed = 0
        for ci in ci_ids:
            try:
                if not await cls._is_connected_integration_active(ci, force_refresh=True):
                    await MetaLeadgenRedisState.mark_ci_inactive(ci)
                    failed += 1
                    continue
                runtime = await cls._load_runtime(
                    ci,
                    require_access_token=False,
                    require_page_id=False,
                )
                await cls._sync_reverse_indexes(runtime)
                await MetaLeadgenRedisState.ensure_consumer_group(
                    MetaLeadgenRedisState.stream_key(ci)
                )
                await cls._ensure_stream_worker(ci)
                await MetaLeadgenRedisState.mark_ci_active(ci)
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
                        await MetaLeadgenRedisState.mark_ci_inactive(ci)
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
            runtime = await cls._load_runtime(
                ci,
                require_access_token=True,
                require_page_id=True,
            )
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

    @staticmethod
    def _html_page(title: str, text: str) -> str:
        safe_title = html.escape(str(title))
        safe_text = html.escape(str(text))
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>"
            + safe_title
            + "</title><style>body{font-family:Arial,sans-serif;margin:40px;line-height:1.5;}</style></head><body><h1>"
            + safe_title
            + "</h1><p>"
            + safe_text
            + "</p></body></html>"
        )

    @staticmethod
    def _ui_page(
        *,
        connected_integration_id: str,
        authorized: bool,
        authorization_url: str,
        authorization_status: str,
        page_id: Optional[str],
        page_name: Optional[str],
        verify_token: str,
    ) -> str:
        safe_ci = html.escape(connected_integration_id or "")
        safe_status = html.escape(authorization_status or "")
        safe_page_id = html.escape(page_id or "")
        safe_page_name = html.escape(page_name or "")
        safe_verify_token = html.escape(verify_token or "")
        safe_url = html.escape(authorization_url or "", quote=True)
        action_html = (
            "<span class='badge ok'>Connected</span>"
            if authorized
            else f"<a class='button' href='{safe_url}'>Connect Meta</a>"
            if authorization_url
            else "<span class='badge warn'>Authorization URL is not ready</span>"
        )
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Meta Leadgen CRM Channel</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #172033; background: #f5f7fb; }}
    main {{ max-width: 760px; margin: 40px auto; padding: 0 20px; }}
    section {{ background: #fff; border: 1px solid #dce3ee; border-radius: 8px; padding: 24px; }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    p {{ margin: 0 0 20px; color: #536176; }}
    dl {{ display: grid; grid-template-columns: 220px 1fr; gap: 10px 16px; margin: 0 0 22px; }}
    dt {{ color: #66758c; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .button {{ display: inline-block; padding: 10px 14px; border-radius: 6px; background: #1769e0; color: #fff; text-decoration: none; font-weight: 600; }}
    .badge {{ display: inline-block; padding: 8px 10px; border-radius: 6px; font-weight: 600; }}
    .ok {{ background: #e7f7ee; color: #0d6b3f; }}
    .warn {{ background: #fff4d8; color: #7a5200; }}
    @media (max-width: 640px) {{ dl {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Meta Leadgen CRM Channel</h1>
      <p>{"Meta page connected" if authorized else "Meta authorization required"}</p>
      <dl>
        <dt>Connected integration</dt><dd>{safe_ci}</dd>
        <dt>Authorization status</dt><dd>{safe_status}</dd>
        <dt>Page ID</dt><dd>{safe_page_id or "-"}</dd>
        <dt>Page name</dt><dd>{safe_page_name or "-"}</dd>
        <dt>Verify token</dt><dd>{safe_verify_token}</dd>
      </dl>
      {action_html}
    </section>
  </main>
</body>
</html>"""

    async def connect(self, **_: Any) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id is required").dict()
        if not redis_enabled():
            return self._error_response(1001, "Redis is required for this integration").dict()

        ci = str(self.connected_integration_id)
        if not await self._is_connected_integration_active(ci, force_refresh=True):
            return self._error_response(1004, f"ConnectedIntegration '{ci}' is inactive").dict()

        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            await self._sync_reverse_indexes(runtime)
            field_result = await MetaLeadgenCrmSync.ensure_required_fields(ci, force=True)
            mapping_result = await MetaLeadgenCrmSync.validate_mapping_fields(runtime, force=True)
            authorized = self._is_runtime_authorized(runtime)
            subscribe_result: Dict[str, Any] = {"status": "skipped"}
            if authorized:
                subscribe_result = await self.meta_api.subscribe_page(
                    str(runtime.page_id),
                    str(runtime.page_access_token),
                )
                authorization_url = ""
                await self._save_authorization_state(ci, authorized=True)
            else:
                generated_at = now_ts()
                authorization_url = await MetaLeadgenApi.build_oauth_url(ci)
                await self._save_authorization_state(
                    ci,
                    authorized=False,
                    authorization_url=authorization_url,
                    generated_at=generated_at,
                )
            await MetaLeadgenRedisState.mark_ci_active(ci)
            await MetaLeadgenRedisState.ensure_consumer_group(
                MetaLeadgenRedisState.stream_key(ci)
            )
            await self._ensure_stream_worker(ci)
        except Exception as error:
            return self._error_response(1001, str(error)).dict()

        return {
            "status": "connected",
            "authorized": authorized,
            "meta_page_id": runtime.page_id,
            "verify_token": runtime.webhook_verify_token,
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
        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            if runtime.page_id:
                await MetaLeadgenRedisState.delete(
                    MetaLeadgenRedisState.page_ci_key(runtime.page_id)
                )
        except Exception:
            pass
        await MetaLeadgenRedisState.mark_ci_inactive(ci)
        await self._stop_stream_worker(ci)
        await MetaLeadgenRedisState.delete(
            MetaLeadgenRedisState.settings_cache_key(ci),
            MetaLeadgenRedisState.ci_active_cache_key(ci),
            MetaLeadgenRedisState.field_ready_key(ci),
        )
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
        return {"status": "settings updated", "reconnect": await self.reconnect()}

    async def handle_ui(self, envelope: Dict[str, Any]) -> Any:
        if str(envelope.get("method") or "").upper() != "GET":
            return Response(status_code=405, content="Method not allowed")
        if not redis_enabled():
            return HTMLResponse(
                self._html_page("Meta Leadgen CRM Channel", "Redis is required for this integration"),
                status_code=503,
            )

        query = envelope.get("query") or {}
        ci = self._resolve_ci_from_envelope(envelope)

        state = _query_get(query, "state")
        state_ci, state_nonce = MetaLeadgenApi.decode_oauth_state(state or "") if state else (None, None)
        if not ci and state_ci:
            ci = state_ci
        if not ci:
            return HTMLResponse(
                self._html_page("Meta Leadgen CRM Channel", "connected_integration_id is required"),
                status_code=400,
            )

        if not await self._is_connected_integration_active(ci):
            return HTMLResponse(
                self._html_page("Meta Leadgen CRM Channel", f"ConnectedIntegration '{ci}' is inactive"),
                status_code=403,
            )

        try:
            runtime = await self._load_runtime(
                ci,
                require_access_token=False,
                require_page_id=False,
            )
            await self._sync_reverse_indexes(runtime)
            settings_map = await self._fetch_settings_map(ci)
        except Exception as error:
            return HTMLResponse(self._html_page("Meta Leadgen CRM Channel", str(error)), status_code=400)

        oauth_error = _query_get(query, "error")
        if oauth_error:
            return HTMLResponse(
                self._html_page("Meta OAuth Error", _query_get(query, "error_description") or oauth_error),
                status_code=400,
            )

        oauth_code = _query_get(query, "code")
        if oauth_code:
            if not state_ci or not state_nonce or state_ci != ci:
                return HTMLResponse(self._html_page("Meta OAuth Error", "Invalid OAuth state"), status_code=400)
            cached_ci = await MetaLeadgenApi.consume_oauth_state(state_nonce)
            if cached_ci != ci:
                return HTMLResponse(self._html_page("Meta OAuth Error", "OAuth state expired or invalid"), status_code=400)

            try:
                short_token, short_expires_at = await self.meta_api.exchange_code(oauth_code)
                long_token, long_expires_at = await self.meta_api.exchange_long_lived(short_token)
                page_id, page_name, page_token = await self.meta_api.resolve_page(runtime, long_token)
                await self.meta_api.subscribe_page(page_id, page_token)
                await self._edit_settings(
                    ci,
                    {
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_ID: page_id,
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_NAME: page_name or "",
                        MetaLeadgenCrmChannelConfig.SETTING_PAGE_ACCESS_TOKEN: page_token,
                        MetaLeadgenCrmChannelConfig.SETTING_ACCESS_TOKEN_EXPIRES_AT: str(long_expires_at or short_expires_at or ""),
                        **self._authorization_settings_patch(authorized=True),
                    },
                )
                runtime = await self._load_runtime(ci, require_access_token=True, require_page_id=True)
                await self._sync_reverse_indexes(runtime)
                await MetaLeadgenCrmSync.ensure_required_fields(ci, force=True)
                await MetaLeadgenCrmSync.validate_mapping_fields(runtime, force=True)
                await MetaLeadgenRedisState.mark_ci_active(ci)
                await MetaLeadgenRedisState.ensure_consumer_group(
                    MetaLeadgenRedisState.stream_key(ci)
                )
                await self._ensure_stream_worker(ci)
                settings_map = await self._fetch_settings_map(ci)
                return HTMLResponse(
                    self._ui_page(
                        connected_integration_id=ci,
                        authorized=True,
                        authorization_url="",
                        authorization_status=settings_map.get(MetaLeadgenCrmChannelConfig.SETTING_AUTHORIZATION_STATUS) or "authorized",
                        page_id=runtime.page_id,
                        page_name=runtime.page_name,
                        verify_token=runtime.webhook_verify_token,
                    ),
                    status_code=200,
                )
            except Exception as error:
                logger.exception("Meta OAuth callback failed: ci=%s", ci)
                return HTMLResponse(self._html_page("Meta OAuth Error", str(error)), status_code=500)

        authorization_url = await self._get_or_refresh_authorization_url(ci, runtime, settings_map)
        authorized = self._is_runtime_authorized(runtime)
        authorization_status = "authorized" if authorized else "authorization_required"
        return HTMLResponse(
            self._ui_page(
                connected_integration_id=ci,
                authorized=authorized,
                authorization_url=authorization_url,
                authorization_status=authorization_status,
                page_id=runtime.page_id,
                page_name=runtime.page_name,
                verify_token=runtime.webhook_verify_token,
            ),
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
                reasons["connected_integration_id_not_resolved"] = reasons.get("connected_integration_id_not_resolved", 0) + 1
                continue
            if not await self._is_connected_integration_active(ci):
                ignored += 1
                reasons["connected_integration_inactive"] = reasons.get("connected_integration_inactive", 0) + 1
                continue
            try:
                runtime = await self._load_runtime(
                    ci,
                    require_access_token=True,
                    require_page_id=True,
                )
                if runtime.page_id != event.page_id:
                    ignored += 1
                    reasons["page_id_mismatch"] = reasons.get("page_id_mismatch", 0) + 1
                    continue
                await self._sync_reverse_indexes(runtime)
                await self._enqueue_event(
                    ci,
                    payload=event.to_payload(),
                    event_id=event.event_id,
                )
                accepted += 1
            except Exception as error:
                logger.exception("Failed to enqueue Meta lead webhook: ci=%s page_id=%s leadgen_id=%s", ci, event.page_id, event.leadgen_id)
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
