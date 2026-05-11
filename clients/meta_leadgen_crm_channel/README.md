# Meta Lead Ads для CRM

## Наименование интеграции

- Русский: `Meta Lead Ads для CRM`
- O'zbekcha: `CRM uchun Meta Lead Ads`
- English: `Meta Lead Ads for CRM`

## Краткое описание

- Русский: `Интеграция автоматически передает заявки из лид-форм Meta в CRM: новые обращения не теряются, менеджеры быстрее видят контактные данные и сразу начинают работу с лидом.`
- O'zbekcha: `Integratsiya Meta lead-formalaridan kelgan arizalarni CRM ga avtomatik o'tkazadi: yangi murojaatlar yo'qolmaydi, menejerlar kontaktlarni tez ko'radi va lid bilan darhol ishlay boshlaydi.`
- English: `The integration automatically sends Meta lead form submissions to CRM: new requests are not lost, managers see contact details faster, and work with the lead starts immediately.`

## Полное описание

- Русский:
  `<p>Решение помогает отделу продаж быстро обрабатывать заявки из рекламных кампаний Meta без ручного переноса данных.</p><ul><li>Новые заявки из лид-форм Meta автоматически попадают в CRM.</li><li>Интеграция создает нового клиента или обновляет найденного по телефону, email или внешнему идентификатору.</li><li>Для каждой заявки создается или обновляется лид с данными формы, рекламной кампании и источника.</li><li>Менеджера, участников, воронку, этап и шаблон названия лида можно настроить под процесс компании.</li><li>Ответы из формы сохраняются в описании лида, а дополнительные поля можно связать с полями CRM.</li><li>Если одна и та же страница Meta подключается к другой интеграции, маршрут заявок переносится на новую интеграцию.</li></ul>`
- O'zbekcha:
  `<p>Yechim savdo bo'limiga Meta reklama kampaniyalaridan kelgan arizalarni ma'lumotlarni qo'lda ko'chirmasdan tez qayta ishlashga yordam beradi.</p><ul><li>Meta lead-formalaridan kelgan yangi arizalar CRM ga avtomatik tushadi.</li><li>Integratsiya telefon, email yoki tashqi identifikator bo'yicha mijozni yaratadi yoki topilgan mijozni yangilaydi.</li><li>Har bir ariza uchun forma, reklama kampaniyasi va manba ma'lumotlari bilan lid yaratiladi yoki yangilanadi.</li><li>Menejer, ishtirokchilar, voronka, bosqich va lid nomi shablonini kompaniya jarayoniga moslash mumkin.</li><li>Forma javoblari lid tavsifida saqlanadi, qo'shimcha maydonlarni esa CRM maydonlariga bog'lash mumkin.</li><li>Bitta Meta sahifa boshqa integratsiyaga ulanganda, arizalar yo'nalishi yangi integratsiyaga o'tkaziladi.</li></ul>`
- English:
  `<p>The solution helps sales teams process Meta campaign submissions quickly without copying data by hand.</p><ul><li>New Meta lead form submissions are automatically delivered to CRM.</li><li>The integration creates a new customer or updates a matched one by phone, email, or external identifier.</li><li>Each submission creates or updates a lead with form, campaign, and source details.</li><li>The responsible manager, participants, pipeline, stage, and lead title template can be adjusted to the company's process.</li><li>Form answers are saved in the lead description, and extra answers can be mapped to CRM fields.</li><li>If the same Meta Page is connected to another integration, the lead route is moved to the new integration.</li></ul>`

## Список обрабатываемых вебхуков

- Meta:
  - `leadgen`
- CRM:
  - Нет входящих CRM-вебхуков.

## Какие действия выполняются автоматически

