# TZ: asterisk_crm_channel

## 1. Цель

Интеграция `asterisk_crm_channel` принимает события звонков из Asterisk (ARI), обрабатывает их через централизованный асинхронный пайплайн, создает/находит активный `Lead` в CRM и фиксирует ход звонка в чате обращения.

Бизнес-результат:

- входящие и исходящие звонки отражаются в CRM в реальном времени;
- при первом контакте по номеру формируется обращение;
- запись звонка автоматически прикрепляется в чат обращения (или публикуется рабочая ссылка);
- повторные доставки событий остаются идемпотентными.

## 2. Каноническая модель интеграции

Ключ интеграции: `asterisk_crm_channel`.

Точки входа:

- `/clients/asterisk_crm_channel` (`Connect`, `ReConnect`, `Disconnect`, `UpdateSettings`);
- `/external/{connected_integration_id}/external/` для HTTP-событий от dialplan/агента;
- ARI WebSocket `ws(s)://<host>:<port>/<prefix>/ari/events`.

Единый принцип обработки:

1. Любой входящий источник приводит событие к одному нормализованному контракту.
2. Событие сразу ставится в Redis Stream.
3. Вся CRM-логика выполняется только воркерами Stream consumer group.
4. HTTP endpoint отвечает `200 OK` после успешной постановки в очередь.

## 3. Настройки (ConnectedIntegrationSetting)

Используются ключи в `lower_snake_case` без дублирующих синонимов.

Обязательные:

- `asterisk_enabled` (`bool`)
- `asterisk_account_key` (`string`)
- `asterisk_base_url` (`string`, содержит HTTP prefix, например `http://127.0.0.1:8088/vuetibhfocbz`)
- `asterisk_ari_app` (`string`)
- `asterisk_ari_user` (`string`)
- `asterisk_ari_password` (`string`)
- `asterisk_pipeline_id` (`int > 0`)
- `asterisk_channel_id` (`int > 0`)

Опциональные:

- `asterisk_default_responsible_user_id` (`int > 0`)
- `asterisk_lead_subject_template` (`string`, default: `Call {direction} {from_phone}`)
- `asterisk_allowed_did_list` (`string`, CSV)
- `asterisk_recording_base_url` (`string`)
- `lead_dedupe_ttl_sec` (`int >= 60`, default: `86400`)
- `state_ttl_sec` (`int >= 60`, default: `86400`)
- `reconcile_lookback_min` (`int >= 1`, default: `120`)

Производные значения:

- `asterisk_hash = md5(asterisk_account_key)`
- `normalized_phone = normalize(phone)` (цифры, канонический формат интеграции)

## 4. Нормализованный контракт события звонка

Минимальные поля:

- `event_id`
- `external_call_id` (приоритетно `linkedid`)
- `asterisk_hash`
- `direction` (`inbound` | `outbound`)
- `from_phone`
- `to_phone`
- `client_phone` (номер, по которому ведется lead-корреляция)
- `status` (`started`, `ringing`, `answered`, `missed`, `completed`, `failed`, `recording_ready`)
- `event_ts`
- `talk_duration_sec` (optional)
- `recording_url` (optional)
- `operator_ext` (optional)
- `raw_payload`

Генерация `event_id`:

- если источник передал `event_id`, используется он;
- иначе: `md5(external_call_id + ":" + status + ":" + event_ts)`.

## 5. CRM-корреляция и единая логика Lead

Ключи корреляции:

- `connected_integration_id`
- `asterisk_hash`
- `normalized_phone`
- `external_call_id`

Каноничное заполнение `Lead/Add`:

- `channel_id = asterisk_channel_id`
- `pipeline_id = asterisk_pipeline_id`
- `responsible_user_id = asterisk_default_responsible_user_id` (если задан)
- `client_phone = normalized_phone`
- `subject = render(asterisk_lead_subject_template)`
- `external_contact_id = ast:{asterisk_hash}:{normalized_phone}`
- `bot_id = asterisk_hash`
- `external_chat_id = normalized_phone`

Алгоритм `resolve_or_create_active_lead`:

1. Проверка Redis mapping по телефону.
2. Если mapping отсутствует: `Lead/Get` по `bot_id + external_contact_id` и статусам `New/InProgress/WaitingClient`.
3. Если активный лид найден: кэширование mapping.
4. Если активный лид не найден: `Lead/Add`, затем `Lead/Get` для получения `chat_id`, затем кэширование mapping.
5. Создание нового лида защищается distributed lock по `(connected_integration_id, asterisk_hash, normalized_phone)`.

## 6. Логика сообщений в чат CRM

Для каждого нормализованного call-события формируется CRM-сообщение с `external_message_id`:

- `astmsg:{asterisk_hash}:{external_call_id}:{status}:{event_id}`

Запись в CRM:

- `ChatMessage/Add` в чат лида;
- при `recording_ready`:
1. попытка загрузить запись и отправить как файл через `ChatMessage/AddFile`;
2. публикация системного/обычного текстового сообщения со ссылкой, если файл недоступен.

