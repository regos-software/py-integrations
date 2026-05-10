from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from clients.base import ClientBase
from config.settings import settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import (
    redis_error_contains,
    redis_is_enabled,
    redis_make_key,
    redis_ops,
    redis_stream_add_with_ttl,
    redis_stream_ack_delete,
    redis_stream_group_create_with_ttl,
)
from schemas.api.base import IDRequest
from schemas.api.docs.doc_contract import (
    ContractDirection,
    DocContractAddRequest,
    DocContractGetRequest,
)
from schemas.api.docs.doc_invoice import (
    DocInvoice,
    DocInvoiceAddRequest,
    DocInvoiceSetExternalDataRequest,
    DocInvoiceSetStatusRequest,
    DocInvoiceStatus,
    DocInvoiceType,
)
from schemas.api.docs.invoice_operation import (
    InvoiceOperation,
    InvoiceOperationAdd,
    InvoiceOperationGetRequest,
)
from schemas.api.integrations.connected_integration import ConnectedIntegrationGetRequest
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)
from schemas.api.references.firm import Firm, FirmGetRequest
from schemas.api.references.item import (
    ItemImportComparationValue,
    ItemImportData,
    ItemImportRequest,
    ItemMatchingData,
    ItemMatchingRequest,
    ItemMatchingType,
)
from schemas.api.references.partner import LegalStatus, PartnerAddRequest, PartnerGetRequest


logger = setup_logger("edo_fakturauz")

_INSTANCE_ID = uuid.uuid4().hex[:12]
_STREAM_WORKER_TASKS: Dict[str, asyncio.Task] = {}
_STREAM_WORKER_LOCK = asyncio.Lock()
_STREAM_GROUP_READY = False
_STREAM_TTL_TOUCH_TS: Dict[str, int] = {}
_STREAM_CLAIM_TS: Dict[str, int] = {}


def _now_ts() -> int:
    return int(time.time())


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw or ""))
    except Exception:
        return None


def _json_response(payload: Dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload, exclude_none=True),
    )


def _ci_lookup(data: Any, *keys: str, default: Any = None) -> Any:
    if data is None:
        return default
    if isinstance(data, dict):
        lower_map = {str(key).lower(): value for key, value in data.items()}
        for key in keys:
            if key in data:
                return data[key]
            value = lower_map.get(str(key).lower())
            if value is not None:
                return value
        return default
    for key in keys:
        if hasattr(data, key):
            return getattr(data, key)
    return default


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _digits(value: Any) -> str:
    return "".join(ch for ch in _text(value) if ch.isdigit())


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(Decimal(str(value)))
        except Exception:
            return default


def _to_optional_int(value: Any) -> Optional[int]:
    parsed = _to_int(value, 0)
    return parsed if parsed > 0 else None


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return default


def _money(value: Any) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_json(value: Any) -> str:
    amount = _money(value)
    return format(amount, "f")


def _parse_date_to_unix(value: Any, default: Optional[int] = None) -> int:
    if value is None or value == "":
        return default if default is not None else _now_ts()
    if isinstance(value, (int, float)):
        parsed = int(value)
        return parsed // 1000 if parsed > 10_000_000_000 else parsed
    text = str(value).strip()
    if not text:
        return default if default is not None else _now_ts()
    if text.isdigit():
        return _parse_date_to_unix(int(text), default)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(text[: len(fmt)], fmt)
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError:
        return default if default is not None else _now_ts()


def _format_date(value: Any, fmt: str = "%d.%m.%Y") -> str:
    unix_ts = _parse_date_to_unix(value, _now_ts())
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime(fmt)


def _display_date(value: Any) -> str:
    if isinstance(value, (int, float)):
        return _format_date(value)
    text = _text(value)
    return text or _format_date(value)


