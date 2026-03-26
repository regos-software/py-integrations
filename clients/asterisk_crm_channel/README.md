# asterisk_crm_channel

## Наименование интеграции

- Русский: `Звонки клиентов в CRM под полным контролем`
- O'zbekcha: `Mijoz qo'ng'iroqlari CRMda to'liq nazoratda`
- English: `Keep Customer Calls Fully Controlled in CRM`

## Краткое описание

- Русский: `Вся история звонка, ключевые этапы и результат общения фиксируются в CRM, чтобы команда быстрее доводила обращения до сделки.`
- O'zbekcha: `Qo'ng'iroq tarixi, muhim bosqichlar va natijalar CRMda saqlanadi, jamoa murojaatlarni tezroq natijaga olib chiqadi.`
- English: `Call history, key stages, and outcomes are recorded in CRM so your team can move requests to results faster.`

## Полное описание

- Русский:
  `<p>Решение помогает превратить телефонные обращения в управляемый процесс продаж и сервиса.</p><ul><li>Каждый звонок отражается в CRM с понятной историей общения.</li><li>Команда видит ключевые этапы звонка и не теряет контекст разговора.</li><li>Записи разговоров сохраняются в карточке обращения для контроля качества.</li><li>Ответственный сотрудник и текущий этап работы всегда под рукой.</li><li>Руководитель получает прозрачную картину по скорости и качеству обработки обращений.</li></ul><p>Подходит для компаний, где важны дисциплина коммуникаций, контроль клиентского опыта и рост конверсии по входящим и исходящим звонкам.</p>`
- O'zbekcha:
  `<p>Yechim telefon orqali kelgan murojaatlarni savdo va servis jarayonida tartibli boshqarishga yordam beradi.</p><ul><li>Har bir qo'ng'iroq CRMda aniq tarix bilan ko'rinadi.</li><li>Jamoa qo'ng'iroqning asosiy bosqichlarini ko'radi va suhbat kontekstini yo'qotmaydi.</li><li>Qo'ng'iroq yozuvlari sifat nazorati uchun murojaat kartasida saqlanadi.</li><li>Mas'ul xodim va joriy ish bosqichi doim ko'z oldida bo'ladi.</li><li>Rahbar murojaatlarni ko'rib chiqish tezligi va sifatini shaffof kuzata oladi.</li></ul><p>Kiruvchi va chiquvchi qo'ng'iroqlar bo'yicha kommunikatsiya intizomi, mijoz tajribasi va konversiyani oshirishni istagan kompaniyalar uchun mos.</p>`
- English:
  `<p>This solution turns phone conversations into a clear and manageable workflow inside CRM.</p><ul><li>Every call appears in CRM with an easy-to-follow interaction history.</li><li>Your team sees key call stages and keeps full conversation context.</li><li>Call recordings are stored in the request card for quality control.</li><li>The responsible employee and current stage stay visible at all times.</li><li>Managers get transparent oversight of response speed and service quality.</li></ul><p>Ideal for companies that want stronger communication discipline, better customer experience, and higher conversion from inbound and outbound calls.</p>`

## Список обрабатываемых вебхуков

- События звонков от Asterisk (через AMI или `/external`):
  - `started`
  - `ringing`
  - `answered`
  - `missed`
  - `completed`
  - `failed`
  - `recording_ready`
- CRM webhook endpoint (`handle_webhook`) для этой интеграции не используется и возвращает `ignored`.

## Настройки интеграции

Примечание по совместимости:
- Для пользователя AMI также поддерживается ключ `asterisk_ami_username` (алиас к `asterisk_ami_user`).
- Для пароля AMI также поддерживается ключ `asterisk_ami_secret` (алиас к `asterisk_ami_password`).

| Ключ | Обяз. | Тип данных | Наименование (RU / UZ / EN) | Описание (RU / UZ / EN) | Placeholder (RU / UZ / EN) |
|---|---|---|---|---|---|
| `asterisk_ami_host` | Да | String | `Хост AMI` / `AMI host` / `AMI host` | `Адрес Asterisk AMI` / `Asterisk AMI manzili` / `Asterisk AMI address` | `pbx.example.com` / `pbx.example.com` / `pbx.example.com` |
| `asterisk_ami_port` | Нет | Integer | `Порт AMI` / `AMI port` / `AMI port` | `Порт подключения AMI` / `AMI ulanish porti` / `AMI connection port` | `5038` / `5038` / `5038` |
| `asterisk_ami_user` | Да | String | `Пользователь AMI` / `AMI foydalanuvchisi` / `AMI username` | `Логин AMI пользователя` / `AMI foydalanuvchi logini` / `AMI login username` | `crm_integration` / `crm_integration` / `crm_integration` |
| `asterisk_ami_password` | Да | String | `Пароль AMI` / `AMI paroli` / `AMI password` | `Пароль AMI пользователя` / `AMI foydalanuvchi paroli` / `AMI user password` | `password_here` / `password_here` / `password_here` |
| `asterisk_pipeline_id` | Да | Integer | `ID воронки` / `Voronka ID` / `Pipeline ID` | `ID воронки для лидов` / `Lidlar uchun voronka ID` / `Pipeline id for leads` | `12` / `12` / `12` |
| `asterisk_channel_id` | Да | Integer | `ID канала` / `Kanal ID` / `Channel ID` | `ID канала CRM` / `CRM kanal ID` / `CRM channel id` | `5` / `5` / `5` |
| `asterisk_default_responsible_user_id` | Нет | Integer | `Ответственный по умолчанию` / `Standart mas'ul` / `Default responsible` | `ID ответственного, если не найден оператор` / `Operator topilmasa mas'ul ID` / `Responsible user id fallback` | `101` / `101` / `101` |
| `asterisk_assign_responsible_by_operator_ext` | Нет | Boolean | `Назначать по внутреннему номеру` / `Ichki raqam bo'yicha tayinlash` / `Assign by extension` | `Назначать лида по внутреннему номеру оператора` / `Lidni operator ichki raqami bo'yicha tayinlash` / `Assign lead by operator extension` | `true` / `true` / `true` |
| `asterisk_lead_subject_template` | Нет | String | `Шаблон темы лида` / `Lid sarlavha shabloni` / `Lead subject template` | `Шаблон названия лида` / `Lid nomi shabloni` / `Lead title template` | `Call {direction} {from_phone}` / `Call {direction} {from_phone}` / `Call {direction} {from_phone}` |
| `asterisk_allowed_did_list` | Нет | String | `Список DID` / `DID ro'yxati` / `DID list` | `Фильтр входящих по DID, через запятую` / `Kiruvchi DID filtri, vergul bilan` / `Inbound DID filter, comma-separated` | `998712000001,998712000002` / `998712000001,998712000002` / `998712000001,998712000002` |
| `asterisk_recording_base_url` | Нет | String | `Базовый URL записей` / `Yozuvlar bazaviy URL` / `Recording base URL` | `База ссылок для файлов записи` / `Yozuv fayllari uchun baza URL` / `Base URL for recording files` | `https://pbx.example.com/records/` / `https://pbx.example.com/records/` / `https://pbx.example.com/records/` |
| `asterisk_default_country_code` | Нет | String | `Код страны` / `Mamlakat kodi` / `Country code` | `Код страны для нормализации номеров` / `Raqamlarni normallashtirish uchun kod` / `Country code for number normalization` | `998` / `998` / `998` |
| `lead_dedupe_ttl_sec` | Нет | Integer | `TTL дедупликации` / `Deduplikatsiya TTL` / `Dedupe TTL` | `Срок защиты от дублей, сек` / `Dublikatdan himoya muddati, sek` / `Duplicate protection TTL, sec` | `86400` / `86400` / `86400` |
| `state_ttl_sec` | Нет | Integer | `TTL состояния` / `Holat TTL` / `State TTL` | `Срок хранения служебного состояния, сек` / `Xizmat holati saqlash muddati, sek` / `Runtime state TTL, sec` | `86400` / `86400` / `86400` |

