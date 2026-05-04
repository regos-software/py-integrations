# Instagram-канал для поддержки клиентов

## Наименование интеграции

- Русский: `Instagram-канал для поддержки клиентов`
- O'zbekcha: `Mijozlarni qo'llab-quvvatlash uchun Instagram kanali`
- English: `Instagram Channel for Customer Support`

## Краткое описание

- Русский: `Интеграция объединяет Instagram Direct и CRM: клиент пишет в Instagram, оператор отвечает из CRM, а вся переписка сохраняется в обращении.`
- O'zbekcha: `Integratsiya Instagram Direct va CRM ni birlashtiradi: mijoz Instagramda yozadi, operator CRM ichidan javob beradi, yozishmalar esa murojaatda saqlanadi.`
- English: `The integration connects Instagram Direct and CRM: customers message in Instagram, operators reply from CRM, and the full conversation stays in one case.`

## Полное описание

- Русский:
  `<p>Решение помогает команде поддержки работать с Instagram Direct из CRM без переключения между окнами.</p><ul><li>Новые сообщения клиента из Instagram автоматически попадают в обращение CRM.</li><li>Если активного обращения нет, интеграция создаёт клиента, обращение и чат.</li><li>Оператор отвечает из CRM, а клиент получает сообщение в том же диалоге Instagram.</li><li>Маршрут ответа сохраняется по клиенту и чату, поэтому последующие сообщения продолжают тот же диалог.</li><li>Повторные webhook-события обрабатываются безопасно через dedupe и очередь.</li><li>Интеграция проверяет подпись Meta webhook-запросов и не принимает неподписанные POST-запросы.</li></ul>`
- O'zbekcha:
  `<p>Yechim qo'llab-quvvatlash jamoasiga Instagram Direct bilan CRM ichida ishlashga yordam beradi.</p><ul><li>Mijozning Instagramdagi yangi xabarlari CRM murojaatiga avtomatik tushadi.</li><li>Faol murojaat topilmasa, integratsiya mijoz, murojaat va chat yaratadi.</li><li>Operator CRM ichida javob beradi, mijoz esa xabarni shu Instagram dialogida oladi.</li><li>Javob yo'nalishi mijoz va chat bo'yicha saqlanadi, shuning uchun keyingi xabarlar shu muloqotda davom etadi.</li><li>Takroriy webhook hodisalari dedupe va navbat orqali xavfsiz qayta ishlanadi.</li><li>Integratsiya Meta webhook so'rovlarining imzosini tekshiradi va imzosiz POST so'rovlarni qabul qilmaydi.</li></ul>`
