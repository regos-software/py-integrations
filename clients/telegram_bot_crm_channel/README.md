# telegram_bot_crm_channel

## Наименование интеграции

- Русский: `Единый чат Telegram в CRM`
- O'zbekcha: `Telegram chatlarini CRMda birlashtirish`
- English: `Unified Telegram Chat in CRM`

## Краткое описание

- Русский: `Объединяет переписку с клиентами из Telegram в CRM, чтобы команда отвечала быстрее и не теряла обращения.`
- O'zbekcha: `Telegramdagi mijoz yozishmalarini CRMga olib kirib, javoblarni tezlashtiradi va murojaatlarni yo'qotmaydi.`
- English: `Brings Telegram customer conversations into CRM so teams respond faster and no request is missed.`

## Полное описание

- Русский:
  `<p>Интеграция переносит диалог с клиентом из Telegram в CRM и сохраняет всю переписку в одной ленте. Менеджеры отвечают из CRM, а клиент получает сообщения в привычном мессенджере.</p><ul><li>Входящие сообщения автоматически попадают в карточку обращения.</li><li>Ответы команды из CRM отправляются клиенту в Telegram.</li><li>История сообщений и файлов хранится в одном месте.</li><li>При необходимости можно аккуратно запрашивать и сохранять номер телефона клиента.</li></ul><p>Решение подходит компаниям, которым важны скорость ответа, прозрачность коммуникаций и контроль качества сервиса.</p>`
- O'zbekcha:
  `<p>Integratsiya Telegramdagi mijoz muloqotini CRMga olib kiradi va barcha yozishmalarni bitta lentada saqlaydi. Menejerlar CRMdan javob beradi, mijoz esa xabarni odatdagi messenjerdan oladi.</p><ul><li>Kiruvchi xabarlar avtomatik ravishda murojaat kartasiga tushadi.</li><li>Jamoa CRMdan javob yuboradi, mijoz Telegramda qabul qiladi.</li><li>Xabarlar va fayllar tarixi bitta joyda saqlanadi.</li><li>Zarurat bo'lsa, mijoz telefon raqamini muloyim so'rab saqlash mumkin.</li></ul><p>Yechim tezkor javob, shaffof aloqa va xizmat sifatini nazorat qilish muhim bo'lgan jamoalar uchun mos.</p>`
- English:
  `<p>The integration brings Telegram customer conversations into CRM and keeps the full message history in one timeline. Managers reply from CRM, while customers continue chatting in Telegram.</p><ul><li>Incoming messages are added to the request card automatically.</li><li>Team replies from CRM are delivered to Telegram.</li><li>Messages and files stay in one place.</li><li>If needed, customer phone numbers can be requested and saved during the conversation.</li></ul><p>This is ideal for teams that need faster response times, transparent communication, and better service control.</p>`

## Список обрабатываемых вебхуков

- CRM:
  - `ChatMessageAdded`
  - `ChatMessageEdited`
  - `ChatMessageDeleted`
  - `ChatWriting`
  - `LeadClosed`
- Telegram update types:
  - `message`
  - `business_message`
  - `edited_message`
  - `edited_business_message`
  - `deleted_business_messages`

## Настройки интеграции

