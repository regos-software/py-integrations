import json
import re
import gzip
from typing import Any, Dict, Optional

from pathlib import Path
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.responses import FileResponse, HTMLResponse, Response


from core.api.regos_api import RegosAPI
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)


from clients.base import ClientBase
from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client


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
        return JSONResponse(
            status_code=status, content={"error": status, "description": description}
        )

    def _gzip_json(self, data: dict, status_code: int = 200) -> Response:
        """Возвращает сжатый gzip JSONResponse."""
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        compressed = gzip.compress(raw)
        return Response(
            content=compressed,
            status_code=status_code,
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )

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
        async with RegosAPI(
            connected_integration_id=self.connected_integration_id
        ) as api:
            settings_response = (
                await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(
                        integration_key=self.INTEGRATION_KEY
                    )
                )
            ).result

        settings_map = {item.key.lower(): item.value for item in settings_response}

        # 3) Cache
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(
                    cache_key, self.SETTINGS_TTL, json.dumps(settings_map)
                )
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

            ci = headers.get("Connected-Integration-Id") or getattr(
                self, "connected_integration_id", None
            )
            if not ci:
                return self._json_error(400, "Missing Connected-Integration-Id")

            body = data.get("body") or {}
            raw_action = body.get("action")
            if not raw_action or not isinstance(raw_action, str):
                return self._json_error(400, "Missing action")

            action_segments = [segment.strip() for segment in raw_action.split(".")]
            if not all(action_segments):
                return self._json_error(400, "Invalid action value")

            params = body.get("params")

            async with RegosAPI(connected_integration_id=ci) as api:
                target = api
                for segment in action_segments:
                    safe_segment = re.sub(r"[^0-9A-Za-z_]+", "", segment)
                    if not safe_segment:
                        return self._json_error(
                            400, f"Invalid action segment: {segment}"
                        )
                    if not hasattr(target, safe_segment):
                        return self._json_error(404, f"Unknown action part: {segment}")
                    target = getattr(target, safe_segment)

                if not callable(target):
                    return self._json_error(400, "Action does not resolve to callable")

                call_args = []
                if params is not None:
                    call_args.append(params)
                result = await target(*call_args)

            json_result = jsonable_encoder(result)
            return self._gzip_json(json_result)

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
                mt = (
                    "application/manifest+json"
                    if ext == ".webmanifest"
                    else "application/json"
                )
            return FileResponse(str(file_path), media_type=mt)

        index_path = self.PWA_DIR / "index.html"

        html = index_path.read_text(encoding="utf-8")
        inject = ""
        if token:
            safe_token = json.dumps(str(token))
            inject = f"<script>window.__CI__={safe_token};</script>"
        pos = html.rfind("</body>")
        html = html[:pos] + inject + html[pos:]

        return HTMLResponse(html, status_code=200)
