# Telegram-канал для поддержки клиентов

## Наименование интеграции

- Русский: `Telegram-канал для поддержки клиентов`
- O'zbekcha: `Mijozlarni qo'llab-quvvatlash uchun Telegram kanali`
- English: `Telegram Channel for Customer Support`

## Краткое описание

- Русский: `Интеграция объединяет Telegram и CRM в один удобный диалог: клиент пишет в мессенджере, оператор отвечает из CRM, а вся переписка хранится в обращении.`
- O'zbekcha: `Integratsiya Telegram va CRM ni bitta qulay muloqotga birlashtiradi: mijoz messenjerda yozadi, operator CRM ichidan javob beradi, yozishmalar esa murojaatda saqlanadi.`
- English: `The integration connects Telegram and CRM into one smooth conversation: customers message in Telegram, operators reply from CRM, and the full history stays in one case.`

## Полное описание

- Русский:
  `<p>Решение помогает команде поддержки отвечать быстрее и аккуратнее, не переключаясь между разными окнами.</p><ul><li>Все сообщения клиента автоматически попадают в обращение в CRM.</li><li>Оператор отвечает в CRM, а клиент получает ответ в том же чате Telegram.</li><li>Если у вас несколько ботов, система закрепляет правильный маршрут ответа и сохраняет целостность диалога.</li><li>Приветственное и завершающее сообщения отправляются клиенту автоматически по сценарию обслуживания.</li><li>Запрос номера телефона у клиента встроен в процесс и не мешает обычной переписке.</li><li>Автоматические сообщения видны и клиенту, и оператору, поэтому история прозрачна для всей команды.</li></ul>`
- O'zbekcha:
  `<p>Yechim qo'llab-quvvatlash jamoasiga turli oynalar orasida almashmasdan, tez va aniq javob berishga yordam beradi.</p><ul><li>Mijozning barcha xabarlari CRM dagi murojaatga avtomatik tushadi.</li><li>Operator CRM ichida javob beradi, mijoz esa javobni shu Telegram chatida oladi.</li><li>Agar bir nechta bot bo'lsa, tizim to'g'ri javob yo'nalishini saqlab, muloqotni yaxlit olib boradi.</li><li>Xizmat jarayoniga ko'ra salomlashuv va yakuniy xabar avtomatik yuboriladi.</li><li>Telefon raqamini so'rash jarayoni muloqotga qulay tarzda qo'shilgan.</li><li>Avtomatik xabarlar ham mijozga, ham operatorga ko'rinadi, shuning uchun tarix jamoa uchun shaffof bo'ladi.</li></ul>`
- English:
  `<p>The solution helps support teams reply faster and more consistently without switching between tools.</p><ul><li>Every customer message is automatically added to the CRM case.</li><li>Operators reply in CRM, and customers receive replies in the same Telegram chat.</li><li>If you use several bots, the system keeps the correct reply route and preserves conversation continuity.</li><li>Welcome and closing messages are sent automatically as part of your service flow.</li><li>Phone number request is built into the journey and stays user-friendly.</li><li>Automatic messages are visible to both customer and operator, making the history transparent for the whole team.</li></ul>`

## Какие действия выполняются автоматически

- Новые сообщения клиента.
- Изменения и удаление сообщений.
- Отображение активности набора текста.
- Завершение обращения с отправкой финального сообщения клиенту.
- Обновление текстов канала без ручного перезапуска.

## Настройки интеграции

| Параметр | Для чего нужен | Пример |
|---|---|---|
| Доступ к Telegram-боту | Подключает вашего бота к CRM | Данные доступа из Telegram |
| Канал CRM для обращений | Определяет, куда будут попадать диалоги клиентов | Канал “Поддержка” |
| Тема нового обращения | Помогает красиво и понятно называть новые обращения | “Обращение от {имя клиента}” |
| Ответственный по умолчанию | Назначает исполнителя, если правила распределения не заданы | Сотрудник первой линии |
| Безопасная проверка входящих сообщений | Защищает канал от несанкционированных запросов | Секретная строка доступа |
| Защита от дублей | Исключает повторную обработку одинаковых сообщений | 10 минут |
| Время хранения служебного состояния | Стабилизирует маршрутизацию и вспомогательные сценарии | 1 час |
| Передача внутренних сообщений в Telegram | Позволяет отправлять в Telegram не только клиентские, но и служебные сообщения | Включено/Выключено |
| Текст запроса номера телефона | Формирует вежливый запрос контакта у клиента | “Поделитесь номером телефона” |
| Текст кнопки отправки номера | Делает сценарий передачи контакта понятным для клиента | “Отправить номер” |
| Режим обмена с Telegram | Выбирает удобный способ получения обновлений | Мгновенный режим |

## Порядок настройки

1. Создайте Telegram-бота и подготовьте данные для подключения.
2. Выберите в CRM канал, куда должны попадать клиентские сообщения.
3. Настройте тексты приветствия, завершения и запроса телефона в вашем стиле.
4. Подключите интеграцию и запустите проверочный диалог.
5. Убедитесь, что оператор отвечает из CRM, а клиент получает ответы в том же чате Telegram.
