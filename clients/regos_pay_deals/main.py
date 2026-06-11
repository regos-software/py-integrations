from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

import httpx

from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from schemas.api.chat.chat_message import ChatMessageAddRequest, ChatMessageTypeEnum
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.crm.deal import Deal, DealEditRequest, DealGetRequest, DealSetStageRequest
from schemas.api.crm.pipeline import CrmEntityTypeEnum, PipelineGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.api.references.field import FieldAddRequest, FieldGetRequest


logger = setup_logger("regos_pay_deals")


DEFAULT_CHECKOUT_URL = "https://pay.regos.uz/api/CheckOut"
DEFAULT_DESCRIPTION_TEMPLATE = "Payment for deal #{deal_id}: {title}"
DEAL_ENTITY_TYPE = "Deal"
CHECKOUT_HTTP_TIMEOUT = 30.0
ORDER_ID_FIELD_RAW_KEY = "regos_pay_order_id"
ORDER_ID_FIELD_KEY = f"field_{ORDER_ID_FIELD_RAW_KEY}"
ORDER_ID_FIELD_NAME = "REGOS Pay order ID"
ACCEPTED_DEAL_WEBHOOKS = {
    "DealStageSet",
}


@dataclass(frozen=True)
class RuntimeConfig:
    connected_integration_id: str
    checkout_url: str
    service_id: str
    secret_key: str
    pipeline_id: int
    checkout_stage_id: int
    paid_stage_id: int


class RegosPayDealsError(Exception):
    pass


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _optional_text(value: Any) -> Optional[str]:
    text = _text(value)
    return text or None


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(Decimal(str(value).strip()))
    except Exception:
        return default


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _money(value: Any) -> Decimal:
    amount = _to_decimal(value)
    if amount is None:
        raise RegosPayDealsError("amount is required")
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise RegosPayDealsError("amount must be greater than zero")
    return amount


def _money_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def _amount_minor_string(value: Any) -> str:
    amount = _to_decimal(value)
    if amount is None:
        return ""
    minor = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return str(int(minor))


