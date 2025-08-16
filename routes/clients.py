import asyncio
import re
from typing import Optional, Union, Any, Dict

from fastapi import APIRouter, Header, Request, Path, Response
from starlette.responses import JSONResponse

from schemas.integration.base import (
    IntegrationRequest,
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from core.logger import setup_logger

# Импорт доступных интеграций (класс, не модуль)
from clients.getsms.main import GetSmsIntegration
from clients.eskiz_sms.main import EskizSmsIntegration
from clients.telegram_bot_notification.main import TelegramBotNotificationIntegration

router = APIRouter()
logger = setup_logger("clients_route")

# Маппинг доступных интеграций
INTEGRATION_CLASSES = {
    "getsms": GetSmsIntegration,
    "eskiz_sms": EskizSmsIntegration,
    "regos_telegram_notifier": TelegramBotNotificationIntegration,
}

# Служебные заголовки, которые не нужно прокидывать обработчикам
EXCLUDED_SERVICE_HEADERS = {
    "host",
    "connection",
    "content-length",
    "accept-encoding",
}

def camel_to_snake(name: str) -> str:
    """Преобразует CamelCase → snake_case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def _sanitize_headers(headers) -> Dict[str, str]:
    """Удаляем служебные заголовки, остальные оставляем как есть."""
    return {k: v for k, v in headers.items() if k.lower() not in EXCLUDED_SERVICE_HEADERS}

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
    include_in_schema=False
)
@router.post(
    "/clients/{client}",
    response_model=Union[IntegrationSuccessResponse, IntegrationErrorResponse],
    tags=["Integration"],
    summary="Обработка запроса от интеграции"
)
async def handle_integration(
    client: str = Path(..., description="Название интеграции"),
    request_body: IntegrationRequest = ...,
    request: Request = ...,
    connected_integration_id: Optional[str] = Header(None, alias="connected-integration-id"),
):
    logger.info(f"--- Обработка запроса от клиента: {client} ---")
    logger.info(f"Заголовок 'connected-integration-id': {connected_integration_id}")
    logger.debug(f"Содержимое запроса: {request_body.dict()}")

    integration_class = INTEGRATION_CLASSES.get(client)
    if not integration_class:
        logger.warning(f"Интеграция '{client}' не зарегистрирована.")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=404,
                description=f"Интеграция '{client}' не найдена"
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
                error=500,
                description="Ошибка инициализации интеграции"
            )
        )

    action_name = camel_to_snake(request_body.action)
    logger.debug(f"Action '{request_body.action}' → метод '{action_name}'")

    action_method = getattr(integration_instance, action_name, None)
    if not callable(action_method):
        logger.warning(f"Метод '{action_name}' не найден в интеграции '{client}'")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=400,
                description=f"Метод '{request_body.action}' не реализован в '{client}'"
            )
        )

    try:
        logger.info(f"Вызов метода '{action_name}' с данными: {type(request_body.data)}")

        if isinstance(request_body.data, dict):
            result = await action_method(**request_body.data)
        elif isinstance(request_body.data, list):
            result = await action_method(messages=request_body.data)
        else:
            logger.error(f"Тип 'data' не поддерживается: {type(request_body.data)}")
            return IntegrationErrorResponse(
                result=IntegrationErrorModel(
                    error=400,
                    description="Неподдерживаемый тип данных в поле 'data'"
                )
            )

        logger.info(f"Метод '{action_name}' завершён успешно")
        logger.debug(f"Результат: {result}")
        return IntegrationSuccessResponse(result=result)

    except Exception as e:
        logger.exception(f"Ошибка при выполнении метода '{action_name}' в '{client}': {e}")
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(
                error=500,
                description=f"Ошибка во время вызова метода '{action_name}'"
            )
        )

# ---------------------------------------- #
#        EXTERNAL → handle_external        #
# ---------------------------------------- #

@router.api_route(
    "/clients/{client}/external",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Integration"],
    summary="Обработка запроса от внешней системы"
)
@router.api_route(
    "/clients/{client}/external/",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False
)
async def handle_external(
    client: str = Path(..., description="Название интеграции"),
    request: Request = ...,
    connected_integration_id: Optional[str] = Header(None, alias="connected-integration-id"),
) -> Any:
    logger.info(f"[external] Обработка внешнего запроса для '{client}' {request.method} {request.url}")
    logger.info(f"[external] Connected-Integration-Id: {connected_integration_id}")

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
        return JSONResponse(
            status_code=400,
            content={"error": 400, "description": f"У интеграции '{client}' нет метода handle_external"},
        )

    try:
        result = await asyncio.wait_for(handler(envelope), timeout=180.0)

        # Проксируем ответ «как есть»:
        if isinstance(result, (dict, list)):
            return JSONResponse(status_code=200, content=result)
        if isinstance(result, (str, bytes)):
            return Response(status_code=200, content=result)
        if isinstance(result, Response):
            return result
        # fallback – сериализуем строкой
        return JSONResponse(status_code=200, content={"result": str(result)})

    except asyncio.TimeoutError:
        logger.error(f"[external] Таймаут обработки внешнего запроса для '{client}' (180 сек)")
        return JSONResponse(
            status_code=504,
            content={"error": 504, "description": "Таймаут обработки внешнего запроса (180 сек)"},
        )
    except Exception as e:
        logger.exception(f"[external] Ошибка при выполнении handle_external в '{client}': {e}")
        return JSONResponse(
            status_code=500,
            content={"error": 500, "description": "Ошибка во время вызова handle_external"},
        )
