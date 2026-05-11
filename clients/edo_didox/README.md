# EDO Didox

## Наименование интеграции

- Русский: `EDO Didox`
- O'zbekcha: `EDO Didox`
- English: `EDO Didox`

## Краткое описание

- Русский: `Интеграция помогает работать с электронными документами Didox прямо из CRM: входящие документы можно загрузить в CRM, а исходящие счета-фактуры подготовить в Didox без ручного переноса данных.`
- O'zbekcha: `Integratsiya Didox elektron hujjatlari bilan CRM ichida ishlashga yordam beradi: kiruvchi hujjatlar CRM ga yuklanadi, chiquvchi hisob-fakturalar esa Didox da qo'lda ko'chirmasdan tayyorlanadi.`
- English: `The integration helps teams work with Didox electronic documents directly from CRM: incoming documents can be imported into CRM, and outgoing invoices can be prepared in Didox without manual copying.`

## Полное описание

- Русский:
  `<p>Решение сокращает ручную работу с электронным документооборотом и помогает держать документы в CRM рядом с клиентами, договорами и товарами.</p><ul><li>Входящие документы из Didox загружаются в CRM.</li><li>Контрагенты, договоры и строки документа создаются или сопоставляются автоматически.</li><li>Повторная загрузка одного и того же документа не создает дубль.</li><li>Исходящие счета-фактуры из CRM создаются в Didox как черновики для дальнейшей проверки и подписания.</li><li>Статус документа обновляется в CRM, чтобы менеджеры видели результат обработки.</li><li>Работа выполняется в фоне, поэтому пользователь может продолжать работу в CRM.</li></ul>`
- O'zbekcha:
  `<p>Yechim elektron hujjat aylanishidagi qo'l mehnatini kamaytiradi va hujjatlarni CRM ichida mijozlar, shartnomalar va tovarlar bilan bir joyda saqlashga yordam beradi.</p><ul><li>Didox dan kiruvchi hujjatlar CRM ga yuklanadi.</li><li>Kontragentlar, shartnomalar va hujjat satrlari avtomatik yaratiladi yoki moslashtiriladi.</li><li>Bitta hujjat qayta yuklanganda dubl yaratilmaydi.</li><li>CRM dagi chiquvchi hisob-fakturalar Didox da tekshirish va imzolash uchun qoralama sifatida yaratiladi.</li><li>Hujjat holati CRM da yangilanadi, menejerlar qayta ishlash natijasini ko'radi.</li><li>Jarayon fonda bajariladi, shuning uchun foydalanuvchi CRM da ishini davom ettirishi mumkin.</li></ul>`
- English:
  `<p>The solution reduces manual work in electronic document exchange and keeps documents in CRM next to customers, contracts, and items.</p><ul><li>Incoming documents from Didox are imported into CRM.</li><li>Counterparties, contracts, and document rows are created or matched automatically.</li><li>Re-importing the same document does not create a duplicate.</li><li>Outgoing CRM invoices are created in Didox as drafts for review and signing.</li><li>Document status is updated in CRM so managers can see the processing result.</li><li>Processing runs in the background, so users can keep working in CRM.</li></ul>`

## Какие действия выполняются автоматически

- Получение списка входящих документов из Didox.
- Загрузка содержимого выбранного документа в CRM.
- Создание или переиспользование контрагента и договора.
- Сопоставление товаров по ИКПУ, штрихкоду или их связке.
- Создание строк счета-фактуры в CRM.
- Создание черновика исходящего счета-фактуры в Didox.
- Обновление статуса документа после успешной обработки или ошибки.

## Список обрабатываемых вебхуков

- Didox:
  - Входящие вебхуки не используются.
- CRM:
  - Входящие CRM-вебхуки не используются.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `DIDOX_PARTNER_TOKEN` | Да | String | Да | `Партнерский токен Didox` / `Didox hamkor tokeni` / `Didox partner token` | `Служебный токен партнера Didox` / `Didox hamkorining xizmat tokeni` / `Service partner token issued by Didox` | `` / `` / `` |
| `DIDOX_PASSWORD` | Да | String | Да | `Пароль Didox` / `Didox paroli` / `Didox password` | `Служебный пароль аккаунта, от имени которого выполняется обмен документами` / `Hujjat almashinuvi bajariladigan xizmat akkaunti paroli` / `Service account password used for document exchange` | `` / `` / `` |
| `DIDOX_LOGIN_TAX_ID` | Нет | String | Да | `ИНН пользователя Didox` / `Didox foydalanuvchi STIR` / `Didox user tax ID` | `ИНН пользователя для первичного входа. Если не задан, используется ИНН компании` / `Kiritilmasa, kompaniya STIR ishlatiladi` / `User tax ID for login. If empty, company tax ID is used` | `` / `` / `` |
| `DIDOX_COMPANY_TAX_ID` | Нет | String | Да | `ИНН компании Didox` / `Didox kompaniya STIR` / `Didox company tax ID` | `ИНН компании для обмена документами. Если не задан, используется ИНН фирмы CRM` / `Kiritilmasa, CRM firma STIR ishlatiladi` / `Company tax ID for document exchange. If empty, CRM firm tax ID is used` | `` / `` / `` |
| `DIDOX_BASE_URL` | Нет | String | Да | `Адрес Didox API` / `Didox API manzili` / `Didox API URL` | `Адрес API Didox. Обычно заполняется только для тестового контура` / `Odatda faqat test muhiti uchun to'ldiriladi` / `Didox API endpoint. Usually set only for test environments` | `https://api-partners.didox.uz` / `https://api-partners.didox.uz` / `https://api-partners.didox.uz` |
| `DIDOX_LOCALE` | Нет | String | Да | `Язык Didox API` / `Didox API tili` / `Didox API locale` | `Язык ответов Didox` / `Didox javoblari tili` / `Didox response language` | `ru` / `ru` / `ru` |
| `DIDOX_DOCUMENT_TYPES` | Нет | String | Да | `Типы документов Didox` / `Didox hujjat turlari` / `Didox document types` | `Список типов документов для загрузки через запятую` / `Yuklash uchun hujjat turlari ro'yxati` / `Comma-separated document types to load` | `002,005,008,023` / `002,005,008,023` / `002,005,008,023` |

Эти данные заполняются администратором при подключении обмена с Didox. Обычному пользователю не нужно вводить их при ежедневной работе с документами.

## Порядок настройки

1. Убедитесь, что у компании есть активный аккаунт Didox и партнерский токен.
2. Заполните служебные данные подключения Didox в настройках интеграции.
3. Проверьте подключение для нужного предприятия CRM.
4. Загрузите список входящих документов и выберите документ для импорта.
5. Убедитесь, что контрагент, договор и строки счета-фактуры корректно появились в CRM.
6. Для исходящего документа выполните отправку из CRM и проверьте созданный черновик в Didox.
