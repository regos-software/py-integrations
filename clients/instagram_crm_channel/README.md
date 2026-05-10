# Instagram-канал для поддержки клиентов

## Наименование интеграции

- Русский: `Instagram-канал для поддержки клиентов`
- O'zbekcha: `Mijozlarni qo'llab-quvvatlash uchun Instagram kanali`
- English: `Instagram Channel for Customer Support`

## Краткое описание

- Русский: `Интеграция объединяет Instagram Direct и CRM в один удобный диалог: клиент пишет в Instagram, оператор отвечает из CRM, а вся переписка хранится в обращении.`
- O'zbekcha: `Integratsiya Instagram Direct va CRM ni bitta qulay muloqotga birlashtiradi: mijoz Instagramda yozadi, operator CRM ichidan javob beradi, yozishmalar esa murojaatda saqlanadi.`
- English: `The integration connects Instagram Direct and CRM into one smooth conversation: customers message in Instagram, operators reply from CRM, and the full history stays in one case.`

## Полное описание

- Русский:
  `<p>Решение помогает команде поддержки отвечать клиентам из Instagram быстрее и аккуратнее, не переключаясь между разными окнами.</p><ul><li>Новые сообщения из Instagram Direct автоматически попадают в обращение в CRM.</li><li>Если активного обращения нет, интеграция создает клиента, обращение и чат.</li><li>Оператор отвечает в CRM, а клиент получает ответ в том же диалоге Instagram.</li><li>Имя и аватар клиента из Instagram помогают оператору быстрее понимать, с кем идет общение.</li><li>Если подключено несколько аккаунтов Instagram, система сохраняет правильный маршрут ответа для каждого диалога.</li><li>История переписки остается в CRM и доступна всей команде поддержки.</li></ul>`
- O'zbekcha:
  `<p>Yechim qo'llab-quvvatlash jamoasiga Instagram mijozlariga turli oynalar orasida almashmasdan, tez va aniq javob berishga yordam beradi.</p><ul><li>Instagram Direct dagi yangi xabarlar CRM dagi murojaatga avtomatik tushadi.</li><li>Faol murojaat topilmasa, integratsiya mijoz, murojaat va chat yaratadi.</li><li>Operator CRM ichida javob beradi, mijoz esa javobni shu Instagram dialogida oladi.</li><li>Instagramdagi mijoz ismi va avatari operatorga suhbatdoshni tezroq tanishga yordam beradi.</li><li>Bir nechta Instagram akkaunti ulangan bo'lsa, tizim har bir dialog uchun to'g'ri javob yo'nalishini saqlaydi.</li><li>Yozishmalar tarixi CRMda qoladi va qo'llab-quvvatlash jamoasi uchun ochiq bo'ladi.</li></ul>`
- English:
  `<p>The solution helps support teams reply to Instagram customers faster and more consistently without switching between tools.</p><ul><li>New Instagram Direct messages are automatically added to the CRM case.</li><li>If no active case exists, the integration creates a customer, case, and chat.</li><li>Operators reply in CRM, and customers receive replies in the same Instagram conversation.</li><li>The customer's Instagram name and avatar help operators recognize who they are talking to.</li><li>If several Instagram accounts are connected, the system keeps the correct reply route for each conversation.</li><li>The conversation history stays in CRM and remains available to the whole support team.</li></ul>`

## Список обрабатываемых вебхуков

- Instagram:
  - `messages`
- CRM:
  - `ChatMessageAdded`

## Какие действия выполняются автоматически

