# core/exception_handlers.py

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas.integration.base import IntegrationErrorResponse, IntegrationErrorModel
from core.logger import setup_logger

logger = setup_logger("exception-handler")


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Неперехваченное исключение: {exc}")
        return JSONResponse(
            status_code=200,
            content=IntegrationErrorResponse(
                result=IntegrationErrorModel(
                    error=500, description="Внутренняя ошибка сервера"
                )
            ).dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.warning(f"Ошибка валидации: {exc}")
        return JSONResponse(
            status_code=200,
            content=IntegrationErrorResponse(
                result=IntegrationErrorModel(
                    error=422, description="Ошибка валидации входных данных"
                )
            ).dict(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP исключение: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=IntegrationErrorResponse(
                result=IntegrationErrorModel(
                    error=exc.status_code, description=exc.detail
                )
            ).dict(),
        )
