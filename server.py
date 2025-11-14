from fastapi import FastAPI
from core.logger import setup_logger
from routes.healthcheck import router as healthcheck
from routes.clients import router as clients
from core.exception_handlers import add_exception_handlers
from fastapi.middleware.gzip import GZipMiddleware



logger = setup_logger("server")


def create_app() -> FastAPI:
    app = FastAPI(title="Python REGOS Integrations Service", version="1.0.0")

    app.add_middleware(GZipMiddleware, minimum_size=500)

    app.include_router(healthcheck)
    app.include_router(clients)
    add_exception_handlers(app)

    logger.info("FastAPI app initialized")

    return app
    

app = create_app()
