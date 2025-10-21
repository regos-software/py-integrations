# Конвенции для сервисов (`services/*`)

> Этот README фиксирует единые правила написания сервисов, которые вызывают бэкенд‑API через общий клиент `api.call(...)`.
> **Важно:** `RetailCustomer` в примерах — лишь шаблон. В реальном коде подставляется **любая** сущность.  
> **Имена методов в коде — в `snake_case`**, полученные из названий действий в документации к API путём конвертации (например, `DeleteMark` → `delete_mark`, `GetByID` → `get_by_id`).  
> **Константы путей (`PATH_*`) — ровно как в серверной документации** (регистр и написание сохраняются).

---

## 1) Область ответственности сервиса
- Инкапсулирует вызовы эндпоинтов конкретной сущности/домена.
- Не содержит бизнес‑логики, только тонкие вызовы `api.call(...)`.
- Транспортные детали (ретраи, таймауты, парсинг ошибок) живут внутри общего клиента `api`.

---

## 2) Структура проекта

```
services/
  <domain>/
    <entity_snake>.py      # один файл = одна сущность (например, references/retail_customer.py)
core/
  logger.py
schemas/
  api/
    <domain>/
      <entity_snake>.py    # pydantic‑схемы запросов/ответов
```

Внутри файла сервиса: импорты → логгер → класс сервиса → константы путей → конструктор → методы.

---

## 3) Импорты, типы и аннотации
- В каждом файле: `from __future__ import annotations`.
- DTO запросов/ответов берём из `schemas.api.<domain>.<entity_snake>`.
- Возвращаемый тип **соответствует фактическому**: чаще всего `APIBaseResponse` (или специализированный/дженерик‑вариант, если предусмотрен контрактом).

Пример импорта:
```python
from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.<domain>.<entity_snake> import (
    <Entity>GetRequest,
    <Entity>AddRequest,
    <Entity>EditRequest,
    <Entity>DeleteMarkRequest,
    <Entity>DeleteRequest,
    # при наличии: <Entity>GetResponse / <Entity>Item и т.п.
)
```

---

## 4) Именование

**Методы сервиса — всегда `snake_case` и 1:1 соответствуют действиям из API‑документации (конвертируем из PascalCase/camelCase):**
- `Get` → `get`
- `Add` → `add`
- `Edit` → `edit`
- `DeleteMark` / `deleteMark` → `delete_mark`
- `GetByID` → `get_by_id`
- `SyncAll` → `sync_all`

**Константы путей в классе — как в серверной документации (без конвертации):**
```python
class <Entity>Service:
    PATH_GET = "<Entity>/Get"
    PATH_ADD = "<Entity>/Add"
    PATH_EDIT = "<Entity>/Edit"
    PATH_DELETE_MARK = "<Entity>/DeleteMark"   # если в доках так
    PATH_DELETE = "<Entity>/Delete"
    # Дополнительно по докам:
    # PATH_SYNC_ALL = "<Entity>/SyncAll"
    # PATH_SEARCH = "<Entity>/Search"
```

> Примечание по аббревиатурам: `ID`, `URL` и др. в названиях методов переходят в нижний регистр через подчёркивание: `GetByID` → `get_by_id`, `GetByURL` → `get_by_url`.

---

## 5) Логирование
- Логгер на уровне модуля с пространством имён `<domain>.<Entity>`:
  ```python
  logger = setup_logger("<domain>.<Entity>")
  ```
- Логи только диагностические (`debug`/`info`) и контекст ошибок (`warning`/`error`). Не логируем PII.

---

## 6) Конструктор
```python
def __init__(self, api):
    self.api = api  # объект с методом call(path, request, response_type)
```

---

## 7) Сигнатуры методов
- Каждый метод принимает **ровно один** DTO‑запрос соответствующего действия.
- Возвращаем ожидаемый тип (обычно `APIBaseResponse`). **Не допускается** аннотация `-> None` при `return await self.api.call(...)`.

