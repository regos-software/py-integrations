import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Sequence
from email.message import EmailMessage

from pathlib import Path
from fastapi.encoders import jsonable_encoder
from httpx import request
from starlette.responses import JSONResponse 
from starlette.responses import FileResponse, HTMLResponse, Response, RedirectResponse
import json

from core.api.regos_api import RegosAPI
from schemas.api.docs.cheque import SortOrder
from schemas.api.docs.purchase import DocPurchaseGetRequest, DocPurchaseSortOrder
from schemas.api.docs.purchase_operation import PurchaseOperationAddRequest, PurchaseOperationDeleteItem, PurchaseOperationEditItem
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

            # --- ping/login/send ---
            if action in ("", "ping"):
                return {"result": {"pong": True, "ci": ci}}

            if action == "login":
                return {"result": {"status": "logged_in", "ci": ci}}

            if action == "send":
                return {"result": {"status": "sent", "ci": ci}}

            # --- список документов ---
            if action == "purchase_list":
                page = int(params.get("page", 1) or 1)
                page_size = int(params.get("page_size", 20) or 20)
                query = (params.get("query") or "").strip() or None
                start = params.get("start_date")
                end = params.get("end_date")

                async with RegosAPI(connected_integration_id=ci) as api:
                    req = DocPurchaseGetRequest(
                        performed=False,
                        deleted_mark=False,
                        start_date=start,
                        end_date=end,
                        search=query,
                        limit=page_size,
                        sort_orders=[DocPurchaseSortOrder(column="date", direction="desc")],
                        offset=(page - 1) * page_size,
                    )
                    docs = await api.docs.purchase.get(req)

                return {"result": {
                    "items": jsonable_encoder(docs),
                    "page": page,
                    "page_size": page_size
                }}

            # --- один документ + операции (ЕДИНСТВЕННАЯ ветка purchase_get) ---
            if action == "purchase_get":
                raw_id = params.get("doc_id")
                if raw_id is None:
                    return self._json_error(400, "doc_id is required")
                try:
                    doc_id = int(raw_id)
                except (TypeError, ValueError):
                    return self._json_error(400, "doc_id must be integer")

                async with RegosAPI(connected_integration_id=ci) as api:
                    doc = await api.docs.purchase.get_by_id(doc_id)
                    ops = await api.docs.purchase_operation.get_by_document_id(doc_id)

                if not doc:
                    return self._json_error(404, f"DocPurchase id={doc_id} not found")

                return {"result": {
                    "doc": jsonable_encoder(doc),
                    "operations": jsonable_encoder(ops)
                }}

            # --- операции документа ---
            if action == "purchase_ops_get":
                try:
                    doc_id = int(params.get("doc_id"))
                except (TypeError, ValueError):
                    return self._json_error(400, "doc_id must be integer")
                async with RegosAPI(connected_integration_id=ci) as api:
                    ops = await api.docs.purchase_operation.get_by_document_id(doc_id)
                return {"result": {"items": jsonable_encoder(ops)}}

            if action == "purchase_ops_add":
                payload = params.get("items") or []
                if not isinstance(payload, list) or not payload:
                    return self._json_error(400, "items (array) required")
                async with RegosAPI(connected_integration_id=ci) as api:
                    res = await api.docs.purchase_operation.add(
                        [PurchaseOperationAddRequest.model_validate(x) for x in payload]
                    )
                return {"result": jsonable_encoder(res)}

            if action == "purchase_ops_edit":
                payload = params.get("items") or []
                if not isinstance(payload, list) or not payload:
                    return self._json_error(400, "items (array) required")
                async with RegosAPI(connected_integration_id=ci) as api:
                    res = await api.docs.purchase_operation.edit(
                        [PurchaseOperationEditItem.model_validate(x) for x in payload]
                    )
                return {"result": jsonable_encoder(res)}

            if action == "purchase_ops_delete":
                payload = params.get("items") or []
                if not isinstance(payload, list) or not payload:
                    return self._json_error(400, "items (array) required")
                async with RegosAPI(connected_integration_id=ci) as api:
                    res = await api.docs.purchase_operation.delete(
                        [PurchaseOperationDeleteItem.model_validate(x) for x in payload]
                    )
                return {"result": jsonable_encoder(res)}

            # --- поиск номенклатуры (с учётом контекста документа) ---
            if action == "product_search":
                q = (params.get("q") or "").strip()
                if not q:
                    return {"result": {"items": []}}

                def _to_int(v):
                    try:
                        return int(v) if v is not None else None
                    except (TypeError, ValueError):
                        return None

                # контекст из запроса
                price_type_id = _to_int(params.get("price_type_id"))
                stock_id      = _to_int(params.get("stock_id"))
                limit         = _to_int(params.get("limit")) or 50
                if limit < 1: limit = 1
                if limit > 200: limit = 200

                # при необходимости — подтягиваем контекст из документа
                raw_doc_id = params.get("doc_id")
                if (price_type_id is None or stock_id is None) and raw_doc_id is not None:
                    doc_id = _to_int(raw_doc_id)
                    if doc_id is None:
                        return self._json_error(400, "doc_id must be integer")

                    async with RegosAPI(connected_integration_id=ci) as api:
                        doc = await api.docs.purchase.get_by_id(doc_id)

                    if not doc:
                        return self._json_error(404, f"DocPurchase id={doc_id} not found")

                    # безопасно извлекаем идентификаторы
                    try:
                        if price_type_id is None and getattr(doc, "price_type", None):
                            price_type_id = _to_int(getattr(doc.price_type, "id", None))
                    except Exception:
                        pass
                    try:
                        if stock_id is None and getattr(doc, "stock", None):
                            stock_id = _to_int(getattr(doc.stock, "id", None))
                    except Exception:
                        pass

                # выполняем поиск: сперва расширенный (GetExt), затем — мягкий откат
                async with RegosAPI(connected_integration_id=ci) as api:
                    try:
                        # Новый путь: расширенные карточки с учётом склада/типа цены
                        items = await api.refrences.item.search_and_get_ext(
                            q,
                            stock_id=stock_id,
                            price_type_id=price_type_id,
                            limit=limit
                        )
                    except AttributeError:
                        # Если метода нет (старый клиент) — откатываемся
                        try:
                            items = await api.refrences.item.search_and_get(
                                q,
                                price_type_id=price_type_id,
                                stock_id=stock_id
                            )
                        except TypeError:
                            # Совсем старый интерфейс: только по строке
                            items = await api.refrences.item.search_and_get(q)

                return {"result": {"items": jsonable_encoder(items)}}


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
                return Response("assets not found", status_code=404)
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
            # определяем текущий путь без query (?pwa=manifest)
            base_path = str(envelope.get("path") or "").rstrip("/")

            # формируем динамические пути для start_url и scope
            manifest = {
                "name": "TSD",
                "short_name": "TSD",
                "start_url": base_path,
                "scope": f"{base_path}/",
                "display": "standalone",
                "background_color": "#f7fafc",
                "theme_color": "#111827",
                "icons": [
                    {"src": "?asset=icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "?asset=icon-512.png", "sizes": "512x512", "type": "image/png"},
                    {"src": "?asset=icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable any"},
                ],
            }

            return Response(json.dumps(manifest, ensure_ascii=False),
                            media_type="application/manifest+json")

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

