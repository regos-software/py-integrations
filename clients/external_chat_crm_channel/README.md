# Единый онлайн-чат для клиентов

## Наименование интеграции

- Русский: `Единый онлайн-чат для клиентов`
- O'zbekcha: `Mijozlar uchun yagona onlayn chat`
- English: `Unified Online Chat for Customers`

## Краткое описание

- Русский: `Удобный онлайн-чат помогает быстро отвечать клиентам, повышать лояльность и делать сервис заметно ближе.`
- O'zbekcha: `Qulay onlayn chat mijozlarga tez javob berishga, sodiqlikni oshirishga va xizmatni yanada yaqin qilishga yordam beradi.`
- English: `A convenient online chat helps you reply faster, increase customer loyalty, and make service feel closer.`

## Полное описание

- Русский:
  `<p>Этот чат помогает выстроить более теплый и современный сервис, где клиенту легко начать разговор и быстро получить помощь.</p><ul><li>Первое обращение начинается без лишних шагов и ожиданий.</li><li>Команда отвечает быстрее и увереннее, сохраняя единый стиль общения.</li><li>Повторным клиентам проще продолжать диалог, не объясняя все заново.</li><li>Качество сервиса становится прозрачнее благодаря цельной истории общения.</li><li>Вид чата можно адаптировать под фирменный стиль компании.</li><li>Итог — выше удовлетворенность клиентов и больше доверия к бренду.</li></ul>`
- O'zbekcha:
  `<p>Ushbu chat xizmatingizni yanada zamonaviy va samimiy qiladi: mijoz suhbatni oson boshlaydi va tez yordam oladi.</p><ul><li>Birinchi murojaat ortiqcha qadamlar va kutishlarsiz boshlanadi.</li><li>Jamoa tezroq va ishonchliroq javob beradi, muloqot uslubi bir xil qoladi.</li><li>Qayta murojaat qilgan mijozga suhbatni davom ettirish oson bo'ladi.</li><li>Yaxlit yozishma tarixi xizmat sifati ustidan nazoratni kuchaytiradi.</li><li>Chat ko'rinishini brendingizga moslashtirish mumkin.</li><li>Natijada mijoz mamnunligi va brendga ishonch oshadi.</li></ul>`
- English:
  `<p>This chat makes your customer service feel modern and approachable, so people can start a conversation easily and get help quickly.</p><ul><li>New conversations begin smoothly, without unnecessary friction.</li><li>Your team responds faster while keeping a consistent tone of communication.</li><li>Returning customers can continue the dialogue with less effort.</li><li>A complete conversation timeline improves service transparency.</li><li>The chat look can be aligned with your brand style.</li><li>The result is higher satisfaction and stronger trust in your brand.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `ChatMessageAdded`
  - `ChatMessageEdited`
  - `ChatMessageDeleted`
  - `TicketStatusSet`
  - `TicketClosed`

## Какие действия выполняются автоматически

- Создание или переиспользование клиента по `external_id`.
- Создание или переиспользование обращения по `external_dialog_id`.
- Автоматическая отправка `start_message` из CRM-канала при создании нового обращения.
- Публикация сообщений посетителя в чат обращения и отметка прочитанности (`mark_read`).
- Применение обязательных полей профиля при открытии чата (если включены в настройках).

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `chat_channel_id` | Да | Integer | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `Канал CRM, куда создаются и маршрутизируются внешние чаты` / `Tashqi chatlar yaratiladigan va yo'naltiriladigan CRM kanal` / `CRM channel where external chats are created and routed` | `1` / `1` / `1` |
| `ticket_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон заголовка обращения. Поддерживаются переменные {channel_name}, {visitor_id}, {display_name}, {current_date}` / `Murojaat sarlavhasi shabloni. {channel_name}, {visitor_id}, {display_name}, {current_date} o'zgaruvchilari qo'llab-quvvatlanadi` / `Template for case subject. Supports {channel_name}, {visitor_id}, {display_name}, {current_date}` | `{channel_name} {display_name}` / `{channel_name} {display_name}` / `{channel_name} {display_name}` |
| `default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным при создании нового обращения` / `Yangi murojaat yaratilganda biriktiriladigan mas'ul xodim` / `User assigned as responsible when a new case is created` | `15` / `15` / `15` |
| `chat_title` | Нет | String | `Заголовок чата` / `Chat sarlavhasi` / `Chat title` | `Заголовок внешнего чата в UI. Если не задан, используется название CRM-канала` / `UI dagi tashqi chat sarlavhasi. Kiritilmasa CRM kanal nomi ishlatiladi` / `External chat title in UI. If empty, CRM channel name is used` | `Support Chat` / `Support Chat` / `Support Chat` |
| `chat_css_url` | Нет | String | `Ссылка на CSS чат-интерфейса` / `Chat CSS manzili` / `Chat CSS URL` | `Если задано, внешний чат подключает CSS по ссылке и не использует встроенный стандартный стиль` / `Kiritilsa, tashqi chat CSS ni ushbu manzildan yuklaydi va standart ichki stil ishlatilmaydi` / `If set, external chat loads CSS from this URL and does not use built-in default style` | `/assets/chat.css` / `/assets/chat.css` / `/assets/chat.css` |
| `require_name_on_open` | Нет | Boolean | `Обязательное имя` / `Ism majburiy` / `Require name` | `Если true, поле имени обязательно при открытии чата` / `true bo'lsa, chat ochilganda ism maydoni majburiy bo'ladi` / `If true, name is required when opening chat` | `false` / `false` / `false` |
| `require_phone_on_open` | Нет | Boolean | `Обязательный телефон` / `Telefon majburiy` / `Require phone` | `Если true, поле телефона обязательно при открытии чата` / `true bo'lsa, chat ochilganda telefon maydoni majburiy bo'ladi` / `If true, phone is required when opening chat` | `false` / `false` / `false` |
| `require_email_on_open` | Нет | Boolean | `Обязательный email` / `Email majburiy` / `Require email` | `Если true, поле email обязательно при открытии чата` / `true bo'lsa, chat ochilganda email maydoni majburiy bo'ladi` / `If true, email is required when opening chat` | `false` / `false` / `false` |

Сообщения канала (не поля интеграции):

- `Channel.start_message` — используется как автоматическое приветствие при создании нового обращения.

## Внешние API-действия для UI

- `init` — инициализация сессии, создание/поиск клиента и обращения, загрузка истории.
- `history` — получение истории сообщений.
- `send_message` — отправка сообщения посетителя в CRM.
- `mark_read` — отметка чата как прочитанного.

## Порядок настройки

1. Создайте/выберите CRM-канал для внешних чатов и задайте в нем `start_message` (при необходимости).
2. Укажите в настройках интеграции обязательный `chat_channel_id`.
3. При необходимости задайте `ticket_subject_template`, `default_responsible_user_id` и `chat_title`.
4. При необходимости настройте внешний вид через `chat_css_url`.
5. Включите обязательные поля профиля (`require_name_on_open`, `require_phone_on_open`, `require_email_on_open`) по требованиям процесса.
6. Откройте UI интеграции и проверьте тестовый диалог: создание обращения, доставку сообщений и отображение истории.

## UI Localization

- Built-in locales: `ru`, `uz`, `en` (separate files in `clients/external_chat_crm_channel/i18n/`).
- Language switcher is available in chat header.
- Automatic language from URL query params: `lang`, `locale`, `language`, `hl`.
