"""Схемы справочника отделов."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema
from schemas.api.common.sort_orders import SortOrders


class Department(BaseSchema):
    """Рид-модель отдела."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID отдела.")
    name: Optional[str] = PydField(default=None, description="Наименование отдела.")
    last_update: int = PydField(
        ..., ge=0, description="Метка последнего обновления (unixtime)."
    )


class DepartmentGetRequest(BaseSchema):
    """Параметры выборки отделов."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по списку идентификаторов отделов."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Правила сортировки результата."
    )
    search: Optional[str] = PydField(
        default=None, description="Поиск по названию отдела."
    )
    limit: Optional[int] = PydField(
        default=None,
        ge=1,
        description="Количество записей в выборке (пагинация).",
    )
    offset: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Смещение для пагинации.",
    )

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class DepartmentAddRequest(BaseSchema):
    """Создание нового отдела."""

    model_config = ConfigDict(extra="forbid")

    name: str = PydField(..., min_length=1, description="Наименование отдела.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class DepartmentEditRequest(BaseSchema):
    """Обновление существующего отдела."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID отдела.")
    name: str = PydField(..., min_length=1, description="Новое название отдела.")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class DepartmentDeleteRequest(BaseSchema):
    """Удаление отдела."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="ID отдела.")


__all__ = [
    "Department",
    "DepartmentAddRequest",
    "DepartmentDeleteRequest",
    "DepartmentEditRequest",
    "DepartmentGetRequest",
]