## Порядок настройки внешней системы (Asterisk / FreePBX)

### 1. Включить AMI

- Asterisk:
  - В `manager.conf` в секции `[general]` включите AMI и укажите порт (обычно `5038`).
- FreePBX:
  - Включите AMI в настройках Asterisk Manager (путь может отличаться по версии FreePBX).

### 2. Создать отдельного AMI-пользователя для интеграции

- Рекомендуется отдельный пользователь, например `crm_integration`.
- Рекомендуемые права:
  - `read = call,cdr,reporting`
  - `write = system`
- Не выдавайте лишние права без необходимости.

### 3. Ограничить сетевой доступ к AMI

- Разрешите доступ к порту AMI только с IP сервера интеграции.
- Если интеграция и Asterisk на одном сервере, ограничьте доступ `127.0.0.1`.

### 4. Применить изменения на стороне Asterisk

- Перезагрузите manager-конфигурацию (`manager reload`) или примените изменения через интерфейс FreePBX.
- Убедитесь, что AMI-пользователь активен.

### 5. Заполнить настройки интеграции в CRM

- Обязательные:
  - `asterisk_ami_host`
  - `asterisk_ami_user`
  - `asterisk_ami_password`
  - `asterisk_pipeline_id`
  - `asterisk_channel_id`
- Необязательные: остальные ключи из таблицы выше.

### 6. Проверить рабочий сценарий

- Выполните входящий и исходящий тестовый звонок.
- Проверьте в CRM:
  - лид создается или переиспользуется;
  - этапы звонка приходят в чат;
  - запись разговора прикладывается при наличии;
  - статус и ответственный обновляются по логике настройки.
