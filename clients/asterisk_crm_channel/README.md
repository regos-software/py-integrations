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
  `<p>Решение помогает отделу продаж и поддержки быстрее обрабатывать звонки и сохранять прозрачную историю общения.</p><ul><li>Каждый звонок обрабатывается по модели “1 звонок = 1 обращение”.</li><li>События звонка последовательно публикуются в чат обращения.</li><li>Система может автоматически назначать ответственного по внутреннему номеру оператора.</li><li>Ссылка на запись разговора публикуется в чате при поступлении события записи или при завершении звонка, если имя файла уже известно.</li><li>Повторные сигналы по одному звонку не создают лишних дублей в CRM.</li><li>Шаблоны системных сообщений поддерживают несколько языков.</li></ul>`
- O'zbekcha:
  `<p>Yechim savdo va qo'llab-quvvatlash bo'limiga qo'ng'iroqlarni tezroq qayta ishlash va muloqot tarixini shaffof saqlashga yordam beradi.</p><ul><li>Har bir qo'ng'iroq “1 qo'ng'iroq = 1 murojaat” modeli bo'yicha yuritiladi.</li><li>Qo'ng'iroq hodisalari murojaat chatiga ketma-ket yuboriladi.</li><li>Tizim operatorning ichki raqamiga ko'ra mas'ulni avtomatik biriktira oladi.</li><li>Yozuv hodisasi kelganda yoki qo'ng'iroq yakunlanganda fayl nomi allaqachon ma'lum bo'lsa, yozuv havolasi chatga yuboriladi.</li><li>Bitta qo'ng'iroq bo'yicha takroriy signallar CRMda ortiqcha dubl yaratmaydi.</li><li>Tizim xabarlari shablonlari bir nechta tilni qo'llab-quvvatlaydi.</li></ul>`
- English:
  `<p>The solution helps sales and support teams process calls faster while keeping communication history transparent.</p><ul><li>Each call follows the “1 call = 1 case” model.</li><li>Call events are posted to the case chat in order.</li><li>The system can auto-assign the responsible user by operator extension.</li><li>A call recording link is posted to the chat when the recording event arrives, or when the call ends if the filename is already known.</li><li>Repeated signals for the same call do not create unnecessary duplicates in CRM.</li><li>System message templates support multiple languages.</li></ul>`

## Список обрабатываемых вебхуков

- CRM:
  - `handle_webhook` не используется (возвращает `ignored`).


## Какие действия выполняются автоматически

Жизненный цикл звонка обрабатывается без задержек, по трём структурным событиям AMI:

