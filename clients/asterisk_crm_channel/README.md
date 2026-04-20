# asterisk_crm_channel

## Назначение
Интеграция синхронизирует события звонков Asterisk с CRM-чатом обращения (ticket).

Ключевая модель работы: **1 звонок = 1 обращение**.

## Текущая логика (ticket-only)
1. Для каждого события обязателен `external_call_id`.
2. `external_call_id` используется как `external_dialog_id` в CRM ticket.
3. При обработке события интеграция:
   - ищет ticket по `external_dialog_id`;
   - если ticket не найден, создает новый ticket;
   - сохраняет mapping только по `external_call_id`.
4. Повторные события того же звонка всегда пишутся в тот же ticket.
5. Если ticket уже закрыт и `ChatMessage/Add` возвращает ошибку 1220, интеграция **не** создает новый ticket и **не** переоткрывает старый.


## Обрабатываемые события
События звонков от Asterisk (через AMI и/или `/external`):
- `started`
- `ringing`
- `answered`
- `missed`
- `completed`
- `failed`
- `recording_ready`

`handle_webhook` для этой интеграции не используется и возвращает `ignored`.

## Настройки интеграции
Совместимость алиасов:
- `asterisk_ami_username` -> `asterisk_ami_user`
- `asterisk_ami_secret` -> `asterisk_ami_password`

| Ключ | Обяз. | Тип | Описание |
|---|---|---|---|
| `asterisk_ami_host` | Да | String | Хост Asterisk AMI |
| `asterisk_ami_port` | Нет | Integer | Порт AMI (по умолчанию `5038`) |
| `asterisk_ami_user` | Да | String | Логин AMI |
| `asterisk_ami_password` | Да | String | Пароль AMI |
| `asterisk_channel_id` | Да | Integer | ID CRM-канала для ticket |
| `asterisk_default_responsible_user_id` | Нет | Integer | Ответственный по умолчанию при создании ticket |
| `asterisk_assign_responsible_by_operator_ext` | Нет | Boolean | Назначать ответственного по внутреннему номеру оператора |
| `asterisk_lead_subject_template` | Нет | String | Шаблон темы ticket (историческое имя ключа сохранено) |
| `asterisk_allowed_did_list` | Нет | String | Список trunk/DID через запятую для определения направления |
| `asterisk_recording_base_url` | Нет | String | Базовый URL для относительных ссылок на записи |
| `asterisk_default_country_code` | Нет | String | Код страны для нормализации номеров |
| `lead_dedupe_ttl_sec` | Нет | Integer | TTL дедупликации событий |
| `state_ttl_sec` | Нет | Integer | TTL служебного state/mapping |
| `asterisk_message_language` | Нет | String | Язык системных сообщений (`ru`, `uz`, `en`) |


## Поведение записи разговора (`asterisk_recording_base_url`)
- Если в событии уже полный URL (`http://` или `https://`) — используется он.
- Если приходит относительный путь, формируется URL через `urljoin(base_url, recording_file)`.
- Если `base_url` не задан и путь относительный — вложение может не скачаться, в чат уйдет текст без файла.

## Проверка активности интеграции
- Интеграция учитывает `ConnectedIntegration.is_active`.
- При `is_active = false` воркеры AMI/stream не поднимаются, `/external` события игнорируются.

## Быстрый запуск
1. Включить AMI на стороне Asterisk/FreePBX.
2. Создать отдельного AMI-пользователя с минимально необходимыми правами.
3. Ограничить доступ к AMI по IP сервера интеграции.
4. Заполнить настройки интеграции в CRM (обязательные: `asterisk_ami_host`, `asterisk_ami_user`, `asterisk_ami_password`, `asterisk_channel_id`).
5. Выполнить тестовый входящий и исходящий звонок.
6. Проверить, что события одного `external_call_id` попадают в один и тот же ticket.
