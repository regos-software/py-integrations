# Ipak Yuli Bank payments

## Наименование интеграции

- Русский: `Ipak Yuli Bank: банковские платежи`
- O'zbekcha: `Ipak Yuli Bank: bank to'lovlari`
- English: `Ipak Yuli Bank Payments`

## Краткое описание

- Русский: `Интеграция сверяет банковскую выписку Ipak Yuli с REGOS и создает входящие или исходящие платежи по ключевым словам в назначении платежа.`
- O'zbekcha: `Integratsiya Ipak Yuli bank ko'chirmasini REGOS bilan solishtiradi va to'lov izohidagi kalit so'zlar bo'yicha kiruvchi yoki chiquvchi to'lovlarni yaratadi.`
- English: `The integration reconciles Ipak Yuli bank statements with REGOS and creates incoming or outgoing payments by keywords in the payment purpose.`

## Полное описание

- Русский:
  `<p>REGOS помогает вести продажи, склад и аналитику в единой рабочей среде. Эта интеграция добавляет аккуратную банковскую синхронизацию: операции из выписки Ipak Yuli попадают в документы оплаты REGOS без ручного переноса.</p><ul><li>Интеграция периодически запрашивает выписку по расчетному счету.</li><li>Можно синхронизировать все платежи, только входящие или только исходящие.</li><li>Для входящих и исходящих платежей настраиваются отдельные ключевые слова и отдельные исключения по ИНН/ПИНФЛ.</li><li>Контрагент находится по ИНН/ПИНФЛ или создается в выбранной группе.</li><li>Входящие и исходящие платежи получают разные статьи доходов и расходов.</li><li>Служебное поле платежа хранит ID банковской операции, поэтому повторный запуск не создает дубль.</li><li>Платеж можно автоматически провести после создания.</li></ul>`
- O'zbekcha:
  `<p>REGOS savdo, ombor va tahlil jarayonlarini yagona ish muhitida yuritishga yordam beradi. Ushbu integratsiya Ipak Yuli bank ko'chirmasidagi mos operatsiyalarni REGOS to'lov hujjatlariga qo'lda ko'chirmasdan olib kiradi.</p><ul><li>Integratsiya hisob raqami bo'yicha ko'chirmani jadval asosida so'raydi.</li><li>Barcha to'lovlarni, faqat kiruvchi yoki faqat chiquvchi to'lovlarni sinxronlash mumkin.</li><li>Kiruvchi va chiquvchi to'lovlar uchun kalit so'zlar hamda STIR/JSHSHIR istisnolari alohida sozlanadi.</li><li>Kontragent STIR/JSHSHIR bo'yicha topiladi yoki tanlangan guruhda yaratiladi.</li><li>Kiruvchi va chiquvchi to'lovlar alohida daromad va xarajat kategoriyalariga yoziladi.</li><li>To'lovning xizmat maydonida bank operatsiyasi ID si saqlanadi, shuning uchun qayta ishga tushirish dubl yaratmaydi.</li><li>To'lov yaratilgandan keyin avtomatik o'tkazilishi mumkin.</li></ul>`
- English:
  `<p>REGOS helps teams run sales, inventory, and analytics in one working environment. This integration adds clean bank synchronization: matching Ipak Yuli statement operations are imported into REGOS payment documents without manual copying.</p><ul><li>The integration periodically requests the bank statement for the configured account.</li><li>You can sync all payments, incoming payments only, or outgoing payments only.</li><li>Incoming and outgoing payments have separate keyword filters and separate TIN/PINFL exclusion lists.</li><li>The counterparty is found by TIN/PINFL or created in the selected group.</li><li>Incoming and outgoing payments use separate income and expense categories.</li><li>A service payment field stores the bank operation ID, so repeated runs do not create duplicates.</li><li>The payment can be posted automatically after creation.</li></ul>`

## Обрабатываемые события и действия

