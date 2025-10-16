import asyncio
import json
import re
import gzip
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
from schemas.api.docs.purchase_operation import (
    PurchaseOperationAddRequest,
    PurchaseOperationDeleteItem,
    PurchaseOperationEditItem,
)
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
)


from clients.base import ClientBase
from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client
from email.utils import formataddr
from email.header import Header

from schemas.integration.integration_base import IntegrationBase

logger = setup_logger("bitrix24")


class TsdIntegration(ClientBase):

    INTEGRATION_KEY = "bitrix24"

    SETTINGS_TTL = settings.redis_cache_ttl
    SETTINGS_KEYS = {
        "bitrix_endpoint": "BITRIX_ENDPOINT",
    }

    # -------------------- helpers --------------------

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
            )

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

    # -------------------- Обработка вебхуков от REGOS --------------------
    async def handle_webhook(self, data: dict) -> Any:
        #  обработки webhook
        # Получаем вебхук от REGOS и обрабатываем его в Bitrix24
        return {"status": "webhook received", "data": data}

    async def handle_external(self, data: dict) -> Any:
        # тут мы должны слушать вебхуки от Битрикс24 и выполнять действия
        # над сущностями в REGOS
        return Response(status_code=200)
