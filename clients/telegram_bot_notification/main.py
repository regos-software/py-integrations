import httpx
import json
from enum import Enum
from typing import Optional, Dict, List, Set
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Update as TelegramUpdate
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from clients.telegram_bot_notification.services import send_messages
from clients.telegram_bot_notification.services.message_formatters import (
    format_cheque_details,
    format_cheque_notification,
    format_session_details,
    format_session_notification,
)
from clients.telegram_polling import telegram_polling_manager
from schemas.api.docs.cash_amount_details import CashAmountDetails, CashAmountDetailsGetRequest
from schemas.api.docs.cheque import DocCheque
from schemas.api.docs.cheque_payment import DocChequePayment, DocChequePaymentGetRequest
from schemas.api.reports.retail_report.count import CountsGetRequest
from schemas.api.reports.retail_report.payment import PaymentGetRequest
from .utils import parse_chat_ids, extract_chat_id
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
from schemas.api.docs.cheque_operation import DocChequeOperation, DocChequeOperationGetRequest
from clients.base import ClientBase
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from config.settings import settings

# Configure logging
logger = setup_logger("telegram_bot_notification")


# Define constants for Telegram settings
class TelegramSettings(Enum):
    BOT_TOKEN = "BOT_TOKEN"
    CHAT_IDS = "CHAT_IDS"
    CHEQUE_NOTIFICATION = "CHEQUE_NOTIFICATION"
    STOCK_IDS = "STOCK_IDS"


# Configuration for Telegram bot
class TelegramBotConfig:
    BASE_URL = "https://api.telegram.org"
    WEBHOOK_BASE_URL = "https://integration.regos.uz/external"
    DEFAULT_TIMEOUT = 10  # HTTP request timeout in seconds
    SETTINGS_TTL = settings.redis_cache_ttl  # Cache duration for settings
    BATCH_SIZE = 50  # Number of messages to process in one batch
    RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
    RETRY_WAIT_SECONDS = 2  # Seconds to wait between retries
    INTEGRATION_KEY = "regos_telegram_notifier"
    SLEEP_BETWEEN_MESSAGES = 0.0  # Delay between sending messages (adjust if needed)


class TelegramBotNotificationIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        # Initialize HTTP client for API requests
        self.http_client = httpx.AsyncClient(timeout=TelegramBotConfig.DEFAULT_TIMEOUT)
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False  # Track if handlers are registered

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up resources
        try:
            await self.http_client.aclose()
        except Exception as error:
            logger.warning("Failed to close http client: %s", error)
        if self.bot and getattr(self.bot, "session", None):
            try:
                await self.bot.session.close()
            except Exception as error:
                logger.warning("Failed to close bot session: %s", error)

    def _create_error_response(
        self, error_code: int, description: str
    ) -> IntegrationErrorResponse:
        """Create a standardized error response."""
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=error_code, description=description)
        )

    def _cheque_notifications_enabled(self, settings_map: Dict[str, str]) -> bool:
        """
        Возвращает True, если уведомления по чекам включены.
        Отсутствие настройки трактуем как включенные уведомления.
        Отключаем только при 'false' или '0' (регистр/пробелы игнорируются).
        """
        raw = settings_map.get(TelegramSettings.CHEQUE_NOTIFICATION.value.lower())
        if raw is None:
            return True  # настройки нет — включено по умолчанию

        s = str(raw).strip().lower()
        return s not in {"false", "0"}
   
    def _parse_stock_ids(self, settings_map: Dict[str, str]) -> Optional[Set[int]]:
        """
        STOCK_IDS — строка с ID складов через запятую.
        Пустая строка или отсутствие настройки = нет фильтрации (все склады).
        """
        raw = settings_map.get(TelegramSettings.STOCK_IDS.value.lower())
        if raw is None:
            return None

        text = str(raw).strip()
        if not text:
            return None

        result: Set[int] = set()
        for part in text.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                result.add(int(part))
            except ValueError:
                logger.warning(
                    "Invalid STOCK_IDS value '%s' in settings (ID=%s)",
                    part,
                    self.connected_integration_id,
                )

        return result or None

    @staticmethod
    def _is_bot_blocked_error(error: object) -> bool:
        text = str(error).lower()
        return "bot was blocked by the user" in text

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _polling_key(self) -> str:
        return f"{TelegramBotConfig.INTEGRATION_KEY}:{self.connected_integration_id or 'unknown'}"
    
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
                            integration_key=str(TelegramBotConfig.INTEGRATION_KEY)
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
                        TelegramBotConfig.SETTINGS_TTL,
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
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id not in subscribers:
                subscribers.append(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = await api.integrations.connected_integration_setting.edit(
                        [
                            ConnectedIntegrationSettingEditItem(
                                key=TelegramSettings.CHAT_IDS.value,
                                value=json.dumps(subscribers),
                                integration_key=str(TelegramBotConfig.INTEGRATION_KEY),
                            )
                        ]
                    )
                success = getattr(edit_resp, "ok", None)
                if success is None:
                    success = bool(getattr(edit_resp, "result", edit_resp))
                if not success:
                    logger.error(
                        "Settings update failed (add): ok=%s result=%s",
                        getattr(edit_resp, "ok", None),
                        getattr(edit_resp, "result", None),
                    )
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
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key) or {}
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            if chat_id in subscribers:
                subscribers.remove(chat_id)
                async with RegosAPI(
                    connected_integration_id=self.connected_integration_id
                ) as api:
                    edit_resp = await api.integrations.connected_integration_setting.edit(
                        [
                            ConnectedIntegrationSettingEditItem(
                                key=TelegramSettings.CHAT_IDS.value,
                                value=json.dumps(subscribers),
                                integration_key=str(TelegramBotConfig.INTEGRATION_KEY),
                            )
                        ]
                    )
                success = getattr(edit_resp, "ok", None)
                if success is None:
                    success = bool(getattr(edit_resp, "result", edit_resp))
                if not success:
                    logger.error(
                        "Settings update failed (remove): ok=%s result=%s",
                        getattr(edit_resp, "ok", None),
                        getattr(edit_resp, "result", None),
                    )
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
            f"clients:settings:telegram:{self.connected_integration_id}"
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

    async def _setup_handlers(self) -> None:
        """Set up command and callback handlers for the bot."""
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        @self.dispatcher.message(Command("start"))
        async def handle_start_command(message: types.Message):
            """Handle /start command to subscribe to notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._add_subscriber(chat_id)
                await message.answer(
                    "You are now subscribed to cheque and session notifications!"
                )
                logger.info(
                    f"Client {chat_id} subscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error subscribing. Please try again later.")

        @self.dispatcher.message(Command("stop"))
        async def handle_stop_command(message: types.Message):
            """Handle /stop command to unsubscribe from notifications."""
            chat_id = str(message.chat.id)
            try:
                await self._remove_subscriber(chat_id)
                await message.answer("You are now unsubscribed from notifications.")
                logger.info(
                    f"Client {chat_id} unsubscribed for ID {self.connected_integration_id}"
                )
            except Exception:
                await message.answer("Error unsubscribing. Please try again later.")

        @self.dispatcher.callback_query(lambda c: c.data.startswith("cdetails_"))
        async def handle_cheque_details(callback_query: types.CallbackQuery):
            try:
                _, uuid, _ = callback_query.data.split("_", 2)
            except Exception:
                await callback_query.answer("Некорректные данные кнопки", show_alert=False)
                return

            try:
                async with RegosAPI(self.connected_integration_id) as api:
                    # Приводим чек к DocCheque
                    raw_cheques = (await api.docs.cheque.get_by_uuids([uuid])).result or []
                    if not raw_cheques:
                        await callback_query.answer("Чек не найден", show_alert=True)
                        return
                    cheque = (
                        raw_cheques[0]
                        if isinstance(raw_cheques[0], DocCheque)
                        else DocCheque.model_validate(raw_cheques[0])
                    )

                    # Приводим операции к DocChequeOperation
                    operations_raw = (
                        await api.docs.cheque_operation.get(
                            DocChequeOperationGetRequest(doc_sale_uuid=uuid)
                        )
                    ).result or []
                    operations = [
                        op if isinstance(op, DocChequeOperation)
                        else DocChequeOperation.model_validate(op)
                        for op in operations_raw
                    ]

                    # Приводим оплаты к DocChequePayment
                    payments_raw = (
                        await api.docs.cheque_payment.get(
                            DocChequePaymentGetRequest(doc_sale_uuid=uuid)
                        )
                    ).result or []
                    payments = [
                        p if isinstance(p, DocChequePayment)
                        else DocChequePayment.model_validate(p)
                        for p in payments_raw
                    ]
            except Exception as error:
                logger.error(f"Error fetching cheque details {uuid}: {error}")
                await callback_query.answer("Ошибка получения данных", show_alert=True)
                return

            message_text = format_cheque_details(
                cheque=cheque, operations=operations, payments=payments
            )

            try:
                await callback_query.message.edit_text(
                    text=message_text, parse_mode=ParseMode.MARKDOWN
                )
                await callback_query.answer()  # закрываем «часики»
            except Exception as error:
                logger.error(f"Error editing cheque details {uuid}: {error}")
                await callback_query.answer(
                    "Не удалось обновить сообщение", show_alert=True
                )

        @self.dispatcher.callback_query(lambda c: c.data.startswith("sdetails_"))
        async def handle_session_details(callback_query: types.CallbackQuery):
            try:
                _, uuid, _ = callback_query.data.split("_", 2)
            except Exception:
                await callback_query.answer("Некорректные данные кнопки", show_alert=False)
                return

            try:
                async with RegosAPI(self.connected_integration_id) as api:
                    sessions_resp = await api.docs.cash_session.get_by_uuids([uuid])
                    sessions = sessions_resp.result or []
                    if not sessions:
                        await callback_query.answer("Смена не найдена", show_alert=True)
                        return

                    session = sessions[0]

            
                    operations_raw = (
                        await api.docs.cash_operation.get_amount_details(
                            CashAmountDetailsGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_id=session.operating_cash_id,
                            )
                        )
                    ).result

                    
                    if isinstance(operations_raw, list):
                        operations = [
                            op if isinstance(op, CashAmountDetails)
                            else CashAmountDetails.model_validate(op)
                            for op in operations_raw
                        ]
                    
                    elif isinstance(operations_raw, dict):
                        operations = CashAmountDetails.model_validate(operations_raw)
                    else:
                        operations = operations_raw  

                    counts = (
                        await api.reports.retail_report.get_counts(
                            CountsGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_ids=[session.operating_cash_id],
                            )
                        )
                    ).result or []

                    payments = (
                        await api.reports.retail_report.get_payments(
                            PaymentGetRequest(
                                start_date=session.start_date,
                                end_date=session.close_date,
                                operating_cash_ids=[session.operating_cash_id],
                            )
                        )
                    ).result or []

            except Exception as error:
                logger.error(f"Error fetching session details {uuid}: {error}")
                await callback_query.answer("Ошибка получения данных", show_alert=True)
                return

            
            message_text = format_session_details(
                session=session, operations=operations, counts=counts, payments=payments
            )

            try:
                await callback_query.message.edit_text(
                    text=message_text, parse_mode=ParseMode.MARKDOWN
                )
                await callback_query.answer()
            except Exception as error:
                logger.error(f"Error editing session details {uuid}: {error}")
                await callback_query.answer("Не удалось обновить сообщение", show_alert=True)


    @retry(
        stop=stop_after_attempt(TelegramBotConfig.RETRY_ATTEMPTS),
        wait=wait_fixed(TelegramBotConfig.RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=lambda retry_state: logger.debug(
            f"Retry attempt: {retry_state.attempt_number}"
        ),
    )
    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Connect to Telegram and set up the webhook."""
        logger.info(
            f"Connecting to TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
        )
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
            await self._initialize_bot()
            await self._setup_handlers()

            if self._is_longpolling_mode():
                await self.bot.delete_webhook(drop_pending_updates=True)
                await telegram_polling_manager.start(
                    self._polling_key(), self.bot, self.dispatcher
                )
                logger.info("Webhook deleted (longpolling mode).")
                return {"status": "connected", "mode": "longpolling"}

            await telegram_polling_manager.stop(self._polling_key())
            webhook_url = (
                f"{TelegramBotConfig.WEBHOOK_BASE_URL}/{self.connected_integration_id}/external/"
            )
            await self.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set: {webhook_url}")
            return {"status": "connected", "mode": "webhook", "webhook_url": webhook_url}
        except (httpx.RequestError, httpx.HTTPStatusError) as error:
            logger.error(f"Connection error: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected connection error: {error}")
            return self._create_error_response(1003, f"Webhook setup failed: {error}")

    async def disconnect(self, **kwargs) -> Dict:
        """Disconnect from Telegram and remove the webhook."""
        logger.info(
            f"Disconnecting from TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
        )
        await telegram_polling_manager.stop(self._polling_key())
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
            f"Reconnecting to TelegramBotNotificationIntegration (ID: {self.connected_integration_id})"
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
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
        if settings.redis_enabled and redis_client:
            await redis_client.delete(cache_key)
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    async def handle_webhook(
        self, action: Optional[str] = None, data: Optional[Dict] = None, **kwargs
    ) -> Dict:
        """Process incoming webhook requests from the API."""
        logger.info(f"Processing webhook for ID {self.connected_integration_id}")

        # Унификация входа: либо {action, data}, либо отдельные аргументы
        if isinstance(data, dict) and "action" in data:
            webhook_action = data.get("action")
            webhook_data = data.get("data", {})
        else:
            webhook_action = action
            webhook_data = data or {}

        if not webhook_action:
            return self._create_error_response(1006, "No action specified in webhook")

        supported_actions = {
            "DocSessionOpened",
            "DocSessionClosed",
            "DocChequeClosed",
            "DocChequeCanceled",
        }
        if webhook_action not in supported_actions:
            return self._create_error_response(
                1006, f"Unsupported action: {webhook_action}"
            )

        uuid = webhook_data.get("uuid") or webhook_data.get("session_uuid")
        if not uuid:
            return self._create_error_response(
                1007, "Webhook missing uuid/session_uuid"
            )

        # Получаем настройки интеграции
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key)
            bot_token = settings_map.get(TelegramSettings.BOT_TOKEN.value.lower())
            raw_chat_ids = settings_map.get(TelegramSettings.CHAT_IDS.value.lower())
            subscribers = parse_chat_ids(raw_chat_ids)

            # --- Фильтр по складам (STOCK_IDS) ---
            allowed_stock_ids = self._parse_stock_ids(settings_map)
            # None -> фильтра нет, шлём по всем складам

            if not bot_token:
                return self._create_error_response(1002, "No bot token in settings")
            if not subscribers:
                logger.warning(f"No subscribers for {webhook_action} (uuid={uuid})")
                return {"status": "ok", "message": "No subscribers"}

            # Отключение чеков на уровне настройки CHEQUE_NOTIFICATION
            if webhook_action in {"DocChequeClosed", "DocChequeCanceled"}:
                if not self._cheque_notifications_enabled(settings_map):
                    logger.info(
                        f"Cheque notifications disabled by settings "
                        f"(ID={self.connected_integration_id}, uuid={uuid})"
                    )
                    return {
                        "status": "ok",
                        "message": "Cheque notifications disabled by CHEQUE_NOTIFICATION setting",
                        "action": webhook_action,
                        "uuid": uuid,
                    }

        except Exception as error:
            logger.error(f"Error fetching settings: {error}")
            return self._create_error_response(
                1001, f"Settings retrieval error: {error}"
            )

        await self._initialize_bot()

        message_text = ""
        keyboard: Optional[InlineKeyboardMarkup] = None

        try:
            # ---------------- ЧЕК ----------------
            if webhook_action in {"DocChequeClosed", "DocChequeCanceled"}:
                async with RegosAPI(self.connected_integration_id) as api:
                    from schemas.api.references.operating_cash import (
                        OperatingCashGetRequest,
                    )

                    cheques_resp = await api.docs.cheque.get_by_uuids([uuid])
                    raw_cheques = getattr(cheques_resp, "result", cheques_resp) or []

                    if not raw_cheques:
                        logger.warning(f"Cheque with UUID {uuid} not found")
                        message_text = (
                            f"*Event:* `{webhook_action}`\n"
                            f"UUID: `{uuid}`\n"
                            f"Details: Cheque not found"
                        )
                    else:
                        # Приводим к DocCheque
                        cheque = (
                            raw_cheques[0]
                            if isinstance(raw_cheques[0], DocCheque)
                            else DocCheque.model_validate(raw_cheques[0])
                        )

                        # --- Фильтрация по STOCK_IDS через смену и кассу ---
                        stock_id_for_filter: Optional[int] = None
                        if allowed_stock_ids:
                            session_uuid = cheque.session  # UUID кассовой сессии

                            try:
                                # 1. Получаем смену
                                sessions_resp = await api.docs.cash_session.get_by_uuids(
                                    [session_uuid]
                                )
                                sessions = getattr(
                                    sessions_resp, "result", sessions_resp
                                ) or []

                                if sessions:
                                    session = sessions[0]

                                    # 2. Получаем кассу (OperatingCash)
                                    oc_resp = await api.references.operating_cash.get(
                                        OperatingCashGetRequest(
                                            ids=[session.operating_cash_id]
                                        )
                                    )
                                    oc_list = getattr(
                                        oc_resp, "result", oc_resp
                                    ) or []
                                    if oc_list:
                                        operating_cash = oc_list[0]
                                        stock = getattr(operating_cash, "stock", None)
                                        stock_id_for_filter = getattr(stock, "id", None)

                            except Exception as error:
                                logger.error(
                                    "Error fetching session/operating cash for cheque %s: %s",
                                    uuid,
                                    error,
                                )

                            # Если склад определён и не входит в список разрешённых — пропускаем вебхук
                            if (
                                stock_id_for_filter is not None
                                and stock_id_for_filter not in allowed_stock_ids
                            ):
                                logger.info(
                                    "Skipping cheque webhook %s due to STOCK_IDS filter "
                                    "(stock_id=%s, allowed=%s)",
                                    uuid,
                                    stock_id_for_filter,
                                    allowed_stock_ids,
                                )
                                return {
                                    "status": "ok",
                                    "message": "Cheque filtered by STOCK_IDS",
                                    "action": webhook_action,
                                    "uuid": uuid,
                                    "stock_id": stock_id_for_filter,
                                }

                        # Если фильтр не сработал / не задан — формируем уведомление как раньше
                        message_text = format_cheque_notification(
                            cheque=cheque, action=webhook_action
                        )
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="Детали чека",
                                        callback_data=f"cdetails_{uuid}_{webhook_action}",
                                    )
                                ]
                            ]
                        )

            # ---------------- СМЕНА ----------------
            elif webhook_action in {"DocSessionOpened", "DocSessionClosed"}:
                async with RegosAPI(self.connected_integration_id) as api:
                    from schemas.api.references.operating_cash import (
                        OperatingCashGetRequest,
                    )

                    sessions_resp = await api.docs.cash_session.get_by_uuids([uuid])
                    sessions = getattr(sessions_resp, "result", sessions_resp) or []

                    if not sessions:
                        logger.warning(f"Session with UUID {uuid} not found")
                        message_text = (
                            f"*Event:* `{webhook_action}`\n"
                            f"UUID: `{uuid}`\n"
                            f"Details: Session not found"
                        )
                    else:
                        session = sessions[0]

                        # --- Фильтр по STOCK_IDS через кассу ---
                        stock_id_for_filter: Optional[int] = None
                        if allowed_stock_ids:
                            try:
                                oc_resp = await api.references.operating_cash.get(
                                    OperatingCashGetRequest(
                                        ids=[session.operating_cash_id]
                                    )
                                )
                                oc_list = getattr(oc_resp, "result", oc_resp) or []
                                if oc_list:
                                    operating_cash = oc_list[0]
                                    stock = getattr(operating_cash, "stock", None)
                                    stock_id_for_filter = getattr(stock, "id", None)
                            except Exception as error:
                                logger.error(
                                    "Error fetching operating cash for session %s: %s",
                                    uuid,
                                    error,
                                )

                            if (
                                stock_id_for_filter is not None
                                and stock_id_for_filter not in allowed_stock_ids
                            ):
                                logger.info(
                                    "Skipping session webhook %s due to STOCK_IDS filter "
                                    "(stock_id=%s, allowed=%s)",
                                    uuid,
                                    stock_id_for_filter,
                                    allowed_stock_ids,
                                )
                                return {
                                    "status": "ok",
                                    "message": "Session filtered by STOCK_IDS",
                                    "action": webhook_action,
                                    "uuid": uuid,
                                    "stock_id": stock_id_for_filter,
                                }

                        # Формируем уведомление как раньше
                        message_text = format_session_notification(
                            session=session, action=webhook_action
                        )
                        if getattr(session, "closed", False):
                            keyboard = InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(
                                            text="Детали смены",
                                            callback_data=f"sdetails_{uuid}_{webhook_action}",
                                        )
                                    ]
                                ]
                            )

            else:
                # На всякий случай fallback (хотя все поддерживаемые action уже перечислены)
                message_text = "Webhook action not supported for notifications"

        except Exception as error:
            logger.error(f"Error formatting message: {error}")
            message_text = (
                f"*Event:* `{webhook_action}`\n"
                f"UUID: `{uuid}`\n"
                f"Details unavailable: `{str(error)}`"
            )

        # Рассылка сообщений подписчикам
        results: List[Dict] = []
        for chat_id in subscribers:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    reply_markup=keyboard if keyboard else None,
                )
                results.append({"status": "sent", "chat_id": chat_id})
            except Exception as error:
                logger.error(f"Error sending message to chat {chat_id}: {error}")
                if self._is_bot_blocked_error(error):
                    try:
                        await self._remove_subscriber(str(chat_id))
                        logger.info(
                            "Removed subscriber %s because bot was blocked", chat_id
                        )
                    except Exception as remove_error:
                        logger.warning(
                            "Failed to remove subscriber %s: %s", chat_id, remove_error
                        )
                results.append(
                    {"status": "error", "chat_id": chat_id, "error": str(error)}
                )

        return {
            "status": "webhook processed",
            "action": webhook_action,
            "uuid": uuid,
            "sent_to": len([r for r in results if r["status"] == "sent"]),
            "details": results,
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
        cache_key = f"clients:settings:telegram:{self.connected_integration_id}"
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
        for i in range(0, len(messages), TelegramBotConfig.BATCH_SIZE):
            batch = messages[i : i + TelegramBotConfig.BATCH_SIZE]
            logger.debug(f"Sending batch {i}-{i + len(batch)}")
            try:
                result = await send_messages(
                    bot=self.bot,
                    messages=batch,
                    sleep_between=TelegramBotConfig.SLEEP_BETWEEN_MESSAGES,
                    logger=logger,
                )
                results.append(result)
            except Exception as error:
                logger.error(f"Error sending batch {i}: {error}")
                results.append({"error": str(error), "batch_index": i})

        for batch_result in results:
            details = batch_result.get("details") if isinstance(batch_result, dict) else None
            if not details:
                continue
            for detail in details:
                if not isinstance(detail, dict) or detail.get("status") != "error":
                    continue
                error_text = detail.get("error", "")
                if not self._is_bot_blocked_error(error_text):
                    continue
                chat_id = detail.get("chat_id")
                if not chat_id:
                    continue
                try:
                    await self._remove_subscriber(str(chat_id))
                    logger.info(
                        "Removed subscriber %s because bot was blocked", chat_id
                    )
                except Exception as remove_error:
                    logger.warning(
                        "Failed to remove subscriber %s: %s", chat_id, remove_error
                    )

        logger.info(f"Message sending completed. Processed {len(results)} batches")
        return {"sent_batches": len(results), "details": results}

    async def handle_external(self, envelope: Dict) -> Dict:
        """Handle incoming Telegram updates."""
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._create_error_response(
                400, "Invalid request body: JSON object expected"
            ).dict()

        await self._initialize_bot()
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
