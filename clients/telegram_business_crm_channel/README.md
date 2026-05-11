# Telegram Business CRM Channel

## Наименование интеграции

- Русский: `Telegram Business канал для поддержки клиентов`
- O'zbekcha: `Mijozlarni qo'llab-quvvatlash uchun Telegram Business kanali`
- English: `Telegram Business Channel for Customer Support`

## Краткое описание

- Русский: `Интеграция подключает реальный Telegram Business аккаунт к CRM: клиент пишет в личный чат Telegram, оператор отвечает из обращения, а клиент видит ответ от подключенного бизнес-аккаунта.`
- O'zbekcha: `Integratsiya haqiqiy Telegram Business akkauntini CRM ga ulaydi: mijoz Telegram shaxsiy chatiga yozadi, operator murojaatdan javob beradi, mijoz esa javobni ulangan biznes akkauntdan oladi.`
- English: `The integration connects a real Telegram Business account to CRM: customers message the Telegram chat, operators reply from the case, and customers receive replies from the connected business account.`

## Полное описание

- Русский:
  `<p>Решение подходит компаниям, которым нужно вести поддержку от имени реального Telegram Business аккаунта, сохраняя работу операторов внутри CRM.</p><ul><li>Входящие сообщения из Telegram Business автоматически создают клиента, обращение и чат в CRM.</li><li>Ответ оператора из CRM отправляется в тот же Telegram диалог от подключенного бизнес-аккаунта.</li><li>Редактирование и удаление сообщений синхронизируется с историей обращения.</li><li>После закрытия обращения можно отправлять финальное сообщение и запрос оценки качества.</li><li>Маршрут диалога хранит Telegram Business connection id, чтобы ответы не уходили через обычный бот.</li></ul>`
- O'zbekcha:
  `<p>Yechim operatorlar CRM ichida ishlagan holda haqiqiy Telegram Business akkaunti nomidan qo'llab-quvvatlash olib borishi kerak bo'lgan kompaniyalar uchun mo'ljallangan.</p><ul><li>Telegram Business dan kelgan xabarlar CRM da mijoz, murojaat va chat yaratadi.</li><li>Operator CRM ichidan javob beradi, javob esa ulangan biznes akkauntdan shu Telegram dialogiga yuboriladi.</li><li>Xabarlarni tahrirlash va o'chirish murojaat tarixida sinxronlanadi.</li><li>Murojaat yopilgandan keyin yakuniy xabar va xizmat sifatini baholash so'rovi yuborilishi mumkin.</li><li>Dialog marshruti Telegram Business connection id ni saqlaydi, shuning uchun javoblar oddiy bot orqali ketmaydi.</li></ul>`
- English:
  `<p>The solution is for teams that need to support customers from a real Telegram Business account while operators stay inside CRM.</p><ul><li>Incoming Telegram Business messages automatically create the client, case, and chat in CRM.</li><li>CRM replies are sent back to the same Telegram conversation from the connected business account.</li><li>Message edits and deletions are synchronized with the case history.</li><li>Closing a case can send a final message and a service rating request.</li><li>The dialog route stores the Telegram Business connection id, so replies are not sent as regular bot messages.</li></ul>`

## Обрабатываемые события

- CRM:
  - `ChatMessageAdded`
  - `ChatMessageEdited`
  - `ChatMessageDeleted`
  - `ChatWriting`
  - `TicketClosed`
  - `ChannelEdited`
