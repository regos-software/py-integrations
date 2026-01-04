from typing import List, Optional


class TelegramBotOrdersTexts:
    ERROR_BOT_TOKEN_MISSING = "Не найден BOT_TOKEN в настройках интеграции"
    ERROR_CONNECTED_ID_MISSING = "connected_integration_id не задан"
    ERROR_INVALID_MESSAGE_FORMAT = "Некорректный формат сообщения"
    ERROR_EXPECTED_JSON = "Ожидается JSON-объект"
    ERROR_INVALID_UPDATE = "Некорректный формат обновления"
    ERROR_PROCESSING = "Ошибка обработки: {error}"
    MAIN_MENU = "Выберите действие:"
    MAIN_MENU_USE_BUTTONS = "Используйте кнопки ниже."
    WELCOME = "Привет! Выберите действие ниже."
    CART_EMPTY = "Корзина пуста."
    CALLBACK_INVALID_DATA = "Некорректные данные"
    CALLBACK_ADD_FAILED = "Не удалось добавить"
    CALLBACK_ADDED = "Добавлено"
    CALLBACK_FILTERS_NOT_READY = "Фильтры пока не настроены"
    REQUEST_PHONE = "Пожалуйста, поделитесь номером телефона для оформления заказа."
    BUTTON_SHARE_PHONE = "Поделиться номером"
    BUTTON_MENU_CATALOG = "Каталог"
    BUTTON_MENU_CART = "Корзина"
    BUTTON_MENU_ORDER = "Оформить заказ"
    BUTTON_MENU_CARDS = "Карты покупателя"
    BUTTON_MENU_MAIN = "Меню"
    BUTTON_CART_CLEAR = "Очистить корзину"
    BUTTON_REMOVE_ITEM = "Удалить {item_id}"
    BUTTON_ADD = "➕ Добавить"
    BUTTON_DETAILS = "Подробнее"
    BUTTON_BACK = "⬅ Назад"
    BUTTON_NEXT = "Вперёд ➡"
    BUTTON_SEARCH = "Поиск"
    BUTTON_FILTERS = "Фильтры"
    BUTTON_BACK_TO_LIST = "Назад к списку"
    BUTTON_BACK_TO_CATALOG = "Назад к каталогу"
    BUTTON_CART = "Корзина"
    ADD_USAGE = "Использование: /add <id> [qty]"
    REMOVE_USAGE = "Использование: /remove <id>"
    INVALID_ID = "Некорректный id"
    INVALID_QTY = "Некорректное количество"
    QTY_GT_ZERO = "Количество должно быть больше 0"
    REMOVED_FROM_CART = "Удалено из корзины."
    WORK_TIME_OFF = "Сейчас вне рабочего времени."
    ORDER_CREATE_ERROR = "Ошибка при создании заказа."
    ORDER_ACCEPTED = "Заказ принят. Спасибо!"
    NO_CARDS = "У покупателя нет карт."
    CART_TITLE = "Корзина:"
    CART_LINE = "- {name} (id={item_id}): {qty} x {price}"
    CART_TOTAL = "Итого: {total}"
    CART_HINT = "Используйте кнопки ниже, чтобы изменить корзину."
    CATALOG_TITLE = "*Каталог* (стр. {page})"
    CATALOG_SEARCH_LINE = "_Поиск:_ {query}"
    CATALOG_EMPTY_LINE = "_Нет товаров_"
    CATALOG_SEARCH_PROMPT = (
        "*Поиск*\nВведите запрос (название, артикул, код или штрих-код)."
    )
    ITEM_LINE = "{index}. *{name}* - {price}{qty_text}"
    ITEM_QTY_SUFFIX = ", остаток {qty}"
    ITEM_DETAIL_ID = "*ID:* {item_id}"
    ITEM_DETAIL_PRICE = "*Цена:* {price}"
    ITEM_DETAIL_QTY = "*Остаток:* {qty}"
    ITEM_DETAIL_ARTICUL = "*Артикул:* {articul}"
    ITEM_DETAIL_CODE = "*Код:* {code}"
    ITEM_DETAIL_DESCRIPTION = "*Описание:* {description}"
    CARD_STATUS_ACTIVE = "активна"
    CARD_STATUS_INACTIVE = "не активна"
    CARD_TEMPLATE = (
        "Карта #{card_id}\nБаланс: {bonus}\nСтатус: {status}\nШтрих-код: {barcode}"
    )
    PHONE_NOT_RECEIVED = "Не удалось получить номер телефона. Попробуйте еще раз."
    PHONE_INVALID = "Номер телефона некорректен. Попробуйте еще раз."
    CUSTOMER_FOUND = "Покупатель найден. Можно продолжать оформление."
    CUSTOMER_CREATED = "Покупатель создан. Можно продолжать оформление."
    CUSTOMER_CREATE_FAILED = (
        "Не удалось создать покупателя. Попробуйте позже или обратитесь в поддержку."
    )
    CUSTOMER_DEFAULT_FIRST_NAME = "Клиент"
    LOCATION_RECEIVED_NOT_STARTED = (
        "Локация получена, но заказ не начат. Выберите «Оформить заказ»."
    )
    DESCRIPTION_ACCEPTED = "Принято. Оформляю заказ."
    REQUEST_LOCATION = "Пожалуйста, отправьте локацию для доставки."
    BUTTON_SEND_LOCATION = "Отправить локацию"
    REQUEST_DESCRIPTION = "Напишите примечание к заказу."
    ITEM_NOT_FOUND = "Номенклатура не найдена."

    @staticmethod
    def log_redis_error(error) -> str:
        return f"Ошибка Redis: {error}, запрашиваю настройки из API"

    @staticmethod
    def log_settings_cache_fail(error) -> str:
        return f"Не удалось закешировать настройки: {error}"

    @staticmethod
    def log_send_message_error(chat_id, error) -> str:
        return f"Ошибка отправки сообщения {chat_id}: {error}"

    @staticmethod
    def log_update_invalid(error) -> str:
        return f"Некорректное обновление Telegram: {error}"

    @staticmethod
    def log_update_processing_error(error) -> str:
        return f"Ошибка обработки: {error}"

    @staticmethod
    def log_update_catalog_fail(error) -> str:
        return f"Не удалось обновить сообщение каталога: {error}"

    @staticmethod
    def log_delete_photo_fail(error) -> str:
        return f"Не удалось удалить фото карточки: {error}"

    @staticmethod
    def log_send_photo_fail(error) -> str:
        return f"Не удалось отправить фото товара: {error}"

    @staticmethod
    def log_catalog_cache_error(error) -> str:
        return f"Ошибка кеширования каталога: {error}"

    @staticmethod
    def log_item_cache_error(error) -> str:
        return f"Ошибка кеширования позиции: {error}"

    @staticmethod
    def log_customer_group_missing() -> str:
        return "CUSTOMER_GROUP_ID не задан в настройках интеграции"

    @staticmethod
    def min_order_amount(amount) -> str:
        return f"Минимальная сумма заказа: {amount}"

    @staticmethod
    def cart_added(name: str, qty) -> str:
        return f"Добавлено в корзину: {name} x {qty}"

    @staticmethod
    def catalog_title(page: int) -> str:
        return TelegramBotOrdersTexts.CATALOG_TITLE.format(page=page)

    @staticmethod
    def catalog_search_line(query: str) -> str:
        return TelegramBotOrdersTexts.CATALOG_SEARCH_LINE.format(query=query)

    @staticmethod
    def catalog_empty_line() -> str:
        return TelegramBotOrdersTexts.CATALOG_EMPTY_LINE

    @staticmethod
    def item_qty_suffix(qty) -> str:
        return TelegramBotOrdersTexts.ITEM_QTY_SUFFIX.format(qty=qty)

    @staticmethod
    def item_line(index: int, name: str, price, qty_text: str) -> str:
        return TelegramBotOrdersTexts.ITEM_LINE.format(
            index=index, name=name, price=price, qty_text=qty_text
        )

    @staticmethod
    def item_detail_lines(
        name: str,
        item_id: int,
        price,
        qty: Optional[float] = None,
        articul: Optional[str] = None,
        code: Optional[int] = None,
        description: Optional[str] = None,
    ) -> List[str]:
        lines = [
            f"*{name}*",
            TelegramBotOrdersTexts.ITEM_DETAIL_ID.format(item_id=item_id),
            TelegramBotOrdersTexts.ITEM_DETAIL_PRICE.format(price=price),
        ]
        if qty is not None:
            lines.append(TelegramBotOrdersTexts.ITEM_DETAIL_QTY.format(qty=qty))
        if articul:
            lines.append(TelegramBotOrdersTexts.ITEM_DETAIL_ARTICUL.format(articul=articul))
        if code:
            lines.append(TelegramBotOrdersTexts.ITEM_DETAIL_CODE.format(code=code))
        if description:
            lines.append(
                TelegramBotOrdersTexts.ITEM_DETAIL_DESCRIPTION.format(
                    description=description
                )
            )
        return lines

    @staticmethod
    def cart_line(name: str, item_id: int, qty, price) -> str:
        return TelegramBotOrdersTexts.CART_LINE.format(
            name=name, item_id=item_id, qty=qty, price=price
        )

    @staticmethod
    def cart_total(total) -> str:
        return TelegramBotOrdersTexts.CART_TOTAL.format(total=total)

    @staticmethod
    def card_status(enabled: bool) -> str:
        return (
            TelegramBotOrdersTexts.CARD_STATUS_ACTIVE
            if enabled
            else TelegramBotOrdersTexts.CARD_STATUS_INACTIVE
        )

    @staticmethod
    def card_text(card_id: int, bonus, enabled: bool, barcode: str) -> str:
        return TelegramBotOrdersTexts.CARD_TEMPLATE.format(
            card_id=card_id,
            bonus=bonus,
            status=TelegramBotOrdersTexts.card_status(enabled),
            barcode=barcode,
        )
