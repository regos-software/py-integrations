# asterisk_crm_channel

## Назначение

Интеграция передает события звонков из Asterisk в CRM:

- создает или переиспользует активный лид по номеру клиента;
- пишет в чат лида этапы звонка;
- прикладывает запись разговора;
- меняет статус лида по ходу звонка.

## Режимы получения событий

Поддерживаются два режима.

1. `ari` (по умолчанию)

- Интеграция сама подключается к Asterisk ARI (`/ari/events`) по websocket.
- Внешний endpoint `/external` остается резервным источником.
- Для этого режима нужен ARI-пользователь и (обычно) `Stasis(...)` в диалплане.

2. `external_only`

- Интеграция не подключается к ARI.
- События принимаются только через `POST /clients/asterisk_crm_channel/external`.
- Подходит для FreePBX, если нельзя трогать текущий диалплан и очереди.

## Настройки интеграции

### Обязательные для всех режимов

- `asterisk_pipeline_id`: ID воронки CRM.
- `asterisk_channel_id`: ID канала CRM.

### Обязательные только для режима `ari`

- `asterisk_base_url`: адрес Asterisk (`http://IP:8088` или `https://domain`).
- `asterisk_ari_user`: логин ARI-пользователя.
- `asterisk_ari_password`: пароль ARI-пользователя.

### Необязательные

- `asterisk_ingest_mode`: режим получения событий (`ari` или `external_only`).
  - По умолчанию: `ari`.
- `asterisk_ari_app`: имя ARI-приложения.
  - По умолчанию: `crm_bridge`.
- `asterisk_default_responsible_user_id`: ответственный по умолчанию.
- `asterisk_lead_subject_template`: шаблон названия лида.
- `asterisk_allowed_did_list`: список DID-номеров для фильтра входящих.
- `asterisk_recording_base_url`: базовый URL для файлов записи.
- `lead_dedupe_ttl_sec`: время защиты от дублей.
- `state_ttl_sec`: время хранения служебного состояния.
- `reconcile_lookback_min`: окно сверки событий звонка.

## Флоу работы

1. Происходит звонок.
2. Интеграция получает событие (из ARI или через `/external`).
3. Определяется номер клиента и направление звонка.
4. Ищется активный лид, либо создается новый.
5. В чат лида записываются этапы звонка.
6. Когда появляется запись, она прикрепляется в тот же лид.
7. Статус лида обновляется автоматически, закрытые/конвертированные лиды не переоткрываются.

## Внешний endpoint (`external`)

Адрес:

- `POST /clients/asterisk_crm_channel/external`
- header: `connected-integration-id: <id>`

Тело может быть:

- один объект события;
- `{ "event": {...} }`;
- `{ "events": [{...}, {...}] }`;
- массив событий.

Минимально для нормализации нужны:

- идентификатор звонка (`external_call_id` или `linkedid/uniqueid/...`);
- статус (`started|ringing|answered|missed|completed|failed|recording_ready`);
- номера (`from_phone`/`to_phone` или их аналоги).

## Настройка FreePBX через интерфейс (без `Stasis`)

Этот вариант рекомендован, если у вас уже рабочая телефония/очереди и вы не хотите менять диалплан.

1. В настройках интеграции установите:

- `asterisk_ingest_mode=external_only`
- `asterisk_pipeline_id=<...>`
- `asterisk_channel_id=<...>`

2. В FreePBX создайте пользователя AMI (Asterisk Manager):

- обычно раздел `Admin` -> `Asterisk Manager Users`.

3. Разрешите доступ к AMI с сервера интеграции:

- через FreePBX Firewall (`Connectivity` -> `Firewall`),
- порт AMI обычно `5038`.

4. Ничего не меняйте в существующих `Inbound Routes`, `Queues`, `Ring Groups`.

5. Ваш текущий адаптер/скрипт, который слушает AMI/CEL/QueueLog, должен отправлять события в:

- `POST /clients/asterisk_crm_channel/external`

6. Выполните тест:

- входящий звонок;
- исходящий звонок;
- проверка, что лид создается/обновляется и события появляются в чате.

## Настройка режима `ari` (если нужен прямой поток из Asterisk)

1. Включите HTTP в `http.conf`.

Пример:

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
```

2. Включите ARI и создайте пользователя в `ari.conf`.

Пример:

```ini
[general]
enabled = yes
pretty = yes

[crm_user]
type = user
read_only = no
password = STRONG_PASSWORD
```

3. Перезагрузите модули Asterisk.

```text
module reload res_http_websocket.so
module reload res_ari.so
http show status
ari show users
```

4. Убедитесь, что имя приложения совпадает:

- в интеграции: `asterisk_ari_app` (или дефолт `crm_bridge`),
- в диалплане: `Stasis(<это же имя>)`.

Пример:

```ini
[from-trunk]
exten => _X.,1,NoOp(Inbound to CRM bridge)
 same => n,Stasis(crm_bridge)
 same => n,Hangup()
```

5. Заполните в CRM:

- `asterisk_ingest_mode=ari`
- `asterisk_base_url`
- `asterisk_ari_user`
- `asterisk_ari_password`
- `asterisk_pipeline_id`
- `asterisk_channel_id`

6. Сделайте тестовые звонки и проверьте лид/сообщения/записи.

## Частые вопросы

`Можно ли не использовать Stasis?`

- Да. Используйте `asterisk_ingest_mode=external_only` и отправку событий через `/external`.

`Нужен ли asterisk_account_key?`

- Нет. Эта настройка удалена.