- Telegram:
  - `business_connection`
  - `business_message`
  - `edited_business_message`
  - `deleted_business_messages`
  - `callback_query`

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `bot_1_token` | Да | String | `Токен Telegram Business бота` / `Telegram Business bot tokeni` / `Telegram Business bot token` | `Токен бота, подключенного к Telegram Business аккаунту` / `Telegram Business akkauntiga ulangan bot tokeni` / `Token of the bot connected to a Telegram Business account` | `123456:ABC...` / `123456:ABC...` / `123456:ABC...` |
| `bot_1_channel_id` | Да | Integer | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `Канал CRM, куда будут попадать диалоги из Telegram Business` / `Telegram Business muloqotlari tushadigan CRM kanal` / `CRM channel where Telegram Business conversations are routed` | `1` / `1` / `1` |
| `bot_1_lead_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон названия нового обращения` / `Yangi murojaat nomi uchun shablon` / `Template for new case subject` | `{display_name}` / `{display_name}` / `{display_name}` |
| `bot_1_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным при создании обращения` / `Murojaat yaratilganda biriktiriladigan mas'ul xodim` / `User assigned as responsible when a case is created` | `15` / `15` / `15` |
| `telegram_secret_token` | Нет | String | `Секрет проверки Telegram` / `Telegram tekshiruv siri` / `Telegram verification secret` | `Секрет для проверки входящих webhook-запросов Telegram Business` / `Telegram Business webhook so'rovlarini tekshirish siri` / `Secret used to validate inbound Telegram Business webhook calls` | `secret-...` / `secret-...` / `secret-...` |
| `send_private_messages` | Нет | Boolean | `Передавать private-сообщения` / `Private xabarlarni uzatish` / `Forward private messages` | `Разрешить отправку private-сообщений CRM в Telegram` / `CRM private xabarlarini Telegramga yuborishga ruxsat` / `Allow forwarding CRM private messages to Telegram` | `false` / `false` / `false` |
| `forward_system_messages` | Нет | Boolean | `Передавать system-сообщения` / `System xabarlarni uzatish` / `Forward system messages` | `Разрешить отправку system-сообщений CRM в Telegram` / `CRM system xabarlarini Telegramga yuborishga ruxsat` / `Allow forwarding CRM system messages to Telegram` | `false` / `false` / `false` |
| `phone_request_text` | Нет | String | `Текст запроса телефона` / `Telefon so'rovi matni` / `Phone request text` | `Текст, который бот отправляет при запросе номера телефона` / `Telefon raqamini so'raganda bot yuboradigan matn` / `Text sent when bot requests phone number` | `Поделитесь номером телефона` / `Telefon raqamingizni ulashing` / `Please share your phone number` |
| `phone_share_button_text` | Нет | String | `Текст кнопки телефона` / `Telefon tugmasi matni` / `Phone button text` | `Подпись кнопки Telegram для отправки контакта` / `Kontakt yuborish uchun Telegram tugmasi matni` / `Telegram contact-share button label` | `Отправить номер / Raqamni ulashish` / `Raqamni ulashish` / `Share phone number` |

Глобальные настройки сервиса (не поля интеграции):

- `TELEGRAM_BUSINESS_WEBHOOK_REFRESH_TTL`: срок кеша проверки webhook, по умолчанию `86400`.
- `TELEGRAM_BUSINESS_UPDATE_MODE`: режим получения событий, по умолчанию `webhook`; допустимо `longpolling`.
- `TELEGRAM_BUSINESS_CRM_CHANNEL_STREAM_WORKERS`: количество воркеров на stream, по умолчанию `2`.
- `TELEGRAM_BUSINESS_CRM_CHANNEL_STREAM_BATCH_SIZE`: размер пачки stream, по умолчанию `50`.
- `TELEGRAM_BUSINESS_CRM_CHANNEL_STREAM_MAXLEN`: максимальная длина stream, по умолчанию `100000`.
- `TELEGRAM_BUSINESS_CRM_CHANNEL_SEND_CONCURRENCY`: параллелизм исходящей отправки, по умолчанию `20`.

## Порядок настройки

1. Создайте Telegram-бота через BotFather.
2. В Telegram Business аккаунте подключите этого бота как connected bot и разрешите доступ к сообщениям.
3. В CRM создайте подключенную интеграцию `telegram_business_crm_channel`. Для каждой подключенной интеграции используйте отдельный токен бота, потому что Telegram хранит один webhook на один bot token.
4. Заполните токен бота, CRM-канал и при необходимости секрет webhook.
5. Выполните подключение интеграции, после чего Telegram webhook будет установлен автоматически.
6. Напишите в личный чат Telegram Business аккаунта и проверьте, что обращение создано в CRM, а ответ оператора приходит в тот же Telegram диалог.
