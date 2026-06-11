# Биллинг-коннектор для обращений

## Наименование интеграции

- Русский: `Биллинг-коннектор для обращений`
- O'zbekcha: `Murojaatlar uchun billing konnektori`
- English: `Billing Connector for Tickets`

## Краткое описание

- Русский: `Интеграция подтягивает данные клиента из биллинга в активные обращения и помогает оператору видеть важный контекст прямо в чате.`
- O'zbekcha: `Integratsiya billingdagi mijoz ma'lumotlarini faol murojaatlarga olib keladi va operatorga muhim kontekstni chat ichida ko'rsatadi.`
- English: `The integration brings customer billing details into active tickets so operators see the right context inside the chat.`

## Полное описание

- Русский:
  `<p>REGOS помогает команде вести обращения, продажи и клиентскую историю в одной рабочей среде. Биллинг-коннектор добавляет к этому живой контекст из вашей биллинговой системы: при создании обращения или изменении клиента интеграция запрашивает актуальные данные, обновляет карточку клиента и публикует понятное системное сообщение в чат обращения.</p><ul><li>Оператор видит баланс, тариф, статус договора или другие параметры без переключения между системами.</li><li>Карточка клиента обновляется только по разрешенным стандартным полям.</li><li>Повторные webhook-и и события от собственного обновления клиента не создают бесконечный цикл.</li></ul>`
- O'zbekcha:
  `<p>REGOS jamoaga murojaatlar, savdo va mijoz tarixini yagona ish muhitida yuritishga yordam beradi. Billing konnektori shu jarayonga billing tizimidagi dolzarb ma'lumotlarni qo'shadi: murojaat yaratilganda yoki mijoz o'zgarganda integratsiya ma'lumotlarni oladi, mijoz kartasini yangilaydi va murojaat chatiga tizimli xabar yozadi.</p><ul><li>Operator balans, tarif, shartnoma holati yoki boshqa parametrlarni alohida tizimga o'tmasdan ko'radi.</li><li>Mijoz kartasi faqat ruxsat berilgan standart maydonlar bo'yicha yangilanadi.</li><li>Takroriy webhooklar va integratsiyaning o'z yangilashi cheksiz sikl yaratmaydi.</li></ul>`
- English:
  `<p>REGOS helps teams keep tickets, sales, and customer history in one working environment. Billing Connector adds live context from your billing system: when a ticket is created or a client changes, the integration requests fresh billing data, updates the client card, and posts a clear system message to the ticket chat.</p><ul><li>Operators can see balance, tariff, contract status, or other billing parameters without switching tools.</li><li>The client card is updated only through allowed standard fields.</li><li>Repeated webhooks and updates made by the integration do not create an endless loop.</li></ul>`

## Обрабатываемые события и действия

| Источник | Событие | Что делает интеграция |
| --- | --- | --- |
| CRM webhook | `TicketAdded` | Загружает новое активное обращение, получает данные клиента из биллинга, обновляет клиента и пишет системное сообщение в чат обращения. |
| CRM webhook | `ClientEdited` | Находит активные обращения клиента и обновляет их чат актуальной информацией из биллинга. |

Webhook-и подписываются вручную в настройках подключенной интеграции. Код интеграции подписки не создает.

## Очередь обработки

Webhook REGOS должен получить быстрый ответ, поэтому интеграция не делает запросы в биллинг прямо в HTTP-обработчике. Событие кладется в Redis Stream, после чего worker забирает его и выполняет обновление клиента и публикацию системного сообщения.

Redis обязателен для работы интеграции. Ключи очереди не создаются навсегда: stream имеет TTL 24 часа и ограничение `MAXLEN`, dedupe-ключи создаются с TTL 10 минут, обработанные записи подтверждаются и удаляются через `XACK`/`XDEL`. После 3 неудачных попыток событие переносится в DLQ-stream с тем же TTL.

## Настройки интеграции

| Ключ | Обяз. | Тип | Назначение |
| --- | --- | --- | --- |
| `billing_client_info_url` | Да | String | URL метода биллинга для получения данных клиента. |
| `billing_bearer_token` | Да | String | Токен биллинга без префикса `Bearer`; интеграция сама добавляет его в заголовок. |
| `billing_message_template` | Нет | String | Шаблон системного сообщения. Если задан, переопределяет `message_template` из ответа биллинга. |

## Авторизация в биллинге

Интеграция отправляет запрос в биллинг методом `POST` и передает токен в заголовке:

```http
Authorization: Bearer <billing_bearer_token>
Content-Type: application/json
Accept: application/json
```

Токен не логируется. Если биллинг возвращает `401` или `403`, интеграция завершает обработку с причиной `billing_auth_failed`.

## Запрос в биллинг

```json
{
  "client": {
    "id": 123,
    "external_id": "external-123",
    "name": "Client name",
    "phone": "998...",
    "email": "client@example.com"
  },
  "ticket": {
    "id": 456,
    "status": "Open",
    "channel_id": 1,
    "subject": "Тема обращения"
  }
}
```

## Ответ биллинга

```json
{
  "client": {
    "name": "Client name",
    "phone": "998...",
    "email": "client@example.com",
    "photo_url": "https://example.com/avatar.jpg",
    "description": "Описание клиента"
  },
  "parameters": [
    { "key": "balance", "name": "Баланс", "value": "125000" },
    { "key": "tariff", "name": "Тариф", "value": "Premium" }
  ],
  "message_template": "Баланс: {balance}\nТариф: {tariff}"
}
```

## Логика работы

1. На `TicketAdded` или `ClientEdited` интеграция принимает webhook и ставит событие в Redis Stream.
2. Worker загружает обращение через `Ticket/Get`.
3. Если обращение закрыто, без клиента или без чата, событие игнорируется.
4. Интеграция загружает клиента через `Client/Get` и отправляет контекст в биллинг.
5. Из ответа биллинга обновляются только `name`, `phone`, `email`, `photo_url`, `description`.
6. `Client/Edit` вызывается только если данные из биллинга отличаются от текущих данных клиента.
7. Текст системного сообщения строится из `billing_message_template` в настройках или из `message_template` ответа биллинга, затем в него подставляются `parameters`.
8. На `ClientEdited` worker находит активные обращения клиента со статусами `Open`, `WaitingClient`, `WaitingStaff` и повторяет тот же сценарий для каждого обращения.

Повторная обработка одинакового ответа биллинга ограничивается TTL-дедупликацией по клиенту, обращению и хэшу данных. Это защищает от дублей и от цикла, который может возникнуть после собственного `Client/Edit`.
