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
  `<p>REGOS помогает бизнесу вести продажи, склад и аналитику в единой рабочей среде. Эта интеграция добавляет к сделкам аккуратный платежный сценарий: менеджер переводит сделку на выбранную стадию, клиент получает ссылку REGOS Pay, а команда видит результат оплаты без ручной сверки.</p><ul><li>Счет создается только на настроенной стадии сделки, поэтому платеж не появляется раньше коммерческого решения.</li><li>Ссылка на оплату публикуется в чат сделки, где ее сразу видит команда.</li><li>После callback-а REGOS Pay интеграция пишет сообщение об оплате и может перевести сделку на стадию оплачено.</li><li>ID заказа хранится в доп. поле сделки, чтобы повторные webhook-и и ручные проверки не создавали дубли.</li></ul>`
- O'zbekcha:
  `<p>REGOS savdo, ombor va tahlil jarayonlarini yagona ish muhitida yuritishga yordam beradi. Ushbu integratsiya bitimlarga tartibli to'lov jarayonini qo'shadi: menejer bitimni tanlangan bosqichga o'tkazadi, mijoz REGOS Pay havolasini oladi, jamoa esa to'lov natijasini qo'lda solishtirmasdan ko'radi.</p><ul><li>Hisob faqat sozlangan bitim bosqichida yaratiladi.</li><li>To'lov havolasi bitim chatiga joylanadi.</li><li>REGOS Pay callback kelgandan so'ng integratsiya to'lov haqida xabar yozadi va kerak bo'lsa bitimni to'langan bosqichiga o'tkazadi.</li><li>Buyurtma ID si bitimning qo'shimcha maydonida saqlanadi, shuning uchun takroriy webhook yoki qo'lda tekshiruv dubl yaratmaydi.</li></ul>`
- English:
  `<p>REGOS helps teams run sales, inventory, and analytics in one working environment. This integration adds a clean payment flow to CRM deals: a manager moves the deal to the selected stage, the customer receives a REGOS Pay link, and the team sees the payment result without manual reconciliation.</p><ul><li>A checkout is created only at the configured deal stage.</li><li>The payment link is posted to the deal chat.</li><li>After the REGOS Pay callback, the integration posts a paid message and can move the deal to the paid stage.</li><li>The order ID is stored in a deal custom field, so retries and manual checks do not create duplicates.</li></ul>`

## Обрабатываемые события и действия

| Источник | Событие или действие | Что делает интеграция |
| --- | --- | --- |
| CRM webhook | `DealStageSet` | Проверяет воронку и стадию сделки, затем создает счет REGOS Pay. |
| REGOS Pay callback | `check` / `Check` | Проверяет подпись, сделку, сохраненный `order_Id`, воронку и сумму платежа. |
| REGOS Pay callback | `perform` / `Perform` | Подтверждает оплату, пишет в чат сделки и переводит сделку на стадию оплаты, если она задана. |
| Ручной вызов | `CreateCheckout` | Запускает тот же stage-gated сценарий для конкретной сделки. |

Webhook `DealStageSet` подписывается вручную в настройках подключенной интеграции. Код интеграции подписки не создает.

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
2. Когда приходит `DealStageSet`, сделка загружается из CRM.
3. Если сделка не в `regos_pay_deal_pipeline_id` или не на `regos_pay_checkout_stage_id`, событие игнорируется.
4. Если в служебном поле уже есть `order_Id`, новый счет не создается.
5. Если счета еще нет, интеграция вызывает `POST https://pay.regos.uz/api/CheckOut`.
6. Полученный `order_Id` сохраняется в доп. поле сделки, а ссылка на оплату публикуется в чат сделки.
7. После `perform` интеграция находит сделку по `order_Id`, пишет в чат информацию об оплате и переводит сделку в `regos_pay_paid_stage_id`, если настройка задана.

Сумма берется из `deal.amount`. Описание заказа формируется как `Payment for deal #<deal_id>: <title>`. В текущей версии номенклатура в `CheckOut.items` не передается.

## Callback URL для REGOS Pay

Для подключенной интеграции с ID `<connected_integration_id>`:

```text
POST /clients/regos_pay_deals/<connected_integration_id>/Check
POST /clients/regos_pay_deals/<connected_integration_id>/Perform
```

## Ручной вызов

Основной сценарий - автоматический через стадию сделки. Для ручной проверки можно вызвать:

```json
{
  "action": "CreateCheckout",
  "data": {
    "deal_id": 123
  }
}
```

Ручной вызов соблюдает то же правило стадии: счет создается только если сделка находится на `regos_pay_checkout_stage_id`.