def _json_amount(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _normalize_settings(rows: Any) -> Dict[str, str]:
    settings: Dict[str, str] = {}
    if not isinstance(rows, list):
        return settings
    for row in rows:
        key = _text(getattr(row, "key", None)).lower()
        if not key:
            continue
        settings[key] = _text(getattr(row, "value", None))
    return settings


def _setting(settings: Dict[str, str], *keys: str) -> str:
    for key in keys:
        value = _text(settings.get(str(key).lower()))
        if value:
            return value
    return ""


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _extract_field_value(entity: Any, field_key: str) -> Optional[str]:
    expected = _text(field_key).lower()
    if not expected:
        return None
    fields = getattr(entity, "fields", None)
    if not isinstance(fields, list):
        return None
    for field in fields:
        key = _text(getattr(field, "key", None)).lower()
        if key != expected:
            continue
        value = getattr(field, "value", None)
        return None if value is None else str(value)
    return None


def _request_id(payload: Dict[str, Any]) -> int:
    value = _to_int(payload.get("id"), 0)
    return value if value > 0 else 0


def _param(params: Dict[str, Any], *names: str) -> Any:
    lower_map = {str(key).lower(): value for key, value in params.items()}
    for name in names:
        if name in params:
            return params[name]
        value = lower_map.get(str(name).lower())
        if value is not None:
            return value
    return None


def _lookup(data: Any, *keys: str) -> Any:
    if not isinstance(data, dict):
        return None
    lower_map = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        if key in data:
            return data[key]
        value = lower_map.get(str(key).lower())
        if value is not None:
            return value
    return None


def _plain_int_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return str(int(Decimal(str(value).strip())))
    except Exception:
        return str(value).strip()


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _parse_json_body(body: Any) -> Dict[str, Any]:
    if isinstance(body, dict):
        return body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="ignore")
    if isinstance(body, str) and body.strip():
        try:
            decoded = json.loads(body)
            return decoded if isinstance(decoded, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_deal_id_from_external_id(external_id: Any) -> int:
    text = _text(external_id)
    if not text:
        return 0
    match = re.fullmatch(r"(?:deal[:_-])?(\d+)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return int(match.group(1))


def _extract_deal_id(payload: Dict[str, Any]) -> int:
    candidates = [
        _lookup(payload, "deal_id", "entity_id", "object_id", "id"),
        _lookup(payload.get("deal") if isinstance(payload.get("deal"), dict) else {}, "id"),
        _lookup(payload.get("entity") if isinstance(payload.get("entity"), dict) else {}, "id"),
        _lookup(payload.get("object") if isinstance(payload.get("object"), dict) else {}, "id"),
    ]
    for candidate in candidates:
        deal_id = _to_int(candidate)
        if deal_id > 0:
            return deal_id
    return 0


def _callback_method_from_path(external_path: Any) -> str:
    parts = [
        part.strip()
        for part in str(external_path or "").strip("/").split("/")
        if part.strip()
    ]
    if parts and re.fullmatch(r"[0-9a-fA-F]{32}", parts[0]):
        parts = parts[1:]
    if not parts:
        return ""
    return parts[-1].lower()


def _normalize_regos_webhook_payload(
    action: Optional[str],
    data: Optional[Dict[str, Any]],
    extra: Dict[str, Any],
) -> tuple[Optional[str], Dict[str, Any], Optional[str]]:
    event_id = _text(extra.get("event_id")) or None

    if isinstance(action, str) and action in ACCEPTED_DEAL_WEBHOOKS:
        if isinstance(data, dict):
            return action, data, event_id
        payload = {
            key: value
            for key, value in extra.items()
            if key not in {"event_id", "connected_integration_id"}
        }
        return action, payload, event_id

    if action == "HandleWebhook":
        payload = data if isinstance(data, dict) else {}
        nested = payload.get("data")
        wrapped_event_id = _text(payload.get("event_id") or event_id) or None
        if isinstance(nested, dict):
            nested_action = nested.get("action")
            nested_data = nested.get("data")
            if isinstance(nested_action, str) and isinstance(nested_data, dict):
                return nested_action, nested_data, wrapped_event_id
        return None, {}, wrapped_event_id

    if isinstance(data, dict):
        nested_action = data.get("action")
        nested_data = data.get("data")
        nested_event_id = _text(data.get("event_id") or event_id) or None
        if isinstance(nested_action, str) and isinstance(nested_data, dict):
            return nested_action, nested_data, nested_event_id

    return None, {}, event_id


def _format_description(template: str, deal: Deal, deal_id: int) -> str:
    title = _text(getattr(deal, "title", None), f"Deal {deal_id}")
    try:
        return template.format(deal_id=deal_id, title=title, amount=getattr(deal, "amount", ""))
    except Exception:
        return DEFAULT_DESCRIPTION_TEMPLATE.format(deal_id=deal_id, title=title)


class RegosPayDealsIntegration(ClientBase):
    integration_key = "regos_pay_deals"

    def __init__(self) -> None:
        self.connected_integration_id: Optional[str] = None

    def _ci(self, connected_integration_id: Optional[str] = None) -> str:
        ci = _text(connected_integration_id or self.connected_integration_id)
        if not ci:
            raise RegosPayDealsError("connected_integration_id is required")
        return ci

    async def connect(self, **kwargs: Any) -> Dict[str, Any]:
        """Validate settings and create the configured deal field once on connection."""
        runtime = await self._load_runtime(
            connected_integration_id=_optional_text(kwargs.get("connected_integration_id")),
        )
        async with RegosAPI(runtime.connected_integration_id) as api:
            await self._ensure_pipeline_stages(api, runtime)
            fields = await self._ensure_configured_fields(api)
        return {
            "status": "connected",
            "integration_key": self.integration_key,
            "pipeline_id": runtime.pipeline_id,
            "checkout_stage_id": runtime.checkout_stage_id,
            "paid_stage_id": runtime.paid_stage_id,
            "fields": fields,
            "callbacks": {
                "check": f"/clients/{self.integration_key}/{runtime.connected_integration_id}/Check",
                "perform": f"/clients/{self.integration_key}/{runtime.connected_integration_id}/Perform",
            },
        }

    async def reconnect(self, **kwargs: Any) -> Dict[str, Any]:
        return await self.connect(**kwargs)

    async def disconnect(self, **kwargs: Any) -> Dict[str, Any]:
        _ = kwargs
        return {"status": "disconnected"}

    async def update_settings(
        self,
        settings: Optional[dict] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        _ = settings
        return await self.connect(**kwargs)

    async def create_checkout(
        self,
        deal_id: int,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Manual action for the same stage-gated checkout flow used by webhooks."""
        runtime = await self._load_runtime(
            connected_integration_id=_optional_text(kwargs.get("connected_integration_id"))
        )
        return await self._create_checkout_for_deal(
            runtime=runtime,
            deal_id=deal_id,
            publish_to_chat=True,
        )

    async def _create_checkout_for_deal(
        self,
        *,
        runtime: RuntimeConfig,
        deal_id: int,
        publish_to_chat: bool = True,
    ) -> Dict[str, Any]:
        """Create one REGOS Pay order for a deal that is on the configured checkout stage."""
        deal_id_int = _to_int(deal_id)
        if deal_id_int <= 0:
            raise RegosPayDealsError("deal_id must be positive")

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._get_deal(api, deal_id_int)
            if deal is None:
                raise RegosPayDealsError(f"deal {deal_id_int} not found")
            self._ensure_deal_pipeline(deal, runtime)
            if not self._deal_checkout_stage_matches(deal, runtime):
                return {
                    "status": "ignored",
                    "reason": "stage_mismatch",
                    "deal_id": deal_id_int,
                    "stage_id": _to_int(getattr(deal, "stage_id", None)),
                    "checkout_stage_id": runtime.checkout_stage_id,
                }

            current_order_id = _text(_extract_field_value(deal, ORDER_ID_FIELD_KEY))
            if current_order_id:
                return _drop_none(
                    {
                        "status": "already_created",
                        "deal_id": deal_id_int,
                        "order_id": current_order_id,
                    }
                )

            checkout_amount = _money(getattr(deal, "amount", None))
            checkout_external_id = f"deal:{deal_id_int}"
            checkout_description = _format_description(
                DEFAULT_DESCRIPTION_TEMPLATE,
                deal,
                deal_id_int,
            )

            payload = {
                "external_id": checkout_external_id,
                "service_id": runtime.service_id,
                "amount": _json_amount(checkout_amount),
                "description": checkout_description,
            }
            payload = _drop_none(payload)

            response_payload = await self._send_checkout(runtime, payload)
            error_code = _to_int(response_payload.get("error_code"), 1)
            if error_code != 0:
                return {
                    "status": "error",
                    "source": "regos_pay",
                    "error_code": error_code,
                    "error_description": _text(response_payload.get("error_description"), "CheckOut failed"),
                }

            order_id = _text(response_payload.get("id"))
            payment_url = _optional_text(response_payload.get("url"))
            if not order_id:
                return {
                    "status": "error",
                    "source": "regos_pay",
                    "error_code": error_code,
                    "error_description": "CheckOut response does not contain id",
                }

            fields = [{"key": ORDER_ID_FIELD_KEY, "value": order_id}]

            edit_response = await api.crm.deal.edit(
                DealEditRequest(id=deal_id_int, fields=fields)
            )
            if not edit_response.ok:
                logger.warning(
                    "Deal/Edit rejected while saving REGOS Pay order id: ci=%s deal_id=%s payload=%s",
                    runtime.connected_integration_id,
                    deal_id_int,
                    edit_response.result,
                )
                return {
                    "status": "created_not_saved",
                    "deal_id": deal_id_int,
                    "order_id": order_id,
                    "external_id": checkout_external_id,
                    "payment_url": payment_url,
                    "warning": "REGOS Pay order was created, but CRM deal field was not updated",
                }

            if publish_to_chat:
                await self._publish_checkout_message(
                    api=api,
                    deal=deal,
                    order_id=order_id,
                    amount=checkout_amount,
                    payment_url=payment_url,
                )

        return _drop_none(
            {
                "status": "created",
                "deal_id": deal_id_int,
                "order_id": order_id,
                "external_id": checkout_external_id,
                "amount": _money_string(checkout_amount),
                "payment_url": payment_url,
            }
        )

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """REGOS Pay callback entrypoint for Check and Perform external URLs."""
        body = _parse_json_body((envelope or {}).get("body"))
        method = _text(body.get("method")).lower()
        if not method:
            method = _callback_method_from_path((envelope or {}).get("external_path"))
        if method in {"check", "perform"}:
            return await self._handle_callback(method, body, envelope or {})
        request_id = _request_id(body)
        return self._callback_response(
            request_id,
            1,
            f"Unsupported method: {method or 'unknown'}",
        )

    async def handle_webhook(
        self,
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Handle REGOS deal webhooks and create a checkout only on the configured stage."""
        if not self.connected_integration_id:
            return {"status": "error", "description": "connected_integration_id is required"}

        webhook_action, payload, event_id = _normalize_regos_webhook_payload(
            action=action,
            data=data,
            extra=kwargs,
        )
        if webhook_action not in ACCEPTED_DEAL_WEBHOOKS:
            return {"status": "ignored", "reason": f"unsupported_action:{webhook_action}"}

        deal_id = _extract_deal_id(payload)
        if deal_id <= 0:
            return {"status": "ignored", "reason": "deal_id_missing", "action": webhook_action}

        runtime = await self._load_runtime()
        result = await self._create_checkout_for_deal(
            runtime=runtime,
            deal_id=deal_id,
            publish_to_chat=True,
        )
        return {
            "status": result.get("status", "processed"),
            "action": webhook_action,
            "event_id": event_id,
            "deal_id": deal_id,
            "result": result,
        }

    async def deal_stage_set(
        self,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Adapter for direct REGOS webhook calls with action=DealStageSet."""
        payload = data if isinstance(data, dict) else dict(kwargs)
        event_id = kwargs.get("event_id")
        if event_id is not None and "event_id" in payload:
            payload = {key: value for key, value in payload.items() if key != "event_id"}
        return await self.handle_webhook(
            action="DealStageSet",
            data=payload,
            event_id=event_id,
        )

    async def _handle_callback(
        self,
        method: str,
        payload: Dict[str, Any],
        envelope: Dict[str, Any],
    ) -> Dict[str, Any]:
        request_id = _request_id(payload)
        params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
        sign = _text(payload.get("sign")).lower()
        try:
            runtime = await self._load_runtime(
                connected_integration_id=_optional_text(envelope.get("connected_integration_id"))
            )
        except Exception as error:
            logger.warning("REGOS Pay callback settings error: %s", error)
            return self._callback_response(request_id, 1, "Integration settings error")

        if not self._verify_callback_sign(runtime, method, sign, params):
            logger.warning(
                "REGOS Pay callback signature mismatch: ci=%s method=%s params=%s",
                runtime.connected_integration_id,
                method,
                params,
            )
            return self._callback_response(request_id, 1, "Invalid sign")

        try:
            if method == "check":
                return await self._callback_check(runtime, request_id, params)
            if method == "perform":
                return await self._callback_perform(runtime, request_id, params)
        except Exception as error:
            logger.exception(
                "REGOS Pay callback failed: ci=%s method=%s error=%s",
                runtime.connected_integration_id,
                method,
                error,
            )
            return self._callback_response(request_id, 1, "Callback processing error")

        return self._callback_response(request_id, 1, f"Unsupported method: {method}")

    async def _callback_check(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Confirm to REGOS Pay that the linked deal exists and still has the same amount."""
        order_id = _text(_param(params, "order_Id", "order_id"))
        external_id = _text(_param(params, "external_Id", "external_id"))
        amount = _to_decimal(_param(params, "amount"))
        if not order_id or not external_id or amount is None:
            return self._callback_response(request_id, 1, "Required params are missing")

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._find_deal_by_order_id(api, runtime, order_id)
            if deal is None:
                return self._callback_response(request_id, 1, "Deal not found")

            if not self._deal_pipeline_matches(deal, runtime):
                return self._callback_response(request_id, 1, "Deal pipeline mismatch")

            external_deal_id = _parse_deal_id_from_external_id(external_id)
            if external_deal_id <= 0 or external_deal_id != _to_int(getattr(deal, "id", None)):
                return self._callback_response(request_id, 1, "External id mismatch")

            expected_amount = self._expected_amount(deal)
            if expected_amount is None:
                return self._callback_response(request_id, 1, "Deal amount is empty")
            if _amount_minor_string(amount) != _amount_minor_string(expected_amount):
                return self._callback_response(request_id, 1, "Amount mismatch")

        return self._callback_response(request_id, 0)

    async def _callback_perform(
        self,
        runtime: RuntimeConfig,
        request_id: int,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mark successful REGOS Pay payment in the deal chat and optional paid stage."""
        order_id = _text(_param(params, "order_Id", "order_id"))
        if not order_id:
            return self._callback_response(request_id, 1, "order_Id is required")

        async with RegosAPI(runtime.connected_integration_id) as api:
            deal = await self._find_deal_by_order_id(api, runtime, order_id)
            if deal is None:
                return self._callback_response(request_id, 1, "Deal not found")
            if not self._deal_pipeline_matches(deal, runtime):
                return self._callback_response(request_id, 1, "Deal pipeline mismatch")

            deal_id = _to_int(getattr(deal, "id", None))
            if deal_id <= 0:
                return self._callback_response(request_id, 1, "Deal id is empty")
            if (
                runtime.paid_stage_id > 0
                and _to_int(getattr(deal, "stage_id", None)) != runtime.paid_stage_id
            ):
                response = await api.crm.deal.set_stage(
                    DealSetStageRequest(
                        id=deal_id,
                        stage_id=runtime.paid_stage_id,
                        comment=f"REGOS Pay order {order_id} paid",
                    )
                )
                if not response.ok:
                    logger.warning(
                        "Deal/SetStage rejected on REGOS Pay perform: ci=%s deal_id=%s payload=%s",
                        runtime.connected_integration_id,
                        deal_id,
                        response.result,
                    )
                    return self._callback_response(request_id, 1, "Deal stage update failed")

            await self._publish_paid_message(
                api=api,
                deal=deal,
                order_id=order_id,
            )

        return self._callback_response(request_id, 0)

    async def _load_runtime(
        self,
        connected_integration_id: Optional[str] = None,
    ) -> RuntimeConfig:
        """Load and validate integration settings from REGOS connected integration storage."""
        ci = self._ci(connected_integration_id)
        async with RegosAPI(ci) as api:
            response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(connected_integration_id=ci)
            )
        if not response.ok:
            raise RegosPayDealsError("ConnectedIntegrationSetting/Get failed")
        settings = _normalize_settings(response.result)

        service_id = _setting(settings, "regos_pay_service_id")
        secret_key = _setting(settings, "regos_pay_secret_key")
        pipeline_id = _to_int(_setting(settings, "regos_pay_deal_pipeline_id"))
        checkout_stage_id = _to_int(_setting(settings, "regos_pay_checkout_stage_id"))
        paid_stage_id = _to_int(_setting(settings, "regos_pay_paid_stage_id"))
        missing = []
        if not service_id:
            missing.append("regos_pay_service_id")
        if not secret_key:
            missing.append("regos_pay_secret_key")
        if pipeline_id <= 0:
            missing.append("regos_pay_deal_pipeline_id")
        if checkout_stage_id <= 0:
            missing.append("regos_pay_checkout_stage_id")
        if missing:
            raise RegosPayDealsError(f"Missing settings: {', '.join(missing)}")

        return RuntimeConfig(
            connected_integration_id=ci,
            checkout_url=DEFAULT_CHECKOUT_URL,
            service_id=service_id,
            secret_key=secret_key,
            pipeline_id=pipeline_id,
            checkout_stage_id=checkout_stage_id,
            paid_stage_id=paid_stage_id,
        )

    async def _send_checkout(
        self,
        runtime: RuntimeConfig,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=CHECKOUT_HTTP_TIMEOUT) as client:
            response = await client.post(runtime.checkout_url, json=payload)
            response.raise_for_status()
        try:
            data = response.json()
        except Exception as error:
            raise RegosPayDealsError("CheckOut response is not valid JSON") from error
        if not isinstance(data, dict):
            raise RegosPayDealsError("CheckOut response must be an object")
        return data

    async def _get_deal(self, api: RegosAPI, deal_id: int) -> Optional[Deal]:
        response = await api.crm.deal.get(
            DealGetRequest(ids=[int(deal_id)], limit=1, offset=0)
        )
        if not response.ok:
            raise RegosPayDealsError(f"Deal/Get failed for id={deal_id}")
        rows = response.result or []
        return rows[0] if rows else None

    async def _find_deal_by_order_id(
        self,
        api: RegosAPI,
        runtime: RuntimeConfig,
        order_id: str,
    ) -> Optional[Deal]:
        """Find the deal through the service order-id field used by callbacks."""
        response = await api.crm.deal.get(
            DealGetRequest(
                pipeline_id=runtime.pipeline_id,
                filters=[
                    Filter(
                        field=ORDER_ID_FIELD_KEY,
                        operator=FilterOperator.Equal,
                        value=str(order_id),
                    )
                ],
                limit=1,
                offset=0,
            )
        )
        if not response.ok:
            raise RegosPayDealsError("Deal/Get by REGOS Pay order id failed")
        rows = response.result or []
        return rows[0] if rows else None

    async def _ensure_pipeline_stages(self, api: RegosAPI, runtime: RuntimeConfig) -> None:
        response = await api.crm.pipeline.get(
            PipelineGetRequest(
                entity_type=CrmEntityTypeEnum.Deal,
                ids=[runtime.pipeline_id],
                active=True,
                limit=1,
                offset=0,
            )
        )
        if not response.ok or not response.result:
            raise RegosPayDealsError(f"Deal pipeline {runtime.pipeline_id} not found")
        pipeline = response.result[0]
        stages = getattr(pipeline, "stages", None) or []
        found_stage_ids = {
            _to_int(getattr(stage, "id", None))
            for stage in stages
            if getattr(stage, "active", True) is not False
        }
        if runtime.checkout_stage_id not in found_stage_ids:
            raise RegosPayDealsError(
                f"Deal checkout stage {runtime.checkout_stage_id} not found "
                f"in pipeline {runtime.pipeline_id}"
            )
        if runtime.paid_stage_id <= 0:
            return
        if runtime.paid_stage_id in found_stage_ids:
            return
        raise RegosPayDealsError(
            f"Deal paid stage {runtime.paid_stage_id} not found "
            f"in pipeline {runtime.pipeline_id}"
        )

    async def _publish_checkout_message(
        self,
        *,
        api: RegosAPI,
        deal: Deal,
        order_id: str,
        amount: Decimal,
        payment_url: Optional[str],
    ) -> None:
        chat_id = _text(getattr(deal, "chat_id", None))
        if not chat_id or not payment_url:
            return
        text = (
            "REGOS Pay payment link\n"
            f"Amount: {_money_string(amount)}\n"
            f"Order: {order_id}\n"
            f"{payment_url}"
        )
        await self._add_deal_chat_message(
            api=api,
            chat_id=chat_id,
            text=text,
            external_message_id=f"regos_pay:checkout:{order_id}",
        )

    async def _publish_paid_message(
        self,
        *,
        api: RegosAPI,
        deal: Deal,
        order_id: str,
    ) -> None:
        chat_id = _text(getattr(deal, "chat_id", None))
        if not chat_id:
            return
        amount = self._expected_amount(deal)
        amount_line = f"\nAmount: {_money_string(amount)}" if amount is not None else ""
        text = f"REGOS Pay payment received{amount_line}\nOrder: {order_id}"
        await self._add_deal_chat_message(
            api=api,
            chat_id=chat_id,
            text=text,
            external_message_id=f"regos_pay:paid:{order_id}",
        )

    async def _add_deal_chat_message(
        self,
        *,
        api: RegosAPI,
        chat_id: str,
        text: str,
        external_message_id: str,
    ) -> None:
        try:
            response = await api.chat.chat_message.add(
                ChatMessageAddRequest(
                    chat_id=chat_id,
                    message_type=ChatMessageTypeEnum.System,
                    text=text,
                    external_message_id=external_message_id,
                )
            )
            if not response.ok:
                logger.warning(
                    "ChatMessage/Add rejected for REGOS Pay deals: chat_id=%s payload=%s",
                    chat_id,
                    response.result,
                )
        except Exception:
            logger.exception(
                "Failed to publish REGOS Pay chat message: chat_id=%s external_message_id=%s",
                chat_id,
                external_message_id,
            )

    async def _ensure_configured_fields(
        self,
        api: RegosAPI,
    ) -> List[Dict[str, Any]]:
        specs = [
            (
                ORDER_ID_FIELD_KEY,
                ORDER_ID_FIELD_RAW_KEY,
                ORDER_ID_FIELD_NAME,
                "string",
                True,
            )
        ]

        result: List[Dict[str, Any]] = []
        for field_key, raw_key, field_name, data_type, required in specs:
            status = await self._ensure_field(
                api=api,
                key=field_key,
                raw_key=raw_key,
                name=field_name,
                data_type=data_type,
            )
            result.append(
                {
                    "key": field_key,
                    "name": field_name,
                    "data_type": data_type,
                    "required": required,
                    "status": status,
                }
            )
        return result

    async def _ensure_field(
        self,
        api: RegosAPI,
        key: str,
        raw_key: str,
        name: str,
        data_type: str,
    ) -> str:
        response = await api.references.field.get(
            FieldGetRequest(entity_type=DEAL_ENTITY_TYPE, keys=[key], limit=1, offset=0)
        )
        if not response.ok:
            raise RegosPayDealsError(f"Field/Get failed for {key}")
        expected = key.strip().lower()
        rows = response.result if isinstance(response.result, list) else []
        for row in rows:
            if _text(getattr(row, "key", None)).lower() == expected:
                return "exists"
        add_response = await api.references.field.add(
            FieldAddRequest(
                key=raw_key,
                name=name,
                entity_type=DEAL_ENTITY_TYPE,
                data_type=data_type,
                required=False,
            )
        )
        if not add_response.ok:
            raise RegosPayDealsError(
                f"Field/Add failed for {key}: {_payload_dict(add_response.result)}"
            )
        return "created"

    def _ensure_deal_pipeline(self, deal: Deal, runtime: RuntimeConfig) -> None:
        if self._deal_pipeline_matches(deal, runtime):
            return
        raise RegosPayDealsError(
            f"deal {getattr(deal, 'id', None)} is not in pipeline {runtime.pipeline_id}"
        )

    def _deal_pipeline_matches(self, deal: Deal, runtime: RuntimeConfig) -> bool:
        return _to_int(getattr(deal, "pipeline_id", None)) == runtime.pipeline_id

    def _deal_checkout_stage_matches(self, deal: Deal, runtime: RuntimeConfig) -> bool:
        return _to_int(getattr(deal, "stage_id", None)) == runtime.checkout_stage_id

    def _expected_amount(self, deal: Deal) -> Optional[Decimal]:
        return _to_decimal(getattr(deal, "amount", None))

    def _verify_callback_sign(
        self,
        runtime: RuntimeConfig,
        method: str,
        sign: str,
        params: Dict[str, Any],
    ) -> bool:
        if method == "check":
            date = _plain_int_text(_param(params, "date"))
            order_id = _text(_param(params, "order_Id", "order_id"))
            external_id = _text(_param(params, "external_Id", "external_id"))
            amount_minor = _amount_minor_string(_param(params, "amount"))
            source = f"{method}{runtime.secret_key}{date}{order_id}{external_id}{amount_minor}"
            expected = _md5(source)
            return bool(sign) and sign == expected.lower()
        if method == "perform":
            order_id = _text(_param(params, "order_Id", "order_id"))
            source = f"{method}{runtime.secret_key}{order_id}"
            expected = _md5(source)
            return bool(sign) and sign == expected.lower()
        return False

    def _callback_response(
        self,
        request_id: int,
        error_code: int,
        error_description: Optional[str] = None,
        data: Any = None,
    ) -> Dict[str, Any]:
        return _drop_none(
            {
                "id": int(request_id or 0),
                "error_code": int(error_code),
                "error_description": error_description if error_code else None,
                "data": data,
            }
        )


__all__ = ["RegosPayDealsIntegration"]
