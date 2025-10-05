import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Sequence
from email.message import EmailMessage

from pathlib import Path
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse 
from starlette.responses import FileResponse, HTMLResponse, Response, RedirectResponse
import json

from core.api.regos_api import RegosAPI
from schemas.api.docs.purchase import DocPurchaseGetRequest
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest


from clients.base import ClientBase
from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client
from email.utils import formataddr
from email.header import Header

from schemas.integration.integration_base import IntegrationBase

logger = setup_logger("tsd")


class TsdIntegration(ClientBase):

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
        
    def _json_error(self, status: int, description: str):
        return JSONResponse(status_code=status, content={"error": status, "description": description})
                                                     

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
        try:
            method = str(data.get("method") or "").upper()
            if method != "POST":
                return self._json_error(405, "Method not allowed; use POST")

            headers: Dict[str, str] = data.get("headers") or {}
            ci = headers.get("Connected-Integration-Id") or getattr(self, "connected_integration_id", None)

            body = data.get("body") or {}
            action = str(body.get("action") or "").lower()
            params = body.get("params") or {}

            if action in ("", "ping"):
                return {"result": {"pong": True, "ci": ci}}

            if action == "login":
                return {"result": {"status": "logged_in", "ci": ci}}

            if action == "send":
                return {"result": {"status": "sent", "ci": ci}}

            # список документов
            if action == "purchase_list":
                page = int(params.get("page", 1) or 1)
                page_size = int(params.get("page_size", 20) or 20)
                query = (params.get("query") or "").strip() or None
                start = params.get("start_date")
                end = params.get("end_date")

                async with RegosAPI(connected_integration_id=ci) as api:
                    req = DocPurchaseGetRequest(
                        start_date=start,
                        end_date=end,
                        search=query,
                        limit=page_size,
                        offset=(page - 1) * page_size,
                    )
                    docs = await api.docs.purchase.get(req)

                return {"result": {
                    "items": jsonable_encoder(docs),
                    "page": page,
                    "page_size": page_size
                }}

            # один документ
            if action == "purchase_get":
                doc_id = params.get("doc_id")
                if not doc_id:
                    return self._json_error(400, "doc_id is required")

                async with RegosAPI(connected_integration_id=ci) as api:
                    doc = await api.docs.purchase.get_by_id(int(doc_id))

                if not doc:
                    return self._json_error(404, f"DocPurchase id={doc_id} not found")

                return {"result": {
                    "doc": jsonable_encoder(doc),
                    "operations": []
                }}

            return self._json_error(400, f"Unknown action '{action}'")

        except Exception as e:
            logger.exception("handle_external error")
            return self._json_error(500, f"Server error: {e}")


    async def handle_ui(self, envelope: dict) -> Any:
        method = str(envelope.get("method") or "").upper()
        if method != "GET":
            return self._json_error(405, "Method not allowed; use GET")

        headers: Dict[str, str] = envelope.get("headers") or {}
        query: Dict[str, Any] = envelope.get("query") or {}

        token = (
            headers.get("Connected-Integration-Id")
            or query.get("ci")
            or getattr(self, "connected_integration_id", None)
        )

        # assets (?asset=...)
        asset_rel = query.get("assets") or query.get("asset")
        if asset_rel:
            file_path = self._safe_join(self.ASSETS_DIR, str(asset_rel))
            if not file_path or not file_path.exists():
                return Response("asset not found", status_code=404)
            # Явно ставим content-type для .js/.css
            mt = None
            ext = file_path.suffix.lower()
            if ext == ".js":
                mt = "application/javascript"
            elif ext == ".css":
                mt = "text/css"
            elif ext in (".webmanifest", ".json"):
                mt = "application/manifest+json" if ext == ".webmanifest" else "application/json"
            return FileResponse(str(file_path), media_type=mt)

        # service worker
        if str(query.get("pwa", "")).lower() == "sw":
            sw_path = self.PWA_DIR / "sw.js"
            if not sw_path.exists():
                return Response("sw.js not found", status_code=404)
            return FileResponse(str(sw_path), media_type="application/javascript")

        # manifest (ОТНОСИТЕЛЬНЫЕ пути!)
        if str(query.get("pwa", "")).lower() == "manifest":
            mf_path = self.PWA_DIR / "manifest.webmanifest"
            if mf_path.exists():
                return FileResponse(str(mf_path), media_type="application/manifest+json")
            manifest = {
                "name": "TSD",
                "short_name": "TSD",
                "start_url": ".",
                "scope": "./",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#111827",
                "icons": [
                    {"src": "?asset=icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "?asset=icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            }
            return Response(json.dumps(manifest, ensure_ascii=False), media_type="application/manifest+json")

        # index.html (+ window.__CI__)
        index_path = self.PWA_DIR / "index.html"
        if not index_path.exists():
            return Response("index.html not found", status_code=500)

        try:
            html = index_path.read_text(encoding="utf-8")
        except Exception:
            return FileResponse(str(index_path), media_type="text/html; charset=utf-8")

        inject = ""
        if token:
            safe_token = json.dumps(str(token))
            inject = f"<script>window.__CI__={safe_token};</script>"

        lower = html.lower()
        if "</body>" in lower:
            pos = lower.rfind("</body>")
            html = html[:pos] + inject + html[pos:]
        else:
            html += inject

        return HTMLResponse(html, status_code=200)

