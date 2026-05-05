from __future__ import annotations

import base64
import hashlib
import hmac
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx

from config.settings import settings as app_settings

from .config import MetaLeadgenCrmChannelConfig
from .models import (
    MetaLeadDetails,
    MetaLeadEvent,
    RuntimeConfig,
    json_dumps,
    json_loads,
    normalize_text,
    now_ts,
    parse_meta_lead_details,
    to_int,
)
from .redis_state import MetaLeadgenRedisState


def headers_ci(headers: Dict[str, Any], key: str) -> Optional[str]:
    key_lower = str(key or "").lower()
    for header_name, header_value in (headers or {}).items():
        if str(header_name or "").lower() == key_lower:
            value = str(header_value or "").strip()
            if value:
                return value
    return None


class MetaLeadgenApi:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client

    @staticmethod
    def app_config() -> Tuple[str, str, str]:
        app_id = str(getattr(app_settings, "meta_leadgen_app_id", "") or "").strip()
        app_secret = str(getattr(app_settings, "meta_leadgen_app_secret", "") or "").strip()
        redirect_uri = str(getattr(app_settings, "meta_leadgen_redirect_uri", "") or "").strip()
        if not app_id or not app_secret or not redirect_uri:
            raise ValueError("Service Meta Leadgen app config is required")
        return app_id, app_secret, redirect_uri

    @staticmethod
    def webhook_verify_token() -> str:
        verify_token = str(
            getattr(app_settings, "meta_leadgen_webhook_verify_token", "") or ""
        ).strip()
        if not verify_token:
            raise ValueError("Service Meta Leadgen webhook verify token is required")
        return verify_token

    @staticmethod
    def encode_oauth_state(connected_integration_id: str, nonce: str) -> str:
        payload = json_dumps({"ci": connected_integration_id, "nonce": nonce}).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def decode_oauth_state(state: str) -> Tuple[Optional[str], Optional[str]]:
        token = str(state or "").strip()
        if not token:
            return None, None
        token += "=" * ((4 - (len(token) % 4)) % 4)
        try:
            payload = json_loads(base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8"))
        except Exception:
            return None, None
        if not isinstance(payload, dict):
            return None, None
        return (
            normalize_text(payload.get("ci"), max_len=128),
            normalize_text(payload.get("nonce"), max_len=128),
        )

    @staticmethod
    async def store_oauth_state(connected_integration_id: str, nonce: str) -> None:
        await MetaLeadgenRedisState.set(
            MetaLeadgenRedisState.key("oauth_state", nonce),
            connected_integration_id,
            MetaLeadgenCrmChannelConfig.OAUTH_STATE_TTL_SEC,
            min_ttl_sec=30,
        )

    @staticmethod
    async def consume_oauth_state(nonce: str) -> Optional[str]:
        key = MetaLeadgenRedisState.key("oauth_state", nonce)
        value = await MetaLeadgenRedisState.get(key)
        await MetaLeadgenRedisState.delete(key)
        return normalize_text(value, max_len=128)

    @classmethod
    async def build_oauth_url(cls, connected_integration_id: str) -> str:
        app_id, _, redirect_uri = cls.app_config()
        nonce = uuid.uuid4().hex
        await cls.store_oauth_state(connected_integration_id, nonce)
        return f"{MetaLeadgenCrmChannelConfig.OAUTH_DIALOG_URL}?{urlencode({
            'client_id': app_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ','.join(MetaLeadgenCrmChannelConfig.OAUTH_SCOPES),
            'state': cls.encode_oauth_state(connected_integration_id, nonce),
        })}"

    @staticmethod
    def verify_signature(
        headers: Dict[str, Any],
        raw_body: Any,
        app_secret: str,
    ) -> bool:
        signature_header = headers_ci(headers, "x-hub-signature-256")
        if not signature_header or not str(signature_header).startswith("sha256="):
            return False
        if isinstance(raw_body, bytes):
            body_bytes = raw_body
        elif isinstance(raw_body, str):
            body_bytes = raw_body.encode("utf-8")
        else:
            return False
        expected = hmac.new(
            str(app_secret or "").encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        provided = str(signature_header).split("=", 1)[1].strip()
        return bool(provided) and hmac.compare_digest(provided, expected)

    async def exchange_code(self, code: str) -> Tuple[str, Optional[int]]:
        app_id, app_secret, redirect_uri = self.app_config()
        response = await self.http_client.get(
            MetaLeadgenCrmChannelConfig.OAUTH_TOKEN_URL,
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        token = normalize_text(payload.get("access_token"))
        if not token:
            raise RuntimeError("Meta OAuth token exchange did not return access_token")
        expires_in = to_int(payload.get("expires_in"), None)
        expires_at = now_ts() + int(expires_in) if expires_in and expires_in > 0 else None
        return token, expires_at

    async def exchange_long_lived(self, short_token: str) -> Tuple[str, Optional[int]]:
        app_id, app_secret, _ = self.app_config()
        response = await self.http_client.get(
            MetaLeadgenCrmChannelConfig.OAUTH_TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": short_token,
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        token = normalize_text(payload.get("access_token"))
        if not token:
            raise RuntimeError("Meta long-lived token exchange did not return access_token")
        expires_in = to_int(payload.get("expires_in"), None)
        expires_at = now_ts() + int(expires_in) if expires_in and expires_in > 0 else None
        return token, expires_at

    async def list_pages(self, user_access_token: str) -> List[Dict[str, Any]]:
        pages: List[Dict[str, Any]] = []
        next_url: Optional[str] = f"{MetaLeadgenCrmChannelConfig.GRAPH_BASE_URL}/me/accounts"
        params: Optional[Dict[str, Any]] = {
            "access_token": user_access_token,
            "fields": "id,name,access_token,tasks",
            "limit": 100,
        }
        for _ in range(10):
            response = await self.http_client.get(next_url, params=params)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            rows = payload.get("data") if isinstance(payload, dict) else None
            if isinstance(rows, list):
                pages.extend(row for row in rows if isinstance(row, dict))
            paging = payload.get("paging") if isinstance(payload, dict) else None
            next_page = paging.get("next") if isinstance(paging, dict) else None
            if not next_page:
                break
            next_url = str(next_page)
            params = None
        return pages

    async def resolve_page(
        self,
        runtime: RuntimeConfig,
        user_access_token: str,
    ) -> Tuple[str, Optional[str], str]:
        pages = await self.list_pages(user_access_token)
        expected_page_id = normalize_text(runtime.page_id, max_len=128)
        selected: Optional[Dict[str, Any]] = None
        if expected_page_id:
            for row in pages:
                if isinstance(row, dict) and str(row.get("id") or "").strip() == expected_page_id:
                    selected = row
                    break
            if not selected:
                raise RuntimeError("Authorized Meta account does not include configured meta_page_id")
        elif len(pages) == 1 and isinstance(pages[0], dict):
            selected = pages[0]
        else:
            raise RuntimeError("meta_page_id is required when OAuth account has zero or multiple pages")

        page_id = normalize_text(selected.get("id"), max_len=128) if selected else None
        page_name = normalize_text(selected.get("name"), max_len=250) if selected else None
        page_token = normalize_text(selected.get("access_token")) if selected else None
        if not page_id or not page_token:
            raise RuntimeError("Meta page id/access token was not returned")
        return page_id, page_name, page_token

    async def subscribe_page(self, page_id: str, page_access_token: str) -> Dict[str, Any]:
        response = await self.http_client.post(
            f"{MetaLeadgenCrmChannelConfig.GRAPH_BASE_URL}/{page_id}/subscribed_apps",
            params={
                "access_token": page_access_token,
                "subscribed_fields": "leadgen",
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        return payload if isinstance(payload, dict) else {}

    async def fetch_lead_details(
        self,
        runtime: RuntimeConfig,
        event: MetaLeadEvent,
    ) -> MetaLeadDetails:
        if not runtime.page_access_token:
            raise RuntimeError("Meta page access token is missing")
        response = await self.http_client.get(
            f"{MetaLeadgenCrmChannelConfig.GRAPH_BASE_URL}/{event.leadgen_id}",
            params={
                "access_token": runtime.page_access_token,
                "fields": (
                    "id,created_time,ad_id,ad_name,adset_id,adset_name,"
                    "campaign_id,campaign_name,form_id,field_data,is_organic,platform"
                ),
            },
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            raise RuntimeError("Meta lead details response is not an object")
        return parse_meta_lead_details(payload, event)
