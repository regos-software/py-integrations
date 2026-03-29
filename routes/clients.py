import asyncio
import re
import time
from typing import Optional, Union, Any, Dict, Tuple

import httpx
from fastapi import APIRouter, Header, Request, Path, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import JSONResponse

from core.api.regos_api import RegosAPI
from schemas.integration.base import (
    IntegrationRequest,
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from schemas.api.base import APIBaseResponse
from core.logger import setup_logger

# Импорт доступных интеграций (класс, не модуль)
from clients.getsms.main import GetSmsIntegration
from clients.eskiz_sms.main import EskizSmsIntegration
from clients.email_sender.main import EmailSenderIntegration
from clients.telegram_bot_notification.main import TelegramBotNotificationIntegration
from clients.telegram_bot_quantity.main import TelegramBotMinQuantityIntegration
from clients.telegram_bot_orders.main import TelegramBotOrdersIntegration
from clients.telegram_bot_crm_channel.main import TelegramBotCrmChannelIntegration
from clients.asterisk_crm_channel.main import AsteriskCrmChannelIntegration
from clients.instagram_crm_channel.main import InstagramCrmChannelIntegration
from clients.gpt_crm_chat_assistant.main import GptCrmChatAssistantIntegration
from clients.tsd.main import TsdIntegration

router = APIRouter()
logger = setup_logger("clients_route")

# Маппинг доступных интеграций
INTEGRATION_CLASSES = {
    "getsms": GetSmsIntegration,
    "eskiz_sms": EskizSmsIntegration,
    "email_sender": EmailSenderIntegration,
    "regos_telegram_notifier": TelegramBotNotificationIntegration,
    "regos_telegram_minquantity": TelegramBotMinQuantityIntegration,
    "telegram_bot_orders": TelegramBotOrdersIntegration,
    "telegram_bot_crm_channel": TelegramBotCrmChannelIntegration,
    "asterisk_crm_channel": AsteriskCrmChannelIntegration,
    "instagram_crm_channel": InstagramCrmChannelIntegration,
    "gpt_crm_chat_assistant": GptCrmChatAssistantIntegration,
    "tsd": TsdIntegration,
}

# Служебные заголовки, которые не нужно прокидывать обработчикам
EXCLUDED_SERVICE_HEADERS = {
    "host",
    "connection",
    "content-length",
    "accept-encoding",
}

CONNECTED_INTEGRATION_ACTIVE_CACHE_TTL_SEC = 60
_CONNECTED_INTEGRATION_ACTIVE_CACHE: Dict[str, Tuple[bool, float]] = {}
_CONNECTED_INTEGRATION_ACTIVE_CACHE_LOCK = asyncio.Lock()


def _extract_connected_integration_active_flag(payload: Any) -> Optional[bool]:
    if isinstance(payload, dict):
        for key in ("is_active", "isActive"):
            if key in payload:
                value = payload.get(key)
                if isinstance(value, bool):
                    return value
                text = str(value or "").strip().lower()
                if text in {"1", "true", "yes", "y", "on"}:
                    return True
                if text in {"0", "false", "no", "n", "off"}:
                    return False
        for nested_key in (
            "connected_integration",
            "integration",
            "item",
            "data",
            "result",
        ):
            nested = payload.get(nested_key)
            if nested is None:
                continue
            nested_value = _extract_connected_integration_active_flag(nested)
            if nested_value is not None:
                return nested_value
        return None
    if isinstance(payload, list):
        for row in payload:
            nested_value = _extract_connected_integration_active_flag(row)
            if nested_value is not None:
                return nested_value
        return None
    return None


async def _is_connected_integration_active(
    connected_integration_id: Optional[str],
    *,
    force_refresh: bool = False,
) -> bool:
    ci = str(connected_integration_id or "").strip()
    if not ci:
        return True

    now = time.monotonic()
    if not force_refresh:
        async with _CONNECTED_INTEGRATION_ACTIVE_CACHE_LOCK:
            cached = _CONNECTED_INTEGRATION_ACTIVE_CACHE.get(ci)
        if cached and cached[1] > now:
            return cached[0]

    detected: Optional[bool] = None
    last_error: Optional[Exception] = None
    request_payloads = (
        {},
        {"connected_integration_id": ci, "limit": 1, "offset": 0},
    )
    for payload in request_payloads:
        try:
            async with RegosAPI(connected_integration_id=ci) as api:
                response = await api.call(
                    "ConnectedIntegration/Get",
                    payload,
                    APIBaseResponse[Any],
                )
            if not response.ok:
                continue
            detected = _extract_connected_integration_active_flag(response.result)
            if detected is not None:
                break
        except httpx.HTTPStatusError as error:
            last_error = error
            status_code = (
                int(error.response.status_code)
                if error.response is not None
                else None
            )
            if status_code in {401, 403, 404}:
                detected = False
                break
        except Exception as error:
            last_error = error

    if detected is None:
        if last_error is not None:
            logger.warning(
                "ConnectedIntegration/Get failed for active check, fallback active=true: ci=%s error=%s",
                ci,
                last_error,
            )
        detected = True

    active = bool(detected)
    async with _CONNECTED_INTEGRATION_ACTIVE_CACHE_LOCK:
        _CONNECTED_INTEGRATION_ACTIVE_CACHE[ci] = (
            active,
            now + CONNECTED_INTEGRATION_ACTIVE_CACHE_TTL_SEC,
        )
    return active


def _inactive_integration_error(connected_integration_id: Optional[str]) -> IntegrationErrorResponse:
    ci = str(connected_integration_id or "").strip()
    description = (
        f"ConnectedIntegration '{ci}' is inactive"
        if ci
        else "ConnectedIntegration is inactive"
    )
    return IntegrationErrorResponse(
        result=IntegrationErrorModel(error=403, description=description)
    )


async def _cleanup_integration(
    integration_instance: Any,
    action_name: Optional[str] = None,
    result: Optional[Any] = None,
) -> None:
    if not integration_instance:
        return

    if action_name in {"reconnect", "update_settings"}:
        is_longpolling = False
        is_longpolling_mode = getattr(integration_instance, "_is_longpolling_mode", None)
        if callable(is_longpolling_mode):
            try:
                is_longpolling = bool(is_longpolling_mode())
            except Exception as error:
                logger.warning("Failed to detect longpolling mode: %s", error)
        if is_longpolling:
            return

    if action_name == "connect":
        payload = getattr(result, "result", result)
        if isinstance(payload, dict) and payload.get("mode") == "longpolling":
            return

    aexit = getattr(integration_instance, "__aexit__", None)
    if callable(aexit):
        try:
            await aexit(None, None, None)
            return
        except Exception as error:
            logger.warning("Cleanup via __aexit__ failed: %s", error)

    bot = getattr(integration_instance, "bot", None)
    if bot:
        session = getattr(bot, "session", None)
        if session:
            try:
                await session.close()
            except Exception as error:
                logger.warning("Failed to close bot session: %s", error)
        else:
            try:
                await bot.close()
            except Exception as error:
                logger.warning("Failed to close bot: %s", error)

    http_client = getattr(integration_instance, "http_client", None)
    if http_client:
        try:
            await http_client.aclose()
        except Exception as error:
            logger.warning("Failed to close http client: %s", error)


def camel_to_snake(name: str) -> str:
    """Преобразует CamelCase → snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _resolve_action_method(integration_instance: Any, action: str):
    """
    Resolve action method tolerant to variants:
    Reconnect / ReConnect / re_connect / reconnect.
    """
    primary_name = camel_to_snake(action)
    method = getattr(integration_instance, primary_name, None)
    if callable(method):
        return primary_name, method

    compact_action = re.sub(r"[^a-z0-9]", "", str(action).lower())
    for attr_name in dir(integration_instance):
        candidate = getattr(integration_instance, attr_name, None)
        if not callable(candidate):
            continue
        compact_attr = re.sub(r"[^a-z0-9]", "", str(attr_name).lower())
        if compact_attr == compact_action:
            return attr_name, candidate

    return primary_name, None


def _sanitize_headers(headers) -> Dict[str, str]:
    """Удаляем служебные заголовки, остальные оставляем как есть."""
    return {
        k: v for k, v in headers.items() if k.lower() not in EXCLUDED_SERVICE_HEADERS
    }


async def _read_body_safely(request: Request) -> Any:
    """Считываем тело: пробуем JSON, затем текст, иначе bytes/None."""
    raw = await request.body()
    if not raw:
        return None
    try:
        return await request.json()
    except Exception:
        pass
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return raw  # bytes


# ------------------------------- #
#          REGOS endpoint         #
# ------------------------------- #


@router.post(
    "/clients/{client}/",
    response_model=Union[IntegrationSuccessResponse, IntegrationErrorResponse],
    include_in_schema=False,
)
@router.post(
    "/clients/{client}",
    response_model=Union[IntegrationSuccessResponse, IntegrationErrorResponse],
    tags=["Integration"],
    summary="Обработка запроса от интеграции",
)
async def handle_integration(
    client: str = Path(..., description="Название интеграции"),
    request_body: IntegrationRequest = ...,
    request: Request = ...,
    connected_integration_id: Optional[str] = Header(
        None, alias="connected-integration-id"
    ),
):
    logger.info(f"--- Обработка запроса от клиента: {client} ---")
    logger.info(f"Заголовок 'connected-integration-id': {connected_integration_id}")
    logger.debug(f"Содержимое запроса: {request_body.dict()}")

    integration_instance = None
    result = None
    integration_class = INTEGRATION_CLASSES.get(client)
    if not integration_class:
        logger.warning(f"Интеграция '{client}' не зарегистрирована.")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=404, description=f"Интеграция '{client}' не найдена"
            )
        )

    try:
        integration_instance = integration_class()
        if connected_integration_id:
            integration_instance.connected_integration_id = connected_integration_id
        logger.debug(f"Инстанс интеграции '{client}' успешно создан.")
    except Exception as e:
        logger.exception(f"Ошибка при инициализации интеграции '{client}': {e}")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=500, description="Ошибка инициализации интеграции"
            )
        )

    action_name, action_method = _resolve_action_method(
        integration_instance, request_body.action
    )
    logger.debug(f"Action '{request_body.action}' → метод '{action_name}'")
    if not callable(action_method):
        await _cleanup_integration(integration_instance)
        logger.warning(f"Метод '{action_name}' не найден в интеграции '{client}'")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=400,
                description=f"Метод '{request_body.action}' не реализован в '{client}'",
            )
        )

    action_key = camel_to_snake(request_body.action)
    if connected_integration_id and action_key not in {"disconnect"}:
        is_active = await _is_connected_integration_active(
            connected_integration_id,
            force_refresh=action_key in {"connect", "reconnect", "update_settings"},
        )
        if not is_active:
            await _cleanup_integration(integration_instance)
            return _inactive_integration_error(connected_integration_id)

    try:
        logger.info(
            f"Вызов метода '{action_name}' с данными: {type(request_body.data)}"
        )

        if isinstance(request_body.data, dict):
            result = await action_method(**request_body.data)
        elif isinstance(request_body.data, list):
            result = await action_method(messages=request_body.data)
        else:
            logger.error(f"Тип 'data' не поддерживается: {type(request_body.data)}")
            return IntegrationErrorResponse(
                result=IntegrationErrorModel(
                    error=400, description="Неподдерживаемый тип данных в поле 'data'"
                )
            )

        logger.info(f"Метод '{action_name}' завершён успешно")
        logger.debug(f"Результат: {result}")
        return IntegrationSuccessResponse(result=result)

    except Exception as e:
        logger.exception(
            f"Ошибка при выполнении метода '{action_name}' в '{client}': {e}"
        )
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=500, description=f"Ошибка во время вызова метода '{action_name}'"
            )
        )


    finally:
        await _cleanup_integration(integration_instance, action_name, result)


@router.get("/clients/{client}/", include_in_schema=False)
@router.get(
    "/clients/{client}",
    tags=["Integration"],
    summary="UI (GET) для интеграции: строго вызывает integration.handle_ui",
)
async def handel_ui(
    client: str = Path(..., description="Название интеграции"),
    request: Request = ...,
    connected_integration_id: Optional[str] = Header(
        None, alias="connected-integration-id"
    ),
) -> Any:
    logger.info(f"[ui] GET UI для '{client}' {request.url}")
    logger.info(f"[ui] Connected-Integration-Id: {connected_integration_id}")

    # 1) Класс интеграции
    integration_class = INTEGRATION_CLASSES.get(client)
    if not integration_class:
        return JSONResponse(
            status_code=404,
            content={"error": 404, "description": f"Интеграция '{client}' не найдена"},
        )

    # 2) Инстанс интеграции
    try:
        integration_instance = integration_class()
        if connected_integration_id:
            integration_instance.connected_integration_id = connected_integration_id
    except Exception as e:
        logger.exception(f"[ui] Ошибка инициализации интеграции '{client}': {e}")
        return JSONResponse(
            status_code=500,
            content={"error": 500, "description": "Ошибка инициализации интеграции"},
        )

    if connected_integration_id:
        is_active = await _is_connected_integration_active(connected_integration_id)
        if not is_active:
            await _cleanup_integration(integration_instance)
            inactive = _inactive_integration_error(connected_integration_id)
            payload = inactive.model_dump(mode="json", exclude_none=True)
            return JSONResponse(status_code=403, content=payload)

    # 3) Envelope (GET без тела)
    headers = _sanitize_headers(request.headers)
    if connected_integration_id:
        headers["Connected-Integration-Id"] = str(connected_integration_id)

    envelope: Dict[str, Any] = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": headers,
        "body": None,
        "client": request.client.host if request.client else None,
    }

    # 4) Строго требуем handle_ui у интеграции
    handler = getattr(integration_instance, "handle_ui", None)
    if not callable(handler):
        return JSONResponse(
            status_code=400,
            content={
                "error": 400,
                "description": f"У интеграции '{client}' нет метода handle_ui",
            },
        )

    try:
        result = await asyncio.wait_for(handler(envelope), timeout=180.0)

        # 5) Проксируем ответ «как есть», с поддержкой редиректов и HTML
        if isinstance(result, RedirectResponse):
            return result

        def _looks_like_url(s: str) -> bool:
            return isinstance(s, str) and (
                s.startswith("http://") or s.startswith("https://") or "://" in s
            )

        payload = getattr(result, "result", result)
        if isinstance(payload, str) and _looks_like_url(payload):
            return RedirectResponse(url=payload, status_code=302)
        if isinstance(payload, dict):
            for key in ("redirect_url", "url", "deeplink", "link"):
                val = payload.get(key)
                if isinstance(val, str) and _looks_like_url(val):
                    return RedirectResponse(url=val, status_code=302)

        accept = request.headers.get("accept", "")
        if isinstance(result, (dict, list)):
            return JSONResponse(status_code=200, content=result)
        if isinstance(result, str):
            if (
                result.lstrip().lower().startswith("<!doctype")
                or result.lstrip().lower().startswith("<html")
                or "text/html" in accept
            ):
                return HTMLResponse(result, status_code=200)
            return Response(status_code=200, content=result)
        if isinstance(result, bytes):
            return Response(status_code=200, content=result)
        if isinstance(result, Response):
            return result

        return JSONResponse(status_code=200, content={"result": str(result)})

    except asyncio.TimeoutError:
        logger.error(f"[ui] Таймаут обработки UI для '{client}' (180 сек)")
        return JSONResponse(
            status_code=504,
            content={"error": 504, "description": "Таймаут обработки UI (180 сек)"},
        )
    except Exception as e:
        logger.exception(f"[ui] Ошибка при выполнении handle_ui для '{client}': {e}")
        return JSONResponse(
            status_code=500,
            content={"error": 500, "description": "Ошибка во время вызова handle_ui"},
        )


# ---------------------------------------- #
#        EXTERNAL → handle_external        #
# ---------------------------------------- #


@router.api_route(
    "/clients/{client}/external",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Integration"],
    summary="Обработка запроса от внешней системы",
)
@router.api_route(
    "/clients/{client}/external/",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False,
)
async def handle_external(
    client: str = Path(..., description="Название интеграции"),
    request: Request = ...,
    connected_integration_id: Optional[str] = Header(
        None, alias="connected-integration-id"
    ),
) -> Any:
    logger.info(
        f"[external] Обработка внешнего запроса для '{client}' {request.method} {request.url}"
    )
    logger.info(f"[external] Connected-Integration-Id: {connected_integration_id}")

    integration_instance = None
    result = None

    # 1) Класс интеграции
    integration_class = INTEGRATION_CLASSES.get(client)
    if not integration_class:
        return JSONResponse(
            status_code=404,
            content={"error": 404, "description": f"Интеграция '{client}' не найдена"},
        )

    # 2) Инстанс интеграции
    try:
        integration_instance = integration_class()
        if connected_integration_id:
            integration_instance.connected_integration_id = connected_integration_id
    except Exception as e:
        logger.exception(f"[external] Ошибка инициализации интеграции '{client}': {e}")
        return JSONResponse(
            status_code=500,
            content={"error": 500, "description": "Ошибка инициализации интеграции"},
        )

    if connected_integration_id:
        is_active = await _is_connected_integration_active(connected_integration_id)
        if not is_active:
            await _cleanup_integration(integration_instance)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "reason": "connected_integration_inactive",
                },
            )

    # 3) Envelope: заголовки (без служебных) + Connected-Integration-Id, тело, query, и т.п.
    headers = _sanitize_headers(request.headers)
    if connected_integration_id:
        headers["Connected-Integration-Id"] = str(connected_integration_id)

    body_data = await _read_body_safely(request)

    envelope: Dict[str, Any] = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": headers,
        "body": body_data,
        "client": request.client.host if request.client else None,
    }

    # 4) Вызов handle_external (обязательный для внешних вызовов)
    handler = getattr(integration_instance, "handle_external", None)
    if not callable(handler):
        await _cleanup_integration(integration_instance)
        return JSONResponse(
            status_code=400,
            content={
                "error": 400,
                "description": f"У интеграции '{client}' нет метода handle_external",
            },
        )

    try:
        result = await asyncio.wait_for(handler(envelope), timeout=180.0)

        if isinstance(result, Response):
            return result

        # Проксируем ответ «как есть»:
        if isinstance(result, (dict, list)):
            return JSONResponse(status_code=200, content=result)
        if isinstance(result, (str, bytes)):
            return Response(status_code=200, content=result)

        # fallback – сериализуем строкой
        return JSONResponse(status_code=200, content={"result": str(result)})

    except asyncio.TimeoutError:
        logger.error(
            f"[external] Таймаут обработки внешнего запроса для '{client}' (180 сек)"
        )
        return JSONResponse(
            status_code=504,
            content={
                "error": 504,
                "description": "Таймаут обработки внешнего запроса (180 сек)",
            },
        )
    except Exception as e:
        logger.exception(
            f"[external] Ошибка при выполнении handle_external в '{client}': {e}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": 500,
                "description": "Ошибка во время вызова handle_external",
            },
        )
    finally:
        await _cleanup_integration(integration_instance, "handle_external", result)
