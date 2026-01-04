import hashlib
import importlib
import json
from datetime import datetime, time as dt_time
from decimal import Decimal
from io import BytesIO
from enum import Enum
from typing import Any, Dict, List, Optional

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Update as TelegramUpdate

from clients.base import ClientBase
from config.settings import settings as app_settings
from core.api.regos_api import RegosAPI
from core.logger import setup_logger
from core.redis import redis_client
from schemas.api.integrations.connected_integration_setting import (
    ConnectedIntegrationSettingEditRequest,
    ConnectedIntegrationSettingRequest,
)
from schemas.integration.base import (
    IntegrationErrorModel,
    IntegrationErrorResponse,
    IntegrationSuccessResponse,
)
from schemas.integration.telegram_integration_base import IntegrationTelegramBase
from schemas.api.common.filters import Filter, FilterOperator
from schemas.api.docs.order_delivery import (
    DocOrderDeliveryAddFullRequest,
    DocOrderDeliveryAddRequest,
    DocOrderDeliveryOperation,
    Location,
)
from schemas.api.references.item import ItemExt, ItemGetExtImageSize, ItemGetExtRequest
from schemas.api.references.retail_card import RetailCardGetRequest
from schemas.api.references.fields import FieldValueAdd, FieldValueEdit
from schemas.api.references.retail_customer import (
    RetailCustomerAddRequest,
    RetailCustomerEditRequest,
    RetailCustomerGetRequest,
)

try:
    qrcode = importlib.import_module("qrcode")
except Exception:  # pragma: no cover - optional dependency
    qrcode = None

logger = setup_logger("telegram_bot_orders")


class TelegramOrdersSettings(Enum):
    BOT_TOKEN = "BOT_TOKEN"
    PRICE_TYPE_ID = "PRICE_TYPE_ID"
    STOCK_ID = "STOCK_ID"
    SHOW_ZERO_QUANTITY = "SHOW_ZERO_QUANTITY"
    SHOW_WITHOUT_IMAGES = "SHOW_WITHOUT_IMAGES"
    ORDER_SOURCE_ID = "ORDER_SOURCE_ID"
    MIN_ORDER_AMOUNT = "MIN_ORDER_AMOUNT"
    WORK_TIME_ENABLED = "WORK_TIME_ENABLED"
    WORK_TIME_START = "WORK_TIME_START"
    WORK_TIME_END = "WORK_TIME_END"
    CUSTOMER_GROUP_ID = "CUSTOMER_GROUP_ID"


class TelegramBotOrdersConfig:
    SETTINGS_TTL = app_settings.redis_cache_ttl
    CART_TTL = app_settings.redis_cache_ttl
    CATALOG_TTL = 60
    CATALOG_PAGE_SIZE = 5
    ORDER_STATE_TTL = app_settings.redis_cache_ttl
    INTEGRATION_KEY = "telegram_bot_orders"
    WEBHOOK_BASE_URL = f"{app_settings.integration_url.rstrip('/')}/external"


def _extract_chat_id(payload: dict) -> Optional[str]:
    for key in ("message", "edited_message", "callback_query"):
        block = payload.get(key)
        if isinstance(block, dict):
            chat = block.get("chat")
            if isinstance(chat, dict) and "id" in chat:
                return str(chat["id"])
            if key == "callback_query":
                msg = block.get("message")
                if isinstance(msg, dict):
                    chat = msg.get("chat")
                    if isinstance(chat, dict) and "id" in chat:
                        return str(chat["id"])
    return None