| Ключ | Обязательно | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `bot_1_token` | Да | String | `Доступ к Telegram-боту` / `Telegram botga kirish` / `Telegram bot access` | `Ключ доступа для работы диалогов` / `Suhbatlar ishlashi uchun kirish kaliti` / `Access key to run conversations` | `Вставьте токен` / `Tokenni kiriting` / `Paste token` |
| `bot_1_pipeline_id` | Да | Integer | `Воронка обращений` / `Murojaatlar voronkasi` / `Leads pipeline` | `Куда попадут новые обращения` / `Yangi murojaatlar qayerga tushadi` / `Where new requests will appear` | `Например: 12` / `Masalan: 12` / `Example: 12` |
| `bot_1_channel_id` | Да | Integer | `Канал общения` / `Muloqot kanali` / `Communication channel` | `Канал CRM для переписки` / `Yozishmalar uchun CRM kanali` / `CRM channel for conversation` | `Например: 5` / `Masalan: 5` / `Example: 5` |
| `bot_1_lead_subject_template` | Нет | String | `Название обращения` / `Murojaat nomi` / `Lead title` | `Шаблон заголовка нового обращения` / `Yangi murojaat sarlavhasi shabloni` / `Template for new lead title` | `{display_name}` / `{display_name}` / `{display_name}` |
| `bot_1_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default owner` | `Кто назначается при создании обращения` / `Murojaat yaratilganda kim biriktiriladi` / `Who is assigned when a lead is created` | `Например: 101` / `Masalan: 101` / `Example: 101` |
| `telegram_secret_token` | Нет | String | `Защита входящих событий` / `Kiruvchi hodisalar himoyasi` / `Inbound event protection` | `Дополнительная проверка подлинности запросов` / `So'rovlarni qo'shimcha tekshirish` / `Extra request authenticity check` | `Введите секрет` / `Maxfiy qiymatni kiriting` / `Enter secret` |
| `lead_dedupe_ttl_sec` | Нет | Integer | `Защита от дублей` / `Dublikatdan himoya` / `Duplicate protection` | `Период подавления повторов в секундах` / `Takrorlarni bloklash muddati (sekund)` / `Duplicate suppression window in seconds` | `21600` / `21600` / `21600` |
| `state_ttl_sec` | Нет | Integer | `Срок хранения состояния` / `Holat saqlash muddati` / `State retention` | `Как долго хранить служебное состояние диалога` / `Suhbat holatini qancha saqlash` / `How long dialog state is retained` | `21600` / `21600` / `21600` |
| `send_private_messages` | Нет | Boolean | `Отправлять приватные сообщения` / `Private xabarlarni yuborish` / `Send private messages` | `Передавать ли приватные сообщения из CRM в Telegram` / `CRMdagi private xabarlarni Telegramga uzatish` / `Forward private CRM messages to Telegram` | `false` / `false` / `false` |
| `forward_system_messages` | Нет | Boolean | `Отправлять системные сообщения` / `Tizim xabarlarini yuborish` / `Forward system messages` | `Передавать ли системные сообщения из CRM в Telegram` / `CRM tizim xabarlarini Telegramga uzatish` / `Forward CRM system messages to Telegram` | `false` / `false` / `false` |
| `lead_closed_message_template` | Нет | String | `Сообщение о завершении` / `Yakunlash xabari` / `Closure message` | `Текст для клиента при закрытии обращения` / `Murojaat yopilganda mijozga matn` / `Client text when lead is closed` | `Спасибо за обращение` / `Murojaatingiz uchun rahmat` / `Thank you for contacting us` |
| `phone_request_text` | Нет | String | `Запрос номера телефона` / `Telefon raqamini so'rash` / `Phone request prompt` | `Текст, которым попросим клиента отправить номер` / `Mijozdan raqam so'rash matni` / `Text used to request a phone number` | `Пожалуйста, отправьте номер` / `Iltimos, raqamingizni yuboring` / `Please share your number` |
| `phone_share_button_text` | Нет | String | `Текст кнопки отправки номера` / `Raqam yuborish tugmasi` / `Phone share button` | `Подпись кнопки для отправки контакта` / `Kontakt yuborish tugmasi yozuvi` / `Caption for contact share button` | `Поделиться номером` / `Raqamni ulashish` / `Share phone number` |

## Дополнительно (глобальная настройка сервиса)

- `app_settings.telegram_update_mode` (Enum: `webhook` или `longpolling`) задаётся на уровне сервиса, а не в настройках конкретного подключения.

## Порядок настройки внешней системы (Telegram)

1. Создайте бота в `@BotFather` и получите токен.
2. Запустите бота (`/start`) от тестового аккаунта, чтобы бот мог отправлять ответы.
3. В CRM заполните обязательные настройки: `bot_1_token`, `bot_1_pipeline_id`, `bot_1_channel_id`.
4. При необходимости заполните дополнительные настройки (тексты, режимы пересылки, защита входящих событий).
5. Выполните подключение интеграции (`Connect`).
6. Проверьте сценарий:
   - сообщение из Telegram появляется в CRM;
   - ответ из CRM уходит в Telegram;
   - редактирование/удаление сообщений и отправка файлов работают корректно.
