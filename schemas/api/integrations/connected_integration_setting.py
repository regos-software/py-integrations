"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ConnectedIntegrationSetting(RegosModel):
    "Модель, описывающая настройку подключенной интеграции"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) настройки интеграции")
    value: str | None = PydField(default=None, description="Значение настройки интеграции")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в формате UnixTime")


class ConnectedIntegrationSettingEdit(RegosModel):
    "Модель описывающая редактирование настройки интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    key: str | None = PydField(default=None, description="Ключ (системное название) настройки интеграции")
    value: str | None = PydField(default=None, description="Значение настройки интеграции")
    integration_key: str | None = PydField(default=None, description="Устаревшее поле. Ключ (системное название) интеграции. Если передан одновременно с connected_integration_id, используется connected_integration_id")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key (если переданы оба поля)")
    firm_id: int | None = PydField(default=None, description="ID предприятия")


class ConnectedIntegrationSettingGet(RegosModel):
    "Модель для получения настроек интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    integration_key: str | None = PydField(default=None, description="Устаревшее поле. Ключ (системное название) интеграции. Если передан одновременно с connected_integration_id, используется connected_integration_id")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key (если переданы оба поля)")
    firm_id: int | None = PydField(default=None, description="ID предприятия")


class ConnectedIntegrationSettingRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ConnectedIntegrationSetting] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error, SingleObjectResult




class ConnectedIntegrationSettingEditRequest(RootModel[list[ConnectedIntegrationSettingEdit]]):
    """Compatibility root model for ConnectedIntegrationSetting/Edit."""

    pass


ConnectedIntegrationSettingEditItem: TypeAlias = ConnectedIntegrationSettingEdit
ConnectedIntegrationSettingEditResponse: TypeAlias = SingleObjectResult
ConnectedIntegrationSettingGetRequest: TypeAlias = ConnectedIntegrationSettingGet
ConnectedIntegrationSettingGetResponse: TypeAlias = ConnectedIntegrationSettingRegosArrayResult
ConnectedIntegrationSettingRequest: TypeAlias = ConnectedIntegrationSettingGet


_MODEL_NAMES = ['ConnectedIntegrationSetting', 'ConnectedIntegrationSettingEdit', 'ConnectedIntegrationSettingGet', 'ConnectedIntegrationSettingRegosArrayResult', 'ConnectedIntegrationSettingEditRequest']


__all__ = [
    'ConnectedIntegrationSetting',
    'ConnectedIntegrationSettingEdit',
    'ConnectedIntegrationSettingGet',
    'ConnectedIntegrationSettingRegosArrayResult',
    'ConnectedIntegrationSettingEditRequest',
    'ConnectedIntegrationSettingGetRequest',
    'ConnectedIntegrationSettingGetResponse',
    'ConnectedIntegrationSettingEditRequest',
    'ConnectedIntegrationSettingEditResponse',
    'ConnectedIntegrationSettingEditItem',
    'ConnectedIntegrationSettingRequest'
]
