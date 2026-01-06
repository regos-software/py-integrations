# Python REGOS Integrations Service

Сервис-шлюз на **FastAPI** для интеграций с REGOS и внешними провайдерами (Telegram-бот, СМС-шлюзами, системами ЭДО и др.).
Проект предоставляет единый REST‑интерфейс для вызовов REGOS API, а также инфраструктуру для
подключения и регистрации новых **API‑сервисов** (оберток над методами REGOS) и новых **clients** (тиражируемых интеграций).

---
## Как работать с репозиторием

### Ветка `main`
Ветка **main** используется для хранения актуального кода, который развернут на продакшн-сервере.  
- В неё попадают только проверенные и стабильные изменения.  
- Внесение правок в `main` допускается **только в случае критических багфиксов**.  
- Все остальные изменения проходят через ветку `dev`.  

### Ветка `dev`
Ветка **dev** предназначена для разработки и тестирования.  
- При работе над задачами создавайте отдельные ветки от `dev`.  
- После завершения задачи отправляйте **pull request** в `dev`.  
- После успешного ревью изменения автоматически публикуются на dev-сервере для тестирования.  
- Если тестирование прошло успешно, изменения из `dev` мержатся в `main`, и обновлённый код публикуется на продакшн-сервере.  


## Как добавить новый API‑сервис (обертку REGOS)

**Цель:** добавить новый метод/набор методов REGOS в фасад `RegosAPI`, чтобы ими могли пользоваться клиенты.

1) **Создайте Pydantic‑схемы** для запросов/ответов в `schemas/api/...`  
   Пример (сокр.): `schemas/api/docs/cheque.py` объявляет `DocChequeGetRequest`, `DocCheque`.

2) **Создайте сервис‑обертку** в `core/api/<домейн>/<имя>.py`  
   Сервис должен использовать `self.api.call(...)` и возвращать валидированные модели.
   Пример: `core/api/docs/cheque.py`:
   ```python
   class DocsChequeService:
       PATH_GET = "DocCheque/Get"
       def __init__(self, api): self.api = api
       async def get(self, req: DocChequeGetRequest) -> list[DocCheque]:
           resp = await self.api.call(self.PATH_GET, req, APIBaseResponse)
           ...
           return [DocCheque.model_validate(x) for x in resp.result]
   ```

3) **Подключите сервис к фасаду `RegosAPI`**  
   Откройте `core/api/regos_api.py` и добавьте инициализацию сервиса
   в соответствующий раздел (например, `class Docs`, `class Integrations`, `class Reports`):
   ```python
   class Docs:
       def __init__(self, api: "RegosAPI"):
           from core.api.docs.cheque import DocsChequeService
           self.cheque = DocsChequeService(api)
   ```
   Тогда использовать можно так:
   ```python
   async with RegosAPI(connected_integration_id) as api:
       cheques = await api.docs.cheque.get(DocChequeGetRequest(...))
   ```

4) **(Опционально) Кэширование/ретраи**  
   - Базовый HTTP‑клиент: `core/api/client.py` (`APIClient`).  
   - Экспоненциальные ретраи на уровне `RegosAPI` уже настроены (`tenacity`).

---

## Standards and conventions
- Schemas: `schemas/api/readme.md`
- Services: `core/api/readme.md`

## Как добавить и зарегистрировать нового клиента (integration)

**Цель:** реализовать нового провайдера/канал интеграции (например, WhatsApp, e‑mail, иной SMS‑провайдер).

1) **Выберите базовый интерфейс**
   - Общий интерфейс: `schemas/integration/integration_base.py` → `IntegrationBase` (абстрактные методы: `connect`, `disconnect`, `reconnect`, `handle_webhook`, `update_settings`, `handle_external`).
   - Для SMS: `schemas/integration/sms_integration_base.py` → `IntegrationSmsBase` (наследует `IntegrationBase`, добавляет `send_messages`).
   - Для Telegram: `schemas/integration/telegram_integration_base.py` → `IntegrationTelegramBase` (наследует `IntegrationBase`, добавляет `send_messages`).

2) **Создайте клиент**
   - Поместите код в `clients/<your_client>/main.py`.
   - Наследуйтесь от подходящей базы (`ClientBase` из `clients/base.py` или от профильного абстрактного класса).  
   - Реализуйте необходимые методы. Смотрите существующие примеры:
     - `clients/telegram_bot_notification/main.py`
     - `clients/eskiz_sms/main.py`
     - `clients/getsms/main.py`

3) **Подключите клиента в роутер**
   - В `routes/clients.py` добавьте импорт класса вашего клиента и зарегистрируйте его в маппинге клиентов (словарь вида `{"telegram_bot_notification": TelegramBotNotificationClient, "eskiz_sms": EskizSmsClient, ...}`).

   - Имя ключа (например, `"eskiz_sms"`) будет использоваться в URL: `/clients/eskiz_sms/...`.

4) **Работа с REGOS из клиента**
   - Используйте фасад `RegosAPI`:
     ```python
     async with RegosAPI(connected_integration_id) as api:
         cheques = await api.docs.cheque.get_by_uuids([...])
     ```
   - Общие модели запросов/ответов REGOS находятся в `schemas/api/**`.

5) **Настройки клиента**
   - Храните и получайте настройки подключённой интеграции через сервис `api.integrations.connected_integration_setting`:
     ```python
     settings = await api.integrations.connected_integration_setting.get(
         ConnectedIntegrationSettingRequest(connected_integration_id=connected_integration_id)
     )
     ```

6) **Входящие вебхуки и внешние вызовы**
   - `handle_webhook(self, data: dict)` — обработка входящих событий от REGOS.
   - `handle_external(self, data: dict)` — обработка внешних запросов (не из REGOS), приходит весь пакет (`method`, `headers`, `query`, `json` и пр.).
   - Оба метода должны возвращать структурированный ответ (`IntegrationSuccessResponse`/`IntegrationErrorResponse`)

7) **Таймауты/ретраи/очереди**
   - Для долгих операций используйте `asyncio` и, при необходимости, ретраи (`tenacity` уже используется в примерах).
   - Если задействуете Redis — смотрите `core/redis.py` (кэш, TTL берется из настроек).

**Минимальный шаблон клиента**
```python
# clients/my_service/main.py
from clients.base import ClientBase
from schemas.integration.base import IntegrationSuccessResponse, IntegrationErrorResponse

class MyServiceClient(ClientBase):
    async def connect(self):
        return {"ok": True, "message": "connected"}

    async def handle_webhook(self, data: dict):
        try:
            # ваша логика
            return IntegrationSuccessResponse(ok=True, result={"handled": True})
        except Exception as e:
            return IntegrationErrorResponse(
                ok=False, error=500, description=f"webhook error: {e}"
            )
```

---

## Стандарты и соглашения

- **Именование клиентов** — папка `clients/<client_key>/`, класс `*Client` в `main.py`, ключ регистрации — `client_key`.
- **Именование API‑сервисов** — модуль `core/api/<домейн>/<имя>.py`, класс `*Service`, доступ через `api.<домейн>.<имя>`.
- **Схемы** — только Pydantic v2 (см. существующие модели).
- **Ответы роутов** — используйте `IntegrationSuccessResponse`/`IntegrationErrorResponse` для универсальности.
- **Логирование** — через `core.logger.setup_logger` с именем компонента.

---

## Отладка и логи

- Уровень логов задаётся `LOG_LEVEL`/`log_level` в `.env` (см. `config/settings.py`).
- Для сетевых вызовов REGOS используется `httpx`, логгер `api_client`/`regos_api` помогает найти ошибку в трейсах.

---