- Создание или переиспользование клиента по Instagram-профилю.
- Создание или переиспользование обращения для активного диалога.
- Передача входящих сообщений Instagram Direct в чат обращения.
- Отправка ответов оператора из CRM в тот же диалог Instagram.
- Обновление статуса обращения после входящих и исходящих сообщений.
- Сохранение имени и аватара клиента, если Instagram передает эти данные.
- Сохранение правильного маршрута ответа для каждой подключенной интеграции.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `instagram_pipeline_id` | Да | Integer | Нет | `Воронка CRM` / `CRM voronkasi` / `CRM pipeline` | `Воронка, в которой создаются обращения из Instagram` / `Instagram murojaatlari yaratiladigan voronka` / `Pipeline where Instagram cases are created` | `1` / `1` / `1` |
| `instagram_channel_id` | Да | Integer | Нет | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `Канал CRM, куда будут попадать диалоги из Instagram` / `Instagram muloqotlari tushadigan CRM kanal` / `CRM channel where Instagram conversations are routed` | `1` / `1` / `1` |
| `instagram_default_responsible_user_id` | Нет | Integer | Нет | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным при создании обращения` / `Murojaat yaratilganda biriktiriladigan mas'ul xodim` / `User assigned as responsible when a case is created` | `15` / `15` / `15` |
| `instagram_ticket_subject_template` | Нет | String | Нет | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон названия нового обращения` / `Yangi murojaat nomi uchun shablon` / `Template for new case subject` | `Instagram {client_name}` / `Instagram {client_name}` / `Instagram {client_name}` |
| `instagram_find_active_ticket_by_external_user` | Нет | Boolean | Нет | `Продолжать активный диалог` / `Faol muloqotni davom ettirish` / `Continue active conversation` | `Если включено, новые сообщения клиента добавляются в его активное обращение` / `Yoqilgan bo'lsa, mijozning yangi xabarlari faol murojaatiga qo'shiladi` / `When enabled, new customer messages are added to the active case` | `true` / `true` / `true` |
| `instagram_business_account_id` | Нет | String | Да | `Подключенный аккаунт Instagram` / `Ulangan Instagram akkaunti` / `Connected Instagram account` | `Служебное поле, заполняется после подключения аккаунта` / `Akkaunt ulangandan keyin avtomatik to'ldiriladigan xizmat maydoni` / `Service field filled automatically after account connection` | `` / `` / `` |
| `instagram_username` | Нет | String | Да | `Имя аккаунта Instagram` / `Instagram akkaunt nomi` / `Instagram account name` | `Служебное поле для отображения подключенного аккаунта` / `Ulangan akkauntni ko'rsatish uchun xizmat maydoni` / `Service field used to display the connected account` | `` / `` / `` |
| `instagram_access_token` | Нет | String | Да | `Доступ Instagram` / `Instagram kirish huquqi` / `Instagram access` | `Служебное поле подключения, заполняется автоматически` / `Avtomatik to'ldiriladigan ulanish xizmat maydoni` / `Service connection field filled automatically` | `` / `` / `` |
| `instagram_access_token_expires_at` | Нет | Integer | Да | `Срок действия подключения` / `Ulanish amal qilish muddati` / `Connection expiry` | `Служебное поле для контроля срока действия подключения` / `Ulanish muddati nazorati uchun xizmat maydoni` / `Service field used to track connection expiry` | `` / `` / `` |
| `instagram_authorization_status` | Нет | String | Да | `Статус подключения Instagram` / `Instagram ulanish holati` / `Instagram connection status` | `Служебное поле статуса подключения аккаунта` / `Akkaunt ulanish holati uchun xizmat maydoni` / `Service field for account connection status` | `authorized` / `authorized` / `authorized` |

Аккаунт Instagram подключается и отключается через страницу интеграции. Токены доступа не нужно вводить вручную.

## Порядок настройки

1. Выберите в CRM воронку и канал, куда должны попадать обращения из Instagram.
2. При необходимости укажите ответственного по умолчанию и шаблон темы обращения.
3. Откройте страницу интеграции и подключите профессиональный аккаунт Instagram.
4. Отправьте тестовое сообщение в Instagram Direct.
5. Убедитесь, что обращение создано в CRM, оператор отвечает из CRM, а клиент получает ответ в том же диалоге Instagram.
