# Сервисы API: как оформлять

Этот документ описывает, как оформлять сервисы для работы с REST-эндпоинтами (асинхронный Python, Pydantic v2).

## Цели

- **Тонкая обёртка над API** без бизнес-логики.
- **Типобезопасность** за счёт Pydantic-схем.
- **Прозрачность**: метаданные ответа (`ok`, `result`, `next_offset`, `total`) доступны через raw-методы.

---

## Структура проекта (фрагмент)

```

core/
logger.py
schemas/
api/
base.py                     # BaseSchema, APIBaseResponse, ArrayResult
common/
filters.py                # Filter, Filters
sort_orders.py            # SortOrder, SortOrders
refrences/                  # (именно 'refrences', как в проекте)
fields.py
region.py
retail_customer_group.py
retail_customer.py        # модели и запросы RetailCustomer
services/
retail_customer_service.py    # 1 файл = 1 сущность

````

---

## Принципы

1. **Один файл — одна сущность**  
   `RetailCustomerService` → `services/retail_customer_service.py`.

2. **Константы путей** в начале класса:  
   ```py
   PATH_GET = "Entity/Get"
   PATH_ADD = "Entity/Add"
   ...
````

3. **Два слоя методов**

   * `*_raw(...) -> APIBaseResponse` — *1:1 к эндпоинтам*, ничего не скрывают.
   * Тонкие методы (`get`, `get_page`, `add`, `edit`, `delete_mark`, `delete`) — удобства для приложения.

4. **Минимум логики в сервисах**
   Нормализация/валидация — в Pydantic-схемах.

5. **Логирование**
   Логер на модуль: `setup_logger("references.<Entity>")`.
   Логируйте `ok=false` и неожиданный формат `result` (без чувствительных данных).

6. **Исключения**
   По умолчанию используйте стандартные:

   * `RuntimeError` — если `ok=False`
   * `TypeError` — если формат `result` не тот

7. **Валидация списков** — через `TypeAdapter`:

   ```py
   from pydantic import TypeAdapter
   TypeAdapter(list[Model]).validate_python(resp.result)
   ```

8. **Пагинация**
   Не скрывайте: давайте `get_page(...) -> (items, next_offset, total)`; при необходимости — генератор `paginate(...)`.

---

## Шаблон сервиса

```py
# services/<entity>_service.py
from __future__ import annotations

from typing import List, Tuple
from pydantic import TypeAdapter

from core.logger import setup_logger
from schemas.api.base import APIBaseResponse
from schemas.api.refrences.<entity> import (  # замените на вашу сущность
    <EntityModel>,
    <EntityGetRequest>,
    <EntityAddRequest>,
    <EntityEditRequest>,
    <EntityDeleteMarkRequest>,
    <EntityDeleteRequest>,
)

logger = setup_logger("references.<EntityName>")


class <EntityName>Service:
    PATH_GET         = "<EntityName>/Get"
    PATH_ADD         = "<EntityName>/Add"
    PATH_EDIT        = "<EntityName>/Edit"
    PATH_DELETE_MARK = "<EntityName>/DeleteMark"
    PATH_DELETE      = "<EntityName>/Delete"

    def __init__(self, api):
        self.api = api

    # ---------- RAW (1:1 к эндпоинтам) ----------
    async def get_raw(self, req: <EntityGetRequest>) -> APIBaseResponse:
        return await self.api.call(self.PATH_GET, req, APIBaseResponse)

    async def add_raw(self, req: <EntityAddRequest>) -> APIBaseResponse:
        return await self.api.call(self.PATH_ADD, req, APIBaseResponse)

    async def edit_raw(self, req: <EntityEditRequest>) -> APIBaseResponse:
        return await self.api.call(self.PATH_EDIT, req, APIBaseResponse)

    async def delete_mark_raw(self, req: <EntityDeleteMarkRequest>) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE_MARK, req, APIBaseResponse)

    async def delete_raw(self, req: <EntityDeleteRequest>) -> APIBaseResponse:
        return await self.api.call(self.PATH_DELETE, req, APIBaseResponse)

    # ---------- Тонкие методы ----------
    async def get(self, req: <EntityGetRequest>) -> List[<EntityModel>]:
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("GET ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False (result={getattr(resp, 'result', None)!r})")
        if not isinstance(resp.result, list):
            logger.error("GET unexpected result format: %r", resp.result)
            raise TypeError("Ожидался список сущностей в result")
        return TypeAdapter(List[<EntityModel>]).validate_python(resp.result)

    async def get_page(self, req: <EntityGetRequest>) -> Tuple[List[<EntityModel>], int, int]:
        resp = await self.get_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("GET ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_GET}: ok=False (result={getattr(resp, 'result', None)!r})")
        if not isinstance(resp.result, list):
            logger.error("GET unexpected result format: %r", resp.result)
            raise TypeError("Ожидался список сущностей в result")
        items = TypeAdapter(List[<EntityModel>]).validate_python(resp.result)
        next_offset = getattr(resp, "next_offset", None) or 0
        total = getattr(resp, "total", None) or len(items)
        return items, next_offset, total

    async def add(self, req: <EntityAddRequest>) -> int:
        resp = await self.add_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("ADD ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_ADD}: ok=False (result={getattr(resp, 'result', None)!r})")
        if isinstance(resp.result, int):
            return resp.result
        if isinstance(resp.result, dict) and isinstance(resp.result.get("id"), int):
            return resp.result["id"]
        logger.error("ADD unexpected result format: %r", resp.result)
        raise TypeError("Ожидался int или {'id': int} в result")

    async def edit(self, req: <EntityEditRequest>) -> None:
        resp = await self.edit_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("EDIT ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_EDIT}: ok=False (result={getattr(resp, 'result', None)!r})")

    async def delete_mark(self, req: <EntityDeleteMarkRequest>) -> None:
        resp = await self.delete_mark_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("DELETE_MARK ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_DELETE_MARK}: ok=False (result={getattr(resp, 'result', None)!r})")

    async def delete(self, req: <EntityDeleteRequest>) -> None:
        resp = await self.delete_raw(req)
        if not getattr(resp, "ok", False):
            logger.warning("DELETE ok=False: %s", getattr(resp, "result", None))
            raise RuntimeError(f"{self.PATH_DELETE}: ok=False (result={getattr(resp, 'result', None)!r})")
```



