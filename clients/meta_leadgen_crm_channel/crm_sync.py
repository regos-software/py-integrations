from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.client import Client, ClientAddRequest, ClientEditRequest, ClientGetRequest
from schemas.api.crm.lead import Lead, LeadAddRequest, LeadEditRequest, LeadGetRequest
from schemas.api.references.field import FieldAddRequest, FieldGetRequest
from schemas.api.references.fields import FieldValueAdd, FieldValueEdit

from .config import MetaLeadgenCrmChannelConfig
from .meta_api import MetaLeadgenApi
from .models import (
    MetaLeadDetails,
    MetaLeadEvent,
    RuntimeConfig,
    extract_add_new_id,
    first_field,
    json_dumps,
    normalize_decimal,
    normalize_email,
    normalize_phone,
    normalize_text,
    row_to_dict,
)
from .redis_state import MetaLeadgenRedisState

logger = setup_logger("meta_leadgen_crm_channel")


class MetaLeadgenCrmSync:
    @classmethod
    async def ensure_required_fields(
        cls,
        connected_integration_id: str,
        *,
        force: bool = False,
    ) -> Dict[str, Any]:
        cache_key = MetaLeadgenRedisState.field_ready_key(connected_integration_id)
        if not force and await MetaLeadgenRedisState.get(cache_key) == "1":
            return {"status": "cached"}

        if await cls._field_exists(
            connected_integration_id,
            MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
            MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
        ):
            await MetaLeadgenRedisState.set(
                cache_key,
                "1",
                MetaLeadgenCrmChannelConfig.FIELD_CACHE_TTL_SEC,
            )
            return {
                "status": "exists",
                "entity_type": MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
                "key": MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
            }

        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.references.field.add(
                FieldAddRequest(
                    key=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_KEY,
                    name=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_NAME,
                    entity_type=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
                    data_type=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_DATA_TYPE,
                    required=False,
                )
            )
        if not response.ok:
            if not await cls._field_exists(
                connected_integration_id,
                MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
                MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
            ):
                raise RuntimeError(
                    "Field/Add rejected for Meta lead reference field: "
                    f"{response.result}"
                )

        new_id = extract_add_new_id(response.result)
        for attempt in range(3):
            if await cls._field_exists(
                connected_integration_id,
                MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
                MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
            ):
                await MetaLeadgenRedisState.set(
                    cache_key,
                    "1",
                    MetaLeadgenCrmChannelConfig.FIELD_CACHE_TTL_SEC,
                )
                return {
                    "status": "created",
                    "entity_type": MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_ENTITY_TYPE,
                    "key": MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
                    "new_id": new_id,
                }
            if attempt < 2:
                await asyncio.sleep(0.2)

        raise RuntimeError("Meta lead reference field is not visible after Field/Add")

    @classmethod
    async def validate_mapping_fields(
        cls,
        runtime: RuntimeConfig,
        *,
        force: bool = False,
    ) -> Dict[str, Any]:
        pairs: List[Tuple[str, str]] = []
        pairs.extend(("Client", key) for key in sorted(runtime.client_field_mapping.values()))
        pairs.extend(("Lead", key) for key in sorted(runtime.lead_field_mapping.values()))
        if not pairs:
            return {"status": "empty"}

        digest = hashlib.sha1(json_dumps(pairs).encode("utf-8")).hexdigest()
        cache_key = MetaLeadgenRedisState.mapping_ready_key(runtime.connected_integration_id, digest)
        if not force and await MetaLeadgenRedisState.get(cache_key) == "1":
            return {"status": "cached"}

        missing: List[str] = []
        for entity_type in ("Client", "Lead"):
            keys = sorted({key for pair_entity, key in pairs if pair_entity == entity_type})
            if not keys:
                continue
            existing = await cls._fetch_existing_field_keys(
                runtime.connected_integration_id,
                entity_type,
                keys,
            )
            missing.extend(
                f"{entity_type}:{key}"
                for key in keys
                if key.lower() not in existing
            )

        if missing:
            raise RuntimeError(f"Unknown mapped CRM fields: {', '.join(missing)}")

        await MetaLeadgenRedisState.set(
            cache_key,
            "1",
            MetaLeadgenCrmChannelConfig.FIELD_CACHE_TTL_SEC,
        )
        return {"status": "ok", "fields": len(pairs)}

    @classmethod
    async def process_meta_lead(
        cls,
        runtime: RuntimeConfig,
        event: MetaLeadEvent,
        meta_api: MetaLeadgenApi,
    ) -> Dict[str, Any]:
        await cls.ensure_required_fields(runtime.connected_integration_id)
        await cls.validate_mapping_fields(runtime)

        lock_key = MetaLeadgenRedisState.lock_key(
            runtime.connected_integration_id,
            event.event_id,
        )
        lock_token = await MetaLeadgenRedisState.acquire_lock(
            lock_key,
            MetaLeadgenCrmChannelConfig.LOCK_TTL_SEC,
        )
        if not lock_token:
            await asyncio.sleep(0.25)
            existing = await cls._find_lead_by_ref(
                runtime,
                event.page_id,
                event.leadgen_id,
            )
            if existing and existing.id:
                return {"status": "ignored", "reason": "locked_existing_lead", "lead_id": existing.id}
            raise RuntimeError("Meta lead processing lock is busy")

        try:
            details = await meta_api.fetch_lead_details(runtime, event)
            result = await cls.sync_lead_details(runtime, details)
            return result
        finally:
            await MetaLeadgenRedisState.release_lock(lock_key, lock_token)

    @classmethod
    async def sync_lead_details(
        cls,
        runtime: RuntimeConfig,
        details: MetaLeadDetails,
    ) -> Dict[str, Any]:
        async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as api:
            client = await cls._resolve_or_create_client(api, runtime, details)
            existing_lead = await cls._find_lead_by_ref(
                runtime,
                details.page_id,
                details.leadgen_id,
                api=api,
            )
            if existing_lead and existing_lead.id:
                edit_payload = cls._build_lead_edit_payload(runtime, existing_lead, details)
                if not edit_payload:
                    return {
                        "status": "ignored",
                        "reason": "lead_unchanged",
                        "lead_id": int(existing_lead.id),
                        "client_id": int(client.id) if client and client.id else None,
                    }
                response = await api.crm.lead.edit(
                    LeadEditRequest(id=int(existing_lead.id), **edit_payload)
                )
                if not response.ok:
                    raise RuntimeError(f"Lead/Edit rejected: {response.result}")
                return {
                    "status": "updated",
                    "lead_id": int(existing_lead.id),
                    "client_id": int(client.id) if client and client.id else None,
                }

            add_request = cls._build_lead_add_request(runtime, client, details)
            response = await api.crm.lead.add(add_request)
            if not response.ok:
                duplicate = await cls._find_lead_by_ref(
                    runtime,
                    details.page_id,
                    details.leadgen_id,
                    api=api,
                )
                if duplicate and duplicate.id:
                    return {
                        "status": "ignored",
                        "reason": "lead_created_concurrently",
                        "lead_id": int(duplicate.id),
                        "client_id": int(client.id) if client and client.id else None,
                    }
                raise RuntimeError(f"Lead/Add rejected: {response.result}")
            lead_id = extract_add_new_id(response.result)
            if not lead_id:
                raise RuntimeError("Lead/Add did not return new_id")
            return {
                "status": "created",
                "lead_id": int(lead_id),
                "client_id": int(client.id) if client and client.id else None,
            }

    @classmethod
    async def _field_exists(
        cls,
        connected_integration_id: str,
        entity_type: str,
        full_key: str,
    ) -> bool:
        existing = await cls._fetch_existing_field_keys(
            connected_integration_id,
            entity_type,
            [full_key],
        )
        return full_key.strip().lower() in existing

    @classmethod
    async def _fetch_existing_field_keys(
        cls,
        connected_integration_id: str,
        entity_type: str,
        keys: List[str],
    ) -> Dict[str, str]:
        normalized_keys = [key for key in (normalize_text(item) for item in keys) if key]
        if not normalized_keys:
            return {}
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            response = await api.references.field.get(
                FieldGetRequest(
                    entity_type=entity_type,
                    keys=normalized_keys,
                    limit=max(len(normalized_keys), 1),
                    offset=0,
                )
            )
        if not response.ok:
            raise RuntimeError(
                f"Field/Get rejected: entity_type={entity_type} payload={response.result}"
            )
        existing: Dict[str, str] = {}
        for row in response.result if isinstance(response.result, list) else []:
            row_key = normalize_text(row.get("key") if isinstance(row, dict) else getattr(row, "key", None))
            if row_key:
                existing[row_key.lower()] = row_key
        return existing

    @classmethod
    async def _resolve_or_create_client(
        cls,
        api: RegosAPI,
        runtime: RuntimeConfig,
        details: MetaLeadDetails,
    ) -> Client:
        profile = cls._client_profile(details)
        client = await cls._find_client(api, details, profile)
        client_fields_add = cls._mapped_field_adds(runtime.client_field_mapping, details)

        if not client or not client.id:
            response = await api.crm.client.add(
                ClientAddRequest(
                    external_id=profile.get("external_id"),
                    name=profile.get("name"),
                    phone=profile.get("phone"),
                    email=profile.get("email"),
                    responsible_user_id=runtime.responsible_user_id,
                    fields=client_fields_add or None,
                )
            )
            if not response.ok:
                client = await cls._find_client(api, details, profile)
                if not client or not client.id:
                    raise RuntimeError(f"Client/Add rejected: {response.result}")
            if not client or not client.id:
                new_client_id = extract_add_new_id(response.result)
                if not new_client_id:
                    raise RuntimeError("Client/Add did not return new_id")
                client = await cls._get_client_by_id(api, int(new_client_id))

        if not client or not client.id:
            raise RuntimeError("Client/Get did not return client after resolve/create")

        patch = cls._build_client_patch(runtime, client, profile, details)
        if patch:
            response = await api.crm.client.edit(ClientEditRequest(id=int(client.id), **patch))
            if not response.ok:
                raise RuntimeError(f"Client/Edit rejected: {response.result}")
            refreshed = await cls._get_client_by_id(api, int(client.id))
            return refreshed or client
        return client

    @classmethod
    def _client_profile(cls, details: MetaLeadDetails) -> Dict[str, Optional[str]]:
        first_name = first_field(details.fields, "first_name", "firstname", "first name")
        last_name = first_field(details.fields, "last_name", "lastname", "last name")
        full_name = (
            first_field(details.fields, "full_name", "full name", "name")
            or " ".join(part for part in (first_name, last_name) if part).strip()
            or None
        )
        email = normalize_email(first_field(details.fields, "email", "e-mail"))
        phone = normalize_phone(
            first_field(
                details.fields,
                "phone_number",
                "phone",
                "mobile_phone",
                "mobile",
                "telephone",
            )
        )
        return {
            "name": normalize_text(full_name, max_len=250),
            "phone": phone,
            "email": email,
            "external_id": None if phone or email else details.client_external_id,
        }

    @classmethod
    async def _find_client(
        cls,
        api: RegosAPI,
        details: MetaLeadDetails,
        profile: Dict[str, Optional[str]],
    ) -> Optional[Client]:
        requests: List[ClientGetRequest] = []
        if profile.get("phone"):
            requests.append(ClientGetRequest(phones=[profile["phone"]], limit=20, offset=0))
        if profile.get("email"):
            requests.append(ClientGetRequest(emails=[profile["email"]], limit=20, offset=0))
        requests.append(
            ClientGetRequest(external_ids=[details.client_external_id], limit=20, offset=0)
        )
        for request in requests:
            response = await api.crm.client.get(request)
            rows = response.result if response.ok and isinstance(response.result, list) else []
            valid = [row for row in rows if row and row.id]
            if valid:
                return max(valid, key=lambda row: int(row.id or 0))
        return None

    @staticmethod
    async def _get_client_by_id(api: RegosAPI, client_id: int) -> Optional[Client]:
        response = await api.crm.client.get(ClientGetRequest(ids=[int(client_id)], limit=1, offset=0))
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    def _build_client_patch(
        cls,
        runtime: RuntimeConfig,
        client: Client,
        profile: Dict[str, Optional[str]],
        details: MetaLeadDetails,
    ) -> Dict[str, Any]:
        patch: Dict[str, Any] = {}
        if profile.get("name") and not normalize_text(client.name):
            patch["name"] = profile["name"]
        if profile.get("phone") and not normalize_phone(client.phone):
            patch["phone"] = profile["phone"]
        if profile.get("email") and not normalize_email(client.email):
            patch["email"] = profile["email"]
        if profile.get("external_id") and not normalize_text(client.external_id):
            patch["external_id"] = profile["external_id"]
        if runtime.responsible_user_id and not client.responsible_user_id:
            patch["responsible_user_id"] = runtime.responsible_user_id

        field_edits = cls._changed_field_edits(
            getattr(client, "fields", None),
            cls._mapped_field_edits(runtime.client_field_mapping, details),
        )
        if field_edits:
            patch["fields"] = field_edits
        return patch

    @classmethod
    async def _find_lead_by_ref(
        cls,
        runtime: RuntimeConfig,
        page_id: str,
        leadgen_id: str,
        *,
        api: Optional[RegosAPI] = None,
    ) -> Optional[Lead]:
        from .models import lead_ref_value

        lead_ref = lead_ref_value(page_id, leadgen_id)
        if api is not None:
            response = await api.crm.lead.get(
                LeadGetRequest(
                    filters=[
                        Filter(
                            field=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
                            operator=FilterOperator.Equal,
                            value=lead_ref,
                        )
                    ],
                    limit=1,
                    offset=0,
                )
            )
        else:
            async with RegosAPI(connected_integration_id=runtime.connected_integration_id) as local_api:
                response = await local_api.crm.lead.get(
                    LeadGetRequest(
                        filters=[
                            Filter(
                                field=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
                                operator=FilterOperator.Equal,
                                value=lead_ref,
                            )
                        ],
                        limit=1,
                        offset=0,
                    )
                )
        rows = response.result if response.ok and isinstance(response.result, list) else []
        return rows[0] if rows else None

    @classmethod
    def _build_lead_add_request(
        cls,
        runtime: RuntimeConfig,
        client: Client,
        details: MetaLeadDetails,
    ) -> LeadAddRequest:
        amount = normalize_decimal(first_field(details.fields, "amount"))
        return LeadAddRequest(
            client_id=int(client.id) if client and client.id else None,
            pipeline_id=runtime.pipeline_id,
            stage_id=runtime.stage_id,
            responsible_user_id=runtime.responsible_user_id,
            participant_user_ids=runtime.participant_user_ids or None,
            title=cls._render_title(runtime, details),
            description=cls._render_description(details),
            amount=amount,
            fields=cls._lead_field_adds(runtime, details),
        )

    @classmethod
    def _build_lead_edit_payload(
        cls,
        runtime: RuntimeConfig,
        lead: Lead,
        details: MetaLeadDetails,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        title = cls._render_title(runtime, details)
        if title and normalize_text(lead.title) != title:
            payload["title"] = title
        description = cls._render_description(details)
        if description and normalize_text(lead.description) != description:
            payload["description"] = description
        amount = normalize_decimal(first_field(details.fields, "amount"))
        existing_amount = normalize_decimal(getattr(lead, "amount", None))
        if amount is not None and existing_amount != amount:
            payload["amount"] = amount
        field_edits = cls._changed_field_edits(
            getattr(lead, "fields", None),
            cls._lead_field_edits(runtime, details),
        )
        if field_edits:
            payload["fields"] = field_edits
        return payload

    @classmethod
    def _lead_field_adds(
        cls,
        runtime: RuntimeConfig,
        details: MetaLeadDetails,
    ) -> List[FieldValueAdd]:
        fields = [
            FieldValueAdd(
                key=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
                value=details.lead_ref,
            )
        ]
        fields.extend(cls._mapped_field_adds(runtime.lead_field_mapping, details))
        return fields

    @classmethod
    def _lead_field_edits(
        cls,
        runtime: RuntimeConfig,
        details: MetaLeadDetails,
    ) -> List[FieldValueEdit]:
        fields = [
            FieldValueEdit(
                key=MetaLeadgenCrmChannelConfig.LEAD_REF_FIELD_FULL_KEY,
                value=details.lead_ref,
                deleted=False,
            )
        ]
        fields.extend(cls._mapped_field_edits(runtime.lead_field_mapping, details))
        return fields

    @classmethod
    def _mapped_field_adds(
        cls,
        mapping: Dict[str, str],
        details: MetaLeadDetails,
    ) -> List[FieldValueAdd]:
        rows: List[FieldValueAdd] = []
        for source, target in mapping.items():
            value = cls._mapped_source_value(source, details)
            if value:
                rows.append(FieldValueAdd(key=target, value=value))
        return rows

    @classmethod
    def _mapped_field_edits(
        cls,
        mapping: Dict[str, str],
        details: MetaLeadDetails,
    ) -> List[FieldValueEdit]:
        rows: List[FieldValueEdit] = []
        for source, target in mapping.items():
            value = cls._mapped_source_value(source, details)
            if value:
                rows.append(FieldValueEdit(key=target, value=value, deleted=False))
        return rows

    @staticmethod
    def _mapped_source_value(source: str, details: MetaLeadDetails) -> Optional[str]:
        source_key = str(source or "").strip().lower()
        direct_values = {
            "leadgen_id": details.leadgen_id,
            "page_id": details.page_id,
            "form_id": details.form_id,
            "created_time": str(details.created_time or ""),
            "lead_ref": details.lead_ref,
        }
        value = details.fields.get(source_key)
        if not value:
            value = details.metadata.get(source_key)
        if not value:
            value = direct_values.get(source_key)
        return normalize_text(value, max_len=MetaLeadgenCrmChannelConfig.MAX_FIELD_VALUE_CHARS)

    @staticmethod
    def _existing_field_values_by_key(fields: Any) -> Dict[str, str]:
        values: Dict[str, str] = {}
        if not isinstance(fields, list):
            return values
        for field in fields:
            row = row_to_dict(field)
            key = normalize_text(row.get("key"))
            if key:
                values[key.lower()] = str(row.get("value") or "")
        return values

    @classmethod
    def _changed_field_edits(
        cls,
        existing_fields: Any,
        requested_fields: List[FieldValueEdit],
    ) -> List[FieldValueEdit]:
        if not requested_fields:
            return []
        existing = cls._existing_field_values_by_key(existing_fields)
        changed: List[FieldValueEdit] = []
        for field in requested_fields:
            key = normalize_text(field.key)
            if not key:
                continue
            value = "" if field.value is None else str(field.value)
            if existing.get(key.lower()) != value:
                changed.append(field)
        return changed

    @classmethod
    def _render_title(cls, runtime: RuntimeConfig, details: MetaLeadDetails) -> str:
        profile = cls._client_profile(details)
        tokens: Dict[str, Any] = {
            "leadgen_id": details.leadgen_id,
            "page_id": details.page_id,
            "page_name": runtime.page_name or "",
            "form_id": details.form_id or "",
            "client_name": profile.get("name") or "",
            "phone": profile.get("phone") or "",
            "email": profile.get("email") or "",
        }
        tokens.update(details.metadata)
        template = runtime.title_template or MetaLeadgenCrmChannelConfig.DEFAULT_TITLE_TEMPLATE
        try:
            title = template.format(**tokens)
        except Exception:
            title = template
        return normalize_text(title, max_len=250) or f"Meta Lead {details.leadgen_id}"

    @classmethod
    def _render_description(cls, details: MetaLeadDetails) -> str:
        lines = [
            "Meta Lead",
            f"Leadgen: {details.leadgen_id}",
            f"Page: {details.page_id}",
        ]
        if details.form_id:
            lines.append(f"Form: {details.form_id}")
        if details.created_time:
            lines.append(f"Created time: {details.created_time}")
        for key in sorted(details.metadata):
            lines.append(f"{key}: {details.metadata[key]}")
        if details.fields:
            lines.append("")
            lines.append("Form fields:")
            for key in sorted(details.fields):
                lines.append(f"{key}: {details.fields[key]}")
        text = "\n".join(lines).strip()
        if len(text) > MetaLeadgenCrmChannelConfig.MAX_DESCRIPTION_CHARS:
            return text[: MetaLeadgenCrmChannelConfig.MAX_DESCRIPTION_CHARS]
        return text
