# EDO Didox Technical Notes

## Назначение

`edo_didox` изолирует обмен REGOS CRM с Didox. Общие части проекта используются только через `core`: Regos API, Redis и настройки.

Автоподпись сейчас не реализована: исходящий документ создается в Didox как черновик, после чего подписывается пользователем в Didox.

## Подключение

- `connect`, `reconnect`, `update_settings` запускают воркеры Redis stream.
- `disconnect` останавливает воркеры.
- `check` выполняет авторизацию в Didox и получает первую страницу входящих документов.

## Настройки подключенной интеграции

| Ключ | Обяз. | Назначение |
|---|---|---|
| `DIDOX_PARTNER_TOKEN` | Да | Partner token для Didox API. |
| `DIDOX_PASSWORD` | Да | Пароль пользователя Didox. |
| `DIDOX_LOGIN_TAX_ID` | Нет | ИНН пользователя для входа. Если пусто, используется ИНН компании. |
| `DIDOX_COMPANY_TAX_ID` | Нет | ИНН компании. Если пусто, используется `Firm.inn`. |
| `DIDOX_BASE_URL` | Нет | API endpoint. По умолчанию `https://api-partners.didox.uz`. |
| `DIDOX_LOCALE` | Нет | Locale для Didox API. По умолчанию `ru`. |
| `DIDOX_DOCUMENT_TYPES` | Нет | Типы документов для списка через запятую. По умолчанию `002,005,008,023`. |

## Env

| Env | Default | Назначение |
|---|---:|---|
| `EDO_DIDOX_STREAM_WORKERS` | `2` | Количество воркеров stream. |
| `EDO_DIDOX_STREAM_BATCH_SIZE` | `20` | Размер пачки чтения stream. |
| `EDO_DIDOX_STREAM_MAXLEN` | `100000` | Ограничение длины stream. |
| `EDO_DIDOX_STREAM_RETRY_LIMIT` | `3` | Количество повторов задачи. |
| `EDO_DIDOX_STREAM_TTL` | `86400` | TTL dedupe ключей и pending-записей stream. |
| `EDO_DIDOX_TOKEN_CACHE_TTL` | `21000` | TTL кеша access token в Redis. |

## Redis

| Ключ | Назначение |
|---|---|
| `edo:didox:stream` | Единый stream задач интеграции. |
| `edo:didox:dedupe:<ci>:<firm_id>:<action>:<object_id>` | Dedupe для параллельных задач импорта/экспорта. |
| `edo:didox:token:<ci>:<firm_id>` | Кеш access token Didox. |

## Didox API

- Авторизация: `POST /v1/auth/{taxId}/password/{locale}`.
- Переключение компании: `POST /v1/auth/company/{companyTaxId}/login/{locale}`.
- Список документов: `GET /v2/documents`.
- Содержимое документа: `GET /v1/documents/{id}`.
- Создание черновика счета-фактуры: `POST /v1/documents/002/create/{locale}`.

Основной документ для исходящей отправки: Didox `002` invoice.

## Idempotency

Для входящих документов постоянная связка хранится в CRM через `DocInvoice.external_code`. Перед созданием документа выполняется `DocInvoice/Get` по `external_code`.

Для исходящих документов повторная отправка не выполняется, если у CRM документа уже заполнен `external_code` и статус находится в процессе отправки или успешно отправлен.

## Ограничения

- Вебхуки Didox не используются.
- Автоматическое подписание документов не выполняется.
- При ошибке обработки статус CRM документа переводится в `ErrorSent` или `ErrorReceived` с текстом ошибки.
