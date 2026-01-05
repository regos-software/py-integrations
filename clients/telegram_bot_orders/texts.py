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
    REQUEST_PHONE = "Пожалуйста, поделитесь номером телефона для оформления заказа."
    BUTTON_SHARE_PHONE = "☎️ Поделиться номером"
    BUTTON_MENU_CATALOG = "Каталог"
    BUTTON_MENU_CART = "🛒 Корзина"
    BUTTON_MENU_ORDER = "Оформить заказ"
    BUTTON_MENU_ORDERS = "Мои заказы"
    BUTTON_MENU_CARDS = "Карты покупателя"
    BUTTON_MENU_MAIN = "Меню"
    BUTTON_CATEGORIES = "Категории"
    BUTTON_ALL_ITEMS = "Все товары"
    BUTTON_CART_CLEAR = "🗑 Очистить корзину"
    BUTTON_CART_REMOVE = "Удалить позицию"
    BUTTON_ADD = "➕ Добавить"
    BUTTON_ADD_ONE = "➕ Добавить (+1)"
    BUTTON_ADD_OTHER = "Добавить другое количество"
    BUTTON_DETAILS = "Подробнее"
    BUTTON_BACK = "⬅ Назад"
    BUTTON_NEXT = "Вперёд ➡"
    BUTTON_SEARCH = "🔍 Поиск"
    BUTTON_BACK_TO_LIST = "Назад к списку"
    BUTTON_BACK_TO_ITEM = "Назад к товару"
    BUTTON_BACK_TO_CATALOG = "Назад к каталогу"
    BUTTON_ORDER_BACK_TO_LIST = "Назад к списку заказов"
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
    ORDERS_DISABLED = "Прием заказов отключен. Доступны только карты покупателя."
    DELIVERY_TYPES_EMPTY = "Способы доставки не найдены. Укажите ID вручную."
    ORDERS_EMPTY = "У вас пока нет заказов."
    ORDERS_TITLE = "*Мои заказы* (стр. {page})"
    ORDERS_HINT = "Нажмите на заказ, чтобы посмотреть детали."
    ORDER_LINE = "{index}. №{code} от {date} — {amount}{status}"
    ORDER_DETAIL_TITLE = "*Заказ №{code}*"
    ORDER_DETAIL_DATE = "*Дата:* {date}"
    ORDER_DETAIL_AMOUNT = "*Сумма:* {amount}"
    ORDER_DETAIL_STATUS = "*Статус:* {status}"
    ORDER_DETAIL_ADDRESS = "*Адрес:* {address}"
    ORDER_DETAIL_DESCRIPTION = "*Комментарий:* {description}"
    ORDER_DETAIL_DELIVERY_TYPE = "*Доставка:* {delivery_type}"
    ORDER_DETAIL_FROM = "*Источник:* {source}"
    ORDER_NOT_FOUND = "Заказ не найден."
    NO_CARDS = "У покупателя нет карт."
    CATEGORIES_TITLE = "Выберите категорию:"
    CATEGORIES_EMPTY = "Категории не найдены."
    CATEGORIES_UNKNOWN = "Категория не найдена. Выберите из списка."
    CATALOG_NUMBER_INVALID = "Некорректный номер. Выберите из списка."
    CART_SELECT_NUMBER_REMOVE = "Отправьте номер позиции для удаления."
    CART_NUMBER_INVALID = "Некорректный номер позиции."
    CART_ITEM_REMOVED = "Позиция удалена."
    CART_TITLE = "*Корзина*"
    CART_SEPARATOR = "----"
    CART_ITEM_HEADER = "❌ {index}. {name}"
    CART_ITEM_DETAILS = "Количество: {qty}\nЦена: {price}\nСумма: {total}"
    CART_TOTAL = "Итого: {total}"
    CART_HINT = "Используйте кнопки ниже, чтобы изменить корзину."
    CATALOG_TITLE = "*Каталог* (стр. {page})"
    CATALOG_CATEGORY_LINE = "_Категория:_ {name}"
    CATALOG_SEARCH_LINE = "_Поиск:_ {query}"
    CATALOG_EMPTY_LINE = "_Нет товаров_"
    CATALOG_SEARCH_PROMPT = (
        "*Поиск*\nВведите запрос (название, артикул, код или штрих-код)."
    )
    ITEM_LINE = "{index}. *{name}*\nЦена: {price}{qty_line}"
    ITEM_QTY_LINE = "\nОстаток: {qty}"
    ITEM_QTY_SUFFIX = ", остаток {qty}"
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
    REQUEST_QTY = "Выберите количество (можно дробное) или введите вручную."
    QTY_INVALID = "Некорректное количество. Введите число больше 0."
    QTY_INTEGER_ONLY = "Для штучных товаров доступно только целое количество."
    REQUEST_DELIVERY_TYPE = "Выберите способ доставки."
    DELIVERY_TYPE_INVALID = "Выберите способ доставки из списка."
    REQUEST_ADDRESS = "Укажите адрес доставки текстом."
    ADDRESS_INVALID = "Адрес не должен быть пустым."
    ITEM_NOT_FOUND = "Номенклатура не найдена."
    ITEM_UNNAMED = "Товар"
    QTY_OPTIONS = ["0.5", "1", "2", "3", "5", "10"]

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
    def catalog_category_line(name: str) -> str:
        return TelegramBotOrdersTexts.CATALOG_CATEGORY_LINE.format(name=name)

    @staticmethod
    def catalog_empty_line() -> str:
        return TelegramBotOrdersTexts.CATALOG_EMPTY_LINE

    @staticmethod
    def orders_title(page: int) -> str:
        return TelegramBotOrdersTexts.ORDERS_TITLE.format(page=page)

    @staticmethod
    def order_line(index: int, code: str, date: str, amount, status: Optional[str]) -> str:
        status_part = f" ({status})" if status else ""
        return TelegramBotOrdersTexts.ORDER_LINE.format(
            index=index, code=code, date=date, amount=amount, status=status_part
        )

    @staticmethod
    def order_button_label(index: int, code: str) -> str:
        return f"{index}. №{code}"

    @staticmethod
    def order_detail_title(code: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_TITLE.format(code=code)

    @staticmethod
    def order_detail_date(date: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_DATE.format(date=date)

    @staticmethod
    def order_detail_amount(amount) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_AMOUNT.format(amount=amount)

    @staticmethod
    def order_detail_status(status: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_STATUS.format(status=status)

    @staticmethod
    def order_detail_address(address: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_ADDRESS.format(address=address)

    @staticmethod
    def order_detail_description(description: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_DESCRIPTION.format(
            description=description
        )

    @staticmethod
    def order_detail_delivery_type(delivery_type: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_DELIVERY_TYPE.format(
            delivery_type=delivery_type
        )

    @staticmethod
    def order_detail_from(source: str) -> str:
        return TelegramBotOrdersTexts.ORDER_DETAIL_FROM.format(source=source)

    @staticmethod
    def item_qty_suffix(qty) -> str:
        return TelegramBotOrdersTexts.ITEM_QTY_SUFFIX.format(qty=qty)

    @staticmethod
    def item_qty_line(qty) -> str:
        return TelegramBotOrdersTexts.ITEM_QTY_LINE.format(qty=qty)

    @staticmethod
    def item_line(index: int, name: str, price, qty_line: str) -> str:
        return TelegramBotOrdersTexts.ITEM_LINE.format(
            index=index, name=name, price=price, qty_line=qty_line
        )

    @staticmethod
    def item_detail_lines(
        name: str,
        price,
        qty: Optional[float] = None,
        articul: Optional[str] = None,
        code: Optional[int] = None,
        description: Optional[str] = None,
    ) -> List[str]:
        lines = [
            f"*{name}*",
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
    def cart_item_header(index: int, name: str) -> str:
        return TelegramBotOrdersTexts.CART_ITEM_HEADER.format(index=index, name=name)

    @staticmethod
    def cart_item_details(qty, price, total) -> str:
        return TelegramBotOrdersTexts.CART_ITEM_DETAILS.format(
            qty=qty, price=price, total=total
        )

    @staticmethod
    def cart_button_label(index: int, name: str) -> str:
        return TelegramBotOrdersTexts.CART_ITEM_HEADER.format(index=index, name=name)

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