```python
async def get(self, req: <Entity>GetRequest) -> APIBaseResponse: ...
async def add(self, req: <Entity>AddRequest) -> APIBaseResponse: ...
async def edit(self, req: <Entity>EditRequest) -> APIBaseResponse: ...
async def delete_mark(self, req: <Entity>DeleteMarkRequest) -> APIBaseResponse: ...
async def delete(self, req: <Entity>DeleteRequest) -> APIBaseResponse: ...
```

> Если по докам метод «ничего не возвращает», возвращаем `APIBaseResponse` с пустым/nullable `result` — это унифицирует обработку успеха/ошибок.

---

## 8) Асинхронность
- Все сетевые методы — `async def ...`.
- Внутри сервиса нет блокирующих операций (`time.sleep`, синхронный I/O и т. п.).

---

## 9) Докстринги (кратко и по делу)
Стиль: краткое описание + `Args` / `Returns` / `Raises`.

```python
async def add(self, req: <Entity>AddRequest) -> APIBaseResponse:
    """Создаёт сущность.

    Args:
        req: Параметры создания.

    Returns:
        APIBaseResponse: при ok=True в `result` может быть ID/данные.

    Raises:
        RuntimeError: если ok=False (пробрасывается из api.call).
        TypeError: при несовпадении формата ответа ожидаемому.
    """
    return await self.api.call(self.PATH_ADD, req, APIBaseResponse)
```

---

## 10) Ошибки
- Исключения из `api.call` **не глотаем**. Допустимо добавить контекст и сделать `raise ... from e`.
- Ложные `ok=False`/валидационные ошибки — ответственность слоя `api.call` и схем.

---

## 11) Пагинация и фильтры
- Параметры пагинации/фильтрации — поля запроса (`count`, `limit`, `next_offset`, `filters`, …).
- Сервис их **не модифицирует** и не «склеивает» сам — только прозрачно передаёт на сервер.

---

## 12) Ретраи, таймауты, идемпотентность
- Настраиваются в общем клиенте `api`.

---

## 13) Шаблон сервиса (generic)

```python
# services/<domain>/<entity_snake>.py
from __future__ import annotations

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.<domain>.<entity_snake> import (
    <Entity>GetRequest,
    <Entity>AddRequest,
    <Entity>EditRequest,
    <Entity>DeleteMarkRequest,
    <Entity>DeleteRequest,
)

logger = setup_logger("<domain>.<Entity>")


class <Entity>Service:
    PATH_GET = "<Entity>/Get"
    PATH_ADD = "<Entity>/Add"
    PATH_EDIT = "<Entity>/Edit"
    PATH_DELETE_MARK = "<Entity>/DeleteMark"
    PATH_DELETE = "<Entity>/Delete"
    # Дополнительно 1:1 из доков:
    # PATH_SYNC_ALL = "<Entity>/SyncAll"
    # PATH_SEARCH = "<Entity>/Search"

    def __init__(self, api):
        self.api = api

    async def get(self, req: <Entity>GetRequest) -> APIBaseResponse:
        """Возвращает список/страницу сущностей."""
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def add(self, req: <Entity>AddRequest) -> APIBaseResponse:
        """Создаёт запись и возвращает ID/данные в result."""
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit(self, req: <Entity>EditRequest) -> APIBaseResponse:
        """Редактирует запись."""
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_mark(self, req: <Entity>DeleteMarkRequest) -> APIBaseResponse:
        """Помечает запись на удаление."""
        return await self.api.call(self.PATH_DELETE_MARK, req, APIBaseResponse)

    async def delete(self, req: <Entity>DeleteRequest) -> APIBaseResponse:
        """Полностью удаляет запись (если deleted_mark=true)."""
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)

    # Пример дополнительных методов — строго с конвертацией в snake_case:
    # async def sync_all(self, req: <Entity>SyncAllRequest) -> APIBaseResponse:
    #     return await self.api.call(self.PATH_SYNC_ALL, req, APIBaseResponse)
```