| Источник | Событие или действие | Что делает интеграция |
| --- | --- | --- |
| Scheduler | `handle_external` | Запускает опрос выписки Ipak Yuli и импорт подходящих операций. |
| REGOS action | `connect` / `reconnect` | Проверяет настройки, создает служебное поле `field_ipak_yuli_payment_id`, проверяет доступность банковского счета. |
| REGOS action | `check` | Проверяет настройки REGOS и доступность банковского счета через `GetAcc1C`. |
| REGOS action | `run` / `do_work` / `do_task` | Запускает импорт вручную. |

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Скрывать в UI | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|---|
| `bank_login` | Да | String | Нет | `Логин банка` / `Bank logini` / `Bank login` | `Служебный логин Ipak Yuli для доступа к OpenAPI; значение помечено как secret в import JSON` / `Ipak Yuli OpenAPI ga ulanish uchun xizmat logini; import JSON da secret sifatida belgilanadi` / `Service login for Ipak Yuli OpenAPI access; marked as secret in import JSON` | `company-api` / `company-api` / `company-api` |
| `bank_password` | Да | String | Нет | `Пароль банка` / `Bank paroli` / `Bank password` | `Пароль служебной учетной записи банка; значение помечено как secret в import JSON` / `Bank xizmat akkaunti paroli; import JSON da secret sifatida belgilanadi` / `Password for the bank service account; marked as secret in import JSON` | `` / `` / `` |
| `bank_api_base_url` | Нет | String | Нет | `URL API банка` / `Bank API URL` / `Bank API URL` | `Базовый URL OpenAPI Ipak Yuli; если пусто, используется боевой URL` / `Ipak Yuli OpenAPI asosiy URL manzili; bo'sh bo'lsa, production URL ishlatiladi` / `Base Ipak Yuli OpenAPI URL; production URL is used when empty` | `https://mb.ipakyulibank.uz:2713` / `https://mb.ipakyulibank.uz:2713` / `https://mb.ipakyulibank.uz:2713` |
| `bank_branch` | Да | String | Нет | `МФО` / `MFO` / `MFO` | `МФО расчетного счета, по которому запрашивается выписка` / `Ko'chirma olinadigan hisob raqami MFO si` / `MFO of the bank account used for statement requests` | `00444` / `00444` / `00444` |
| `bank_account` | Да | String | Нет | `Расчетный счет` / `Hisob raqami` / `Bank account` | `Счет, по которому интеграция получает выписку` / `Integratsiya ko'chirma oladigan hisob raqami` / `Account used by the integration to request statements` | `20208000...` / `20208000...` / `20208000...` |
| `firm_id` | Да | Integer | Нет | `Предприятие REGOS` / `REGOS korxonasi` / `REGOS firm` | `ID предприятия REGOS, для которого создаются платежи` / `To'lovlar yaratiladigan REGOS korxonasi ID si` / `REGOS firm ID for created payments` | `1` / `1` / `1` |
| `sync_payment_directions` | Да | Enum | Нет | `Какие платежи синхронизировать` / `Qaysi to'lovlarni sinxronlash` / `Payments to sync` | `All — входящие и исходящие, Income — только входящие, Outcome — только исходящие` / `All — kiruvchi va chiquvchi, Income — faqat kiruvchi, Outcome — faqat chiquvchi` / `All syncs incoming and outgoing payments, Income only incoming, Outcome only outgoing` | `All` / `All` / `All` |
| `income_purpose_keywords` | Нет | Text | Нет | `Ключевые слова для входящих` / `Kiruvchi to'lov kalit so'zlari` / `Incoming keywords` | `Слова или фразы в назначении входящего платежа; если пусто, входящие не фильтруются по назначению` / `Kiruvchi to'lov izohidagi so'z yoki iboralar; bo'sh bo'lsa, kiruvchi to'lovlar izoh bo'yicha filtrlanmaydi` / `Words or phrases in incoming payment purpose; when empty, incoming payments are not filtered by purpose` | `оплата заказа, поступление` / `buyurtma to'lovi, kirim` / `order payment, incoming` |
| `outcome_purpose_keywords` | Нет | Text | Нет | `Ключевые слова для исходящих` / `Chiquvchi to'lov kalit so'zlari` / `Outgoing keywords` | `Слова или фразы в назначении исходящего платежа; если пусто, исходящие не фильтруются по назначению` / `Chiquvchi to'lov izohidagi so'z yoki iboralar; bo'sh bo'lsa, chiquvchi to'lovlar izoh bo'yicha filtrlanmaydi` / `Words or phrases in outgoing payment purpose; when empty, outgoing payments are not filtered by purpose` | `поставка, комиссия` / `yetkazib berish, komissiya` / `supply, commission` |
| `income_excluded_counterparty_inns` | Нет | Text | Нет | `Исключаемые ИНН для входящих` / `Kiruvchi uchun istisno STIR/JSHSHIR` / `Incoming excluded TINs` | `ИНН или ПИНФЛ плательщиков, входящие платежи от которых не нужно обрабатывать; если пусто, исключений нет` / `Kiruvchi to'lovlari qayta ishlanmaydigan to'lovchi STIR yoki JSHSHIRlari; bo'sh bo'lsa, istisnolar yo'q` / `Payer TIN or PINFL values whose incoming payments should not be processed; when empty, no TINs are excluded` | `123456789, 12345678901234` / `123456789, 12345678901234` / `123456789, 12345678901234` |
| `outcome_excluded_counterparty_inns` | Нет | Text | Нет | `Исключаемые ИНН для исходящих` / `Chiquvchi uchun istisno STIR/JSHSHIR` / `Outgoing excluded TINs` | `ИНН или ПИНФЛ получателей, исходящие платежи которым не нужно обрабатывать; если пусто, исключений нет` / `Chiquvchi to'lovlari qayta ishlanmaydigan oluvchi STIR yoki JSHSHIRlari; bo'sh bo'lsa, istisnolar yo'q` / `Recipient TIN or PINFL values whose outgoing payments should not be processed; when empty, no TINs are excluded` | `123456789, 12345678901234` / `123456789, 12345678901234` / `123456789, 12345678901234` |
| `payment_type_id` | Да | Catalog | Нет | `Форма оплаты` / `To'lov turi` / `Payment type` | `Форма оплаты REGOS для создаваемых платежей` / `Yaratiladigan to'lovlar uchun REGOS to'lov turi` / `REGOS payment type for created payments` | `Выберите форму оплаты` / `To'lov turini tanlang` / `Select payment type` |
| `partner_group_id` | Да | Catalog | Нет | `Группа контрагентов` / `Kontragentlar guruhi` / `Counterparty group` | `Группа, куда создаются новые контрагенты банка` / `Yangi bank kontragentlari yaratiladigan guruh` / `Group where new bank counterparties are created` | `Выберите группу` / `Guruhni tanlang` / `Select group` |
| `income_category_id` | Да | Catalog | Нет | `Статья дохода` / `Daromad kategoriyasi` / `Income category` | `Статья дохода для входящих платежей` / `Kiruvchi to'lovlar uchun daromad kategoriyasi` / `Income category for incoming payments` | `Выберите статью дохода` / `Daromad kategoriyasini tanlang` / `Select income category` |
| `outcome_category_id` | Да | Catalog | Нет | `Статья расхода` / `Xarajat kategoriyasi` / `Expense category` | `Статья расхода для исходящих платежей` / `Chiquvchi to'lovlar uchun xarajat kategoriyasi` / `Expense category for outgoing payments` | `Выберите статью расхода` / `Xarajat kategoriyasini tanlang` / `Select expense category` |
| `perform_after_create` | Да | Boolean | Нет | `Проводить платеж` / `To'lovni o'tkazish` / `Post payment` | `Если включено, документ оплаты проводится сразу после создания` / `Yoqilgan bo'lsa, to'lov hujjati yaratilgandan keyin darhol o'tkaziladi` / `When enabled, the payment document is posted immediately after creation` | `true` / `true` / `true` |
| `lookback_days` | Нет | Integer | Нет | `Глубина проверки` / `Tekshirish chuqurligi` / `Lookback days` | `Сколько предыдущих дней дополнительно проверять при каждом запуске; по умолчанию 1` / `Har ishga tushishda nechta oldingi kun qo'shimcha tekshiriladi; standart qiymat 1` / `How many previous days to recheck on each run; default is 1` | `1` / `1` / `1` |
| `poll_from_time` | Нет | String | Нет | `Время с` / `Boshlanish vaqti` / `From time` | `Начало временного окна выписки в формате ЧЧ:ММ:СС` / `Ko'chirma vaqt oynasi boshlanishi HH:MM:SS formatida` / `Statement time window start in HH:MM:SS format` | `00:00:00` / `00:00:00` / `00:00:00` |
| `poll_to_time` | Нет | String | Нет | `Время по` / `Tugash vaqti` / `To time` | `Конец временного окна выписки в формате ЧЧ:ММ:СС` / `Ko'chirma vaqt oynasi tugashi HH:MM:SS formatida` / `Statement time window end in HH:MM:SS format` | `23:59:59` / `23:59:59` / `23:59:59` |
| `attached_user_id` | Нет | Integer | Нет | `Ответственный` / `Mas'ul` / `Responsible user` | `ID ответственного пользователя REGOS для создаваемых платежей` / `Yaratiladigan to'lovlar uchun REGOS mas'ul foydalanuvchisi ID si` / `Responsible REGOS user ID for created payments` | `7` / `7` / `7` |