class TelegramBotOrdersIntegration(IntegrationTelegramBase, ClientBase):
    def __init__(self):
        super().__init__()
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.handlers_registered = False
        self._memory_carts: Dict[str, List[dict]] = {}
        self._memory_catalog_state: Dict[str, Dict[str, Any]] = {}
        self._memory_order_state: Dict[str, Dict[str, Any]] = {}

    def _error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    async def _fetch_settings(self, cache_key: str) -> Dict[str, str]:
        if app_settings.redis_enabled and redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    if isinstance(cached, (bytes, bytearray)):
                        cached = cached.decode("utf-8")
                    return json.loads(cached)
            except Exception as error:
                logger.warning(f"Ошибка Redis: {error}, запрашиваю настройки из API")

        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            settings_response = (
                await api.integrations.connected_integration_setting.get(
                    ConnectedIntegrationSettingRequest(
                        integration_key=TelegramBotOrdersConfig.INTEGRATION_KEY
                    )
                )
            ).result

        settings_map = {item.key.lower(): item.value for item in settings_response}
        if app_settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    TelegramBotOrdersConfig.SETTINGS_TTL,
                    json.dumps(settings_map),
                )
            except Exception as error:
                logger.warning(f"Не удалось закешировать настройки: {error}")
        return settings_map

    async def _initialize_bot(self) -> None:
        if self.bot:
            return
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        settings_map = await self._fetch_settings(cache_key)
        bot_token = settings_map.get(TelegramOrdersSettings.BOT_TOKEN.value.lower())
        if not bot_token:
            raise ValueError("Не найден BOT_TOKEN в настройках интеграции")
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )

    @staticmethod
    def _parse_bool(value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
        return None

    @staticmethod
    def _parse_time(value: Optional[str]) -> Optional[dt_time]:
        if value is None:
            return None
        text = str(value).strip()
        try:
            return datetime.strptime(text, "%H:%M").time()
        except ValueError:
            return None

    @staticmethod
    def _is_longpolling_mode() -> bool:
        mode = str(app_settings.telegram_update_mode or "").strip().lower()
        return mode in {"longpolling", "long_polling", "long-polling", "polling"}

    def _is_work_time(self, settings_map: Dict[str, str]) -> bool:
        enabled = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_ENABLED.value.lower())
        )
        if not enabled:
            return True
        start = self._parse_time(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_START.value.lower())
        )
        end = self._parse_time(
            settings_map.get(TelegramOrdersSettings.WORK_TIME_END.value.lower())
        )
        if not start or not end:
            return True
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    async def connect(self, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        await self._initialize_bot()
        await self._setup_handlers()
        if not self.bot:
            return {"status": "connected"}
        if self._is_longpolling_mode():
            await self.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted (longpolling mode).")
            return {"status": "connected", "mode": "longpolling"}
        webhook_url = (
            f"{TelegramBotOrdersConfig.WEBHOOK_BASE_URL}/"
            f"{self.connected_integration_id}/external/"
        )
        await self.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set: {webhook_url}")
        return {"status": "connected", "mode": "webhook", "webhook_url": webhook_url}

    async def update_settings(
        self,
        request: Optional[ConnectedIntegrationSettingEditRequest] = None,
        data: Optional[List[Dict]] = None,
        incoming_settings: Optional[List[Dict]] = None,
        **kwargs,
    ) -> IntegrationSuccessResponse:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        if app_settings.redis_enabled and redis_client:
            try:
                await redis_client.delete(cache_key)
            except Exception as error:
                logger.warning(f"Redis error while clearing settings cache: {error}")
        await self.connect()
        return IntegrationSuccessResponse(result={"status": "settings updated"})

    async def _setup_handlers(self) -> None:
        if not self.dispatcher:
            self.dispatcher = Dispatcher()
        if self.handlers_registered:
            return

        @self.dispatcher.message(Command("start"))
        async def handle_start(message: types.Message):
            text = (
                "Привет! Я бот для оформления заказов.\n"
                "Команды: /catalog, /cart, /order, /card, /help"
            )
            await message.answer(text)
            await self._request_phone(message)

        @self.dispatcher.message(Command("help"))
        async def handle_help(message: types.Message):
            text = (
                "Доступные команды:\n"
                "/catalog — каталог\n"
                "/cart — корзина\n"
                "/order — оформление заказа\n"
                "/card — карты покупателя"
            )
            await message.answer(text)

        @self.dispatcher.message(Command("catalog"))
        async def handle_catalog(message: types.Message):
            if not self._is_work_time(
                await self._fetch_settings(
                    f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
                )
            ):
                await message.answer("Заказы принимаются вне рабочего времени.")
                return
            search = self._command_arg(message.text)
            await self._save_catalog_state(str(message.chat.id), search, 0)
            await self._send_catalog_page(str(message.chat.id))

        @self.dispatcher.message(Command("cart"))
        async def handle_cart(message: types.Message):
            cart = await self._get_cart(str(message.chat.id))
            if not cart:
                await message.answer("Корзина пуста.")
                return
            text = self._format_cart(cart)
            await message.answer(text)

        @self.dispatcher.message(Command("order"))
        async def handle_order(message: types.Message):
            await self._handle_order(message)

        @self.dispatcher.message(Command("card"))
        async def handle_card(message: types.Message):
            await self._handle_cards(message)

        @self.dispatcher.message(Command("add"))
        async def handle_add(message: types.Message):
            await self._handle_add_to_cart(message)

        @self.dispatcher.message(Command("remove"))
        async def handle_remove(message: types.Message):
            await self._handle_remove_from_cart(message)

        @self.dispatcher.message(Command("clear"))
        async def handle_clear(message: types.Message):
            await self._clear_cart(str(message.chat.id))
            await message.answer("Корзина очищена.")

        @self.dispatcher.message(lambda message: message.contact is not None)
        async def handle_contact(message: types.Message):
            await self._handle_contact(message)

        @self.dispatcher.message(lambda message: message.location is not None)
        async def handle_location(message: types.Message):
            await self._handle_location(message)

        @self.dispatcher.message()
        async def handle_description(message: types.Message):
            await self._handle_description(message)

        @self.dispatcher.callback_query(lambda c: c.data and c.data.startswith("cat:add:"))
        async def handle_catalog_add(callback_query: types.CallbackQuery):
            try:
                item_id = int(callback_query.data.split(":")[2])
            except Exception:
                await callback_query.answer("Не удалось добавить")
                return
            result = await self._add_item_to_cart(
                str(callback_query.from_user.id),
                item_id,
                Decimal("1"),
            )
            await callback_query.answer("Добавлено")
            if result:
                await self.bot.send_message(
                    chat_id=callback_query.from_user.id, text=result
                )

        @self.dispatcher.callback_query(lambda c: c.data == "cat:next")
        async def handle_catalog_next(callback_query: types.CallbackQuery):
            await callback_query.answer()
            await self._send_catalog_page(str(callback_query.from_user.id), next_page=True)

        self.handlers_registered = True

    async def send_messages(self, messages: List[Dict]) -> Any:
        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id не задан")

        await self._initialize_bot()

        results = []
        for msg in messages:
            chat_id = msg.get("recipient")
            text = msg.get("message")
            if not chat_id or not text:
                return self._error_response(1001, "Некорректный формат сообщения")
            try:
                await self.bot.send_message(chat_id=chat_id, text=text)
                results.append({"status": "sent", "chat_id": chat_id})
            except Exception as error:
                logger.error(f"Ошибка отправки сообщения {chat_id}: {error}")
                results.append({"status": "error", "chat_id": chat_id, "error": str(error)})

        return {"sent": len([r for r in results if r["status"] == "sent"]), "details": results}

    async def handle_external(self, envelope: Dict) -> Dict:
        payload = envelope.get("body")
        if not isinstance(payload, dict):
            return self._error_response(400, "Ожидается JSON-объект").dict()

        await self._initialize_bot()
        await self._setup_handlers()

        chat_id = _extract_chat_id(payload)
        if chat_id:
            logger.info(f"Telegram update from chat_id={chat_id}")

        try:
            telegram_update = TelegramUpdate.model_validate(payload)
        except Exception as error:
            logger.error(f"Некорректное обновление Telegram: {error}")
            return self._error_response(400, "Некорректный формат обновления").dict()

        try:
            await self.dispatcher.feed_update(self.bot, telegram_update)
        except Exception as error:
            logger.exception("Ошибка обработки Telegram update")
            return self._error_response(500, f"Ошибка обработки: {error}").dict()

        return {
            "status": "processed",
            "connected_integration_id": self.connected_integration_id,
            "chat_id": chat_id,
        }

    async def update_settings(self, settings: dict) -> Any:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        if app_settings.redis_enabled and redis_client:
            await redis_client.delete(cache_key)
        return {"status": "settings updated"}

    async def _request_phone(self, message: types.Message) -> None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text="Поделиться номером", request_contact=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "Поделитесь номером телефона для оформления заказа.",
            reply_markup=keyboard,
        )

    @staticmethod
    def _command_arg(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return None
        return parts[1].strip() or None

    def _cart_key(self, chat_id: str) -> str:
        return f"clients:cart:telegram_bot_orders:{self.connected_integration_id}:{chat_id}"

    def _catalog_state_key(self, chat_id: str) -> str:
        return f"clients:catalog_state:telegram_bot_orders:{self.connected_integration_id}:{chat_id}"

    def _order_state_key(self, chat_id: str) -> str:
        return f"clients:order_state:telegram_bot_orders:{self.connected_integration_id}:{chat_id}"

    async def _get_cart(self, chat_id: str) -> List[dict]:
        key = self._cart_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            cached = await redis_client.get(key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                return json.loads(cached)
            return []
        return self._memory_carts.get(key, [])

    async def _save_cart(self, chat_id: str, cart: List[dict]) -> None:
        key = self._cart_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            await redis_client.setex(key, TelegramBotOrdersConfig.CART_TTL, json.dumps(cart))
            return
        self._memory_carts[key] = cart

    async def _clear_cart(self, chat_id: str) -> None:
        key = self._cart_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            await redis_client.delete(key)
            return
        self._memory_carts.pop(key, None)

    async def _save_catalog_state(self, chat_id: str, search: Optional[str], offset: int) -> None:
        key = self._catalog_state_key(chat_id)
        payload = {"search": search, "offset": offset}
        if app_settings.redis_enabled and redis_client:
            await redis_client.setex(key, TelegramBotOrdersConfig.CATALOG_TTL, json.dumps(payload))
            return
        self._memory_catalog_state[key] = payload

    async def _get_catalog_state(self, chat_id: str) -> Dict[str, Any]:
        key = self._catalog_state_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            cached = await redis_client.get(key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                return json.loads(cached)
            return {"search": None, "offset": 0}
        return self._memory_catalog_state.get(key, {"search": None, "offset": 0})

    async def _get_order_state(self, chat_id: str) -> Dict[str, Any]:
        key = self._order_state_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            cached = await redis_client.get(key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                return json.loads(cached)
            return {}
        return self._memory_order_state.get(key, {})

    async def _save_order_state(self, chat_id: str, state: Dict[str, Any]) -> None:
        key = self._order_state_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            await redis_client.setex(
                key, TelegramBotOrdersConfig.ORDER_STATE_TTL, json.dumps(state)
            )
            return
        self._memory_order_state[key] = state

    async def _clear_order_state(self, chat_id: str) -> None:
        key = self._order_state_key(chat_id)
        if app_settings.redis_enabled and redis_client:
            await redis_client.delete(key)
            return
        self._memory_order_state.pop(key, None)

    async def _fetch_catalog(self, search: Optional[str], offset: int) -> List[ItemExt]:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        settings_map = await self._fetch_settings(cache_key)
        stock_id = self._parse_int(settings_map.get(TelegramOrdersSettings.STOCK_ID.value.lower()))
        price_type_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        zero_qty = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.SHOW_ZERO_QUANTITY.value.lower())
        )
        show_without_images = self._parse_bool(
            settings_map.get(TelegramOrdersSettings.SHOW_WITHOUT_IMAGES.value.lower())
        )
        if show_without_images is True:
            has_image = None
        elif show_without_images is False:
            has_image = True
        else:
            has_image = None

        hash_input = json.dumps(
            {
                "search": search,
                "offset": offset,
                "stock_id": stock_id,
                "price_type_id": price_type_id,
                "zero_qty": zero_qty,
                "has_image": has_image,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        key_hash = hashlib.sha1(hash_input.encode("utf-8")).hexdigest()
        cache_key = (
            f"clients:cache:catalog:{self.connected_integration_id}:{key_hash}"
        )
        if app_settings.redis_enabled and redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                raw_items = json.loads(cached)
                return [ItemExt.model_validate(item) for item in raw_items]

        req = ItemGetExtRequest(
            stock_id=stock_id,
            price_type_id=price_type_id,
            zero_quantity=zero_qty,
            has_image=has_image,
            image_size=ItemGetExtImageSize.Small,
            search=search,
            limit=TelegramBotOrdersConfig.CATALOG_PAGE_SIZE,
            offset=offset,
        )
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.item.get_ext(req)
            result = resp.result or []
            if app_settings.redis_enabled and redis_client:
                try:
                    payload = [item.model_dump(mode="json") for item in result]
                    await redis_client.setex(
                        cache_key,
                        TelegramBotOrdersConfig.CATALOG_TTL,
                        json.dumps(payload, ensure_ascii=False),
                    )
                except Exception as error:
                    logger.warning(f"Ошибка кеширования каталога: {error}")
            return result

    async def _send_catalog_page(self, chat_id: str, *, next_page: bool = False) -> None:
        state = await self._get_catalog_state(chat_id)
        search = state.get("search")
        offset = int(state.get("offset", 0))
        if next_page:
            offset += TelegramBotOrdersConfig.CATALOG_PAGE_SIZE
        items = await self._fetch_catalog(search=search, offset=offset)
        if not items:
            await self.bot.send_message(chat_id=chat_id, text="Больше ничего нет.")
            return
        await self._save_catalog_state(chat_id, search, offset)

        for entry in items:
            text = self._format_item(entry)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Добавить",
                            callback_data=f"cat:add:{entry.item.id}",
                        )
                    ]
                ]
            )
            if entry.image_url:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=entry.image_url,
                    caption=text,
                    reply_markup=keyboard,
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                )

        if len(items) >= TelegramBotOrdersConfig.CATALOG_PAGE_SIZE:
            next_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Следующая страница", callback_data="cat:next")]
                ]
            )
            await self.bot.send_message(
                chat_id=chat_id,
                text="Показать еще?",
                reply_markup=next_keyboard,
            )

    def _format_item(self, entry: ItemExt) -> str:
        item = entry.item
        name = item.name or f"ID {item.id}"
        price = entry.price if entry.price is not None else Decimal(0)
        qty = (
            entry.quantity.common if entry.quantity and entry.quantity.common is not None else None
        )
        qty_text = f", остаток {qty}" if qty is not None else ""
        return f"{name} (id={item.id})\nЦена: {price}{qty_text}"

    def _format_cart(self, cart: List[dict]) -> str:
        total = Decimal("0")
        lines = ["Корзина:"]
        for row in cart:
            price = Decimal(str(row["price"]))
            qty = Decimal(str(row["qty"]))
            total += price * qty
            lines.append(f"- {row['name']} (id={row['item_id']}): {qty} x {price}")
        lines.append(f"Итого: {total}")
        lines.append("Удалить: /remove <id> | Очистить: /clear")
        return "\n".join(lines)

    async def _handle_add_to_cart(self, message: types.Message) -> None:
        if not message.text:
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Использование: /add <id> [qty]")
            return
        try:
            item_id = int(parts[1])
        except ValueError:
            await message.answer("Некорректный id")
            return
        qty = Decimal("1")
        if len(parts) > 2:
            try:
                qty = Decimal(parts[2])
            except Exception:
                await message.answer("Некорректное количество")
                return
        if qty <= 0:
            await message.answer("Количество должно быть больше 0")
            return

        result = await self._add_item_to_cart(str(message.chat.id), item_id, qty)
        if result:
            await message.answer(result)

    async def _handle_remove_from_cart(self, message: types.Message) -> None:
        if not message.text:
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Использование: /remove <id>")
            return
        try:
            item_id = int(parts[1])
        except ValueError:
            await message.answer("Некорректный id")
            return
        cart = await self._get_cart(str(message.chat.id))
        new_cart = [row for row in cart if row["item_id"] != item_id]
        await self._save_cart(str(message.chat.id), new_cart)
        await message.answer("Удалено из корзины.")

    async def _handle_order(self, message: types.Message) -> None:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        settings_map = await self._fetch_settings(cache_key)
        if not self._is_work_time(settings_map):
            await message.answer("Заказы принимаются вне рабочего времени.")
            return

        cart = await self._get_cart(str(message.chat.id))
        if not cart:
            await message.answer("Корзина пуста.")
            return

        min_amount = self._parse_decimal(
            settings_map.get(TelegramOrdersSettings.MIN_ORDER_AMOUNT.value.lower())
        )
        total = sum(
            Decimal(str(row["price"])) * Decimal(str(row["qty"])) for row in cart
        )
        if min_amount and min_amount > 0 and total < min_amount:
            await message.answer(f"Минимальная сумма заказа: {min_amount}")
            return

        customer = await self._find_customer_by_chat(str(message.chat.id))
        if not customer:
            await self._request_phone(message)
            return

        state = await self._get_order_state(str(message.chat.id))
        if not state.get("location"):
            await self._save_order_state(
                str(message.chat.id),
                {"step": "await_location", "location": None, "description": state.get("description")},
            )
            await self._request_location(message)
            return
        if not state.get("description"):
            await self._save_order_state(
                str(message.chat.id),
                {"step": "await_description", "location": state.get("location"), "description": None},
            )
            await self._request_description(message)
            return

        stock_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.STOCK_ID.value.lower())
        )
        price_type_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        from_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.ORDER_SOURCE_ID.value.lower())
        )

        operations = [
            DocOrderDeliveryOperation(
                item_id=row["item_id"],
                quantity=Decimal(str(row["qty"])),
                price=Decimal(str(row["price"])),
            )
            for row in cart
        ]
        location = state.get("location") or {}
        location_payload = Location(
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        )
        document = DocOrderDeliveryAddRequest(
            date=int(datetime.utcnow().timestamp()),
            stock_id=stock_id,
            customer_id=customer.id,
            from_id=from_id,
            price_type_id=price_type_id,
            amount=total,
            phone=customer.main_phone,
            description=state.get("description"),
            location=location_payload,
            external_code=f"tg-{message.chat.id}-{int(datetime.utcnow().timestamp())}",
        )
        req = DocOrderDeliveryAddFullRequest(document=document, operations=operations)

        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.docs.order_delivery.add_full(req)
        if not resp.ok:
            await message.answer("Ошибка создания заказа.")
            return

        await self._clear_cart(str(message.chat.id))
        await self._clear_order_state(str(message.chat.id))
        await message.answer("Заказ создан. Спасибо!")

    async def _handle_cards(self, message: types.Message) -> None:
        customer = await self._find_customer_by_chat(str(message.chat.id))
        if not customer:
            await self._request_phone(message)
            return
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.retail_card.get(
                RetailCardGetRequest(customer_ids=[customer.id])
            )
        cards = resp.result or []
        if not cards:
            await message.answer("Карты покупателя не найдены.")
            return
        for card in cards:
            text = (
                f"Карта #{card.id}\n"
                f"Бонусы: {card.bonus_amount}\n"
                f"Статус: {'активна' if card.enabled else 'не активна'}\n"
                f"Штрих-код: {card.barcode_value}"
            )
            image = self._make_qr(card.barcode_value)
            if image:
                await self.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=BufferedInputFile(image, filename="card.png"),
                    caption=text,
                )
            else:
                await message.answer(text)

    async def _find_customer_by_chat(self, chat_id: str):
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerGetRequest(
                filters=[
                    Filter(
                        field="field_telegram_id",
                        operator=FilterOperator.Equal,
                        value=str(chat_id),
                    )
                ],
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            return resp.result[0] if resp.result else None

    async def _fetch_item_ext(self, item_id: int, settings_map: Dict[str, str]) -> Optional[ItemExt]:
        stock_id = self._parse_int(settings_map.get(TelegramOrdersSettings.STOCK_ID.value.lower()))
        price_type_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.PRICE_TYPE_ID.value.lower())
        )
        cache_key = (
            f"clients:cache:item_ext:{self.connected_integration_id}:{item_id}:"
            f"{stock_id}:{price_type_id}"
        )
        if app_settings.redis_enabled and redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                if isinstance(cached, (bytes, bytearray)):
                    cached = cached.decode("utf-8")
                return ItemExt.model_validate(json.loads(cached))
        req = ItemGetExtRequest(
            ids=[item_id],
            stock_id=stock_id,
            price_type_id=price_type_id,
            limit=1,
            offset=0,
        )
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.item.get_ext(req)
            item = resp.result[0] if resp.result else None
            if item and app_settings.redis_enabled and redis_client:
                try:
                    await redis_client.setex(
                        cache_key,
                        TelegramBotOrdersConfig.CATALOG_TTL,
                        json.dumps(item.model_dump(mode="json"), ensure_ascii=False),
                    )
                except Exception as error:
                    logger.warning(f"Ошибка кеширования позиции: {error}")
            return item

    async def _add_item_to_cart(
        self, chat_id: str, item_id: int, qty: Decimal
    ) -> Optional[str]:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        settings_map = await self._fetch_settings(cache_key)
        item_ext = await self._fetch_item_ext(item_id, settings_map)
        if not item_ext:
            return "Товар не найден."

        cart = await self._get_cart(chat_id)
        existing = next((x for x in cart if x["item_id"] == item_id), None)
        price = item_ext.price if item_ext.price is not None else Decimal(0)
        name = item_ext.item.name or f"ID {item_id}"
        if existing:
            existing["qty"] = str(Decimal(existing["qty"]) + qty)
        else:
            cart.append(
                {"item_id": item_id, "name": name, "price": str(price), "qty": str(qty)}
            )
        await self._save_cart(chat_id, cart)
        return f"Добавлено в корзину: {name} x {qty}"

    async def _handle_contact(self, message: types.Message) -> None:
        contact = message.contact
        if not contact or not contact.phone_number:
            await message.answer("Не удалось получить номер телефона.")
            return
        phone = self._normalize_phone(contact.phone_number)
        if not phone:
            await message.answer("Некорректный номер телефона.")
            return

        customer = await self._find_customer_by_phone(phone)
        if customer:
            await self._update_customer_telegram_id(customer.id, str(message.chat.id))
            await message.answer(
                "Номер сохранен. Теперь можно оформлять заказ.",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return

        created = await self._create_customer_from_contact(message, phone)
        if created:
            await message.answer(
                "Покупатель создан. Теперь можно оформлять заказ.",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return

        await message.answer("Не удалось создать покупателя. Обратитесь к администратору.")

    async def _handle_location(self, message: types.Message) -> None:
        location = message.location
        if not location:
            return
        state = await self._get_order_state(str(message.chat.id))
        if not state:
            await message.answer("Локация получена. Для оформления используйте /order.")
            return
        state["location"] = {
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        state["step"] = "await_description"
        await self._save_order_state(str(message.chat.id), state)
        await self._request_description(message)

    async def _handle_description(self, message: types.Message) -> None:
        if not message.text or message.text.startswith("/"):
            return
        state = await self._get_order_state(str(message.chat.id))
        if state.get("step") != "await_description":
            return
        state["description"] = message.text.strip()
        state["step"] = "ready"
        await self._save_order_state(str(message.chat.id), state)
        await message.answer("Примечание сохранено.")
        await self._handle_order(message)

    async def _find_customer_by_phone(self, phone: str):
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerGetRequest(
                main_phone=phone,
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            if resp.result:
                return resp.result[0]
            req = RetailCustomerGetRequest(
                search=phone,
                limit=1,
                offset=0,
            )
            resp = await api.references.retail_customer.get(req)
            return resp.result[0] if resp.result else None

    async def _update_customer_telegram_id(self, customer_id: int, chat_id: str) -> None:
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            req = RetailCustomerEditRequest(
                id=customer_id,
                fields=[FieldValueEdit(key="field_telegram_id", value=chat_id)],
            )
            await api.references.retail_customer.edit(req)

    async def _create_customer_from_contact(self, message: types.Message, phone: str) -> bool:
        cache_key = f"clients:settings:telegram_bot_orders:{self.connected_integration_id}"
        settings_map = await self._fetch_settings(cache_key)
        group_id = self._parse_int(
            settings_map.get(TelegramOrdersSettings.CUSTOMER_GROUP_ID.value.lower())
        )
        if not group_id:
            logger.warning("CUSTOMER_GROUP_ID не задан в настройках интеграции")
            return False

        first_name = message.contact.first_name or "Клиент"
        last_name = message.contact.last_name
        full_name = " ".join(
            [x for x in [first_name, last_name] if x]
        ).strip()

        req = RetailCustomerAddRequest(
            group_id=group_id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name or None,
            main_phone=phone,
            fields=[FieldValueAdd(key="field_telegram_id", value=str(message.chat.id))],
        )
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            resp = await api.references.retail_customer.add(req)
            return bool(resp.ok)

    async def _request_location(self, message: types.Message) -> None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text="Отправить локацию", request_location=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "Пожалуйста, отправьте локацию для доставки.",
            reply_markup=keyboard,
        )

    async def _request_description(self, message: types.Message) -> None:
        await message.answer("Напишите примечание к заказу.")

    @staticmethod
    def _make_qr(value: str) -> Optional[bytes]:
        if not value or qrcode is None:
            return None
        img = qrcode.make(value)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value).strip())
        except Exception:
            return None

    @staticmethod
    def _normalize_phone(value: str) -> Optional[str]:
        if not value:
            return None
        digits = "".join(ch for ch in value if ch.isdigit())
        return digits or None