def _iso_from_ms(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    ts = _parse_date_to_unix(value, 0)
    if ts <= 0:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _list_payload(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        for key in ("result", "data", "items", "documents", "Documents"):
            nested = _ci_lookup(value, key)
            if isinstance(nested, list):
                return nested
    return []


def _result_new_id(response: Any, context: str) -> int:
    if not getattr(response, "ok", False):
        raise EdoFakturaUzError(111600, f"{context} failed")
    result = getattr(response, "result", None)
    new_id = _ci_lookup(result, "new_id", "newId", "id")
    parsed = _to_int(new_id, 0)
    if parsed <= 0:
        raise EdoFakturaUzError(111601, f"{context} did not return new_id")
    return parsed


def _ensure_api_ok(response: Any, context: str) -> None:
    if not getattr(response, "ok", False):
        payload = getattr(response, "result", None)
        raise EdoFakturaUzError(111602, f"{context} failed: {payload}")


def _firm_field(firm: Optional[Firm], name: str) -> str:
    if firm is None:
        return ""
    if name in {"full_name", "fullname"}:
        return _text(
            getattr(firm, "full_name", None)
            or getattr(firm, "fullname", None)
        )
    return _text(getattr(firm, name, ""))


def _model_enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return _text(value)


class EdoFakturaUzError(Exception):
    def __init__(self, code: int, description: str, status_code: int = 500):
        super().__init__(description)
        self.code = int(code)
        self.description = str(description)
        self.status_code = int(status_code)


class EdoFakturaUzNonRetryableError(EdoFakturaUzError):
    pass


class FakturaUzClient:
    TOKEN_ENDPOINT = "https://account.faktura.uz"
    API_ENDPOINT = "https://api.faktura.uz/Api"
    REQUIRED_SETTINGS = {
        "FAKTURA_UZ_CLIENT_ID",
        "FAKTURA_UZ_LOGIN",
        "FAKTURA_UZ_PASSWORD",
        "FAKTURA_UZ_PRIVATE_KEY",
    }

    def __init__(
        self,
        *,
        connected_integration_id: str,
        firm_id: int,
        firm: Firm,
        settings_map: Dict[str, str],
        access_token: str,
        token_type: str = "Bearer",
    ) -> None:
        self.connected_integration_id = connected_integration_id
        self.firm_id = int(firm_id)
        self.firm = firm
        self.settings_map = settings_map
        self.access_token = access_token
        self.token_type = token_type or "Bearer"

    @classmethod
    async def create(cls, connected_integration_id: str, firm_id: int) -> "FakturaUzClient":
        ci = _text(connected_integration_id)
        if not ci:
            raise EdoFakturaUzError(111001, "connected_integration_id is required", 400)
        parsed_firm_id = _to_int(firm_id, 0)
        if parsed_firm_id <= 0:
            raise EdoFakturaUzError(111002, "firm_id is required", 400)

        async with RegosAPI(connected_integration_id=ci) as api:
            firm_response = await api.references.firm.get(
                FirmGetRequest(ids=[parsed_firm_id], limit=1)
            )
            firms = firm_response.result or []
            if not firms:
                raise EdoFakturaUzError(
                    111003,
                    f"Firm {parsed_firm_id} was not found",
                    400,
                )
            settings_map = await cls._load_settings(api, ci, parsed_firm_id)

        access_token, token_type = await cls._get_access_token(ci, parsed_firm_id, settings_map)
        return cls(
            connected_integration_id=ci,
            firm_id=parsed_firm_id,
            firm=firms[0],
            settings_map=settings_map,
            access_token=access_token,
            token_type=token_type,
        )

    @classmethod
    async def _load_settings(
        cls,
        api: RegosAPI,
        connected_integration_id: str,
        firm_id: int,
    ) -> Dict[str, str]:
        response = await api.integrations.connected_integration_setting.get(
            ConnectedIntegrationSettingRequest(
                connected_integration_id=connected_integration_id,
                firm_id=firm_id,
            )
        )
        settings_map: Dict[str, str] = {}
        for item in response.result or []:
            key = _text(getattr(item, "key", "")).upper()
            if key:
                settings_map[key] = _text(getattr(item, "value", ""))
        missing = sorted(key for key in cls.REQUIRED_SETTINGS if not settings_map.get(key))
        if missing:
            raise EdoFakturaUzError(
                111004,
                f"Missing Faktura.uz settings: {', '.join(missing)}",
                400,
            )
        return settings_map

    @classmethod
    def _token_cache_key(cls, connected_integration_id: str, firm_id: int) -> str:
        return redis_make_key("edo", "fakturauz", "token", connected_integration_id, firm_id)

    @classmethod
    async def _get_access_token(
        cls,
        connected_integration_id: str,
        firm_id: int,
        settings_map: Dict[str, str],
    ) -> Tuple[str, str]:
        cache_key = cls._token_cache_key(connected_integration_id, firm_id)
        if redis_is_enabled():
            try:
                cached = await redis_ops.get(cache_key)
                if cached:
                    token_payload = _json_loads(cached)
                    token = _text(_ci_lookup(token_payload, "access_token", "accessToken"))
                    token_type = _text(_ci_lookup(token_payload, "token_type", "tokenType"), "Bearer")
                    if token:
                        return token, token_type
            except Exception as error:
                logger.debug("Faktura token cache read failed: %s", error)

        payload = {
            "grant_type": "password",
            "username": settings_map["FAKTURA_UZ_LOGIN"],
            "password": settings_map["FAKTURA_UZ_PASSWORD"],
            "client_id": settings_map["FAKTURA_UZ_CLIENT_ID"],
            "client_secret": settings_map["FAKTURA_UZ_PRIVATE_KEY"],
        }
        url = f"{cls.TOKEN_ENDPOINT.rstrip('/')}/token"
        try:
            async with httpx.AsyncClient(timeout=30) as http_client:
                response = await http_client.post(url, data=payload)
                text = response.text
                response.raise_for_status()
                data = response.json()
        except Exception as error:
            raise EdoFakturaUzError(
                111005,
                f"Faktura.uz token request failed: {error}",
            ) from error

        token = _text(_ci_lookup(data, "access_token", "accessToken"))
        token_type = _text(_ci_lookup(data, "token_type", "tokenType"), "Bearer")
        expires_in = _to_int(_ci_lookup(data, "expires_in", "expiresIn"), 300)
        if not token:
            raise EdoFakturaUzError(
                111006,
                f"Faktura.uz token response does not contain access_token: {text[:300]}",
            )
        if redis_is_enabled():
            ttl_limit = max(int(settings.edo_fakturauz_token_cache_ttl or 0), 1)
            ttl = min(max(expires_in - 60, 1), ttl_limit)
            try:
                await redis_ops.setex(
                    cache_key,
                    ttl,
                    _json_dumps({"access_token": token, "token_type": token_type}),
                )
            except Exception as error:
                logger.debug("Faktura token cache write failed: %s", error)
        return token, token_type

    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"{self.token_type} {self.access_token}",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.API_ENDPOINT.rstrip('/')}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=90) as http_client:
                response = await http_client.request(
                    method,
                    url,
                    headers=self._headers(),
                    params={k: v for k, v in (params or {}).items() if v is not None},
                    json=json_body,
                )
                text = response.text
                response.raise_for_status()
                if not text.strip():
                    return {}
                return response.json()
        except Exception as error:
            raise EdoFakturaUzError(
                111007,
                f"Faktura.uz request failed: {method} {path}: {error}",
            ) from error

    async def get_documents(
        self,
        *,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        page_limit = max(_to_int(limit, 500), 1)
        page_offset = max(_to_int(offset, 0), 0)
        params: Dict[str, Any] = {
            "companyInn": _digits(self.firm.inn),
            "isInbox": "true",
            "types": "2,5,28,29",
            "statuses": "22,24",
            "limit": page_limit,
            "skip": page_offset,
        }
        if start_date:
            params["invoiceDateFrom"] = _parse_date_to_unix(start_date, 0) * 1000
        if end_date:
            params["invoiceDateTo"] = _parse_date_to_unix(end_date, 0) * 1000

        payload = await self._request("GET", "Document/GetDocuments", params=params)
        raw_documents = _list_payload(payload)
        total = _to_int(
            _ci_lookup(payload, "total", "Total", "totalCount", "TotalCount", "recordsTotal", "count"),
            len(raw_documents),
        )
        return [self._map_document_row(item) for item in raw_documents], total

    def _map_document_row(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        contractor = _ci_lookup(raw, "contractor", "Contractor", default={}) or {}
        member = _ci_lookup(raw, "contractorMember", "ContractorMember", default={}) or {}
        return {
            "id": _text(_ci_lookup(raw, "uniqueId", "UniqueId", "id")),
            "roaming_id": _text(_ci_lookup(raw, "roamingUid", "RoamingUid", "roaming_id")),
            "name": _text(_ci_lookup(raw, "title", "Title", "name")),
            "create_date": _iso_from_ms(_ci_lookup(raw, "createdDateTime", "CreatedDateTime")),
            "update_date": _iso_from_ms(_ci_lookup(raw, "updatedDateTime", "UpdatedDateTime")),
            "amount": _money(_ci_lookup(raw, "totalPrice", "TotalPrice", "amount")),
            "contract": _ci_lookup(raw, "contract", "Contract"),
            "partner_inn": _digits(_ci_lookup(contractor, "inn", "Inn")),
            "partner_name": _text(_ci_lookup(contractor, "name", "Name")),
            "firm": {
                "inn": _digits(_ci_lookup(member, "inn", "Inn")),
                "name": _text(_ci_lookup(member, "name", "Name")),
            },
        }

    async def get_document_content(self, document_id: str) -> Dict[str, Any]:
        payload = await self._request(
            "POST",
            "Document/GetDocumentsContent",
            json_body={"DocumentUniqueIds": [_text(document_id)]},
        )
        rows = _list_payload(payload)
        raw_row = rows[0] if rows else payload
        if not isinstance(raw_row, dict):
            raise EdoFakturaUzError(111008, "Faktura.uz document content is empty")
        content_raw = _ci_lookup(raw_row, "Content", "content")
        content = _json_loads(content_raw)
        if not isinstance(content, dict):
            raise EdoFakturaUzError(111009, "Faktura.uz document content is invalid")
        external_id = _text(
            _ci_lookup(raw_row, "UniqueId", "uniqueId", "id"),
            _text(document_id),
        )
        roaming_id = _text(_ci_lookup(raw_row, "RoamingUid", "roamingUid", "roaming_id"))
        return self._map_document_content(content, external_id=external_id, roaming_id=roaming_id)

    def _map_document_content(
        self,
        content: Dict[str, Any],
        *,
        external_id: str,
        roaming_id: str,
    ) -> Dict[str, Any]:
        act_services = _ci_lookup(content, "actServices", "ActServices")
        document_kind = "act" if act_services is not None else "invoice"
        services = _ci_lookup(content, "invoiceServices", "InvoiceServices", default=[])
        if (not isinstance(services, list) or not services) and isinstance(act_services, list):
            services = act_services
        if not isinstance(services, list):
            services = []

        invoice_number = _text(_ci_lookup(content, "invoiceNumber", "InvoiceNumber"))
        invoice_date = _ci_lookup(content, "invoiceDate", "InvoiceDate")
        invoice_date_text = _display_date(invoice_date)
        contract_number = _text(_ci_lookup(content, "invoiceContractNumber", "InvoiceContractNumber"))
        contract_date = _ci_lookup(content, "invoiceContractDate", "InvoiceContractDate")
        contract_date_text = _display_date(contract_date)
        contract_parts = []
        if contract_date:
            contract_parts.append(f"№{contract_date_text}")
        if contract_number:
            contract_parts.append(f"от {contract_number}")
        contract_name = " ".join(contract_parts).strip() or invoice_number or external_id

        if document_kind == "act":
            name = f"Акт и счёт фактура (ПКМ №489) №{invoice_number} от {invoice_date_text}"
        else:
            name = f"Счет-фактура {invoice_number} от {invoice_date_text}"

        operations = [self._map_operation(row, index) for index, row in enumerate(services)]
        return {
            "id": external_id,
            "external_id": external_id,
            "roaming_id": roaming_id,
            "name": name,
            "date": _parse_date_to_unix(invoice_date),
            "contract": contract_name,
            "amount": _money(
                _ci_lookup(
                    content,
                    "invoiceServicesTotalPrice",
                    "InvoiceServicesTotalPrice",
                    "actServicesTotalPrice",
                    "ActServicesTotalPrice",
                    default=sum((_money(item.get("amount")) for item in operations), Decimal("0")),
                )
            ),
            "partner_inn": _digits(_ci_lookup(content, "ownerInn", "OwnerInn")),
            "partner_name": _text(_ci_lookup(content, "ownerName", "OwnerName")),
            "firm": {
                "inn": _digits(_ci_lookup(content, "contractorInn", "ContractorInn")),
                "name": _text(_ci_lookup(content, "contractorName", "ContractorName")),
            },
            "operations": operations,
        }

    def _map_operation(self, raw: Dict[str, Any], index: int) -> Dict[str, Any]:
        catalog = _ci_lookup(raw, "catalog", "Catalog", default={}) or {}
        marks = _ci_lookup(raw, "marks", "Marks", default={}) or {}
        quantity = _to_decimal(_ci_lookup(raw, "quantity", "Quantity"), Decimal("0"))
        price = _to_decimal(_ci_lookup(raw, "pricePerItem", "PricePerItem", "price"), Decimal("0"))
        vat_rate = _to_decimal(_ci_lookup(raw, "vatRate", "VatRate"), Decimal("0"))
        amount = _money(_ci_lookup(raw, "totalPrice", "TotalPrice", default=quantity * price))
        return {
            "index": str(index),
            "name": _text(_ci_lookup(raw, "title", "Title", "name"), f"Item {index + 1}"),
            "icps": _text(_ci_lookup(catalog, "code", "Code")),
            "barcode": _text(_ci_lookup(raw, "barcode", "Barcode")),
            "package_code": _to_optional_int(_ci_lookup(raw, "measurementCode", "MeasurementCode")),
            "package_name": _text(_ci_lookup(raw, "measurement", "Measurement")),
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "vat_rate": vat_rate,
            "origin": _to_optional_int(_ci_lookup(raw, "origin", "Origin")),
            "labels": _ci_lookup(marks, "kiz", "Kiz", default=[]),
            "group_labels": _ci_lookup(marks, "nomUpak", "NomUpak", default=[]),
            "transport_labels": _ci_lookup(marks, "identTransUpak", "IdentTransUpak", default=[]),
        }

    async def send_document_invoice(
        self,
        document: DocInvoice,
        operations: List[InvoiceOperation],
    ) -> str:
        payload = {"invoices": [self._build_invoice_payload(document, operations)]}
        response = await self._request(
            "POST",
            "Document/ImportDocumentRegister",
            json_body=payload,
        )
        error_count = _to_int(_ci_lookup(response, "ErrorCount", "errorCount"), 0)
        if error_count > 0:
            errors = _ci_lookup(response, "ErrorItems", "errorItems", default=[])
            raise EdoFakturaUzNonRetryableError(
                111010,
                f"Faktura.uz rejected invoice: {errors}",
            )
        success_items = _ci_lookup(response, "SuccessItems", "successItems", default=[])
        if not isinstance(success_items, list) or not success_items:
            raise EdoFakturaUzNonRetryableError(
                111011,
                f"Faktura.uz response does not contain success item: {response}",
            )
        first = success_items[0]
        external_id = _text(_ci_lookup(first, "UniqueId", "uniqueId", "id"))
        if not external_id:
            raise EdoFakturaUzNonRetryableError(
                111012,
                f"Faktura.uz response does not contain UniqueId: {response}",
            )
        return external_id

    def _build_invoice_payload(
        self,
        document: DocInvoice,
        operations: List[InvoiceOperation],
    ) -> Dict[str, Any]:
        firm_info = self._company_info_from_firm(self.firm)
        partner_info = self._company_info_from_partner(getattr(document, "partner", None))
        document_date = _format_date(getattr(document, "date", None))
        contract = getattr(document, "contract", None)
        contract_date = _format_date(getattr(contract, "date", None)) if contract else document_date
        contract_number = _text(getattr(contract, "code", None) or getattr(contract, "name", None), "1")
        invoice_number = _text(getattr(document, "code", None), str(getattr(document, "id", "")))
        currency = getattr(document, "currency", None)
        currency_code = _text(
            getattr(currency, "code_num", None),
            _text(getattr(currency, "code_chr", None), "860"),
        )
        currency_name = _text(getattr(currency, "code_chr", None), "UZS")
        exchange_rate = _to_decimal(getattr(document, "exchange_rate", None), Decimal("1"))

        invoice_type = _model_enum_value(getattr(document, "invoice_type", None)).lower()
        is_corrective = invoice_type == DocInvoiceType.Corrective.value.lower()
        item_rows: List[Dict[str, Any]] = []
        subtotal = Decimal("0")
        vat_total = Decimal("0")
        for index, operation in enumerate(operations, start=1):
            row, row_subtotal, row_vat = self._build_invoice_item(
                index,
                operation,
                is_corrective=is_corrective,
            )
            item_rows.append(row)
            subtotal += row_subtotal
            vat_total += row_vat
        subtotal_with_taxes = _money(getattr(document, "amount", None) or subtotal)
        if is_corrective:
            subtotal_with_taxes = -subtotal_with_taxes
        doc_payload: Dict[str, Any] = {
            "document_date": document_date,
            "document_number": invoice_number,
            "contract_date": contract_date,
            "contract_number": contract_number,
            "currency_code": currency_code,
            "currency_rate": _decimal_json(exchange_rate),
            "factura_type": "1" if is_corrective else "0",
            "items": item_rows,
            "column_summary_values": {
                "column_subtotal": _decimal_json(subtotal),
                "column_subtotal_uzs": _decimal_json(subtotal * exchange_rate),
                "column_subtotal_with_taxes": _decimal_json(subtotal_with_taxes),
                "column_subtotal_with_taxes_total": _decimal_json(subtotal_with_taxes),
                "column_subtotal_with_taxes_uzs": _decimal_json(subtotal_with_taxes * exchange_rate),
                "column_vat_value": _decimal_json(vat_total),
                "column_vat_value_uzs": _decimal_json(vat_total * exchange_rate),
            },
            "column_summary_values_in_words": {
                "column_subtotal_in_words": f"{_decimal_json(subtotal)} {currency_name}",
                "column_subtotal_uzs_in_words": f"{_decimal_json(subtotal)} {currency_name}",
                "column_subtotal_with_taxes_in_words": f"{_decimal_json(subtotal_with_taxes)} {currency_name}",
                "column_subtotal_with_taxes_uzs_in_words": f"{_decimal_json(subtotal_with_taxes)} {currency_name}",
            },
        }
        if is_corrective:
            doc_payload["korrektirovoch_document_number"] = _text(
                getattr(document, "corrected_code", None)
            )
            doc_payload["korrektirovoch_document_date"] = _format_date(
                getattr(document, "corrected_date", None)
            )

        partner = getattr(document, "partner", None)
        if _model_enum_value(getattr(partner, "legal_status", None)) == LegalStatus.Natural.value:
            doc_payload["single_sided_type"] = "1"

        return {
            "head": {
                "file_name": f"invoice-{getattr(document, 'id', '')}.json",
                "receiver": {
                    "receiver_info": partner_info,
                    "approver_and_signers": {},
                },
                "sender": {
                    "sender_info": firm_info,
                    "approver_and_signers": {},
                },
            },
            "document": doc_payload,
        }

    def _company_info_from_firm(self, firm: Firm) -> Dict[str, Any]:
        return {
            "company_name": _firm_field(firm, "fullname") or _firm_field(firm, "name"),
            "INN": _digits(_firm_field(firm, "inn")),
            "phone": _firm_field(firm, "phones"),
            "company_vat_code": _firm_field(firm, "vat_index"),
            "address": {
                "region": "",
                "street": _firm_field(firm, "address"),
            },
            "bank_details": {
                "bank_code": _firm_field(firm, "mfo"),
                "bank_name": _firm_field(firm, "bank_name"),
                "account_number": _firm_field(firm, "rs"),
            },
        }

    def _company_info_from_partner(self, partner: Any) -> Dict[str, Any]:
        return {
            "company_name": _text(getattr(partner, "fullname", None) or getattr(partner, "name", None)),
            "INN": _digits(getattr(partner, "inn", None)),
            "phone": _text(getattr(partner, "phones", None)),
            "company_vat_code": _text(getattr(partner, "vat_index", None)),
            "address": {
                "region": "",
                "street": _text(getattr(partner, "address", None)),
            },
            "bank_details": {
                "bank_code": _text(getattr(partner, "mfo", None)),
                "bank_name": _text(getattr(partner, "bank_name", None)),
                "account_number": _text(getattr(partner, "rs", None)),
            },
        }

    def _build_invoice_item(
        self,
        index: int,
        operation: InvoiceOperation,
        *,
        is_corrective: bool,
    ) -> Tuple[Dict[str, Any], Decimal, Decimal]:
        item = getattr(operation, "item", None)
        quantity = _to_decimal(getattr(operation, "quantity", None), Decimal("0"))
        price = _to_decimal(getattr(operation, "price", None), Decimal("0"))
        if is_corrective:
            price = -price
        subtotal = _money(quantity * price)
        vat_rate = _to_decimal(getattr(operation, "vat_value", None), Decimal("0"))
        vat_calc_type = _model_enum_value(getattr(operation, "vat_calculation_type", None))

        vat_amount = Decimal("0")
        subtotal_with_taxes = subtotal
        if vat_rate > 0 and vat_calc_type.lower() != "no":
            if vat_calc_type.lower() == "exclude":
                vat_amount = _money(price * vat_rate / (Decimal("100") + vat_rate))
                subtotal_with_taxes = subtotal
            elif vat_calc_type.lower() == "include":
                vat_amount = _money(price * vat_rate / Decimal("100"))
                subtotal_with_taxes = _money(price + vat_amount)

        has_vat = vat_rate > 0 and vat_calc_type.lower() in {"exclude", "include"}
        row = {
            "item_number": str(index),
            "description": _text(getattr(item, "name", None), f"Item {index}"),
            "volume": _decimal_json(quantity),
            "unit_price": _decimal_json(price),
            "measurement_unit_code": _text(getattr(item, "package_code", None)),
            "excise": {},
            "catalog": {
                "code": _text(getattr(item, "icps", None)),
                "name": "",
            },
            "subtotal": _decimal_json(subtotal),
            "vat": {
                "vat_rate": _decimal_json(vat_rate),
                "vat_value": _decimal_json(vat_amount),
            }
            if has_vat
            else {},
            "subtotal_with_taxes": _decimal_json(subtotal_with_taxes),
        }
        return row, subtotal, vat_amount


class EdoFakturaUzIntegration(ClientBase):
    integration_key = "edo_fakturauz"
    REDIS_PREFIX = "edo:fakturauz"
    STREAM_GROUP = "edo_fakturauz_workers"
    STREAM_READ_BLOCK_MS = 5000
    STREAM_MIN_IDLE_MS = 60_000
    STREAM_CLAIM_INTERVAL_SEC = 30

    @staticmethod
    def _redis_enabled() -> bool:
        return bool(redis_is_enabled() and redis_ops)

    @classmethod
    def _require_redis(cls) -> None:
        if not cls._redis_enabled():
            raise RuntimeError("Redis is required for edo_fakturauz")

    @classmethod
    def _stream_key(cls) -> str:
        return redis_make_key(cls.REDIS_PREFIX, "stream")

    @classmethod
    def _dlq_stream_key(cls) -> str:
        return redis_make_key(cls.REDIS_PREFIX, "stream", "dlq")

    @classmethod
    def _worker_task_key(cls, worker_index: int) -> str:
        return f"{cls._stream_key()}:{int(worker_index)}"

    @classmethod
    def _stream_ttl(cls) -> int:
        return max(int(settings.edo_fakturauz_stream_ttl or 0), 60)

    @classmethod
    def _stream_workers(cls) -> int:
        return max(int(settings.edo_fakturauz_stream_workers or 0), 1)

    @classmethod
    def _stream_batch_size(cls) -> int:
        return max(int(settings.edo_fakturauz_stream_batch_size or 0), 1)

    @classmethod
    def _stream_maxlen(cls) -> int:
        return max(int(settings.edo_fakturauz_stream_maxlen or 0), 1000)

    @classmethod
    def _stream_retry_limit(cls) -> int:
        return max(int(settings.edo_fakturauz_stream_retry_limit or 0), 1)

    @staticmethod
    def _serialize_stream_fields(fields: Dict[str, Any]) -> Dict[str, str]:
        serialized: Dict[str, str] = {}
        for key, value in fields.items():
            if isinstance(value, (dict, list)):
                serialized[str(key)] = _json_dumps(value)
            elif value is None:
                serialized[str(key)] = ""
            else:
                serialized[str(key)] = str(value)
        return serialized

    @classmethod
    async def _ensure_consumer_group(cls, *, force: bool = False) -> None:
        global _STREAM_GROUP_READY
        cls._require_redis()
        if _STREAM_GROUP_READY and not force:
            return
        await redis_stream_group_create_with_ttl(
            cls._stream_key(),
            cls.STREAM_GROUP,
            ttl_sec=cls._stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        _STREAM_GROUP_READY = True

    @classmethod
    async def _enqueue_stream(cls, fields: Dict[str, Any], *, dlq: bool = False) -> str:
        cls._require_redis()
        stream_key = cls._dlq_stream_key() if dlq else cls._stream_key()
        message_id = uuid.uuid4().hex
        payload = dict(fields)
        payload.setdefault("message_id", message_id)
        await redis_stream_add_with_ttl(
            stream_key,
            cls._serialize_stream_fields(payload),
            maxlen=cls._stream_maxlen(),
            ttl_sec=cls._stream_ttl(),
            touch_ts_by_key=_STREAM_TTL_TOUCH_TS,
            now_ts=_now_ts(),
        )
        return message_id

    @classmethod
    def _stream_workers_ready(cls) -> bool:
        for index in range(cls._stream_workers()):
            task = _STREAM_WORKER_TASKS.get(cls._worker_task_key(index))
            if not task or task.done():
                return False
        return True

    @classmethod
    async def _ensure_stream_workers(cls, *, ensure_group: bool = True) -> None:
        cls._require_redis()
        if ensure_group:
            await cls._ensure_consumer_group()
        if cls._stream_workers_ready():
            return
        for index in range(cls._stream_workers()):
            task_key = cls._worker_task_key(index)
            async with _STREAM_WORKER_LOCK:
                task = _STREAM_WORKER_TASKS.get(task_key)
                if task and not task.done():
                    continue
                _STREAM_WORKER_TASKS[task_key] = asyncio.create_task(
                    cls._stream_worker_loop(index),
                    name=f"edo_fakturauz_stream_{index}",
                )

    @classmethod
    async def shutdown_all(cls) -> None:
        async with _STREAM_WORKER_LOCK:
            tasks = list(_STREAM_WORKER_TASKS.values())
            _STREAM_WORKER_TASKS.clear()
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error while stopping EDO Faktura.uz stream worker")

    @classmethod
    async def restore_active_connections(cls) -> Dict[str, int]:
        if not cls._redis_enabled():
            return {"streams": 0, "workers": 0}
        await cls._ensure_stream_workers()
        return {"streams": 1, "workers": len(_STREAM_WORKER_TASKS)}

    @classmethod
    async def _ack_stream_entry(cls, entry_id: str) -> None:
        await redis_stream_ack_delete(cls._stream_key(), cls.STREAM_GROUP, entry_id)

    @classmethod
    async def _process_claimed_entries(
        cls,
        consumer: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        try:
            claimed_raw = await redis_ops.xautoclaim(
                cls._stream_key(),
                cls.STREAM_GROUP,
                consumer,
                min_idle_time=cls.STREAM_MIN_IDLE_MS,
                start_id="0-0",
                count=cls._stream_batch_size(),
            )
        except Exception as error:
            if redis_error_contains(error, "NOGROUP"):
                await cls._ensure_consumer_group(force=True)
                return []
            logger.warning("EDO Faktura.uz xautoclaim failed: %s", error)
            return []

        entries: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(claimed_raw, (list, tuple)) and len(claimed_raw) >= 2:
            entries = claimed_raw[1] or []
        return [
            (str(entry_id), fields if isinstance(fields, dict) else {})
            for entry_id, fields in entries
        ]

    @classmethod
    async def _stream_worker_loop(cls, worker_index: int) -> None:
        task_key = cls._worker_task_key(worker_index)
        consumer = f"{_INSTANCE_ID}:{worker_index}"
        logger.info("EDO Faktura.uz stream worker started: worker=%s", worker_index)
        try:
            await cls._ensure_consumer_group()
            while True:
                try:
                    now = _now_ts()
                    last_claim_ts = int(_STREAM_CLAIM_TS.get(cls._stream_key()) or 0)
                    if now - last_claim_ts >= cls.STREAM_CLAIM_INTERVAL_SEC:
                        _STREAM_CLAIM_TS[cls._stream_key()] = now
                        for entry_id, fields in await cls._process_claimed_entries(consumer):
                            await cls._process_stream_entry(entry_id, fields)

                    try:
                        records = await redis_ops.xreadgroup(
                            groupname=cls.STREAM_GROUP,
                            consumername=consumer,
                            streams={cls._stream_key(): ">"},
                            count=cls._stream_batch_size(),
                            block=cls.STREAM_READ_BLOCK_MS,
                        )
                    except Exception as error:
                        if redis_error_contains(error, "NOGROUP"):
                            await cls._ensure_consumer_group(force=True)
                            continue
                        raise

                    for _, entries in records or []:
                        for entry_id, fields in entries or []:
                            await cls._process_stream_entry(
                                str(entry_id),
                                fields if isinstance(fields, dict) else {},
                            )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.exception("EDO Faktura.uz stream worker error: %s", error)
                    await asyncio.sleep(2)
        finally:
            async with _STREAM_WORKER_LOCK:
                current = _STREAM_WORKER_TASKS.get(task_key)
                if current is asyncio.current_task():
                    _STREAM_WORKER_TASKS.pop(task_key, None)

    @classmethod
    def _stream_entry_attempt(cls, fields: Dict[str, Any]) -> int:
        return max(_to_int(fields.get("attempt"), 0), 0)

    @classmethod
    async def _process_stream_entry(cls, entry_id: str, fields: Dict[str, Any]) -> None:
        ci = _text(fields.get("connected_integration_id"))
        action = _text(fields.get("action"))
        firm_id = _to_int(fields.get("firm_id"), 0)
        document_id = _text(fields.get("data"))
        user_id = _to_int(fields.get("user_id"), 0)
        attempt = cls._stream_entry_attempt(fields)

        if not ci or action not in {"import", "export"} or firm_id <= 0 or not document_id:
            logger.warning("EDO Faktura.uz invalid stream entry: entry_id=%s fields=%s", entry_id, fields)
            await cls._ack_stream_entry(entry_id)
            return

        worker = cls()
        worker.connected_integration_id = ci
        try:
            await worker._process_task(
                action=action,
                document_id=document_id,
                firm_id=firm_id,
                user_id=user_id,
            )
            await cls._ack_stream_entry(entry_id)
        except EdoFakturaUzNonRetryableError as error:
            await cls._move_to_dlq(entry_id, fields, error, attempt + 1)
            await cls._ack_stream_entry(entry_id)
        except Exception as error:
            next_attempt = attempt + 1
            if next_attempt >= cls._stream_retry_limit():
                await cls._move_to_dlq(entry_id, fields, error, next_attempt)
                await cls._ack_stream_entry(entry_id)
                return
            retry_fields = dict(fields)
            retry_fields["attempt"] = str(next_attempt)
            retry_fields["last_error"] = str(error)
            retry_fields["created_at"] = str(_now_ts())
            await cls._enqueue_stream(retry_fields)
            await cls._ack_stream_entry(entry_id)
            logger.warning(
                "EDO Faktura.uz job requeued: ci=%s action=%s doc=%s attempt=%s error=%s",
                ci,
                action,
                document_id,
                next_attempt,
                error,
            )

    @classmethod
    async def _move_to_dlq(
        cls,
        entry_id: str,
        fields: Dict[str, Any],
        error: Exception,
        attempt: int,
    ) -> None:
        payload = dict(fields)
        payload["attempt"] = str(attempt)
        payload["source_stream"] = cls._stream_key()
        payload["source_entry_id"] = entry_id
        payload["failed_at"] = str(_now_ts())
        payload["error"] = str(error)
        await cls._enqueue_stream(payload, dlq=True)
        logger.error(
            "EDO Faktura.uz job moved to DLQ: entry_id=%s attempt=%s error=%s",
            entry_id,
            attempt,
            error,
        )

    def _ci(self) -> str:
        return _text(getattr(self, "connected_integration_id", ""))

    async def _ensure_active_integration(self) -> None:
        ci = self._ci()
        if not ci:
            raise EdoFakturaUzError(111020, "connected_integration_id is required", 400)
        async with RegosAPI(connected_integration_id=ci) as api:
            response = await api.integrations.connected_integration.get(
                ConnectedIntegrationGetRequest(
                    connected_integration_ids=[ci],
                    include_name=False,
                    include_schedule=False,
                )
            )
        rows = response.result if isinstance(response.result, list) else []
        for row in rows:
            if _text(getattr(row, "connected_integration_id", "")) != ci:
                continue
            if _text(getattr(row, "key", "")) != self.integration_key:
                raise EdoFakturaUzError(
                    111021,
                    f"Connected integration {ci} is not {self.integration_key}",
                    400,
                )
            if getattr(row, "is_active", None) is False:
                raise EdoFakturaUzError(111022, f"Connected integration {ci} is inactive", 403)
            return
        raise EdoFakturaUzError(111023, f"Connected integration {ci} was not found", 404)

    async def connect(self, **kwargs) -> Dict[str, Any]:
        await self._ensure_active_integration()
        await self._ensure_stream_workers()
        return {
            "status": "connected",
            "connected_integration_id": self._ci(),
            "queue": "redis_stream",
        }

    async def disconnect(self, **kwargs) -> Dict[str, Any]:
        return {"status": "disconnected", "connected_integration_id": self._ci()}

    async def reconnect(self, **kwargs) -> Dict[str, Any]:
        return await self.connect(**kwargs)

    async def update_settings(self, **kwargs) -> Dict[str, Any]:
        return {"status": "settings updated", "connected_integration_id": self._ci()}

    async def check(self, firm_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        await self._ensure_active_integration()
        if firm_id:
            await FakturaUzClient.create(self._ci(), int(firm_id))
        return {"status": "ok", "connected_integration_id": self._ci()}

    async def handle_webhook(self, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return {"status": "ignored"}

    async def handle_external(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ignored"}

    async def get_documents(
        self,
        firm_id: int,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs,
    ) -> JSONResponse:
        try:
            await self._ensure_active_integration()
            provider = await FakturaUzClient.create(self._ci(), int(firm_id))
            page_limit = max(_to_int(limit, 500), 1)
            page_offset = max(_to_int(offset, 0), 0)
            rows, total = await provider.get_documents(
                start_date=start_date,
                end_date=end_date,
                limit=page_limit,
                offset=page_offset,
            )
            next_offset = page_offset + page_limit if page_offset + page_limit < total else 0
            return _json_response(
                {
                    "ok": True,
                    "result": rows,
                    "next_offset": next_offset,
                    "total": total,
                }
            )
        except EdoFakturaUzError as error:
            return _json_response(
                {
                    "ok": False,
                    "result": {
                        "error": error.code,
                        "description": error.description,
                    },
                },
                status_code=error.status_code,
            )

    async def get_document_operations(
        self,
        id: Optional[str] = None,
        document_id: Optional[str] = None,
        firm_id: Optional[int] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        doc_id = _text(document_id or id)
        if not doc_id:
            raise EdoFakturaUzError(111030, "document id is required", 400)
        provider = await FakturaUzClient.create(self._ci(), int(firm_id or 0))
        content = await provider.get_document_content(doc_id)
        return content.get("operations") or []

    async def get_document_content(self, **kwargs) -> List[Dict[str, Any]]:
        return await self.get_document_operations(**kwargs)

    async def import_document(
        self,
        id: Optional[str] = None,
        document_id: Optional[str] = None,
        firm_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs,
    ) -> str:
        doc_id = _text(document_id or id)
        if not doc_id:
            raise EdoFakturaUzError(111031, "document id is required", 400)
        if _to_int(firm_id, 0) <= 0:
            raise EdoFakturaUzError(111032, "firm_id is required", 400)
        await self._ensure_active_integration()
        await self._ensure_stream_workers()
        return await self._enqueue_stream(
            {
                "connected_integration_id": self._ci(),
                "action": "import",
                "firm_id": str(int(firm_id or 0)),
                "data": doc_id,
                "user_id": str(_to_int(user_id, 0)),
                "attempt": "0",
                "created_at": str(_now_ts()),
            }
        )

    async def export_documents(
        self,
        ids: Optional[List[Any]] = None,
        messages: Optional[List[Any]] = None,
        firm_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        raw_ids = ids if ids is not None else messages
        if not isinstance(raw_ids, list) or not raw_ids:
            raise EdoFakturaUzError(111033, "ids are required", 400)
        if _to_int(firm_id, 0) <= 0:
            raise EdoFakturaUzError(111034, "firm_id is required", 400)
        await self._ensure_active_integration()
        await self._ensure_stream_workers()
        task_ids: List[str] = []
        for doc_id in raw_ids:
            task_ids.append(
                await self._enqueue_stream(
                    {
                        "connected_integration_id": self._ci(),
                        "action": "export",
                        "firm_id": str(int(firm_id or 0)),
                        "data": _text(doc_id),
                        "user_id": "0",
                        "attempt": "0",
                        "created_at": str(_now_ts()),
                    }
                )
            )
        return {"queued": len(task_ids), "task_ids": task_ids}

    async def _process_task(
        self,
        *,
        action: str,
        document_id: str,
        firm_id: int,
        user_id: int = 0,
    ) -> None:
        ci = self._ci()
        if action == "import":
            provider = await FakturaUzClient.create(ci, firm_id)
            content = await provider.get_document_content(document_id)
            async with RegosAPI(connected_integration_id=ci) as api:
                await self._import_document_to_regos(
                    api,
                    content,
                    firm_id=firm_id,
                    user_id=user_id,
                    connected_integration_id=ci,
                )
            return
        if action == "export":
            await self._export_document_to_faktura(
                document_id=_to_int(document_id, 0),
                firm_id=firm_id,
                connected_integration_id=ci,
            )
            return
        raise EdoFakturaUzError(111035, f"Unsupported EDO action: {action}", 400)

    async def _import_document_to_regos(
        self,
        api: RegosAPI,
        document: Dict[str, Any],
        *,
        firm_id: int,
        user_id: int,
        connected_integration_id: str,
    ) -> int:
        doc_id = 0
        try:
            partner_id = await self._resolve_partner(api, document)
            contract_id = await self._resolve_contract(api, document, firm_id, partner_id)
            invoice_kwargs = {
                "date": _parse_date_to_unix(document.get("date")),
                "contract_id": contract_id,
                "firm_id": firm_id,
                "partner_id": partner_id,
                "currency_id": 1,
                "description": _text(document.get("name"), _text(document.get("id"))),
                "invoice_type": DocInvoiceType.Income,
            }
            if user_id > 0:
                invoice_kwargs["attached_user_id"] = user_id
            add_response = await api.docs.doc_invoice.add(DocInvoiceAddRequest(**invoice_kwargs))
            doc_id = _result_new_id(add_response, "DocInvoice/Add")

            await api.docs.doc_invoice.set_status(
                DocInvoiceSetStatusRequest(
                    document_id=doc_id,
                    status=DocInvoiceStatus.InReceivedProgress,
                )
            )
            await api.docs.doc_invoice.set_external_data(
                DocInvoiceSetExternalDataRequest(
                    document_id=doc_id,
                    connected_integration_id=connected_integration_id,
                    external_id=_text(document.get("external_id") or document.get("id")),
                    roaming_id=_text(document.get("roaming_id")) or None,
                )
            )
            await self._import_and_add_operations(api, doc_id, document.get("operations") or [])
            await api.docs.doc_invoice.set_status(
                DocInvoiceSetStatusRequest(
                    document_id=doc_id,
                    status=DocInvoiceStatus.Received,
                )
            )
            return doc_id
        except Exception as error:
            if doc_id > 0:
                await self._set_invoice_error(
                    api,
                    doc_id,
                    DocInvoiceStatus.ErrorReceived,
                    str(error),
                )
                raise EdoFakturaUzNonRetryableError(111036, str(error)) from error
            raise

    async def _resolve_partner(self, api: RegosAPI, document: Dict[str, Any]) -> int:
        partner_inn = _digits(document.get("partner_inn"))
        partner_name = _text(document.get("partner_name"), partner_inn or "Unknown partner")
        search = partner_inn or partner_name
        response = await api.references.partner.get(
            PartnerGetRequest(
                legal_status=LegalStatus.Legal,
                search=search,
                limit=10,
                offset=0,
            )
        )
        _ensure_api_ok(response, "Partner/Get")
        partners = response.result or []
        if partner_inn:
            for partner in partners:
                if _digits(getattr(partner, "inn", "")) == partner_inn:
                    return int(partner.id)
        if partners:
            return int(partners[0].id)
        add_response = await api.references.partner.add(
            PartnerAddRequest(
                group_id=1,
                legal_status=LegalStatus.Legal,
                name=partner_name,
                fullname=partner_name,
                inn=partner_inn or None,
            )
        )
        return _result_new_id(add_response, "Partner/Add")

    async def _resolve_contract(
        self,
        api: RegosAPI,
        document: Dict[str, Any],
        firm_id: int,
        partner_id: int,
    ) -> int:
        contract_name = _text(document.get("contract"), _text(document.get("id"), "EDO"))
        response = await api.docs.doc_contract.get_short(
            DocContractGetRequest(
                direction=ContractDirection.Income,
                firm_ids=[firm_id],
                partner_ids=[partner_id],
                search=contract_name,
                limit=10,
                offset=0,
            )
        )
        _ensure_api_ok(response, "DocContract/GetShort")
        contracts = response.result or []
        for contract in contracts:
            if _text(getattr(contract, "code", "")) == contract_name or _text(
                getattr(contract, "name", "")
            ) == contract_name:
                return int(contract.id)
        if contracts:
            return int(contracts[0].id)

        doc_date = _parse_date_to_unix(document.get("date"))
        add_response = await api.docs.doc_contract.add(
            DocContractAddRequest(
                code=contract_name,
                date=doc_date,
                direction=ContractDirection.Income,
                name=contract_name,
                firm_id=firm_id,
                partner_id=partner_id,
                amount=_money(document.get("amount")),
                currency_id=1,
                start_date=doc_date,
                end_date=doc_date,
                details=contract_name,
                active=True,
            )
        )
        return _result_new_id(add_response, "DocContract/Add")

    async def _import_and_add_operations(
        self,
        api: RegosAPI,
        document_id: int,
        operations: List[Dict[str, Any]],
    ) -> None:
        if not operations:
            raise EdoFakturaUzError(111037, "Document operations are empty", 400)
        groups = self._build_item_import_groups(operations)
        for matching_type, import_request in groups:
            response = await api.references.item.import_items(import_request)
            _ensure_api_ok(response, f"Item/Import {matching_type.value}")
            failed_rows = [row for row in response.result or [] if getattr(row, "success", None) is False]
            if failed_rows:
                raise EdoFakturaUzError(111038, f"Item import failed: {failed_rows}", 400)

        matches = await self._match_items(api, operations)
        missing = [row["index"] for row in operations if _text(row.get("index")) not in matches]
        if missing:
            raise EdoFakturaUzError(111039, f"Items were not matched: {', '.join(missing)}", 400)

        rows = [
            InvoiceOperationAdd(
                document_id=document_id,
                item_id=matches[_text(operation.get("index"))],
                quantity=_to_decimal(operation.get("quantity"), Decimal("0")),
                price=_to_decimal(operation.get("price"), Decimal("0")),
                vat_value=_to_decimal(operation.get("vat_rate"), Decimal("0")),
            )
            for operation in operations
        ]
        await api.docs.doc_invoice.lock(IDRequest(id=document_id))
        try:
            response = await api.docs.invoice_operation.add(rows)
            _ensure_api_ok(response, "InvoiceOperation/Add")
        finally:
            await api.docs.doc_invoice.unlock(IDRequest(id=document_id))

    def _build_item_import_groups(
        self,
        operations: List[Dict[str, Any]],
    ) -> List[Tuple[ItemMatchingType, ItemImportRequest]]:
        grouped: Dict[ItemMatchingType, List[ItemImportData]] = {
            ItemMatchingType.ICPSBarcode: [],
            ItemMatchingType.ICPS: [],
            ItemMatchingType.Barcode: [],
        }
        for operation in operations:
            index = _text(operation.get("index"))
            name = _text(operation.get("name"), f"Item {index}")
            icps = _text(operation.get("icps"))
            barcode = _text(operation.get("barcode"))
            data = ItemImportData(
                index=index,
                name=name,
                icps=icps or None,
                icpsbarcode=f"{icps}|{barcode}" if icps and barcode else None,
                barcodes=barcode or None,
                package_code=_to_optional_int(operation.get("package_code")),
            )
            if icps and barcode:
                grouped[ItemMatchingType.ICPSBarcode].append(data)
            elif icps:
                grouped[ItemMatchingType.ICPS].append(data)
            elif barcode:
                grouped[ItemMatchingType.Barcode].append(data)
            else:
                raise EdoFakturaUzError(111040, f"Operation {index} does not contain ICPS or barcode", 400)

        result: List[Tuple[ItemMatchingType, ItemImportRequest]] = []
        for matching_type, rows in grouped.items():
            if not rows:
                continue
            comparation = ItemImportComparationValue(matching_type.value)
            result.append(
                (
                    matching_type,
                    ItemImportRequest(
                        comparation_value=comparation,
                        barcode_separator=",",
                        group_id=0,
                        unit_id=0,
                        vat_value_id=0,
                        data=rows,
                    ),
                )
            )
        return result

    async def _match_items(
        self,
        api: RegosAPI,
        operations: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        grouped: Dict[ItemMatchingType, List[ItemMatchingData]] = {}
        for operation in operations:
            matching_type, value = self._operation_matching_value(operation)
            grouped.setdefault(matching_type, []).append(
                ItemMatchingData(index=_text(operation.get("index")), value=value)
            )

        matches: Dict[str, int] = {}
        for matching_type, data in grouped.items():
            response = await api.references.item.match(
                ItemMatchingRequest(type=matching_type, data=data)
            )
            _ensure_api_ok(response, f"Item/Match {matching_type.value}")
            for row in response.result or []:
                item_id = _to_int(getattr(row, "item_id", None), 0)
                index = _text(getattr(row, "index", ""))
                if item_id > 0 and index:
                    matches[index] = item_id
        return matches

    def _operation_matching_value(self, operation: Dict[str, Any]) -> Tuple[ItemMatchingType, str]:
        icps = _text(operation.get("icps"))
        barcode = _text(operation.get("barcode"))
        if icps and barcode:
            return ItemMatchingType.ICPSBarcode, f"{icps}|{barcode}"
        if icps:
            return ItemMatchingType.ICPS, icps
        if barcode:
            return ItemMatchingType.Barcode, barcode
        raise EdoFakturaUzError(111041, "Operation does not contain ICPS or barcode", 400)

    async def _export_document_to_faktura(
        self,
        *,
        document_id: int,
        firm_id: int,
        connected_integration_id: str,
    ) -> None:
        if document_id <= 0:
            raise EdoFakturaUzError(111042, "document_id is required", 400)
        async with RegosAPI(connected_integration_id=connected_integration_id) as api:
            document = await api.docs.doc_invoice.get_by_id(document_id)
            if not document:
                raise EdoFakturaUzNonRetryableError(
                    111043,
                    f"DocInvoice {document_id} was not found",
                    404,
                )
            try:
                await self._validate_export_document(document)
                await api.docs.doc_invoice.set_status(
                    DocInvoiceSetStatusRequest(
                        document_id=document_id,
                        status=DocInvoiceStatus.InSentProgress,
                    )
                )
                operations_response = await api.docs.invoice_operation.get(
                    InvoiceOperationGetRequest(document_ids=[document_id])
                )
                _ensure_api_ok(operations_response, "InvoiceOperation/Get")
                provider = await FakturaUzClient.create(connected_integration_id, firm_id)
                external_id = await provider.send_document_invoice(
                    document,
                    operations_response.result or [],
                )
                await api.docs.doc_invoice.set_external_data(
                    DocInvoiceSetExternalDataRequest(
                        document_id=document_id,
                        connected_integration_id=connected_integration_id,
                        external_id=external_id,
                    )
                )
                await api.docs.doc_invoice.set_status(
                    DocInvoiceSetStatusRequest(
                        document_id=document_id,
                        status=DocInvoiceStatus.Sent,
                    )
                )
            except EdoFakturaUzNonRetryableError as error:
                await self._set_invoice_error(
                    api,
                    document_id,
                    DocInvoiceStatus.ErrorSent,
                    error.description,
                )
                raise
            except Exception as error:
                await self._set_invoice_error(
                    api,
                    document_id,
                    DocInvoiceStatus.ErrorSent,
                    str(error),
                )
                raise EdoFakturaUzNonRetryableError(111044, str(error)) from error

    async def _validate_export_document(self, document: DocInvoice) -> None:
        if getattr(document, "performed", None) is False:
            raise EdoFakturaUzNonRetryableError(
                111045,
                f"DocInvoice {document.id} is not performed",
                400,
            )
        if not getattr(document, "partner", None):
            raise EdoFakturaUzNonRetryableError(
                111046,
                f"DocInvoice {document.id} does not contain partner",
                400,
            )
        if not getattr(document, "firm", None):
            raise EdoFakturaUzNonRetryableError(
                111047,
                f"DocInvoice {document.id} does not contain firm",
                400,
            )

    async def _set_invoice_error(
        self,
        api: RegosAPI,
        document_id: int,
        status: DocInvoiceStatus,
        message: str,
    ) -> None:
        try:
            await api.docs.doc_invoice.set_status(
                DocInvoiceSetStatusRequest(
                    document_id=document_id,
                    status=status,
                    error_message=str(message)[:1000],
                )
            )
        except Exception as error:
            logger.warning(
                "Failed to set EDO invoice error status: document_id=%s error=%s",
                document_id,
                error,
            )


__all__ = ["EdoFakturaUzIntegration", "FakturaUzClient"]