## Логика работы

1. При подключении интеграция проверяет настройки, справочники REGOS и банковский счет.
2. Если доп. поля `field_ipak_yuli_payment_id` для `DocPayment` нет, интеграция создает его.
3. Scheduler периодически вызывает внешний endpoint подключенной интеграции.
4. Интеграция берет lock, чтобы два запуска не импортировали одну выписку одновременно.
5. Для каждой даты от сегодняшней до `lookback_days` назад вызывается `GetDoc1C`.
6. Если дата валютирования строки банка `vdate` не совпадает с операционным днем выписки, строка пропускается; `ddate` считается датой документа, а не датой выписки.
7. Операция обрабатывается только при `state = 3` и `dir = 1` или `dir = 2`; по справочнику банка `dir = 1` — исходящий платеж, `dir = 2` — поступление средств.
8. `sync_payment_directions` определяет, какие направления попадут в импорт: `All`, `Income` или `Outcome`.
9. Для входящих применяются только `income_purpose_keywords` и `income_excluded_counterparty_inns`; для исходящих — только `outcome_purpose_keywords` и `outcome_excluded_counterparty_inns`. Пустой список ключевых слов означает импорт всех платежей направления, пустой список ИНН означает отсутствие исключений.
10. Если ИНН/ПИНФЛ контрагента указан в списке исключений для направления, операция пропускается без поиска контрагента и создания `DocPayment`.
11. Внешний ID операции строится из `b2_id`, затем из `branch + general_id`, затем из стабильного hash.
12. Если `DocPayment` с таким `field_ipak_yuli_payment_id` уже есть, операция пропускается.
13. Контрагент ищется по ИНН/ПИНФЛ; если не найден, создается в `partner_group_id`.
14. Создается `DocPayment`; для входящих используется `income_category_id`, для исходящих `outcome_category_id`, а в примечание записывается банковское назначение платежа, обрезанное до 300 символов.
15. Если `perform_after_create = true`, интеграция вызывает `DocPayment/Perform`.

## Scheduler

Для подключенной интеграции с ID `<connected_integration_id>` scheduler должен отправлять задачу на публичный URL:

```text
POST https://integration.regos.uz/external/<connected_integration_id>/
```

В теле scheduler передает `uuid` задачи. Интеграция получает информацию о задаче, выставляет статус `Processing`, выполняет импорт и затем выставляет `Finished` или `Error`.

## Банковский доступ

Интеграция использует Basic-авторизацию `Authorization: Basic <base64(login:password)>` для каждого запроса. Для продуктивного режима рекомендуется выделить отдельную учетную запись банка и настроить доступ по IP/VPN на стороне банка.
