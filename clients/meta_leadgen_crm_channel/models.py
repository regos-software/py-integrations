from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .config import MetaLeadgenCrmChannelConfig


def now_ts() -> int:
    return int(time.time())


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def json_loads(raw: str) -> Any:
    return json.loads(raw)


def to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text)
    except Exception:
        return default


def normalize_text(value: Any, *, max_len: Optional[int] = None) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    if max_len and len(text) > max_len:
        return text[:max_len]
    return text


def normalize_email(value: Any) -> Optional[str]:
    text = normalize_text(value, max_len=254)
    if not text or "@" not in text:
        return None
    return text.lower()


def normalize_phone(value: Any) -> Optional[str]:
    text = normalize_text(value, max_len=64)
    if not text:
        return None
    has_plus = text.startswith("+")
    digits = re.sub(r"\D+", "", text)
    if not digits:
        return None
    if has_plus:
        return f"+{digits}"
    if digits.startswith("00") and len(digits) > 2:
        return f"+{digits[2:]}"
    return digits


def normalize_custom_field_key(value: Any) -> Optional[str]:
    key = normalize_text(value, max_len=128)
    if not key:
        return None
    if not key.startswith("field_"):
        key = f"field_{key}"
    return key


def parse_int_list(value: Any) -> List[int]:
    if value is None:
        return []
    rows: List[Any]
    if isinstance(value, list):
        rows = value
    else:
        text = str(value or "").strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json_loads(text)
                rows = parsed if isinstance(parsed, list) else []
            except Exception:
                rows = []
        else:
            rows = [item.strip() for item in text.split(",")]
    values: List[int] = []
    seen = set()
    for row in rows:
        parsed = to_int(row, None)
        if parsed and parsed > 0 and parsed not in seen:
            seen.add(parsed)
            values.append(parsed)
    return values


def parse_field_mapping(value: Any) -> Dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        parsed = json_loads(text)
    except Exception as error:
        raise ValueError(f"Invalid field mapping JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise ValueError("Field mapping must be a JSON object")
    mapping: Dict[str, str] = {}
    for source_raw, target_raw in parsed.items():
        source = normalize_text(source_raw, max_len=128)
        target = normalize_custom_field_key(target_raw)
        if source and target:
            mapping[source.lower()] = target
    return mapping


def row_to_dict(row: Any) -> Dict[str, Any]:
    if isinstance(row, dict):
        return row
    if hasattr(row, "model_dump"):
        try:
            dumped = row.model_dump(mode="json")
            return dumped if isinstance(dumped, dict) else {}
        except Exception:
            return {}
    return {}


def extract_add_new_id(result: Any) -> Optional[int]:
    payload = row_to_dict(result)
    return to_int(payload.get("new_id"), None)


def normalize_decimal(value: Any) -> Optional[Decimal]:
    text = normalize_text(value, max_len=64)
    if not text:
        return None
    text = text.replace(" ", "").replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def lead_ref_value(page_id: str, leadgen_id: str) -> str:
    return f"v1;page_id={str(page_id).strip()};leadgen_id={str(leadgen_id).strip()}"


def client_external_id(page_id: str, leadgen_id: str) -> str:
    return f"meta_leadgen:{str(page_id).strip()}:{str(leadgen_id).strip()}"[:150]


@dataclass
class RuntimeConfig:
    connected_integration_id: str
    page_id: Optional[str]
    page_name: Optional[str]
    page_access_token: Optional[str]
    access_token_expires_at: Optional[int]
    pipeline_id: Optional[int]
    stage_id: Optional[int]
    responsible_user_id: Optional[int]
    participant_user_ids: List[int]
    title_template: str
    webhook_verify_token: str
    client_field_mapping: Dict[str, str]
    lead_field_mapping: Dict[str, str]


@dataclass
class MetaLeadEvent:
    page_id: str
    leadgen_id: str
    form_id: Optional[str]
    created_time: Optional[int]
    ad_id: Optional[str]
    raw_value: Dict[str, Any]

    @property
    def event_id(self) -> str:
        return f"{self.page_id}:{self.leadgen_id}"

    def to_payload(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id,
            "leadgen_id": self.leadgen_id,
            "form_id": self.form_id or "",
            "created_time": str(self.created_time or ""),
            "ad_id": self.ad_id or "",
            "raw_value": self.raw_value,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> Optional["MetaLeadEvent"]:
        page_id = normalize_text(payload.get("page_id"), max_len=128)
        leadgen_id = normalize_text(payload.get("leadgen_id"), max_len=128)
        if not page_id or not leadgen_id:
            return None
        raw_value = payload.get("raw_value") if isinstance(payload.get("raw_value"), dict) else {}
        return cls(
            page_id=page_id,
            leadgen_id=leadgen_id,
            form_id=normalize_text(payload.get("form_id"), max_len=128),
            created_time=to_int(payload.get("created_time"), None),
            ad_id=normalize_text(payload.get("ad_id"), max_len=128),
            raw_value=raw_value,
        )


@dataclass
class MetaLeadDetails:
    leadgen_id: str
    page_id: str
    form_id: Optional[str]
    created_time: Optional[int]
    fields: Dict[str, str]
    metadata: Dict[str, str]
    raw_payload: Dict[str, Any]

    @property
    def lead_ref(self) -> str:
        return lead_ref_value(self.page_id, self.leadgen_id)

    @property
    def client_external_id(self) -> str:
        return client_external_id(self.page_id, self.leadgen_id)


def parse_meta_field_data(rows: Any) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    if not isinstance(rows, list):
        return fields
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = normalize_text(row.get("name"), max_len=128)
        if not key:
            continue
        values = row.get("values")
        if isinstance(values, list):
            value = ", ".join(
                item for item in (normalize_text(part) for part in values) if item
            )
        else:
            value = normalize_text(row.get("value"))
        if value:
            fields[key.lower()] = value[: MetaLeadgenCrmChannelConfig.MAX_FIELD_VALUE_CHARS]
    return fields


def parse_meta_lead_details(raw: Dict[str, Any], event: MetaLeadEvent) -> MetaLeadDetails:
    leadgen_id = normalize_text(raw.get("id"), max_len=128) or event.leadgen_id
    page_id = (
        normalize_text(raw.get("page_id"), max_len=128)
        or normalize_text(event.page_id, max_len=128)
        or ""
    )
    form_id = normalize_text(raw.get("form_id"), max_len=128) or event.form_id
    created_time_raw = normalize_text(raw.get("created_time"), max_len=128)
    created_time = to_int(created_time_raw, None) or event.created_time
    fields = parse_meta_field_data(raw.get("field_data"))

    metadata: Dict[str, str] = {}
    if created_time_raw and created_time is None:
        metadata["created_time"] = created_time_raw
    for key in (
        "ad_id",
        "ad_name",
        "adset_id",
        "adset_name",
        "campaign_id",
        "campaign_name",
        "is_organic",
        "platform",
    ):
        value = normalize_text(raw.get(key), max_len=512)
        if value:
            metadata[key] = value
    if event.ad_id and "ad_id" not in metadata:
        metadata["ad_id"] = event.ad_id
    return MetaLeadDetails(
        leadgen_id=leadgen_id,
        page_id=page_id,
        form_id=form_id,
        created_time=created_time,
        fields=fields,
        metadata=metadata,
        raw_payload=raw,
    )


def first_field(fields: Dict[str, str], *names: str) -> Optional[str]:
    for name in names:
        value = normalize_text(fields.get(str(name).lower()))
        if value:
            return value
    return None
