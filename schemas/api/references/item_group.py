"""Схемы справочника групп товаров."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, field_validator

from schemas.api.base import BaseSchema


class ItemGroup(BaseSchema):
    """Рид-модель группы номенклатуры."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID группы в системе.")
    parent_id: Optional[int] = PydField(
        default=None, ge=1, description="ID родительской группы."
    )
    path: Optional[str] = PydField(
        default=None,
        description="Полный путь группы (вложенность через '/').",
    )
    name: Optional[str] = PydField(default=None, description="Наименование группы.")
    child_count: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Количество непосредственных дочерних групп.",
    )
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Дата последнего изменения (unixtime)."
    )

    @field_validator("path", "name", mode="before")
    @classmethod
    def _strip_fields(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class ItemGroupGetRequest(BaseSchema):
    """Фильтры для получения групп номенклатуры."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(
        default=None, description="Список ID групп для выборки."
    )
    parent_ids: Optional[List[int]] = PydField(
        default=None, description="Фильтр по родительским группам."
    )
    name: Optional[str] = PydField(
        default=None, description="Фильтр по названию (подстрочный поиск)."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


__all__ = [
    "ItemGroup",
    "ItemGroupGetRequest",
]
