# EDO Didox

## Наименование интеграции

- Русский: `EDO Didox`
- O'zbekcha: `EDO Didox`
- English: `EDO Didox`

## Краткое описание

- Русский: `Интеграция с Didox позволяет организовать обмен электронными документами прямо в Сервисе REGOS: входящие документы можно загрузить без ручного переноса данных, а исходящие счета-фактуры подготовить в Didox для дальнейшей проверки и подписания.`
- O'zbekcha: `Didox integratsiyasi REGOS servisida elektron hujjatlar almashinuvini tashkil qilishga yordam beradi: kiruvchi hujjatlar qo'lda ko'chirmasdan yuklanadi, chiquvchi hisob-fakturalar esa Didox da tekshirish va imzolash uchun tayyorlanadi.`
- English: `The Didox integration helps organize electronic document exchange in the REGOS service: incoming documents can be imported without manual copying, and outgoing invoices can be prepared in Didox for review and signing.`

## Полное описание

- Русский:
  `<p>Интеграция с Didox позволяет организовать обмен электронными документами прямо в Сервисе REGOS без ручной загрузки и передачи данных.</p><ul><li>Входящие документы из Didox загружаются автоматически.</li><li>Контрагенты, договоры и строки документа создаются или сопоставляются автоматически.</li><li>Повторная загрузка одного и того же документа не создает дубль.</li><li>Исходящие счета-фактуры создаются в Didox как черновики для дальнейшей проверки и подписания.</li><li>Статус документа обновляется после успешной обработки или ошибки.</li><li>Обмен выполняется в фоне и не мешает ежедневной работе с документами.</li></ul>`
- O'zbekcha:
  `<p>Didox integratsiyasi REGOS servisida elektron hujjatlar almashinuvini qo'lda yuklash va uzatishsiz tashkil qilishga yordam beradi.</p><ul><li>Didox dan kiruvchi hujjatlar avtomatik yuklanadi.</li><li>Kontragentlar, shartnomalar va hujjat satrlari avtomatik yaratiladi yoki moslashtiriladi.</li><li>Bitta hujjat qayta yuklanganda dubl yaratilmaydi.</li><li>Chiquvchi hisob-fakturalar Didox da tekshirish va imzolash uchun qoralama sifatida yaratiladi.</li><li>Hujjat holati muvaffaqiyatli qayta ishlangandan yoki xatodan keyin yangilanadi.</li><li>Almashinuv fonda bajariladi va hujjatlar bilan kundalik ishlashga xalaqit bermaydi.</li></ul>`
- English:
  `<p>The Didox integration helps organize electronic document exchange in the REGOS service without manual upload or data transfer.</p><ul><li>Incoming documents from Didox are imported automatically.</li><li>Counterparties, contracts, and document rows are created or matched automatically.</li><li>Re-importing the same document does not create a duplicate.</li><li>Outgoing invoices are created in Didox as drafts for review and signing.</li><li>Document status is updated after successful processing or an error.</li><li>Exchange runs in the background and does not interrupt daily document work.</li></ul>`

## Какие действия выполняются автоматически

- Получение списка входящих документов из Didox.
- Загрузка содержимого выбранного документа в Сервис REGOS.
- Создание или переиспользование контрагента и договора.
- Сопоставление товаров по ИКПУ, штрихкоду или их связке.
- Создание строк счета-фактуры в Сервисе REGOS.
- Создание черновика исходящего счета-фактуры в Didox.
- Обновление статуса документа после успешной обработки или ошибки.

## Список обрабатываемых вебхуков

- Didox:
  - Входящие вебхуки не используются.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `DIDOX_PASSWORD` | Да | String | Да | `Пароль Didox` / `Didox paroli` / `Didox password` | `Служебный пароль аккаунта, от имени которого выполняется обмен документами` / `Hujjat almashinuvi bajariladigan xizmat akkaunti paroli` / `Service account password used for document exchange` | `` / `` / `` |
| `DIDOX_LOCALE` | Нет | String | Да | `Язык Didox API` / `Didox API tili` / `Didox API locale` | `Язык ответов Didox` / `Didox javoblari tili` / `Didox response language` | `ru` / `ru` / `ru` |

Эти данные заполняются администратором при подключении обмена с Didox. Обычному пользователю не нужно вводить их при ежедневной работе с документами.

Партнерский токен Didox задается один раз на уровне сервиса через env `DIDOX_PARTNER_TOKEN`. ИНН компании берется из выбранной фирмы REGOS.

## Порядок настройки

1. Убедитесь, что у компании есть активный аккаунт Didox и партнерский токен.
2. Заполните служебные данные подключения Didox в настройках интеграции.
3. Проверьте подключение для нужного предприятия.
4. Загрузите список входящих документов и выберите документ для импорта.
5. Убедитесь, что контрагент, договор и строки счета-фактуры корректно появились в Сервисе REGOS.
6. Для исходящего документа выполните отправку из Сервиса REGOS и проверьте созданный черновик в Didox.