- **Звонок инициирован** (root `Newchannel`) → сразу создаётся обращение. Направление определяется по контексту (`from-trunk`/`from-pstn` → входящий, `from-internal` → исходящий) с резервом по номерам и списку DID. Входящие создаются без ответственного, исходящие — с ответственным по extension инициатора (опционально с проверкой смены).
- **Звонок принят** (`BridgeEnter` с реальным внутренним номером оператора) → сразу назначается ответственный.
- **Звонок завершён** (root `Hangup` / мастер-CDR) → обращение сразу закрывается, если оно было принято оператором. Пропущенный входящий (без ответственного) остаётся **открытым** для перезвона.
- Ссылка на запись разговора публикуется в чате по готовности; для старых AMI-сценариев ссылка также публикуется при завершении звонка, если имя файла записи уже было получено через `MIXMONITOR_FILENAME` или `CDR(recordingfile)`.
- Сканер-звонки из контекста `from-sip-external` игнорируются; повторные сигналы по одному звонку дублей не создают.

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
| `asterisk_close_ticket_on_call_end` | Нет | Boolean | `Автозакрытие обращения после звонка` / `Qo'ng'iroq tugagach murojaatni yopish` / `Close case after call ends` | `Если включено, обращение закрывается сразу при завершении звонка, но только если оно было принято оператором (есть ответственный); пропущенные входящие остаются открытыми` / `Yoqilgan bo'lsa, murojaat qo'ng'iroq tugashi bilan yopiladi, lekin faqat operator qabul qilgan bo'lsa (mas'ul bor); o'tkazib yuborilgan kiruvchilar ochiq qoladi` / `When enabled, the case closes as soon as the call ends, but only if it was answered (has a responsible); missed inbound calls stay open` | `true` / `true` / `true` |
| `asterisk_lead_subject_template` | Нет | String | `Шаблон темы обращения` / `Murojaat mavzusi shabloni` / `Case subject template` | `Шаблон заголовка обращения` / `Murojaat sarlavhasi shabloni` / `Template for case subject` | `Call {direction} {client_phone}` / `Call {direction} {client_phone}` / `Call {direction} {client_phone}` |
| `asterisk_allowed_did_list` | Нет | String | `Список DID/линий` / `DID/liniyalar ro'yxati` / `DID lines list` | `Список линий для определения направления звонка` / `Qo'ng'iroq yo'nalishini aniqlash uchun liniyalar ro'yxati` / `List of lines used for call direction detection` | `998712000000,998712000001` / `998712000000,998712000001` / `998712000000,998712000001` |
| `asterisk_recording_base_url` | Нет | String | `Базовый URL записей` / `Yozuvlar bazaviy URL` / `Recording base URL` | `База для формирования ссылок на записи` / `Yozuv havolalarini shakllantirish uchun baza` / `Base URL used to build recording links` | `https://pbx.example.com/records/` / `https://pbx.example.com/records/` / `https://pbx.example.com/records/` |
| `asterisk_default_country_code` | Нет | String | `Код страны` / `Mamlakat kodi` / `Country code` | `Код страны для нормализации телефонов` / `Telefonlarni normallashtirish uchun mamlakat kodi` / `Country code for phone normalization` | `998` / `998` / `998` |
| `asterisk_message_language` | Нет | String | `Язык системных сообщений` / `Tizim xabarlari tili` / `System message language` | `Язык служебных сообщений в чате` / `Chatdagi xizmat xabarlari tili` / `Language of service messages in chat` | `ru` / `uz` / `en` |
| `asterisk_min_external_digits` | Нет | Integer | `Мин. длина внешнего номера` / `Tashqi raqam min. uzunligi` / `Min external number length` | `Минимальная длина набранного номера, начиная с которой звонок из контекста from-internal считается исходящим внешним` / `from-internal kontekstidan terilgan raqam shu uzunlikdan boshlab tashqi chiquvchi deb hisoblanadi` / `Minimum dialed-number length at which a from-internal call counts as an outbound external call` | `6` / `6` / `6` |
| `asterisk_create_ticket_on_call_start` | Нет | Boolean | `Создавать обращение в начале звонка` / `Qo'ng'iroq boshida murojaat yaratish` / `Create case at call start` | `Включено по умолчанию: обращение создается сразу при инициации звонка (root Newchannel). Отключите, чтобы откладывать создание до первого значимого этапа (ответ/завершение)` / `Standart yoqilgan: murojaat qo'ng'iroq boshlanishida (root Newchannel) yaratiladi. O'chirsangiz, yaratish birinchi muhim bosqichgacha (javob/yakun) kechiktiriladi` / `Enabled by default: the case is created at call initiation (root Newchannel). Disable to defer creation to the first meaningful stage (answered/hangup)` | `true` / `true` / `true` |
| `asterisk_assign_responsible_requires_attendance` | Нет | Boolean | `Назначать только сотрудников на смене` / `Faqat smenadagi xodimni biriktirish` / `Assign only on-shift staff` | `Если включено, ответственный назначается по extension только если сотрудник на смене (WorkAttendance/Status). Иначе используется ответственный по умолчанию` / `Yoqilsa, mas'ul extension bo'yicha faqat xodim smenada bo'lsa biriktiriladi (WorkAttendance/Status), aks holda standart mas'ul ishlatiladi` / `When enabled, the responsible is assigned by extension only if the user is on shift (WorkAttendance/Status); otherwise the default responsible is used` | `false` / `false` / `false` |
| `asterisk_log_ami_events` | Нет | Boolean | `Логировать события AMI` / `AMI hodisalarini loglash` / `Log AMI events` | `Диагностика: если включено, каждое событие AMI пишется в лог одной строкой (тип + ключевые поля). По умолчанию выключено; включайте временно для отладки определения этапов звонка` / `Diagnostika: yoqilsa, har bir AMI hodisasi bitta qatorda logga yoziladi. Standart o'chirilgan; faqat nosozliklarni tuzatish uchun vaqtincha yoqing` / `Diagnostics: when enabled, every AMI event is logged as one line (type + key fields). Off by default; enable temporarily to debug call-stage detection` | `false` / `false` / `false` |
| `asterisk_post_status_messages` | Нет | Boolean | `Сообщения о статусах звонка в чат` / `Chatga qo'ng'iroq holati xabarlari` / `Post call-status messages to chat` | `Если включено, в чат обращения публикуются системные сообщения по этапам звонка (начат/принят/завершён). Если выключено, выполняются только действия (создание/назначение/закрытие) и публикация ссылки на запись` / `Yoqilsa, murojaat chatiga qo'ng'iroq bosqichlari bo'yicha tizim xabarlari yuboriladi. O'chirilsa, faqat amallar (yaratish/biriktirish/yopish) va yozuv havolasi yuboriladi` / `When enabled, per-stage system messages (started/answered/completed) are posted to the case chat. When disabled, only the actions (create/assign/close) and the recording link are posted` | `true` / `true` / `true` |


## Порядок настройки

1. Включите AMI на стороне Asterisk и подготовьте учетные данные доступа.
2. Заполните обязательные настройки (`asterisk_ami_host`, `asterisk_ami_user`, `asterisk_ami_password`, `asterisk_channel_id`).
3. При необходимости настройте автоназначение ответственного и шаблоны сообщений.
4. Подключите интеграцию и выполните тестовый входящий и исходящий звонок.
5. Проверьте цикл: входящий создаёт обращение в начале звонка, ответ назначает ответственного, завершение закрывает обращение; пропущенный входящий остаётся открытым.

