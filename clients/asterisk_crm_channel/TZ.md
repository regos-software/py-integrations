# TZ: asterisk_crm_channel

## 1. Цель

Реализовать интеграцию `asterisk_crm_channel`, которая получает события звонков из Asterisk (ARI), создает/находит обращения в CRM и пишет события звонка в чат обращения.

Результат для бизнеса:

- входящие/исходящие звонки фиксируются в CRM;
- при первом контакте автоматически создается `Lead`;
- запись звонка прикрепляется в чат обращения (или отправляется ссылка на запись).

## 2. Исходные условия

По вашему серверу:

- включен Asterisk HTTP/ARI;
- HTTP Prefix: `/vuetibhfocbz`;
- сервер Asterisk слушает `127.0.0.1:8088`;
- доступны URI: `/ari/...`, `/ws`, `/metrics/...`.

Вывод:

- интеграция должна подключаться к Asterisk локально (на том же сервере), либо через reverse proxy;
- во все Asterisk URL обязательно добавлять prefix `/vuetibhfocbz`.

## 3. Границы MVP

Входит в MVP:

- подписка на поток событий ARI (WebSocket);
- нормализация событий звонка;
- поиск/создание `Lead` по номеру телефона;
- запись событий звонка в чат `Lead`;
- обработка события готовности записи и прикрепление файла;
- работа с несколькими `connected_integration_id`;
- корректная работа в кластере (несколько инстансов интеграции).

Не входит в MVP:

- управление звонком из CRM (answer/hold/transfer/hangup);
- полноценная call-center аналитика;
- потоковая передача аудио в реальном времени.

## 4. Модель интеграции

Ключ интеграции:

- `asterisk_crm_channel` (lower snake_case).

Точки входа:

- `/clients/asterisk_crm_channel` (`Connect`, `ReConnect`, `Disconnect`, `UpdateSettings`);
- `/external/{connected_integration_id}/external/` (опционально для HTTP-событий от dialplan/агента);
- `/webhook/{connected_integration_id}/` (входящие webhook REGOS, если понадобятся).

Важно:

- для HTTP webhook: сначала `200 OK`, затем асинхронная обработка.

## 5. Настройки (single account)

Набор настроек для одного Asterisk-аккаунта:

1. `ASTERISK_ENABLED`  
Тип: bool  
Описание: включает/выключает интеграцию.

2. `ASTERISK_ACCOUNT_KEY`  
Тип: string  
Описание: стабильный уникальный ключ экземпляра Asterisk; используется для вычисления `asterisk_hash`.

3. `ASTERISK_BASE_URL`  
Тип: string  
Описание: базовый URL Asterisk с prefix, пример: `http://127.0.0.1:8088/vuetibhfocbz`.

4. `ASTERISK_ARI_APP`  
Тип: string  
Описание: имя ARI приложения (`Stasis app`), события которого слушает интеграция.

5. `ASTERISK_ARI_USER`  
Тип: string  
Описание: ARI username.

6. `ASTERISK_ARI_PASSWORD`  
Тип: string  
Описание: ARI password.

7. `ASTERISK_PIPELINE_ID`  
Тип: int  
Описание: pipeline для создания `Lead`.

8. `ASTERISK_CHANNEL_ID`  
Тип: int  
Описание: CRM channel для `Lead`.

9. `ASTERISK_DEFAULT_RESPONSIBLE_USER_ID`  
Тип: int, optional  
Описание: ответственный по умолчанию.

10. `ASTERISK_LEAD_SUBJECT_TEMPLATE`  
Тип: string, optional  
Описание: шаблон темы лида, например: `Call {direction} {from_phone}`.

11. `ASTERISK_ALLOWED_DID_LIST`  
Тип: string, optional  
Описание: список разрешенных DID/входящих номеров (через запятую).

12. `ASTERISK_RECORDING_BASE_URL`  
Тип: string, optional  
Описание: URL для скачивания записей (если запись отдается HTTP).

13. `ASTERISK_RECONCILE_ENABLED`  
Тип: bool  
Описание: включить восстановление состояния после рестарта/потери Redis.

14. `ASTERISK_RECONCILE_LOOKBACK_MIN`  
Тип: int  
Описание: окно истории (в минутах) для reconcile.

Общие:

- `LEAD_DEDUPE_TTL_SEC`
- `STATE_TTL_SEC`

Внутренний идентификатор:

- `asterisk_hash = md5(ASTERISK_ACCOUNT_KEY)`.

## 6. Нормализованный контракт события звонка

Минимальные поля после нормализации:

