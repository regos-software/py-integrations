# gpt_crm_chat_assistant

## Наименование интеграции

- Русский: `GPT-помощник оператора в CRM-чате`
- O'zbekcha: `CRM chat uchun GPT operator yordamchisi`
- English: `GPT Operator Assistant for CRM Chat`

## Краткое описание

- Русский: `Интеграция анализирует диалог и предлагает оператору готовые варианты ответа в CRM-чате.`
- O'zbekcha: `Integratsiya muloqotni tahlil qilib, operatorga CRM chat ichida tayyor javob variantlarini beradi.`
- English: `The integration analyzes conversation context and suggests ready-to-send operator replies in CRM chat.`

## Полное описание

- Русский:
  `<p>Решение помогает оператору отвечать быстрее и единообразно: при новом клиентском сообщении бот оценивает контекст и формирует подсказки ответов прямо в чате.</p><ul><li>Подсказки выводятся оператору внутри CRM через механизм быстрых ответов.</li><li>Можно задать стиль и правила коммуникации через текстовую инструкцию.</li><li>Бот может автоматически вступать в выбранные типы чатов.</li><li>При высокой уверенности бот может отправлять ответ автоматически с учетом ограничений по частоте.</li></ul>`
- O'zbekcha:
  `<p>Yechim operatorga tezroq va bir xil uslubda javob berishga yordam beradi: yangi mijoz xabari kelganda bot kontekstni baholab, chat ichida javob takliflarini chiqaradi.</p><ul><li>Takliflar CRM ichida tezkor javob ko'rinishida beriladi.</li><li>Uslub va qoidalarni matnli yo'riqnoma bilan belgilash mumkin.</li><li>Bot tanlangan chat turlariga avtomatik qo'shilishi mumkin.</li><li>Ishonch yuqori bo'lsa, javobni chastota cheklovlari bilan avtomatik yuborishi mumkin.</li></ul>`
- English:
  `<p>The solution helps operators respond faster and more consistently: when a new client message arrives, the bot evaluates context and generates reply suggestions inside chat.</p><ul><li>Suggestions are shown to operators as quick replies in CRM.</li><li>Communication style and rules can be controlled by a text instruction.</li><li>The bot can auto-join selected chat entity types.</li><li>When confidence is high, it can auto-send a reply with rate limits.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `ChatMessageAdded`

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `assistant_api_key` | Да | String | `Ключ доступа к GPT` / `GPT kirish kaliti` / `GPT access key` | `Токен для доступа к модели` / `Modelga kirish tokeni` / `Token for model access` | `sk-...` / `sk-...` / `sk-...` |
| `assistant_model` | Да | String | `Модель` / `Model` / `Model` | `Модель генерации подсказок` / `Takliflar generatsiyasi modeli` / `Model used for suggestion generation` | `gpt-4.1-mini` / `gpt-4.1-mini` / `gpt-4.1-mini` |
| `assistant_prompt` | Да | String | `Инструкция помощника` / `Yordamchi instruktsiyasi` / `Assistant instruction` | `Требования к тону, стилю и правилам ответа` / `Ohang, uslub va javob qoidalari` / `Tone, style and response rules` | `Отвечай кратко и вежливо` / `Qisqa va muloyim javob ber` / `Respond briefly and politely` |
| `assistant_auto_join_enabled` | Нет | Boolean | `Авто-вступление` / `Auto-qo'shilish` / `Auto-join` | `Разрешить автоматическое вступление бота в чат` / `Botni chatga avtomatik qo'shishga ruxsat` / `Allow bot to join chat automatically` | `true` / `true` / `true` |
| `assistant_auto_join_entities` | Нет | Enum (MultiSelect) | `Типы чатов для авто-вступления` / `Auto-qo'shilish chat turlari` / `Auto-join chat types` | `Допустимые значения: Lead, Deal, Task` / `Mumkin qiymatlar: Lead, Deal, Task` / `Allowed values: Lead, Deal, Task` | `Lead, Deal` / `Lead, Deal` / `Lead, Deal` |
| `assistant_suggestions_count` | Нет | Integer | `Количество подсказок` / `Takliflar soni` / `Suggestions count` | `Сколько вариантов ответа показать оператору (1..5)` / `Operatorga nechta javob varianti ko'rsatilsin (1..5)` / `How many reply options to show (1..5)` | `3` / `3` / `3` |
| `assistant_history_limit` | Нет | Integer | `Глубина контекста` / `Kontekst chuqurligi` / `Context depth` | `Сколько последних сообщений учитывать` / `Nechta oxirgi xabar inobatga olinsin` / `How many recent messages are used` | `20` / `20` / `20` |
| `assistant_temperature` | Нет | Float | `Вариативность текста` / `Matn variativligi` / `Text variability` | `Насколько креативно формулировать подсказки` / `Takliflar qanchalik kreativ bo'lsin` / `How creatively suggestions are phrased` | `0.3` / `0.3` / `0.3` |
| `assistant_include_staff_private` | Нет | Boolean | `Учитывать staff/private` / `staff/private ni hisobga olish` / `Include staff/private` | `Добавлять служебные private-сообщения в контекст` / `Kontekstga staff private xabarlarni qo'shish` / `Include staff private messages into context` | `false` / `false` / `false` |
| `assistant_auto_send_enabled` | Нет | Boolean | `Автоотправка при уверенности` / `Ishonchda auto-yuborish` / `Auto-send when confident` | `Автоматически отправлять ответ от бота при высокой уверенности` / `Ishonch yuqori bo'lsa bot javobni avtomatik yuboradi` / `Automatically send bot reply when confidence is high` | `false` / `false` / `false` |
| `assistant_auto_send_confidence_threshold` | Нет | Float | `Порог уверенности` / `Ishonch chegarasi` / `Confidence threshold` | `Минимальная уверенность для автоотправки (0..1)` / `Auto-yuborish uchun minimal ishonch (0..1)` / `Minimum confidence required for auto-send (0..1)` | `0.9` / `0.9` / `0.9` |
| `assistant_auto_send_max_per_chat_hour` | Нет | Integer | `Лимит автоответов в час` / `Soatlik auto-javob limiti` / `Hourly auto-reply limit` | `Максимум автоответов в одном чате за час` / `Bir chatda soatiga maksimal auto-javob` / `Maximum auto replies per chat per hour` | `3` / `3` / `3` |
| `assistant_auto_send_cooldown_sec` | Нет | Integer | `Пауза между автоответами` / `Auto-javoblar oralig'i` / `Cooldown between auto replies` | `Минимальный интервал между автоответами в одном чате` / `Bir chatda auto-javoblar orasidagi minimal interval` / `Minimum interval between auto replies in one chat` | `60` / `60` / `60` |

## Порядок настройки

1. Подключите интеграцию и заполните обязательные поля доступа к модели и инструкции.
2. При необходимости включите авто-вступление и выберите типы чатов.
3. При необходимости включите автоотправку и задайте порог уверенности и ограничения частоты.
4. Нажмите `Connect`, чтобы подписаться на событие `ChatMessageAdded`.
5. Проверьте сценарий:
   - приходит новое клиентское сообщение;
   - оператор видит подсказки;
   - при достаточной уверенности бот отправляет ответ автоматически (если включено).
