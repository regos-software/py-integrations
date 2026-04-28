# Telegram-канал для поддержки клиентов

## Наименование интеграции

- Русский: `Telegram-канал для поддержки клиентов`
- O'zbekcha: `Mijozlarni qo'llab-quvvatlash uchun Telegram kanali`
- English: `Telegram Channel for Customer Support`

## Краткое описание

- Русский: `Интеграция объединяет Telegram и CRM в один удобный диалог: клиент пишет в мессенджере, оператор отвечает из CRM, а вся переписка хранится в обращении.`
- O'zbekcha: `Integratsiya Telegram va CRM ni bitta qulay muloqotga birlashtiradi: mijoz messenjerda yozadi, operator CRM ichidan javob beradi, yozishmalar esa murojaatda saqlanadi.`
- English: `The integration connects Telegram and CRM into one smooth conversation: customers message in Telegram, operators reply from CRM, and the full history stays in one case.`

## Полное описание

- Русский:
  `<p>Решение помогает команде поддержки отвечать быстрее и аккуратнее, не переключаясь между разными окнами.</p><ul><li>Все сообщения клиента автоматически попадают в обращение в CRM.</li><li>Оператор отвечает в CRM, а клиент получает ответ в том же чате Telegram.</li><li>Если у вас несколько ботов, система закрепляет правильный маршрут ответа и сохраняет целостность диалога.</li><li>Приветственное и завершающее сообщения отправляются клиенту автоматически по сценарию обслуживания.</li><li>Запрос номера телефона у клиента встроен в процесс и не мешает обычной переписке.</li><li>Автоматические сообщения видны и клиенту, и оператору, поэтому история прозрачна для всей команды.</li></ul>`
- O'zbekcha:
  `<p>Yechim qo'llab-quvvatlash jamoasiga turli oynalar orasida almashmasdan, tez va aniq javob berishga yordam beradi.</p><ul><li>Mijozning barcha xabarlari CRM dagi murojaatga avtomatik tushadi.</li><li>Operator CRM ichida javob beradi, mijoz esa javobni shu Telegram chatida oladi.</li><li>Agar bir nechta bot bo'lsa, tizim to'g'ri javob yo'nalishini saqlab, muloqotni yaxlit olib boradi.</li><li>Xizmat jarayoniga ko'ra salomlashuv va yakuniy xabar avtomatik yuboriladi.</li><li>Telefon raqamini so'rash jarayoni muloqotga qulay tarzda qo'shilgan.</li><li>Avtomatik xabarlar ham mijozga, ham operatorga ko'rinadi, shuning uchun tarix jamoa uchun shaffof bo'ladi.</li></ul>`
- English:
  `<p>The solution helps support teams reply faster and more consistently without switching between tools.</p><ul><li>Every customer message is automatically added to the CRM case.</li><li>Operators reply in CRM, and customers receive replies in the same Telegram chat.</li><li>If you use several bots, the system keeps the correct reply route and preserves conversation continuity.</li><li>Welcome and closing messages are sent automatically as part of your service flow.</li><li>Phone number request is built into the journey and stays user-friendly.</li><li>Automatic messages are visible to both customer and operator, making the history transparent for the whole team.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `ChatMessageAdded`
  - `ChatMessageEdited`
  - `ChatMessageDeleted`
  - `ChatWriting`
  - `TicketClosed`
  - `ChannelEdited`

## Какие действия выполняются автоматически

- Новые сообщения клиента.
- Изменения и удаление сообщений.
- Отображение активности набора текста.
- Завершение обращения с отправкой финального сообщения клиенту.
- Обновление текстов канала без ручного перезапуска.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `bot_1_token` | Да | String | `Токен Telegram-бота` / `Telegram bot tokeni` / `Telegram bot token` | `Токен доступа к вашему боту в Telegram` / `Telegram botga kirish tokeni` / `Access token for your Telegram bot` | `123456:ABC...` / `123456:ABC...` / `123456:ABC...` |
| `bot_1_channel_id` | Да | Integer | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `Канал CRM, куда будут попадать клиентские диалоги` / `Mijoz muloqotlari tushadigan CRM kanal` / `CRM channel where customer conversations are routed` | `1` / `1` / `1` |
| `bot_1_lead_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон названия нового обращения` / `Yangi murojaat nomi uchun shablon` / `Template for new case subject` | `{display_name}` / `{display_name}` / `{display_name}` |
| `bot_1_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным при создании обращения` / `Murojaat yaratilganda biriktiriladigan mas'ul xodim` / `User assigned as responsible when a case is created` | `15` / `15` / `15` |
| `telegram_secret_token` | Нет | String | `Секрет проверки Telegram` / `Telegram tekshiruv siri` / `Telegram verification secret` | `Секрет для проверки входящих webhook-запросов Telegram` / `Telegram webhook so'rovlarini tekshirish siri` / `Secret used to validate inbound Telegram webhook calls` | `secret-...` / `secret-...` / `secret-...` |
| `send_private_messages` | Нет | Boolean | `Передавать private-сообщения` / `Private xabarlarni uzatish` / `Forward private messages` | `Разрешить отправку private-сообщений CRM в Telegram` / `CRM private xabarlarini Telegramga yuborishga ruxsat` / `Allow forwarding CRM private messages to Telegram` | `false` / `false` / `false` |
| `forward_system_messages` | Нет | Boolean | `Передавать system-сообщения` / `System xabarlarni uzatish` / `Forward system messages` | `Разрешить отправку system-сообщений CRM в Telegram` / `CRM system xabarlarini Telegramga yuborishga ruxsat` / `Allow forwarding CRM system messages to Telegram` | `false` / `false` / `false` |
| `phone_request_text` | Нет | String | `Текст запроса телефона` / `Telefon so'rovi matni` / `Phone request text` | `Текст, который бот отправляет при запросе номера телефона` / `Telefon raqamini so'raganda bot yuboradigan matn` / `Text sent when bot requests phone number` | `Поделитесь номером телефона` / `Telefon raqamingizni ulashing` / `Please share your phone number` |
| `phone_share_button_text` | Нет | String | `Текст кнопки телефона` / `Telefon tugmasi matni` / `Phone button text` | `Подпись кнопки Telegram для отправки контакта` / `Kontakt yuborish uchun Telegram tugmasi matni` / `Telegram contact-share button label` | `Отправить номер / Raqamni ulashish` / `Raqamni ulashish` / `Share phone number` |

Глобальная настройка сервиса (не поле интеграции):

- `app_settings.telegram_update_mode`: `webhook` или `longpolling`.

## Порядок настройки

1. Создайте Telegram-бота и подготовьте данные для подключения.
2. Выберите в CRM канал, куда должны попадать клиентские сообщения.
3. Настройте тексты приветствия, завершения и запроса телефона в вашем стиле.
4. Подключите интеграцию и запустите проверочный диалог.
5. Убедитесь, что оператор отвечает из CRM, а клиент получает ответы в том же чате Telegram.