Обработка ошибки закрытой связанной сущности (`error=1220`):

Для call-state событий (`started`, `ringing`, `answered`, `missed`, `completed`, `failed`):

1. Сбросить mapping для старой связки.
2. Выполнить `resolve_or_create_active_lead`.
3. Повторить `ChatMessage/Add` один раз с новым `lead_id/chat_id`.
4. Если повтор неуспешен, событие идет в retry/DLQ.

Для `recording_ready`:

1. Обработать событие как `late_recording_closed_lead`.
2. Сохранить `recording_url` и метаданные звонка в audit/reconcile state.
3. Завершить обработку события без создания нового лида.

## 7. Политика статусов лида

Статусы меняются централизованно через `Lead/Edit` (best-effort):

- `InProgress`:
  - входящий звонок (`direction=inbound`) со статусами `started|ringing|answered`;
  - исходящий звонок после фактического ответа клиента (`direction=outbound`, `status=answered`).
- `WaitingClient`:
  - исходящий звонок оператора со статусами `started|ringing`.

Терминальные статусы (`Closed`, `Converted`) не перезаписываются.

## 8. Redis: централизация ключей

Префикс: `clients:asterisk_crm_channel:`

Системные ключи:

- `settings:{connected_integration_id}`
- `active_ci_ids`
- `stream:asterisk_in:{connected_integration_id}`
- `stream:dlq:{connected_integration_id}`
- `worker:heartbeat:{connected_integration_id}:{instance_id}`
- `lock:ari_consumer:{connected_integration_id}`
- `lock:create_lead:{connected_integration_id}:{asterisk_hash}:{normalized_phone}`
- `dedupe:event:{connected_integration_id}:{event_id}`

Централизованный mapping (единый payload):

- `mapping:by_phone:{connected_integration_id}:{asterisk_hash}:{normalized_phone}`
- `mapping:by_call:{connected_integration_id}:{asterisk_hash}:{external_call_id}`

Оба mapping-ключа хранят одинаковый JSON:

- `lead_id`
- `chat_id`
- `asterisk_hash`
- `normalized_phone`
- `external_call_id`
- `last_event_ts`

TTL-политика:

- ключи runtime-состояния всегда создаются с явным TTL;
- `TTL=1` для любых ключей интеграции запрещен;
- бессрочные runtime-ключи (`TTL=-1`) запрещены;
- `dedupe:event:*` использует `lead_dedupe_ttl_sec` (`>= 60`);
- `mapping:*`, `settings:*` используют `state_ttl_sec` (`>= 60`);
- `lock:*` и `worker:heartbeat:*` используют фиксированный операционный TTL `>= 30`.

## 9. Надежность и кластер

Базовый runtime-контур:

- Redis Streams + consumer group;
- retry с ограничением попыток;
- DLQ для финально неуспешных событий;
- идемпотентность на уровне `event_id`;
- единственный активный ARI consumer на `connected_integration_id` через leader lock;
- горизонтальная масштабируемость воркеров обработки.

Reconcile:

- после перезапуска сервиса/Redis интеграция выполняет восстановление состояния за окно `reconcile_lookback_min`;
- в процессе reconcile восстанавливаются mapping-ключи и незавершенные call-связки.

## 10. Безопасность и наблюдаемость

Безопасность:

- маскирование auth-данных в логах;
- хранение секретов только в интеграционных настройках;
- доступ к Asterisk API через локальный контур или доверенный reverse proxy.

Наблюдаемость:

- метрики подключения/переподключения ARI;
- счетчики processed/retried/dlq;
- счетчики lead_created/lead_reused;
- счетчики recording_attached/recording_link_fallback;
- отдельные счетчики обработки `error=1220`, успешных повторов и `late_recording_closed_lead`.

## 11. Используемые REGOS API методы

- `Lead/Get`, `Lead/Add`, `Lead/Edit`
- `ChatMessage/Add`, `ChatMessage/Get`
- `ChatMessage/AddFile`
- `ConnectedIntegrationSetting/Get`

## 12. Критерии приемки

1. Входящий звонок создает или находит активный лид и добавляет событие в чат.
2. Повторная доставка того же call-события не создает дубли сообщений.
3. `recording_ready` прикрепляет файл записи в чат, ссылка работает как fallback.
4. Обработка `error=1220` для call-state событий приводит к созданию/поиску нового активного лида и успешному повтору записи сообщения.
5. Обработка `error=1220` для `recording_ready` завершается как `late_recording_closed_lead` с сохранением `recording_url` в состоянии reconcile.
6. Интеграция стабильно работает при нескольких инстансах и нескольких `connected_integration_id`.
7. После восстановления Redis reconcile возвращает рабочие mapping-связи.

## 13. Deliverables

- `clients/asterisk_crm_channel/main.py`
- `clients/asterisk_crm_channel/README.md`
- регистрация клиента в `routes/clients.py`
- runbook с настройками и операционными шагами reconnect/reconcile
