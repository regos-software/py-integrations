import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Sequence
from email.message import EmailMessage

from pathlib import Path
from starlette.responses import FileResponse, HTMLResponse, Response, RedirectResponse
import json

from core.api.regos_api import RegosAPI
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest
from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)

from clients.base import ClientBase
from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client
from email.utils import formataddr
from email.header import Header

from schemas.integration.integration_base import IntegrationBase

logger = setup_logger("tsd")


class TsdIntegration(IntegrationBase, ClientBase):

    INTEGRATION_KEY = "tsd"

    # где лежат вьюхи PWA: clients/tsd/pwa/*
    PWA_DIR = Path(__file__).resolve().parent / "pwa"
    ASSETS_DIR = PWA_DIR / "assets"


    SETTINGS_TTL = settings.redis_cache_ttl
    SETTINGS_KEYS = {
        "": "",
    }

    # -------------------- helpers --------------------
    @staticmethod
    def _safe_join(base: Path, rel: str) -> Optional[Path]:
        try:
            p = (base / rel).resolve()
            return p if str(p).startswith(str(base.resolve())) else None
        except Exception:
            return None
        
    def _create_error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(result=IntegrationErrorModel(error=code, description=description))

    async def _fetch_settings(self, cache_key: str) -> dict:
        # 1) Redis
        if settings.redis_enabled and redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    if isinstance(cached, (bytes, bytearray)):
                        cached = cached.decode("utf-8")
                    logger.debug(f"Настройки получены из Redis: {cache_key}")
                    return json.loads(cached)
            except Exception as err:
                logger.warning(f"Ошибка Redis: {err}, загружаем из API")

        # 2) API
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            settings_response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(integration_key=self.INTEGRATION_KEY)
            )

        settings_map = {item.key.lower(): item.value for item in settings_response}

        # 3) Cache
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(cache_key, self.SETTINGS_TTL, json.dumps(settings_map))
            except Exception as err:
                logger.warning(f"Не удалось сохранить настройки в Redis: {err}")

        return settings_map


    # -------------------- public API --------------------

    async def handle_external(self, data: dict) -> Any:
        """
        POST API для PWA:
          body: {"action": "...", "params": {...}}
        """
        try:
            method = str(data.get("method") or "").upper()
            if method != "POST":
                return self._create_error_response(405, "Method not allowed; use POST")

            headers: Dict[str, str] = data.get("headers") or {}
            ci = headers.get("Connected-Integration-Id") or getattr(self, "connected_integration_id", None)

            body = data.get("body") or {}
            action = str(body.get("action") or "").lower()
            params = body.get("params") or {}

            if action in ("", "ping"):
                return IntegrationSuccessResponse(result={"pong": True, "ci": ci})

            # пример: login
            if action == "login":
                # TODO: ваша логика
                return IntegrationSuccessResponse(result={"status": "logged_in", "ci": ci})

            # пример: отправка/сохранение чего-либо
            if action == "send":
                # TODO: ваша логика с params
                return IntegrationSuccessResponse(result={"status": "sent", "ci": ci})

            return IntegrationErrorResponse(
                result=IntegrationErrorModel(error=400, description=f"Unknown action '{action}'")
            )
        except Exception as e:
            logger.exception("handle_external error")
            return IntegrationErrorResponse(
                result=IntegrationErrorModel(error=500, description=f"Server error: {e}")
            )


    async def handle_ui(self, envelope: dict) -> Any:
        """
        UI (GET) — отдаём PWA из папки рядом:
          /clients/tsd?pwa=sw          -> sw.js (application/javascript)
          /clients/tsd?pwa=manifest    -> manifest.webmanifest (application/manifest+json)
          /clients/tsd?asset=icon.png  -> assets/icon.png (content-type по расширению)
          /clients/tsd[?ci=TOKEN]      -> index.html (+вставим window.__CI__=TOKEN)
        """
        method = str(envelope.get("method") or "").upper()
        if method != "GET":
            return self._create_error_response(405, "Method not allowed; use GET")

        headers: Dict[str, str] = envelope.get("headers") or {}
        query: Dict[str, Any] = envelope.get("query") or {}

        # token из заголовка/квери/контекста
        token = (
            headers.get("Connected-Integration-Id")
            or query.get("ci")
            or getattr(self, "connected_integration_id", None)
        )

        # 1) assets: ?asset=...
        asset_rel = query.get("asset")
        if asset_rel:
            file_path = self._safe_join(self.ASSETS_DIR, str(asset_rel))
            if not file_path or not file_path.exists():
                return Response("asset not found", status_code=404)
            return FileResponse(str(file_path))  # content-type определится автоматически

        # 2) service worker: ?pwa=sw
        if str(query.get("pwa", "")).lower() == "sw":
            sw_path = self.PWA_DIR / "sw.js"
            if not sw_path.exists():
                return Response("sw.js not found", status_code=404)
            return FileResponse(str(sw_path), media_type="application/javascript")

        # 3) manifest: ?pwa=manifest
        if str(query.get("pwa", "")).lower() == "manifest":
            mf_path = self.PWA_DIR / "manifest.webmanifest"
            if mf_path.exists():
                return FileResponse(str(mf_path), media_type="application/manifest+json")
            # fallback: сгенерим минимальный manifest на лету
            manifest = {
                "name": "TSD",
                "short_name": "TSD",
                "start_url": ".",
                "scope": "/clients/",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#111827",
                "icons": [
                    {"src": "/clients/tsd?asset=icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/clients/tsd?asset=icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            }
            return Response(json.dumps(manifest, ensure_ascii=False), media_type="application/manifest+json")

        # 4) index.html (по умолчанию)
        index_path = self.PWA_DIR / "index.html"
        if not index_path.exists():
            return Response("index.html not found", status_code=500)

        # читаем как текст и мягко внедрим токен (если есть)
        try:
            html = index_path.read_text(encoding="utf-8")
        except Exception:
            return FileResponse(str(index_path), media_type="text/html; charset=utf-8")

        inject = ""
        if token:
            # window.__CI__ доступен приложению
            safe_token = json.dumps(str(token))
            inject = f"<script>window.__CI__={safe_token};</script>"

        if "</body>" in html.lower():
            # простая вставка перед </body>
            # ищем закрывающий тег без учета регистра
            lower = html.lower()
            pos = lower.rfind("</body>")
            html = html[:pos] + inject + html[pos:]
        else:
            html += inject

        return HTMLResponse(html, status_code=200)

