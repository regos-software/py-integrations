from typing import Any

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config.settings import settings


DEFAULT_TELEGRAM_API_BASE_URL = "https://api.telegram.org"


def telegram_api_base_url() -> str:
    base_url = str(
        settings.telegram_api_base_url or DEFAULT_TELEGRAM_API_BASE_URL
    ).strip()
    return (base_url or DEFAULT_TELEGRAM_API_BASE_URL).rstrip("/")


def telegram_api_server() -> TelegramAPIServer:
    return TelegramAPIServer.from_base(telegram_api_base_url())


def create_telegram_bot(token: str, **kwargs: Any) -> Bot:
    return Bot(
        token=token,
        session=AiohttpSession(api=telegram_api_server()),
        **kwargs,
    )


def telegram_file_url(token: str, file_path: str) -> str:
    return telegram_api_server().file_url(token=token, path=file_path)
