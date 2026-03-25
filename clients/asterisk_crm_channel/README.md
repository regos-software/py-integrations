# asterisk_crm_channel

## Назначение

Интеграция работает в режиме AMI и передает события звонков из Asterisk в CRM:

- создает или переиспользует активный лид по номеру клиента;
- пишет этапы звонка в чат лида;
- прикладывает запись разговора;
- обновляет статус лида по логике звонка.

## Режим работы

Поддерживаемый рабочий режим: AMI.

- интеграция подключается к Asterisk Manager Interface;
- поток событий берется из AMI, без `Stasis(...)`;
- `/external` остается как резервный endpoint для внешней подачи событий.

## Настройки интеграции

### Обязательные

- `asterisk_ami_host`: адрес Asterisk AMI (IP/домен).
- `asterisk_ami_user`: логин AMI-пользователя.
- `asterisk_ami_password`: пароль AMI-пользователя.
- `asterisk_pipeline_id`: ID воронки CRM.
- `asterisk_channel_id`: ID канала CRM.

### Необязательные

- `asterisk_ami_port`: порт AMI.
- `asterisk_default_responsible_user_id`: ответственный по умолчанию.
- `asterisk_lead_subject_template`: шаблон названия лида.
- `asterisk_allowed_did_list`: список DID-номеров для фильтра входящих.
- `asterisk_recording_base_url`: базовый URL для файлов записи.
- `lead_dedupe_ttl_sec`: время защиты от дублей.
- `state_ttl_sec`: время хранения служебного состояния.
- `reconcile_lookback_min`: окно сверки событий звонка.

Значение по умолчанию для `asterisk_ami_port`: `5038`.

## Флоу работы

1. В Asterisk происходит звонок.
2. Интеграция получает события этого звонка через AMI.
3. Определяются номер клиента и направление звонка.
4. Ищется активный лид или создается новый.
5. Этапы звонка пишутся в чат лида.
6. Если появляется запись разговора, она прикрепляется в тот же лид.
7. Статус лида обновляется по этапам звонка.

## Порядок настройки на стороне Asterisk (AMI)

1. Откройте `manager.conf` и включите AMI в секции `[general]`:
```ini
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0
```

2. Ограничьте сетевой доступ к AMI:
- откройте порт `5038` только для IP сервера интеграции;
- если интеграция стоит на том же сервере, используйте только `127.0.0.1`.

3. Создайте отдельного AMI-пользователя для интеграции в `manager.conf`:
```ini
[crm_integration]
secret = CHANGE_ME_STRONG_PASSWORD
deny = 0.0.0.0/0.0.0.0
permit = 10.10.10.25/255.255.255.255
read = call,cdr,reporting
write = system
writetimeout = 1000
```

4. Не выдавайте лишние права:
- не используйте `write=originate`;
- не добавляйте `write=config,command,dialplan,user,agent` без реальной необходимости;
- для этой интеграции обычно достаточно `read=call,cdr,reporting` и `write=system`.

5. Примените конфигурацию:
```bash
asterisk -rx "manager reload"
```

6. Проверьте, что пользователь активен:
```bash
asterisk -rx "manager show users"
```

7. Заполните настройки интеграции в CRM:
- `asterisk_ami_host`
- `asterisk_ami_port` (если не `5038`)
- `asterisk_ami_user`
- `asterisk_ami_password`
- `asterisk_pipeline_id`
- `asterisk_channel_id`

8. Выполните тест:
- один входящий звонок;
- один исходящий звонок;
- проверка: лид создается или обновляется, этапы пишутся в чат, запись привязывается к лиду.

## FreePBX

Для FreePBX используйте AMI-пользователя, которого создает или обслуживает FreePBX, и откройте доступ к AMI только для сервера интеграции. Маршрутизацию через `Stasis(...)` настраивать не нужно.