- `event_id`
- `external_call_id` (предпочтительно `linkedid`)
- `asterisk_hash`
- `direction` (`inbound` / `outbound`)
- `from_phone`
- `to_phone`
- `status` (`started`, `ringing`, `answered`, `missed`, `completed`, `failed`, `recording_ready`)
- `event_ts`
- `talk_duration_sec` (optional)
- `recording_url` (optional)
- `operator_ext` (optional)
- `raw_payload`

Если `event_id` не пришел из источника, вычисляется детерминированно из `external_call_id + status + event_ts`.

## 7. Источники событий Asterisk

Основной источник (MVP):

- ARI WebSocket: `ws(s)://<host>:<port>/<prefix>/ari/events?...`

Целевые события:

- `StasisStart`
- `ChannelStateChange`
- `Dial`
- `ChannelHangupRequest`
- `ChannelDestroyed`
- события записи (`RecordingStarted`, `RecordingFinished` или эквивалентный поток вашего сценария)

Опциональный источник:

- HTTP push от dialplan/внешнего агента на `/external/{connected_integration_id}/external/`.

## 8. Бизнес-флоу

1. Интеграция подключается к ARI и получает событие звонка.
2. Событие нормализуется и ставится в Redis Stream.
3. Worker проверяет идемпотентность события.
4. По номеру телефона ищется активный `Lead`.
5. Если активного `Lead` нет, создается новый в `ASTERISK_PIPELINE_ID` / `ASTERISK_CHANNEL_ID`.
6. В чат обращения добавляется сообщение о состоянии звонка.
7. При `recording_ready` запись прикрепляется в чат (или отправляется ссылка fallback).
8. Повторные доставки/повторы Asterisk не создают дубликаты в CRM.

## 9. Правила маппинга в CRM

Ключи корреляции:

- `connected_integration_id`
- `asterisk_hash`
- нормализованный номер телефона
- `external_call_id`

Поля `Lead/Add`:

- `channel_id = ASTERISK_CHANNEL_ID`
- `pipeline_id = ASTERISK_PIPELINE_ID`
- `responsible_user_id = ASTERISK_DEFAULT_RESPONSIBLE_USER_ID` (optional)
- `client_phone` = номер клиента
- `subject` = шаблон/дефолт
- `external_contact_id = ast:{asterisk_hash}:{normalized_phone}`
- `bot_id = asterisk_hash`
- `external_chat_id` = стабильный call/party id (если применимо)

Примечание:

- `dedupe_key` не используется.

## 10. Надежность и кластер

Обязательно:

- Redis обязателен;
- обработка через Redis Streams + consumer group;
- retry + DLQ;
- идемпотентность событий;
- distributed lock для критических секций (создание лида);
- только один активный ARI consumer на `connected_integration_id` (leader lock);
- изоляция ключей Redis по `connected_integration_id`.

Сценарий потери Redis:

- маппинги восстанавливаются из CRM и/или reconcile из истории Asterisk.

## 11. Безопасность

- не логировать `ASTERISK_ARI_PASSWORD` и секреты;
- маскировать auth-заголовки;
- валидировать входящие HTTP события (если используются);
- ограничить доступ к Asterisk API (лучше localhost/reverse proxy/IP allowlist).

## 12. Наблюдаемость

Логи/метрики:

- подключения/переподключения ARI;
- принято/обработано/повторно обработано/в DLQ;
- создано лидов / найдено существующих;
- ошибки прикрепления записей;
- reconcile summary.

## 13. Достаточность REGOS API

Для MVP достаточно текущего API:

- `Lead/Get`, `Lead/Add`, `Lead/Edit`, `Lead/Close`
- `ChatMessage/Add`, `ChatMessage/Get`, `ChatMessage/MarkSent`
- `ChatMessage/AddFile`
- `ConnectedIntegrationSetting/Get`
- `ConnectedIntegration/Edit` (если нужны подписки webhook REGOS)

## 14. Критерии приемки

- входящий звонок создает/находит `Lead` и пишет событие в чат;
- повтор одного и того же события не создает дублей;
- запись звонка прикрепляется как файл или отправляется ссылкой;
- интеграция работает с несколькими `connected_integration_id`;
- корректная работа при нескольких инстансах;
- после перезапуска Redis состояние восстанавливается reconcile-механизмом.

## 15. Deliverables

- `clients/asterisk_crm_channel/main.py`
- `clients/asterisk_crm_channel/README.md`
- регистрация клиента в `routes/clients.py`
- runbook с примерами env и шагами reconnect
