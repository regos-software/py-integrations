# README

Единые правила оформления **схем (Pydantic v2)** и **сервисов** для работы с REST-эндпоинтами.  
Проект — асинхронный Python, Pydantic v2.

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
    references/                 # Справочники
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

   - Метаданные и значения — в `schemas/api/references/fields.py`.
   - В сущности: `fields: Optional[FieldValues]`.
   - В Add — `FieldValueAdds`, в Edit — `FieldValueEdits`.

7. **Публичный API файла** — в конце:
   ```py
   __all__ = ["<Имена_моделей_и_DTO>"]
   ```

### Шаблон файла сущности

```py
# schemas/api/references/<entity>.py
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import Field as PydField, EmailStr, field_validator
from pydantic.config import ConfigDict

from schemas.api.base import BaseSchema
from schemas.api.common.filters import Filters
from schemas.api.common.sort_orders import SortOrders
from schemas.api.references.fields import FieldValueAdds, FieldValueEdits, FieldValues
# from schemas.api.references.<linked_ref> import <LinkedRefModel>  # при необходимости


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