- English:
  `<p>The solution lets support teams handle Instagram Direct from CRM without switching tools.</p><ul><li>New customer messages from Instagram are automatically added to a CRM case.</li><li>If no active case exists, the integration creates a customer, case, and chat.</li><li>Operators reply from CRM, and customers receive replies in the same Instagram conversation.</li><li>The reply route is stored per customer and chat, keeping follow-up messages in the same conversation.</li><li>Duplicate webhook events are handled safely with dedupe and a queue.</li><li>The integration verifies Meta webhook signatures and rejects unsigned POST requests.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `ChatMessageAdded`
- Meta / Instagram:
  - Webhook verification: `GET /clients/instagram_crm_channel/external`
  - Messaging events: `POST /clients/instagram_crm_channel/external`

## Какие действия выполняются автоматически

- При подключении подписывает интеграцию на CRM webhook `ChatMessageAdded`.
- При Connect сохраняет `instagram_authorization_url`, если Instagram ещё не авторизован.
- При OAuth-подключении сохраняет `instagram_business_account_id`, `instagram_access_token`, срок действия токена, username и статус авторизации.
- Создаёт или находит клиента по Instagram ID / external ID.
- Создаёт новое CRM-обращение, если активное обращение для Instagram-диалога не найдено.
- Добавляет входящие сообщения Instagram в CRM-чат от имени клиента.
- Отправляет ответы оператора из CRM в Instagram Direct.
- Отмечает исходящие CRM-сообщения как отправленные через `ChatMessage/MarkSent`.
- Восстанавливает активные очереди и reverse-indexes после рестарта сервиса.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `instagram_business_account_id` | Нет | String | `ID Instagram Business Account` / `Instagram Business Account ID` / `Instagram Business Account ID` | `Заполняется автоматически после OAuth. Если задан заранее, OAuth должен вернуть именно этот аккаунт` / `OAuthdan keyin avtomatik to'ldiriladi. Oldindan berilgan bo'lsa, OAuth aynan shu akkauntni qaytarishi kerak` / `Filled automatically after OAuth. If set in advance, OAuth must return this exact account` | `1784...` / `1784...` / `1784...` |
| `instagram_pipeline_id` | Да | Integer | `ID воронки CRM` / `CRM voronkasi ID` / `CRM pipeline ID` | `Воронка, где создаются обращения Instagram` / `Instagram murojaatlari yaratiladigan voronka` / `Pipeline where Instagram cases are created` | `1` / `1` / `1` |
| `instagram_channel_id` | Да | Integer | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `CRM-канал, куда попадают Instagram-диалоги` / `Instagram muloqotlari tushadigan CRM kanali` / `CRM channel where Instagram conversations are routed` | `1` / `1` / `1` |
| `instagram_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным при создании обращения` / `Murojaat yaratilganda biriktiriladigan mas'ul xodim` / `User assigned as responsible when a case is created` | `15` / `15` / `15` |
| `instagram_ticket_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон названия нового обращения. Доступны {client_id} и {external_user_id}` / `Yangi murojaat nomi shabloni. {client_id} va {external_user_id} mavjud` / `Template for new case subject. {client_id} and {external_user_id} are available` | `Instagram {client_id}` / `Instagram {client_id}` / `Instagram {client_id}` |
| `instagram_access_token` | Нет | String | `Instagram access token` / `Instagram access token` / `Instagram access token` | `Long-lived token Instagram Business Login для отправки и получения сообщений` / `Xabar yuborish va olish uchun Instagram Business Login long-lived token` / `Instagram Business Login long-lived token for sending and receiving messages` | `IGQVJ...` / `IGQVJ...` / `IGQVJ...` |
| `instagram_access_token_expires_at` | Нет | Integer | `Срок действия токена` / `Token muddati` / `Token expiration` | `Unix-время окончания действия Instagram access token` / `Instagram access token tugash Unix-vaqti` / `Unix time when the Instagram access token expires` | `1783182160` / `1783182160` / `1783182160` |
| `instagram_username` | Нет | String | `Instagram username` / `Instagram username` / `Instagram username` | `Заполняется автоматически после OAuth` / `OAuthdan keyin avtomatik to'ldiriladi` / `Filled automatically after OAuth` | `regos_support` / `regos_support` / `regos_support` |
| `instagram_authorization_url` | Нет | String | `URL подключения Instagram` / `Instagram ulash URL` / `Instagram authorization URL` | `Заполняется автоматически при Connect и обновляется UI, если OAuth state истёк` / `Connect vaqtida avtomatik to'ldiriladi va OAuth state muddati tugasa UI yangilaydi` / `Filled automatically on Connect and refreshed by the UI when OAuth state expires` | `https://www.instagram.com/oauth/authorize...` / `https://www.instagram.com/oauth/authorize...` / `https://www.instagram.com/oauth/authorize...` |
| `instagram_authorized` | Нет | Boolean | `Instagram авторизован` / `Instagram avtorizatsiya qilingan` / `Instagram authorized` | `Служебный статус авторизации, заполняется автоматически` / `Avtorizatsiya xizmati holati, avtomatik to'ldiriladi` / `Service authorization status, filled automatically` | `false` / `false` / `false` |
| `instagram_authorization_status` | Нет | String | `Статус авторизации` / `Avtorizatsiya holati` / `Authorization status` | `Служебное состояние: authorization_required или authorized` / `Xizmat holati: authorization_required yoki authorized` / `Service state: authorization_required or authorized` | `authorization_required` / `authorization_required` / `authorization_required` |
| `instagram_authorization_url_generated_at` | Нет | Integer | `Дата генерации URL` / `URL yaratish vaqti` / `URL generated at` | `Unix-время генерации authorization URL, используется для обновления истёкшего OAuth state` / `Authorization URL yaratish Unix-vaqti, muddati tugagan OAuth state ni yangilash uchun ishlatiladi` / `Unix time when the authorization URL was generated, used to refresh expired OAuth state` | `1777902160` / `1777902160` / `1777902160` |
| `instagram_find_active_ticket_by_external_user` | Нет | Boolean | `Искать активное обращение по external ID` / `External ID bo'yicha faol murojaatni qidirish` / `Find active case by external ID` | `Разрешает дополнительный поиск клиента и обращения по external ID` / `External ID bo'yicha mijoz va murojaatni qo'shimcha qidirishga ruxsat beradi` / `Allows an additional customer and case lookup by external ID` | `true` / `true` / `true` |

Глобальные настройки сервиса:

- Redis должен быть включён: очередь, dedupe, OAuth state и reverse-indexes хранятся в Redis.
- `instagram_app_id`: Instagram App ID единого приложения REGOS.
- `instagram_app_secret`: Instagram App Secret единого приложения REGOS.
- `instagram_redirect_uri`: OAuth callback URL для Instagram Business Login.
- `instagram_webhook_verify_token`: единый verify token для Instagram Webhooks.
- OAuth scopes: `instagram_business_basic`, `instagram_business_manage_messages`, `instagram_business_manage_comments`.
- Внешний Meta webhook URL: `/clients/instagram_crm_channel/external`.
- CRM UI / OAuth URL: `/clients/instagram_crm_channel`.

## Порядок настройки

1. Создайте приложение Meta с Instagram API / Instagram Business Login.
2. Заполните глобальные настройки сервиса: `instagram_app_id`, `instagram_app_secret`, `instagram_redirect_uri`, `instagram_webhook_verify_token`.
3. В подключенной интеграции заполните настройки маршрутизации: `instagram_pipeline_id`, `instagram_channel_id`. `instagram_business_account_id` можно оставить пустым, он заполнится после Instagram Business Login.
4. Вызовите `Connect`, чтобы подписать CRM webhook, сохранить reverse-indexes и записать `instagram_authorization_url`, если Instagram ещё не авторизован.
5. Откройте UI интеграции. Если статус `authorization_required`, нажмите кнопку подключения Instagram и пройдите Instagram Business Login, чтобы автоматически связать подключенную интеграцию с Instagram Business Account пользователя.
6. В Meta настройте webhook URL `/clients/instagram_crm_channel/external` и verify token из глобальной настройки `instagram_webhook_verify_token`.
7. Проверьте входящее сообщение из Instagram: в CRM должно появиться обращение и чат.
8. Ответьте из CRM: клиент должен получить сообщение в Instagram Direct.
