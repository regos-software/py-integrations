# Телефония Asterisk для CRM-поддержки

## Наименование интеграции

- Русский: `Телефония Asterisk для CRM-поддержки`
- O'zbekcha: `CRM qo'llab-quvvatlash uchun Asterisk telefoniyasi`
- English: `Asterisk Telephony for CRM Support`

## Краткое описание

- Русский: `Интеграция превращает звонки в CRM-обращения: команда видит статус разговора, ответственного и запись звонка в одной карточке.`
- O'zbekcha: `Integratsiya qo'ng'iroqlarni CRM murojaatlariga aylantiradi: jamoa qo'ng'iroq holati, mas'ul xodim va yozuvni bitta kartada ko'radi.`
- English: `The integration converts calls into CRM cases so your team can track call status, responsible user, and recording in one place.`

## Полное описание

- Русский:
  `<p>Решение помогает отделу продаж и поддержки быстрее обрабатывать звонки и сохранять прозрачную историю общения.</p><ul><li>Каждый звонок обрабатывается по модели “1 звонок = 1 обращение”.</li><li>События звонка последовательно публикуются в чат обращения.</li><li>Система может автоматически назначать ответственного по внутреннему номеру оператора.</li><li>Запись разговора прикладывается в обращение при поступлении события записи.</li><li>Повторные сигналы по одному звонку не создают лишних дублей в CRM.</li><li>Шаблоны системных сообщений поддерживают несколько языков.</li></ul>`
- O'zbekcha:
  `<p>Yechim savdo va qo'llab-quvvatlash bo'limiga qo'ng'iroqlarni tezroq qayta ishlash va muloqot tarixini shaffof saqlashga yordam beradi.</p><ul><li>Har bir qo'ng'iroq “1 qo'ng'iroq = 1 murojaat” modeli bo'yicha yuritiladi.</li><li>Qo'ng'iroq hodisalari murojaat chatiga ketma-ket yuboriladi.</li><li>Tizim operatorning ichki raqamiga ko'ra mas'ulni avtomatik biriktira oladi.</li><li>Yozuv hodisasi kelganda qo'ng'iroq yozuvi murojaatga biriktiriladi.</li><li>Bitta qo'ng'iroq bo'yicha takroriy signallar CRMda ortiqcha dubl yaratmaydi.</li><li>Tizim xabarlari shablonlari bir nechta tilni qo'llab-quvvatlaydi.</li></ul>`
