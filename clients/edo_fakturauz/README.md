# EDO Faktura.uz

## Наименование интеграции

- Русский: `EDO Faktura.uz`
- O'zbekcha: `EDO Faktura.uz`
- English: `EDO Faktura.uz`

## Краткое описание

- Русский: `Интеграция помогает работать с электронными счетами-фактурами Faktura.uz прямо из CRM: входящие документы можно загрузить в CRM, а исходящие отправить контрагенту без ручного переноса данных.`
- O'zbekcha: `Integratsiya Faktura.uz elektron hisob-fakturalari bilan CRM ichida ishlashga yordam beradi: kiruvchi hujjatlar CRM ga yuklanadi, chiquvchi hujjatlar esa qo'lda ko'chirmasdan kontragentga yuboriladi.`
- English: `The integration helps teams work with Faktura.uz electronic invoices directly from CRM: incoming documents can be imported into CRM, and outgoing documents can be sent to counterparties without manual copying.`

## Полное описание

- Русский:
  `<p>Решение сокращает ручную работу с электронным документооборотом и помогает держать документы в CRM рядом с клиентами, договорами и товарами.</p><ul><li>Входящие счета-фактуры и акты из Faktura.uz загружаются в CRM.</li><li>Контрагенты, договоры и строки документа создаются или сопоставляются автоматически.</li><li>Повторная загрузка одного и того же документа не создает дубль.</li><li>Исходящие счета-фактуры из CRM отправляются в Faktura.uz с правильными суммами и НДС.</li><li>Статус документа обновляется в CRM, чтобы менеджеры видели результат обработки.</li><li>Работа выполняется в фоне, поэтому пользователь может продолжать работу в CRM.</li></ul>`
- O'zbekcha:
  `<p>Yechim elektron hujjat aylanishidagi qo'l mehnatini kamaytiradi va hujjatlarni CRM ichida mijozlar, shartnomalar va tovarlar bilan bir joyda saqlashga yordam beradi.</p><ul><li>Faktura.uz dan kiruvchi hisob-fakturalar va dalolatnomalar CRM ga yuklanadi.</li><li>Kontragentlar, shartnomalar va hujjat satrlari avtomatik yaratiladi yoki moslashtiriladi.</li><li>Bitta hujjat qayta yuklanganda dubl yaratilmaydi.</li><li>CRM dagi chiquvchi hisob-fakturalar to'g'ri summa va QQS bilan Faktura.uz ga yuboriladi.</li><li>Hujjat holati CRM da yangilanadi, menejerlar qayta ishlash natijasini ko'radi.</li><li>Jarayon fonda bajariladi, shuning uchun foydalanuvchi CRM da ishini davom ettirishi mumkin.</li></ul>`
- English:
  `<p>The solution reduces manual work in electronic document exchange and keeps documents in CRM next to customers, contracts, and items.</p><ul><li>Incoming invoices and acts from Faktura.uz are imported into CRM.</li><li>Counterparties, contracts, and document rows are created or matched automatically.</li><li>Re-importing the same document does not create a duplicate.</li><li>Outgoing CRM invoices are sent to Faktura.uz with correct totals and VAT.</li><li>Document status is updated in CRM so managers can see the processing result.</li><li>Processing runs in the background, so users can keep working in CRM.</li></ul>`

## Какие действия выполняются автоматически

- Получение списка входящих документов из Faktura.uz.
- Загрузка содержимого выбранного документа в CRM.
- Создание или переиспользование контрагента и договора.
- Сопоставление товаров по ИКПУ, штрихкоду или их связке.
- Создание строк счета-фактуры в CRM.
- Отправка исходящих счетов-фактур из CRM в Faktura.uz.
- Обновление статуса документа после успешной обработки или ошибки.

## Список обрабатываемых вебхуков

- Faktura.uz:
  - Входящие вебхуки не используются.
- CRM:
  - Входящие CRM-вебхуки не используются.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `FAKTURA_UZ_CLIENT_ID` | Да | String | Да | `ID приложения Faktura.uz` / `Faktura.uz ilova ID` / `Faktura.uz app ID` | `Служебный идентификатор подключения Faktura.uz` / `Faktura.uz ulanishining xizmat identifikatori` / `Service identifier for the Faktura.uz connection` | `` / `` / `` |
| `FAKTURA_UZ_LOGIN` | Да | String | Да | `Логин Faktura.uz` / `Faktura.uz login` / `Faktura.uz login` | `Служебный логин аккаунта, от имени которого выполняется обмен документами` / `Hujjat almashinuvi bajariladigan xizmat akkaunti logini` / `Service account login used for document exchange` | `` / `` / `` |
| `FAKTURA_UZ_PASSWORD` | Да | String | Да | `Пароль Faktura.uz` / `Faktura.uz parol` / `Faktura.uz password` | `Служебный пароль аккаунта, от имени которого выполняется обмен документами` / `Hujjat almashinuvi bajariladigan xizmat akkaunti paroli` / `Service account password used for document exchange` | `` / `` / `` |
| `FAKTURA_UZ_PRIVATE_KEY` | Да | String | Да | `Ключ доступа Faktura.uz` / `Faktura.uz kirish kaliti` / `Faktura.uz access key` | `Служебный ключ подключения для обмена с Faktura.uz` / `Faktura.uz bilan almashish uchun xizmat ulanish kaliti` / `Service connection key for Faktura.uz exchange` | `` / `` / `` |

Эти данные заполняются администратором при подключении обмена с Faktura.uz. Обычному пользователю не нужно вводить их при ежедневной работе с документами.

## Порядок настройки

1. Убедитесь, что у компании есть активный аккаунт Faktura.uz для обмена электронными документами.
2. Заполните служебные данные подключения Faktura.uz в настройках интеграции.
3. Проверьте подключение для нужного предприятия CRM.
4. Загрузите список входящих документов и выберите документ для импорта.
5. Убедитесь, что контрагент, договор и строки счета-фактуры корректно появились в CRM.
6. Для исходящего документа выполните отправку из CRM и проверьте статус обработки.
