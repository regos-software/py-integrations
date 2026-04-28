from fastapi import FastAPI
from core.logger import setup_logger
from routes.healthcheck import router as healthcheck
from routes.clients import router as clients
from core.exception_handlers import add_exception_handlers
from fastapi.middleware.gzip import GZipMiddleware
from clients.asterisk_crm_channel.main import AsteriskCrmChannelIntegration
from clients.telegram_bot_crm_channel.main import TelegramBotCrmChannelIntegration



logger = setup_logger("server")


def create_app() -> FastAPI:
    app = FastAPI(title="Python REGOS Integrations Service", version="1.0.0")

    @app.on_event("startup")
    async def _restore_integrations_on_startup() -> None:
        try:
            summary = await AsteriskCrmChannelIntegration.restore_active_connections()
            logger.info("Asterisk auto-restore on startup: %s", summary)
        except Exception as error:
            logger.exception("Asterisk auto-restore failed on startup: %s", error)
        try:
            summary = await TelegramBotCrmChannelIntegration.restore_active_connections()
            logger.info("Telegram auto-restore on startup: %s", summary)
        except Exception as error:
            logger.exception("Telegram auto-restore failed on startup: %s", error)

    @app.on_event("shutdown")
    async def _shutdown_integrations_on_shutdown() -> None:
        try:
            await TelegramBotCrmChannelIntegration.shutdown_all()
            logger.info("Telegram integrations shutdown cleanup completed")
        except Exception as error:
            logger.exception("Telegram shutdown cleanup failed: %s", error)
        try:
            await AsteriskCrmChannelIntegration.shutdown_all()
            logger.info("Asterisk integrations shutdown cleanup completed")
        except Exception as error:
            logger.exception("Asterisk shutdown cleanup failed: %s", error)

    app.add_middleware(GZipMiddleware, minimum_size=500)

    app.include_router(healthcheck)
    app.include_router(clients)
    add_exception_handlers(app)

    logger.info("FastAPI app initialized")

    return app
    

app = create_app()
