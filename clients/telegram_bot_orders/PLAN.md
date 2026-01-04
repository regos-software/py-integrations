# План внедрения: telegram_bot_orders

## 0) Уточнения и входные данные (требуют подтверждения)
- Уточнить обязательные поля DocOrderDelivery/AddFull (payment_type/delivery_type и т.д.).
- Подтвердить часовой пояс для ограничений времени работы.
- Задать CUSTOMER_GROUP_ID для создания новых покупателей.

## 1) Схемы (schemas) — сделано
- ItemExt и ItemGetExtRequest уже были в schemas/api/references/item.py.
- Добавлены схемы DocOrderDelivery (document/operations/add_full/get) в schemas/api/docs/order_delivery.py.
- Вынесены справочники DeliveryFrom/DeliveryType/DeliveryCourier в schemas/api/references/.
- Обновлены схемы RetailCard (BaseSchema + RetailCardGetRequest).

## 2) Сервисы (core/api) — сделано
- ItemService.get_ext уже был.
- Добавлен DocOrderDeliveryService (PATH_ADD_FULL, PATH_GET, PATH_GET_POS).
- Добавлен RetailCardService и регистрация в RegosAPI.References.
- Регистрация order_delivery в RegosAPI.Docs.

## 3) Настройки интеграции (ConnectedIntegrationSetting) — в работе
Ключи:
- price_type_id
- stock_id
- show_zero_quantity
- show_without_images
- order_source_id (from_id)
- min_order_amount
- work_time_enabled
- work_time_start
- work_time_end
- customer_group_id

## 4) Клиент telegram_bot_orders — сделано (каркас + логика)
- Создан clients/telegram_bot_orders/main.py.
- Реализован handle_external для webhook Telegram.
- Управление через inline-кнопки (каталог, корзина, оформление заказа, карты покупателя).
- Подключен Redis для корзины и кеша настроек.
- Поиск покупателя по телефону (после "Поделиться номером"), установка field_telegram_id.
- Создание RetailCustomer/Add при отсутствии.

## 5) Каталог (Item/GetExt) — сделано
- Получение номенклатуры с учетом настроек: stock_id, price_type_id, zero_quantity, has_image, image_size.
- Пагинация и inline-кнопки ("Добавить", "Следующая страница").
- Выдача картинок по image_url.
- Кеширование страниц каталога в Redis (TTL 60 сек).

## 6) Корзина (Redis) — сделано
- Ключ: clients:cart:telegram_bot_orders:{connected_integration_id}:{chat_id}
- Операции: add/update/remove/clear.
- TTL корзины используется.

## 7) Оформление заказа (DocOrderDelivery/AddFull) — сделано базово
- Проверка времени работы и минимальной суммы.
- Привязка покупателя через field_telegram_id (по телефону) или создание нового.
- Формирование document + operations (item_id).
- Запрос локации и описания заказа (description) перед созданием документа.
- Очистка корзины после успеха.

## 8) Карты покупателя (RetailCard/Get) — сделано базово
- Получение списка карт по customer_id.
- Отображение баланса и статуса.
- Генерация QR-картинки (qrcode/pillow).

## 9) Регистрация интеграции — сделано
- Добавлен класс в routes/clients.py (INTEGRATION_CLASSES).

## 10) Кеширование данных от API — сделано
- Каталог и карточка товара кешируются в Redis с небольшим TTL.

## 11) Проверки — осталось
- Ручные сценарии: каталог -> корзина -> заказ.
- Проверка карточки покупателя и QR.
- Проверка запроса локации и описания заказа.
- Логи и обработка ошибок.

## 12) Технический долг / улучшения
- Уточнить и добавить обязательные поля DocOrderDelivery/AddFull (payment_type/delivery_type и т.п.).
- Если qrcode/pillow недопустимы — заменить на другой генератор QR.