- Получение заявок из лид-форм Meta.
- Получение полной информации по заявке из Meta.
- Создание или обновление клиента в CRM.
- Создание или обновление лида в CRM без дублей по одной и той же заявке.
- Заполнение стандартных полей клиента и лида, если эти данные есть в форме.
- Сохранение ответов формы в описании лида.
- Перенос дополнительных ответов формы в поля CRM по настроенной карте полей.
- Назначение ответственного, участников, воронки и этапа лида по настройкам интеграции.
- Сохранение правильного маршрута заявок для каждой подключенной интеграции.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `meta_page_id` | Нет | String | Нет | `ID страницы Meta` / `Meta sahifa ID` / `Meta Page ID` | `Страница, с которой нужно получать заявки; можно оставить пустым, если при подключении доступна одна страница` / `Arizalar olinadigan sahifa; ulash vaqtida bitta sahifa mavjud bo'lsa, bo'sh qoldirish mumkin` / `Page to receive submissions from; can be empty when only one Page is available during connection` | `1234567890` / `1234567890` / `1234567890` |
| `meta_lead_pipeline_id` | Нет | Integer | Нет | `Воронка лида` / `Lid voronkasi` / `Lead pipeline` | `Воронка CRM, куда будут попадать лиды из Meta` / `Meta lidlari tushadigan CRM voronkasi` / `CRM pipeline where Meta leads are created` | `1` / `1` / `1` |
| `meta_lead_stage_id` | Нет | Integer | Нет | `Этап лида` / `Lid bosqichi` / `Lead stage` | `Этап CRM, назначаемый новым лидам из Meta` / `Meta lidlariga beriladigan CRM bosqichi` / `CRM stage assigned to new Meta leads` | `3` / `3` / `3` |
| `meta_default_responsible_user_id` | Нет | Integer | Нет | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Сотрудник, назначаемый ответственным за новый лид` / `Yangi lid uchun mas'ul bo'ladigan xodim` / `User assigned as responsible for a new lead` | `15` / `15` / `15` |
| `meta_participant_user_ids` | Нет | String | Нет | `Участники лида` / `Lid ishtirokchilari` / `Lead participants` | `Список сотрудников через запятую или JSON-массив` / `Xodimlar ro'yxati vergul bilan yoki JSON massiv` / `Comma-separated user list or JSON array` | `15,24` / `15,24` / `15,24` |
| `meta_lead_title_template` | Нет | String | Нет | `Шаблон названия лида` / `Lid nomi shabloni` / `Lead title template` | `Шаблон названия нового лида` / `Yangi lid nomi uchun shablon` / `Template for new lead title` | `Meta Lead {leadgen_id}` / `Meta Lead {leadgen_id}` / `Meta Lead {leadgen_id}` |
| `meta_client_field_mapping` | Нет | JSON Object | Нет | `Поля клиента` / `Mijoz maydonlari` / `Customer fields` | `Связь ответов формы с дополнительными полями клиента CRM` / `Forma javoblarini CRM mijoz qo'shimcha maydonlariga bog'lash` / `Maps form answers to CRM customer custom fields` | `{"city":"field_city"}` / `{"city":"field_city"}` / `{"city":"field_city"}` |
| `meta_lead_field_mapping` | Нет | JSON Object | Нет | `Поля лида` / `Lid maydonlari` / `Lead fields` | `Связь ответов формы с дополнительными полями лида CRM` / `Forma javoblarini CRM lid qo'shimcha maydonlariga bog'lash` / `Maps form answers to CRM lead custom fields` | `{"leadgen_id":"field_external_source_id"}` / `{"leadgen_id":"field_external_source_id"}` / `{"leadgen_id":"field_external_source_id"}` |
| `meta_page_name` | Нет | String | Да | `Название страницы Meta` / `Meta sahifa nomi` / `Meta Page name` | `Служебное поле для отображения подключенной страницы` / `Ulangan sahifani ko'rsatish uchun xizmat maydoni` / `Service field used to display the connected Page` | `` / `` / `` |
| `meta_page_access_token` | Нет | String | Да | `Доступ к странице Meta` / `Meta sahifa kirish huquqi` / `Meta Page access` | `Служебное поле подключения, заполняется автоматически` / `Avtomatik to'ldiriladigan ulanish xizmat maydoni` / `Service connection field filled automatically` | `` / `` / `` |
| `meta_access_token_expires_at` | Нет | Integer | Да | `Срок действия подключения` / `Ulanish amal qilish muddati` / `Connection expiry` | `Служебное поле для контроля срока действия подключения` / `Ulanish muddati nazorati uchun xizmat maydoni` / `Service field used to track connection expiry` | `` / `` / `` |
| `meta_authorization_url` | Нет | String | Да | `Ссылка подключения Meta` / `Meta ulash havolasi` / `Meta connection link` | `Временная служебная ссылка для подключения страницы` / `Sahifani ulash uchun vaqtinchalik xizmat havolasi` / `Temporary service link for Page connection` | `` / `` / `` |
| `meta_authorization_url_generated_at` | Нет | Integer | Да | `Время создания ссылки` / `Havola yaratilgan vaqt` / `Connection link time` | `Служебное поле срока действия ссылки подключения` / `Ulash havolasi muddati uchun xizmat maydoni` / `Service field used to expire the connection link` | `` / `` / `` |
| `meta_authorization_status` | Нет | String | Да | `Статус подключения Meta` / `Meta ulanish holati` / `Meta connection status` | `Служебное поле статуса подключения страницы` / `Sahifa ulanish holati uchun xizmat maydoni` / `Service field for Page connection status` | `authorized` / `authorized` / `authorized` |
| `meta_authorized` | Нет | Boolean | Да | `Подключение подтверждено` / `Ulanish tasdiqlangan` / `Connection confirmed` | `Служебное поле совместимости статуса подключения` / `Ulanish holati mosligi uchun xizmat maydoni` / `Service compatibility field for connection status` | `true` / `true` / `true` |

Страница Meta подключается и отключается через страницу интеграции. Токены доступа не нужно вводить вручную.

## Порядок настройки

1. Выберите в CRM воронку, этап и ответственного, если лиды должны попадать в конкретный процесс.
2. При необходимости укажите ID страницы Meta, если у пользователя при подключении доступно несколько страниц.
3. Настройте карту полей, если ответы формы нужно сохранять в дополнительные поля CRM.
4. Откройте страницу интеграции и подключите страницу Meta.
5. Отправьте тестовую заявку из лид-формы.
6. Убедитесь, что клиент и лид созданы или обновлены в CRM.
