# README

Единые правила оформления **схем (Pydantic v2)** и **сервисов** для работы с REST-эндпоинтами.  
Проект — асинхронный Python, Pydantic v2.

> ⚠️ В проекте используется пакет **`schemas/api/refrences/`** (именно `refrences`). Во всех файлах и импортax придерживаемся одного написания.

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
    refrences/                  # (именно 'refrences')
      fields.py                 # Field, FieldValue*, FieldValues/FieldValueAdds/FieldValueEdits
      region.py
      retail_customer_group.py
      retail_customer.py        # модели и DTO для RetailCustomer
services/
  retail_customer_service.py    # 1 сущность = 1 файл сервиса
```

---

## Конвенции для схем

### Базовые правила

1. **Базовый класс** — наследуем от `BaseSchema`.
   - В `BaseSchema` уже настроен `json_encoders={Decimal: float}`.
   - **Рид-модели** (ответы сервера): `model_config = ConfigDict(extra="ignore")`.
   - **Запросы** (наши payload’ы): `model_config = ConfigDict(extra="forbid")`.

2. **Документация** — у каждого поля обязателен `description` через `Field`:
   ```py
   id: int = Field(..., description="ID записи.")
   ```

3. **Типы**:
   - Идентификаторы: `int` с `ge=1` в запросах.
   - Денежные и количественные: `Decimal`.
   - Даты: **строки** (указать формат в `description`, напр. `YYYY-MM-DD`).
   - Email: в **Add/Edit** — `EmailStr`; в **рид-моделях** — `str`.
   - Пол (`sex`): только `non|male|female` в Add/Edit (без числовых кодов).

4. **Нормализация строк** — общий валидатор `.strip()`:
   ```py
   @field_validator("name", mode="before")
   def _strip(cls, v): return v.strip() if isinstance(v, str) else v
   ```

5. **Фильтры/сортировки** — используем общие модели:
   ```py
   from schemas.api.common.filters import Filters
   from schemas.api.common.sort_orders import SortOrders
   ```

6. **Доп. поля**:
   - Метаданные и значения — в `schemas/api/refrences/fields.py`.
   - В сущности: `fields: Optional[FieldValues]`.
   - В Add — `FieldValueAdds`, в Edit — `FieldValueEdits`.

7. **Публичный API файла** — в конце:
   ```py
   __all__ = ["<Имена_моделей_и_DTO>"]
   ```

### Шаблон файла сущности

```py
# schemas/api/refrences/<entity>.py
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import Field as PydField, EmailStr, field_validator
from pydantic.config import ConfigDict

from schemas.api.base import BaseSchema
from schemas.api.common.filters import Filters
from schemas.api.common.sort_orders import SortOrders
from schemas.api.refrences.fields import FieldValueAdds, FieldValueEdits, FieldValues
# from schemas.api.refrences.<linked_ref> import <LinkedRefModel>  # при необходимости


# ---------- Enum / helpers ----------
class Sex(str, Enum):
    non = "non"
    male = "male"
    female = "female"


# ---------- Рид-модель ----------
class <EntityName>(BaseSchema):
    """Описание сущности."""
    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID записи.")
    # region: Optional[Region] = PydField(None, description="Регион.")
    # group: <LinkedRefModel> = PydField(..., description="Группа.")

    amount: Optional[Decimal] = PydField(None, description="Числовое поле (Decimal).")
    name: Optional[str] = PydField(None, description="Название.")
    fields: Optional[FieldValues] = PydField(None, description="Доп. поля (FieldValue[]).")

    deleted_mark: bool = PydField(..., description="Метка удаления.")
    last_update: int = PydField(..., description="Unix time (сек).")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- Get ----------
class <EntityName>GetRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = None
    # ... другие фильтры/ID
    sort_orders: Optional[SortOrders] = None
    filters: Optional[Filters] = None

    search: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


# ---------- Add ----------
class <EntityName>AddRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    # обязательные поля
    # group_id: int = PydField(..., ge=1, description="ID группы.")
    name: str = PydField(..., description="Название.")

    # опциональные поля
    email: Optional[EmailStr] = PydField(None, description="E-mail.")
    sex: Optional[Sex] = PydField(None, description="Пол: non|male|female.")
    fields: Optional[FieldValueAdds] = PydField(None, description="FieldValueAdd[].")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- Edit ----------
class <EntityName>EditRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID записи.")

    name: Optional[str] = PydField(None, description="Название.")
    email: Optional[EmailStr] = PydField(None, description="E-mail.")
    sex: Optional[Sex] = PydField(None, description="Пол: non|male|female.")
    fields: Optional[FieldValueEdits] = PydField(None, description="FieldValueEdit[].")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- DeleteMark ----------
class <EntityName>DeleteMarkRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")
    id: int = PydField(..., ge=1, description="ID записи.")


# ---------- Delete ----------
class <EntityName>DeleteRequest(BaseSchema):
    model_config = ConfigDict(extra="forbid")
    id: int = PydField(..., ge=1, description="ID записи.")


__all__ = [
    "<EntityName>",
    "<EntityName>GetRequest",
    "<EntityName>AddRequest",
    "<EntityName>EditRequest",
    "<EntityName>DeleteMarkRequest",
    "<EntityName>DeleteRequest",
]
```

---

## Конвенции для сервисов

### Цели

- **Тонкая обёртка** над API без бизнес-логики.
- **Типобезопасность** через Pydantic-схемы.
- **Прозрачность**: метаданные (`ok`, `result`, `next_offset`, `total`) доступны через RAW-методы.

### Принципы

1. **Один файл — одна сущность**: `services/<entity>_service.py`.
2. **Константы путей**:
   ```py
   PATH_GET = "Entity/Get"
   PATH_ADD = "Entity/Add"
   ...
   ```
3. **Два слоя**:
   - `*_raw(...) -> APIBaseResponse` — *1:1 к эндпоинтам*, ничего не скрывают.
   - Тонкие методы (`get`, `get_page`, `add`, `edit`, `delete_mark`, `delete`) — удобства без «магии».
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

