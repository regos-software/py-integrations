from fastapi import FastAPI
from core.logger import setup_logger
from routes.healthcheck import router as healthcheck
from routes.clients import router as clients
from core.exception_handlers import add_exception_handlers
from fastapi.middleware.gzip import GZipMiddleware
from clients.asterisk_crm_channel.main import AsteriskCrmChannelIntegration
from clients.gpt_crm_chat_assistant.main import GptCrmChatAssistantIntegration
from clients.telegram_bot_crm_channel.main import TelegramBotCrmChannelIntegration


_RESTORE_INTEGRATIONS = (
    ("Asterisk", AsteriskCrmChannelIntegration),
    ("Telegram", TelegramBotCrmChannelIntegration),
    ("GPT assistant", GptCrmChatAssistantIntegration),
)

_SHUTDOWN_INTEGRATIONS = (
    ("Telegram", TelegramBotCrmChannelIntegration),
    ("Asterisk", AsteriskCrmChannelIntegration),
    ("GPT assistant", GptCrmChatAssistantIntegration),
)


logger = setup_logger("server")

def create_app() -> FastAPI:
    app = FastAPI(title="Python REGOS Integrations Service", version="1.0.0")

    @app.on_event("startup")
    async def _restore_integrations_on_startup() -> None:
        for name, integration_cls in _RESTORE_INTEGRATIONS:
            try:
                summary = await integration_cls.restore_active_connections()
                logger.info("%s auto-restore on startup: %s", name, summary)
            except Exception as error:
                logger.exception("%s auto-restore failed on startup: %s", name, error)

    @app.on_event("shutdown")
    async def _shutdown_integrations_on_shutdown() -> None:
        for name, integration_cls in _SHUTDOWN_INTEGRATIONS:
            try:
                await integration_cls.shutdown_all()
                logger.info("%s shutdown cleanup completed", name)
            except Exception as error:
                logger.exception("%s shutdown cleanup failed: %s", name, error)

    app.add_middleware(GZipMiddleware, minimum_size=500)

    app.include_router(healthcheck)
    app.include_router(clients)
    add_exception_handlers(app)

    logger.info("FastAPI app initialized")

    return app

app = create_app()
