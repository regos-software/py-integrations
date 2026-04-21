# Телефония Asterisk для CRM-поддержки

## Наименование интеграции

- Русский: `Телефония Asterisk для CRM-поддержки`
- O'zbekcha: `CRM qo'llab-quvvatlash uchun Asterisk telefoniyasi`
- English: `Asterisk Telephony for CRM Support`

## Краткое описание

- Русский: `Интеграция превращает звонки в понятные CRM-обращения: команда видит ход разговора, результат и историю обслуживания в одном месте.`
- O'zbekcha: `Integratsiya qo'ng'iroqlarni tushunarli CRM murojaatlariga aylantiradi: jamoa suhbat jarayoni, natija va xizmat tarixini bitta joyda ko'radi.`
- English: `The integration turns calls into clear CRM cases so your team can track call progress, outcomes, and service history in one place.`

## Полное описание

- Русский:
  `<p>Решение помогает отделу продаж и поддержки быстрее работать со звонками и не терять детали общения.</p><ul><li>Каждый звонок фиксируется как отдельное обращение по принципу “1 звонок = 1 обращение”.</li><li>Этапы разговора отражаются в ленте обращения и формируют прозрачную историю контакта.</li><li>Система может автоматически назначать ответственного сотрудника по внутреннему номеру.</li><li>Если обращение уже завершено, повторные уведомления по тому же звонку не создают лишних новых карточек.</li><li>Запись разговора автоматически добавляется в обращение, чтобы менеджер видел полный контекст.</li><li>Язык системных сообщений выбирается в настройках и подходит для многоязычной команды.</li></ul>`
- O'zbekcha:
  `<p>Yechim savdo va qo'llab-quvvatlash bo'limiga qo'ng'iroqlar bilan tezroq ishlash va muloqot tafsilotlarini yo'qotmaslikka yordam beradi.</p><ul><li>Har bir qo'ng'iroq “1 qo'ng'iroq = 1 murojaat” tamoyili bo'yicha alohida murojaat sifatida qayd etiladi.</li><li>Suhbat bosqichlari murojaat tarixida ko'rinib, aloqa jarayonini shaffof qiladi.</li><li>Tizim ichki raqam asosida mas'ul xodimni avtomatik biriktira oladi.</li><li>Murojaat yakunlangan bo'lsa, shu qo'ng'iroq bo'yicha takroriy signallar ortiqcha yangi yozuv yaratmaydi.</li><li>Qo'ng'iroq yozuvi murojaatga avtomatik qo'shiladi va menejerga to'liq kontekst beradi.</li><li>Tizim xabarlari tili sozlamalarda tanlanadi va ko'p tilli jamoaga moslashadi.</li></ul>`
- English:
  `<p>The solution helps sales and support teams handle calls faster and keep every important detail.</p><ul><li>Each call is recorded as a separate case under the “1 call = 1 case” principle.</li><li>Call stages are reflected in the case timeline for full interaction visibility.</li><li>The system can automatically assign the responsible employee by internal line.</li><li>If a case is already closed, repeated updates for the same call do not create unnecessary new records.</li><li>Call recording is added automatically so managers have full context.</li><li>System message language is configurable and suitable for multilingual teams.</li></ul>`

## Какие события обрабатываются

- Начало звонка.
- Дозвон и ожидание ответа.
- Принятие звонка.
- Пропущенный звонок.
- Завершение разговора.
- Неуспешный вызов.
- Появление записи разговора.

## Настройки интеграции

| Параметр | Для чего нужен | Пример |
|---|---|---|
| Адрес телефонии | Подключает интеграцию к вашей телефонной станции | Адрес вашей телефонии |
| Порт подключения | Уточняет канал связи с телефонией | Стандартный канал подключения |
| Логин для подключения | Открывает доступ к событиям звонков | Учетная запись интеграции |
| Пароль для подключения | Защищает подключение и подтверждает права доступа | Надежный пароль |
| Канал CRM для звонков | Определяет, где создаются обращения по звонкам | Канал “Телефония” |
| Ответственный по умолчанию | Назначает исполнителя, если автоопределение недоступно | Старший оператор смены |
| Автораспределение по внутренним номерам | Автоматически связывает звонок с нужным сотрудником | Включено |
| Шаблон названия обращения | Делает карточки звонков понятными для команды | “Входящий звонок от клиента” |
| Список приоритетных линий | Помогает точнее определять сценарий звонка | Список внутренних линий компании |
| Адрес хранения записей разговоров | Позволяет корректно прикладывать записи к обращению | Корпоративный адрес записей |
| Код страны по умолчанию | Нормализует номера в едином формате | Код вашей страны |
| Защита от дублей событий | Убирает повторную обработку одинаковых сигналов | 10 минут |
| Время хранения служебного состояния | Сохраняет стабильность маршрутизации и обработки | 1 час |
| Язык системных сообщений | Показывает служебные тексты на нужном языке | Русский / O'zbekcha / English |

## Порядок настройки

1. Подготовьте телефонную станцию и учетные данные для безопасного подключения.
2. Выберите в CRM канал, в котором команда будет работать со звонками.
3. Настройте правила назначения ответственных и тексты карточек обращений.
4. Включите интеграцию и выполните тестовый входящий и исходящий звонок.
5. Проверьте, что каждый звонок сохраняется как отдельное обращение с корректной историей.