- English:
  `<p>The solution helps sales and support teams process calls faster while keeping communication history transparent.</p><ul><li>Each call follows the “1 call = 1 case” model.</li><li>Call events are posted to the case chat in order.</li><li>The system can auto-assign the responsible user by operator extension.</li><li>Call recording is attached to the case when recording event arrives.</li><li>Repeated signals for the same call do not create unnecessary duplicates in CRM.</li><li>System message templates support multiple languages.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `handle_webhook` не используется (возвращает `ignored`).


## Какие действия выполняются автоматически

- Создание или переиспользование обращения по звонку.
- Публикация статусов звонка в чат обращения.
- Назначение ответственного по внутреннему номеру (если включено).
- Загрузка и прикрепление записи разговора.
- Защита от повторной обработки дублей.

## Настройки интеграции

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `asterisk_ami_host` | Да | String | `Хост Asterisk AMI` / `Asterisk AMI hosti` / `Asterisk AMI host` | `Адрес AMI-сервера Asterisk` / `Asterisk AMI server manzili` / `Address of Asterisk AMI server` | `192.168.1.10` / `192.168.1.10` / `192.168.1.10` |
| `asterisk_ami_port` | Нет | Integer | `Порт Asterisk AMI` / `Asterisk AMI porti` / `Asterisk AMI port` | `Порт подключения к AMI` / `AMI ga ulanish porti` / `AMI connection port` | `5038` / `5038` / `5038` |
| `asterisk_ami_user` | Да | String | `Пользователь AMI` / `AMI foydalanuvchisi` / `AMI user` | `Логин для доступа к AMI` / `AMI ga kirish logini` / `AMI access login` | `ami_user` / `ami_user` / `ami_user` |
| `asterisk_ami_password` | Да | String | `Пароль AMI` / `AMI paroli` / `AMI password` | `Пароль для доступа к AMI` / `AMI ga kirish paroli` / `AMI access password` | `********` / `********` / `********` |
| `asterisk_channel_id` | Да | Integer | `ID CRM-канала` / `CRM kanal ID` / `CRM channel ID` | `Канал CRM для публикации событий звонка` / `Qo'ng'iroq hodisalari yuboriladigan CRM kanal` / `CRM channel where call events are published` | `1` / `1` / `1` |
| `asterisk_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible user` | `Ответственный, если автоопределение не сработало` / `Avtoaniqlash bo'lmasa biriktiriladigan mas'ul` / `Responsible user if auto-detection is not available` | `15` / `15` / `15` |
| `asterisk_assign_responsible_by_operator_ext` | Нет | Boolean | `Назначение по внутреннему номеру` / `Ichki raqam bo'yicha biriktirish` / `Assign by operator extension` | `Назначать ответственного по extension оператора` / `Operator extension bo'yicha mas'ul biriktirish` / `Assign responsible by operator extension` | `true` / `true` / `true` |
| `asterisk_close_ticket_on_call_end` | Нет | Boolean | `Автозакрытие обращения после звонка` / `Qo'ng'iroq tugagach murojaatni yopish` / `Close case after call ends` | `Если включено, обращение закрывается только после успешно завершенного разговора и только когда назначен ответственный` / `Yoqilgan bo'lsa, murojaat faqat muvaffaqiyatli yakunlangan suhbatdan keyin va mas'ul biriktirilganda yopiladi` / `When enabled, the case is closed only after a successful completed call and only when a responsible user is assigned` | `false` / `false` / `false` |
| `asterisk_lead_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон заголовка обращения` / `Murojaat sarlavhasi shabloni` / `Template for case subject` | `Call {direction} {from_phone}` / `Call {direction} {from_phone}` / `Call {direction} {from_phone}` |
| `asterisk_allowed_did_list` | Нет | String | `Список DID/линий` / `DID/liniyalar ro'yxati` / `DID lines list` | `Список линий для определения направления звонка` / `Qo'ng'iroq yo'nalishini aniqlash uchun liniyalar ro'yxati` / `List of lines used for call direction detection` | `998712000000,998712000001` / `998712000000,998712000001` / `998712000000,998712000001` |
| `asterisk_recording_base_url` | Нет | String | `Базовый URL записей` / `Yozuvlar bazaviy URL` / `Recording base URL` | `База для формирования ссылок на записи` / `Yozuv havolalarini shakllantirish uchun baza` / `Base URL used to build recording links` | `https://pbx.example.com/records/` / `https://pbx.example.com/records/` / `https://pbx.example.com/records/` |
| `asterisk_default_country_code` | Нет | String | `Код страны` / `Mamlakat kodi` / `Country code` | `Код страны для нормализации телефонов` / `Telefonlarni normallashtirish uchun mamlakat kodi` / `Country code for phone normalization` | `998` / `998` / `998` |
| `asterisk_message_language` | Нет | String | `Язык системных сообщений` / `Tizim xabarlari tili` / `System message language` | `Язык служебных сообщений в чате` / `Chatdagi xizmat xabarlari tili` / `Language of service messages in chat` | `ru` / `uz` / `en` |


## Порядок настройки

1. Включите AMI на стороне Asterisk и подготовьте учетные данные доступа.
2. Заполните обязательные настройки (`asterisk_ami_host`, `asterisk_ami_user`, `asterisk_ami_password`, `asterisk_channel_id`).
3. При необходимости настройте автоназначение ответственного и шаблоны сообщений.
4. Подключите интеграцию и выполните тестовый входящий и исходящий звонок.
5. Проверьте, что один звонок создает одно обращение и события публикуются в его чат.

