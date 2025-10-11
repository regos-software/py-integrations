## Конвенции для сервисов

### Цели

- **Тонкая обёртка** над API без бизнес-логики.
- **Типобезопасность** через Pydantic-схемы.
- **Прозрачность**: метаданные (`ok`, `result`, `next_offset`, `total`) доступны через RAW-методы.

### Принципы

1. **Один файл — одна сущность**: `core/api/<entity>.py`.
2. **Константы путей**:
   ```py
   PATH_GET = "Entity/Get"
   PATH_ADD = "Entity/Add"
   ...
   ```
3. **Два слоя**:
   - `*_raw(...) -> APIBaseResponse` — *1:1 к эндпоинтам*, ничего не скрывают.
   - Тонкие методы (`get`, `get_page`, `add`, `edit`, `delete_mark`, `delete`) — для удобства.
4. **Логирование**: логируем `ok=False` и неожиданный формат `result` (без чувствительных данных).
5. **Исключения** (стандартные):
   - `RuntimeError` — если `ok=False`;
   - `TypeError` — если формат `result` неожиданный.
6. **Валидация списков** — через `TypeAdapter`:
   ```py
   from pydantic import TypeAdapter
   TypeAdapter(list[Model]).validate_python(resp.result)
   ```
7. **Пагинация** — не скрывать: `get_page(...) -> (items, next_offset, total)`.

### Шаблон сервиса

```py
# core/api/<entity>.py
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

---

## Пример использования (RetailCustomer)

```py
from services.retail_customer_service import RetailCustomerService
from schemas.api.refrences.retail_customer import (
    RetailCustomerGetRequest,
    RetailCustomerAddRequest,
    RetailCustomerDeleteMarkRequest,
    RetailCustomerDeleteRequest,
)

svc = RetailCustomerService(api)

# Страница покупателей
items, next_offset, total = await svc.get_page(RetailCustomerGetRequest(limit=50, offset=0))

# Добавить покупателя
new_id = await svc.add(RetailCustomerAddRequest(
    group_id=1,
    first_name="Alexey",
    sex="male",  # только: non|male|female
))

# Тоггл пометки на удаление
await svc.delete_mark(RetailCustomerDeleteMarkRequest(id=new_id))

# Удалить покупателя
await svc.delete(RetailCustomerDeleteRequest(id=new_id))
```

---

