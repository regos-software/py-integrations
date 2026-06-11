# REGOS Pay и сделки CRM

## Наименование интеграции

- Русский: `REGOS Pay для сделок CRM`
- O'zbekcha: `CRM bitimlari uchun REGOS Pay`
- English: `REGOS Pay for CRM Deals`

## Краткое описание

- Русский: `Интеграция выставляет ссылку на оплату REGOS Pay в нужный момент сделки и фиксирует оплату прямо в ее чате.`
- O'zbekcha: `Integratsiya bitim kerakli bosqichga o'tganda REGOS Pay to'lov havolasini yaratadi va to'lovni bitim chatida qayd etadi.`
- English: `The integration creates a REGOS Pay payment link at the right deal stage and records the payment in the deal chat.`

## Полное описание

- Русский:
  `<p>REGOS помогает бизнесу вести продажи, склад и аналитику в единой рабочей среде. Эта интеграция добавляет к сделкам аккуратный платежный сценарий: менеджер переводит сделку на выбранную стадию, клиент получает ссылку REGOS Pay, а команда видит результат оплаты без ручной сверки.</p><ul><li>Счет создается только на настроенной стадии сделки, поэтому платеж не появляется раньше коммерческого решения.</li><li>Ссылка на оплату публикуется в чат сделки, где ее сразу видит команда.</li><li>После callback-а REGOS Pay интеграция пишет сообщение об оплате и может перевести сделку на стадию оплачено.</li><li>ID заказа хранится в доп. поле сделки, чтобы повторные webhook-и и callback-и не создавали дубли.</li></ul>`
- O'zbekcha:
  `<p>REGOS savdo, ombor va tahlil jarayonlarini yagona ish muhitida yuritishga yordam beradi. Ushbu integratsiya bitimlarga tartibli to'lov jarayonini qo'shadi: menejer bitimni tanlangan bosqichga o'tkazadi, mijoz REGOS Pay havolasini oladi, jamoa esa to'lov natijasini qo'lda solishtirmasdan ko'radi.</p><ul><li>Hisob faqat sozlangan bitim bosqichida yaratiladi.</li><li>To'lov havolasi bitim chatiga joylanadi.</li><li>REGOS Pay callback kelgandan so'ng integratsiya to'lov haqida xabar yozadi va kerak bo'lsa bitimni to'langan bosqichiga o'tkazadi.</li><li>Buyurtma ID si bitimning qo'shimcha maydonida saqlanadi, shuning uchun takroriy webhook yoki qo'lda tekshiruv dubl yaratmaydi.</li></ul>`
- English:
  `<p>REGOS helps teams run sales, inventory, and analytics in one working environment. This integration adds a clean payment flow to CRM deals: a manager moves the deal to the selected stage, the customer receives a REGOS Pay link, and the team sees the payment result without manual reconciliation.</p><ul><li>A checkout is created only at the configured deal stage.</li><li>The payment link is posted to the deal chat.</li><li>After the REGOS Pay callback, the integration posts a paid message and can move the deal to the paid stage.</li><li>The order ID is stored in a deal custom field, so repeated webhooks and callbacks do not create duplicates.</li></ul>`

## Обрабатываемые события и действия

| Источник | Событие или действие | Что делает интеграция |
| --- | --- | --- |
| CRM webhook | `DealStageSet` | Проверяет воронку и стадию сделки, затем создает счет REGOS Pay. |
| REGOS Pay callback | `check` / `Check` | Проверяет подпись, сделку, сохраненный `order_Id`, воронку и сумму платежа. |
| REGOS Pay callback | `perform` / `Perform` | Подтверждает оплату, пишет в чат сделки и переводит сделку на стадию оплаты, если она задана. |
Webhook `DealStageSet` подписывается вручную в настройках подключенной интеграции. Код интеграции подписки не создает.

## Очередь обработки

Webhook `DealStageSet` должен получить быстрый ответ, поэтому интеграция не вызывает REGOS Pay `CheckOut` прямо в HTTP-обработчике. Событие кладется в Redis Stream, после чего worker проверяет сделку, создает счет и публикует ссылку в чат.

Redis обязателен для обработки `DealStageSet`. Ключи очереди не создаются навсегда: stream имеет TTL 24 часа и ограничение `MAXLEN`, dedupe-ключи создаются с TTL 10 минут, обработанные записи подтверждаются и удаляются через `XACK`/`XDEL`. После 3 неудачных попыток событие переносится в DLQ-stream с тем же TTL.

Callback-и REGOS Pay `Check` и `Perform` не ставятся в очередь: платежный сервис ожидает синхронный ответ проверки или проведения платежа.

## Настройки интеграции

| Ключ | Обяз. | Тип | Назначение |
| --- | --- | --- | --- |
| `regos_pay_service_id` | Да | String | ID сервиса REGOS Pay, по которому создается платеж. |
| `regos_pay_secret_key` | Да | String | Секретный ключ для проверки подписи callback-ов REGOS Pay. |
| `regos_pay_deal_pipeline_id` | Да | Integer | ID воронки сделок, где работает платежный сценарий. |
| `regos_pay_checkout_stage_id` | Да | Integer | ID стадии, на которой нужно выставить счет. |
| `regos_pay_paid_stage_id` | Нет | Integer | ID стадии после успешной оплаты. Если пусто или `0`, стадия не меняется. |

## Логика работы

1. Интеграция при подключении проверяет воронку, стадии и создает служебное доп. поле `field_regos_pay_order_id` для `order_Id`.
2. Когда приходит `DealStageSet`, интеграция ставит событие в Redis Stream.
3. Worker загружает сделку из CRM.
4. Если сделка не в `regos_pay_deal_pipeline_id` или не на `regos_pay_checkout_stage_id`, событие игнорируется.
5. Если в служебном поле уже есть `order_Id`, новый счет не создается.
6. Если счета еще нет, интеграция вызывает `POST https://pay.regos.uz/api/CheckOut`.
7. Полученный `order_Id` сохраняется в доп. поле сделки, а ссылка на оплату публикуется в чат сделки.
8. После `perform` интеграция находит сделку по `order_Id`, пишет в чат информацию об оплате и переводит сделку в `regos_pay_paid_stage_id`, если настройка задана.

Сумма берется из `deal.amount`. Описание заказа формируется как `Payment for deal #<deal_id>: <title>`. В текущей версии номенклатура в `CheckOut.items` не передается.

## Callback URL для REGOS Pay

Для подключенной интеграции с ID `<connected_integration_id>`:

```text
POST /clients/regos_pay_deals/<connected_integration_id>/Check
POST /clients/regos_pay_deals/<connected_integration_id>/Perform
```
