"""Схемы настроек подключённых интеграций."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.base import BaseSchema


class ConnectedIntegrationSetting(BaseSchema):
    """Рид-модель настройки интеграции."""

    model_config = ConfigDict(extra="ignore")

    key: Optional[str] = PydField(
        default=None, description="Ключ настройки (верхний регистр)."
    )
    value: Optional[str] = PydField(
        default=None, description="Значение настройки в текстовом виде."
    )
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Метка последнего изменения (unixtime)."
    )


class ConnectedIntegrationSettingRequest(BaseSchema):
    """Запрос получения настроек по ключу интеграции."""

    model_config = ConfigDict(extra="forbid")

    integration_key: str = PydField(
        ..., min_length=1, description="Системный ключ интеграции."
    )
    firm_id: Optional[int] = PydField(
        default=0,
        ge=1,
        description="Фильтр по ID фирмы (если требуется уточнение).",
    )


class ConnectedIntegrationSettingEditItem(BaseSchema):
    """Элемент массового редактирования настроек."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = PydField(
        default=None, ge=1, description="ID настройки для обновления."
    )
    key: Optional[str] = PydField(
        default=None, description="Ключ настройки (верхний регистр)."
    )
    value: Optional[str] = PydField(
        default=None, description="Новое значение настройки."
    )
    integration_key: Optional[str] = PydField(
        default=None, description="Ключ интеграции, если требуется сменить."
    )
    firm_id: Optional[int] = PydField(
        default=None,
        ge=1,
        description="ID фирмы, к которой относится настройка.",
    )


class ConnectedIntegrationSettingEditRequest(
    RootModel[List[ConnectedIntegrationSettingEditItem]]
):
    """Запрос на массовое редактирование настроек (root=list)."""


__all__ = [
    "ConnectedIntegrationSetting",
    "ConnectedIntegrationSettingEditItem",
    "ConnectedIntegrationSettingEditRequest",
    "ConnectedIntegrationSettingRequest",
]
