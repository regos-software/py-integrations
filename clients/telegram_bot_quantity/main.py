import httpx
import json
import hashlib
from enum import Enum
from typing import Optional, Dict, List, Set
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, BaseFilter
from aiogram.types import Update as TelegramUpdate
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from clients.telegram_bot_notification.services import send_messages
from clients.telegram_bot_notification.services.message_formatters import (
    format_cheque_details,
    format_cheque_notification,
    format_session_details,
    format_session_notification,
)
from clients.telegram_polling import telegram_polling_manager
from schemas.api.docs.cash_amount_details import (
    CashAmountDetails,
    CashAmountDetailsGetRequest,
)
from schemas.api.docs.cheque import DocCheque
from schemas.api.docs.cheque_payment import DocChequePayment, DocChequePaymentGetRequest
from schemas.api.reports.retail_report.count import CountsGetRequest
from schemas.api.reports.retail_report.payment import PaymentGetRequest
from .utils import parse_chat_ids, extract_chat_id
from .handlers.get_quantity import handle_get_quantity
from schemas.integration.telegram_integration_base import IntegrationTelegramBase
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingRequest,
    ConnectedIntegrationSettingEditItem,
    ConnectedIntegrationSettingEditRequest,
)
from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from schemas.api.docs.cheque_operation import (
    DocChequeOperation,
    DocChequeOperationGetRequest,
)
from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from config.settings import settings

# Configure logging
logger = setup_logger("telegram_bot_min_quantity")


PENDING_GET_QUANTITY_SEARCH_TTL_SECONDS = 5 * 60
_PENDING_GET_QUANTITY_SEARCH_LOCAL: Set[str] = set()


# Define constants for Telegram settings
class TelegramSettings(Enum):
    BOT_TOKEN = "BOT_TOKEN"
    CHAT_IDS = "CHAT_IDS"
    STOCK_IDS = "STOCK_IDS"


# Configuration for Telegram bot
class TelegramBotMinQuantityConfig:
    BASE_URL = "https://api.telegram.org"
    WEBHOOK_BASE_URL = "https://integration.regos.uz/external"
    DEFAULT_TIMEOUT = 10  # HTTP request timeout in seconds
    SETTINGS_TTL = settings.redis_cache_ttl  # Cache duration for settings
    BATCH_SIZE = 50  # Number of messages to process in one batch
    RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
    RETRY_WAIT_SECONDS = 2  # Seconds to wait between retries
    INTEGRATION_KEY = "regos_telegram_minquantity"
    SLEEP_BETWEEN_MESSAGES = 0.0  # Delay between sending messages (adjust if needed)


class TelegramBotMinQuantityIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        # Initialize HTTP client for API requests
        self.http_client = httpx.AsyncClient(
            timeout=TelegramBotMinQuantityConfig.DEFAULT_TIMEOUT
        )
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False  # Track if handlers are registered

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _polling_key(self) -> str:
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:{self.connected_integration_id or 'unknown'}"

    def _polling_key_unknown(self) -> str:
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:unknown"

    @staticmethod
    def _polling_key_for_token(bot_token: str) -> str:
        token_hash = hashlib.sha256(str(bot_token).encode("utf-8")).hexdigest()[:16]
        return f"{TelegramBotMinQuantityConfig.INTEGRATION_KEY}:token:{token_hash}"

    def _pending_get_quantity_search_key(self, chat_id: str) -> str:
        return (
            f"clients:telegram-min-qty:pending-get-quantity-search:"
            f"{self.connected_integration_id}:{chat_id}"
        )

    async def _set_pending_get_quantity_search(self, chat_id: str) -> None:
        key = self._pending_get_quantity_search_key(chat_id)
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(
                    key, PENDING_GET_QUANTITY_SEARCH_TTL_SECONDS, "1"
                )
                return
            except Exception as error:
                logger.warning("Failed to set pending search in Redis: %s", error)

        _PENDING_GET_QUANTITY_SEARCH_LOCAL.add(key)

    async def _clear_pending_get_quantity_search(self, chat_id: str) -> None:
        key = self._pending_get_quantity_search_key(chat_id)
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.delete(key)
            except Exception as error:
                logger.warning("Failed to clear pending search in Redis: %s", error)
        _PENDING_GET_QUANTITY_SEARCH_LOCAL.discard(key)

    async def _has_pending_get_quantity_search(self, chat_id: str) -> bool:
        key = self._pending_get_quantity_search_key(chat_id)
        if settings.redis_enabled and redis_client:
            try:
                exists = await redis_client.exists(key)
                return bool(exists)
            except Exception as error:
                logger.warning("Failed to check pending search in Redis: %s", error)
        return key in _PENDING_GET_QUANTITY_SEARCH_LOCAL

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up resources
        await self.http_client.aclose()
        if self.bot:
            await self.bot.close()

    def _create_error_response(
        self, error_code: int, description: str
    ) -> IntegrationErrorResponse:
        """Create a standardized error response."""
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=error_code, description=description)
        )

    def _parse_stock_ids(self, settings_map: Dict[str, str]) -> Optional[Set[int]]:
        """
        STOCK_IDS — строка с ID складов через запятую.
        Пустая строка или отсутствие настройки = нет фильтрации (все склады).
        """
        raw = settings_map.get(TelegramSettings.STOCK_IDS.value.lower())
        if raw is None:
            return None

        # Accept either: "1,2,3" or JSON list like "[1, 2, 3]".
        if isinstance(raw, (list, tuple, set)):
            candidates = list(raw)
        else:
            text = str(raw).strip()
            if not text:
                return None

            candidates = None
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        candidates = parsed
                except Exception:
                    candidates = None

            if candidates is None:
                candidates = [
                    p.strip() for p in text.replace(";", ",").split(",") if p.strip()
                ]

        if not candidates:
            return None

        result: Set[int] = set()
        for part in candidates:
            try:
                result.add(int(str(part).strip()))
            except ValueError:
                logger.warning(
                    "Invalid STOCK_IDS value '%s' in settings (ID=%s)",
                    part,
                    self.connected_integration_id,
                )

        return result or None

    async def _fetch_settings(self, cache_key: str) -> Optional[Dict[str, str]]:
        """Retrieve settings from Redis cache or API."""
        # Try to get settings from Redis cache
        if settings.redis_enabled and redis_client:
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Retrieved settings from Redis: {cache_key}")
                    if isinstance(cached_data, (bytes, bytearray)):
                        cached_data = cached_data.decode("utf-8")
                    return json.loads(cached_data)
            except Exception as error:
                logger.warning(f"Redis error: {error}, fetching from API")

        # Fetch settings from Regos API
        logger.debug(f"Fetching settings from API: {cache_key}")
        try:
            async with RegosAPI(
                connected_integration_id=self.connected_integration_id
            ) as api:
                settings_response = (
                    await api.integrations.connected_integration_setting.get(
                        ConnectedIntegrationSettingRequest(
                            integration_key=str(
                                TelegramBotMinQuantityConfig.INTEGRATION_KEY
                            )
                        )
                    )
                ).result
            # Normalize keys to lowercase for case-insensitive access
            settings_map = {item.key.lower(): item.value for item in settings_response}

            # Cache settings in Redis
            if settings.redis_enabled and redis_client:
                try:
                    await redis_client.setex(
                        cache_key,
                        TelegramBotMinQuantityConfig.SETTINGS_TTL,
                        json.dumps(settings_map),
                    )
                except Exception as error:
                    logger.warning(f"Failed to cache settings: {error}")
            return settings_map
        except Exception as error:
            logger.error(
                f"Error fetching settings for ID {self.connected_integration_id}: {error}"
            )
            raise

    async def _add_subscriber(self, chat_id: str) -> None:
        """Add a chat ID to the subscribers list."""
        cache_key = f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id not in subscribers:
                subscribers.append(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = (
                        await api.integrations.connected_integration_setting.edit(
                            [
                                ConnectedIntegrationSettingEditItem(
                                    key=TelegramSettings.CHAT_IDS.value,
                                    value=json.dumps(subscribers),
                                    integration_key=str(
                                        TelegramBotMinQuantityConfig.INTEGRATION_KEY
                                    ),
                                )
                            ]
                        )
                    )
                success = getattr(edit_resp, "result", edit_resp)
                if not success:
                    raise RuntimeError("Failed to update settings")
                if settings.redis_enabled and redis_client:
                    await redis_client.delete(cache_key)
                logger.info(
                    f"Added subscriber {chat_id} for ID {self.connected_integration_id}"
                )
        except Exception as error:
            logger.error(f"Error adding subscriber {chat_id}: {error}")
            raise

    async def _remove_subscriber(self, chat_id: str) -> None:
        """Remove a chat ID from the subscribers list."""
        cache_key = f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id in subscribers:
                subscribers.remove(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = (
                        await api.integrations.connected_integration_setting.edit(
                            [
                                ConnectedIntegrationSettingEditItem(
                                    key=TelegramSettings.CHAT_IDS.value,
                                    value=json.dumps(subscribers),
                                    integration_key=str(
                                        TelegramBotMinQuantityConfig.INTEGRATION_KEY
                                    ),
                                )
                            ]
                        )
                    )
                success = getattr(edit_resp, "result", edit_resp)
                if not success:
                    raise RuntimeError("Failed to update settings")
                if settings.redis_enabled and redis_client:
                    await redis_client.delete(cache_key)
                logger.info(
                    f"Removed subscriber {chat_id} for ID {self.connected_integration_id}"
                )
        except Exception as error:
            logger.error(f"Error removing subscriber {chat_id}: {error}")
            raise

    async def _initialize_bot(self) -> None:
        """Initialize the Telegram bot if not already done."""
        if self.bot:
            return
        settings_map = await self._fetch_settings(
            f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        )
        bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
        if not bot_token:
            raise ValueError(
                f"Bot token not found for ID {self.connected_integration_id}"
            )
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )

    async def _set_bot_commands(self) -> None:
        """Publish bot commands so they show up in Telegram UI."""
        if not self.bot:
            return
        await self.bot.set_my_commands(
            commands=[
                BotCommand(
                    command="start",
                    description="Активировать бота минимальных остатков",
                ),
                BotCommand(
                    command="get_quantity",
                    description="Получить минимальные остатки",
                ),
                BotCommand(
                    command="get_quantity_search",
                    description="Получить минимальные остатки по поиску",
                ),
                BotCommand(
                    command="stop",
                    description="Отписаться от уведомлений",
                ),
            ]
        )

    async def _setup_handlers(self) -> None:
        """Set up command and callback handlers for the bot."""
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        class _PendingGetQuantitySearchFilter(BaseFilter):
            def __init__(self, integration: "TelegramBotMinQuantityIntegration"):
                self._integration = integration

            async def __call__(self, message: types.Message) -> bool:
                try:
                    chat_id = str(message.chat.id)
                except Exception:
                    return False
                if not isinstance(message.text, str):
                    return False
                return await self._integration._has_pending_get_quantity_search(chat_id)

        @self.dispatcher.message(Command("start"))
        async def handle_start_command(message: types.Message):
            """Handle /start command to subscribe to notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._add_subscriber(chat_id)
                await message.answer("Вы активировали бота минимальных остатков!")
                logger.info(
                    f"Client {chat_id} subscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error subscribing. Please try again later.")

        @self.dispatcher.message(Command("get_quantity"))
        async def handle_get_quantity_command(message: types.Message):
            """Handle /get_quantity command to provide quantity information."""
            try:
                settings_map = (
                    await self._fetch_settings(
                        f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
                    )
                    or {}
                )
                stock_ids_set = self._parse_stock_ids(settings_map) or set()
                await handle_get_quantity(
                    integration=self,
                    message=message,
                    stock_ids=sorted(stock_ids_set),
                )
            except Exception as error:
                logger.exception("/get_quantity failed: %s", error)
                await message.answer(
                    "Ошибка при формировании отчета. Попробуйте позже."
                )

        @self.dispatcher.message(Command("get_quantity_search", "get_quanity_search"))
        async def handle_get_quantity_search_command(message: types.Message):
            """Ask user for a search string, then generate report filtered by it."""
            chat_id = str(message.chat.id)
            await self._set_pending_get_quantity_search(chat_id)
            await message.answer(
                "Введите название товара по которому нужно "
                "составить отчет по минимальным остаткам."
                "(например makfa. Отчет будет содержать список товаров в названии которых "
                "содержиться слово makfa) (или /cancel для отмены)."
            )

        @self.dispatcher.message(Command("cancel"))
        async def handle_cancel_command(message: types.Message):
            chat_id = str(message.chat.id)
            if await self._has_pending_get_quantity_search(chat_id):
                await self._clear_pending_get_quantity_search(chat_id)
                await message.answer("Отменено.")

        @self.dispatcher.message(_PendingGetQuantitySearchFilter(self))
        async def handle_get_quantity_search_text(message: types.Message):
            """Receive the search string and run the report."""
            chat_id = str(message.chat.id)
            text = (message.text or "").strip()
            if not text or text.startswith("/"):
                await message.answer(
                    "Пожалуйста, отправьте текст для поиска (или /cancel)."
                )
                return

            await self._clear_pending_get_quantity_search(chat_id)
            try:
                settings_map = (
                    await self._fetch_settings(
                        f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
                    )
                    or {}
                )
                stock_ids_set = self._parse_stock_ids(settings_map) or set()
                await handle_get_quantity(
                    integration=self,
                    message=message,
                    stock_ids=sorted(stock_ids_set),
                    search=text,
                )
            except Exception as error:
                logger.exception("/get_quantity_search failed: %s", error)
                await message.answer(
                    "Ошибка при формировании отчета. Попробуйте позже."
                )

        @self.dispatcher.message(Command("stop"))
        async def handle_stop_command(message: types.Message):
            """Handle /stop command to unsubscribe from notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._remove_subscriber(chat_id)
                await message.answer("Вы отписались от уведомлений.")
                logger.info(
                    f"Client {chat_id} unsubscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error unsubscribing. Please try again later.")

        self.handlers_registered = True

    @retry(
        stop=stop_after_attempt(TelegramBotMinQuantityConfig.RETRY_ATTEMPTS),
        wait=wait_fixed(TelegramBotMinQuantityConfig.RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=lambda retry_state: logger.debug(
            f"Retry attempt: {retry_state.attempt_number}"
        ),
    )
    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Connect to Telegram and set up the webhook or long-polling."""
        logger.info(
            f"Connecting to TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        cache_key = f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")

            polling_key_token = self._polling_key_for_token(bot_token)
            await self._initialize_bot()
            await self._set_bot_commands()
            await self._setup_handlers()

            if self._is_longpolling_mode():
                # Ensure we never run multiple getUpdates streams for the same bot token.
                # Also stop any legacy sessions started under connected_integration_id/unknown keys.
                await telegram_polling_manager.stop(self._polling_key_unknown())
                await telegram_polling_manager.stop(self._polling_key())
                await self.bot.delete_webhook(drop_pending_updates=True)
                await telegram_polling_manager.start(
                    polling_key_token, self.bot, self.dispatcher
                )
                logger.info("Webhook deleted (longpolling mode).")
                return {"status": "connected", "mode": "longpolling"}

            await telegram_polling_manager.stop(self._polling_key_unknown())
            await telegram_polling_manager.stop(self._polling_key())
            await telegram_polling_manager.stop(polling_key_token)

            webhook_url = f"{TelegramBotMinQuantityConfig.WEBHOOK_BASE_URL}/{self.connected_integration_id}/external/"
            await self.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set: {webhook_url}")
            return {
                "status": "connected",
                "mode": "webhook",
                "webhook_url": webhook_url,
            }
        except (httpx.RequestError, httpx.HTTPStatusError) as error:
            logger.error(f"Connection error: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected connection error: {error}")
            return self._create_error_response(1003, f"Webhook setup failed: {error}")

    async def disconnect(self, **kwargs) -> Dict:
        """Disconnect from Telegram and remove the webhook."""
        logger.info(
            f"Disconnecting from TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        # Best-effort stop for all possible polling keys.
        await telegram_polling_manager.stop(self._polling_key_unknown())
        await telegram_polling_manager.stop(self._polling_key())
        try:
            settings_map = await self._fetch_settings(
                f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
            )
            bot_token = (settings_map or {}).get(
                TelegramSettings.BOT_TOKEN.value.lower()
            )
            if bot_token:
                await telegram_polling_manager.stop(
                    self._polling_key_for_token(bot_token)
                )
        except Exception as error:
            logger.debug("Failed to resolve bot token for polling stop: %s", error)
        if not self.bot:
            return {"status": "disconnected", "message": "Bot not initialized"}
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.bot.close()
            self.bot = None
            self.dispatcher = None
            self.handlers_registered = False
            logger.info("Webhook removed")
            return {"status": "disconnected"}
        except Exception as error:
            logger.error(f"Disconnection error: {error}")
            return self._create_error_response(1004, f"Webhook removal failed: {error}")

    async def reconnect(self, **kwargs) -> Dict:
        """Reconnect to Telegram by disconnecting and connecting again."""
        logger.info(
            f"Reconnecting to TelegramBotMinQuantityIntegration (ID: {self.connected_integration_id})"
        )
        await self.disconnect()
        return await self.connect()

    async def update_settings(
        self,
        request: Optional[ConnectedIntegrationSettingEditRequest] = None,
        data: Optional[List[Dict]] = None,
        incoming_settings: Optional[List[Dict]] = None,
        **kwargs,
    ) -> IntegrationSuccessResponse:
        """Update integration settings and refresh the connection."""
        logger.info(f"Updating settings (ID: {self.connected_integration_id})")
        cache_key = f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        if settings.redis_enabled and redis_client:
            await redis_client.delete(cache_key)
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict:
        """Process incoming webhook requests from the API."""
        logger.info(f"Processing webhook for ID {self.connected_integration_id}")

        return {
            "status": "webhook processed",
        }

    async def handle_external(self, envelope: Dict) -> Dict:
        """Handle incoming Telegram updates."""
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._create_error_response(
                400, "Invalid request body: JSON object expected"
            ).dict()

        await self._initialize_bot()
        await self._set_bot_commands()
        await self._setup_handlers()

        chat_id = extract_chat_id(payload)
        if chat_id:
            try:
                await self._add_subscriber(chat_id)
            except Exception as error:
                logger.warning(f"Failed to add subscriber {chat_id}: {error}")

        try:
            telegram_update = TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error(f"Invalid Telegram update: {error}")
            return self._create_error_response(400, "Invalid Telegram update").dict()

        try:
            await self.dispatcher.feed_update(self.bot, telegram_update)
        except Exception as error:
            logger.exception(f"Error processing Telegram update: {error}")
            return self._create_error_response(
                500, "Error processing Telegram update"
            ).dict()

        return {
            "status": "processed",
            "connected_integration_id": self.connected_integration_id,
            "chat_id": chat_id,
        }

    async def send_messages(self, messages: List[Dict]) -> Dict:
        """Send multiple messages to Telegram in batches."""
        logger.info(f"Starting message send for ID {self.connected_integration_id}")
        if not self.connected_integration_id:
            return self._create_error_response(
                1000, "No connected_integration_id specified"
            )

        # Validate messages
        for message in messages:
            if "message" not in message or not message["message"]:
                return self._create_error_response(
                    1009, f"Message missing text: {message}"
                )
            if "recipient" not in message or not message["recipient"]:
                return self._create_error_response(
                    1010, f"Message missing recipient: {message}"
                )

        # Fetch bot token
        cache_key = f"clients:settings:telegram-min-qty:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
        except Exception as error:
            return self._create_error_response(
                1001, f"Settings retrieval error: {error}"
            )

        # Initialize bot and handlers
        await self._initialize_bot()
        await self._setup_handlers()

        results = []
        for i in range(0, len(messages), TelegramBotMinQuantityConfig.BATCH_SIZE):
            batch = messages[i : i + TelegramBotMinQuantityConfig.BATCH_SIZE]
            logger.debug(f"Sending batch {i}-{i + len(batch)}")
            try:
                result = await send_messages(
                    bot=self.bot,
                    messages=batch,
                    sleep_between=TelegramBotMinQuantityConfig.SLEEP_BETWEEN_MESSAGES,
                    logger=logger,
                )
                results.append(result)
            except Exception as error:
                logger.error(f"Error sending batch {i}: {error}")
                results.append({"error": str(error), "batch_index": i})

        logger.info(f"Message sending completed. Processed {len(results)} batches")
        return {"sent_batches": len(results), "details": results}
