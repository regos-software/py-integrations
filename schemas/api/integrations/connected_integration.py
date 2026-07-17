"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class ConnectedIntegrationEdit(RegosModel):
    "Модель описывающая редактирование интеграции"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    integration_key: str | None = PydField(default=None, description="Ключ (системное название) интеграции. Если передан одновременно с connected_integration_id, используется\nconnected_integration_id. Если по integration_key найдено более одной подключённой интеграции, метод вернёт ошибку 1100")
    connected_integration_id: str | None = PydField(default=None, description="ID подключённой интеграции. Имеет приоритет над integration_key (если переданы оба поля)")
    is_active: bool | None = PydField(default=None, description="Является ли интеграция активной: true - Активная, fatse - Не активная")
    alias: str | None = PydField(default=None, description="Alias интеграции (для версии БД 365+). Если передано null, значение в БД не меняется; пустая строка сохраняется как null; длина после EscapeStr — не более 255 символов")
    settings: list[ConnectedIntegrationSettingEdit] | None = PydField(default=None, description="Массив настроек интеграции")
    schedule: IntegrationSchedule | None = PydField(default=None, description="Обработчки интеграции: <MarketPlace | 1> - Маркетлпейсы (выгрузка номенклатуры, заказы), <EPS | 2> -\nПлатежные системы, <EDO | 3> - Электронный документооборот, <SMS | 4> - СМС шлюзы, <TG_BOT | 5> -\nТелеграмм боты")


class ConnectedIntegrationID(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    connected_integration_id: str | None = PydField(default=None, description="-")


class ConnectedIntegrationWebhookInfoGet(RegosModel):
    "Модель для отправки уведомления об изменениях настроек"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    connected_integration_id: str | None = PydField(default=None, description="ID подключенной интеграции")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BooleanRegosObjectResult, SingleObjectResult
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingEdit
from schemas.api.integrations.integration import IntegrationConnectedGet, IntegrationConnectedRegosArrayResult, IntegrationDisconnect, IntegrationReconnect, IntegrationSchedule
from schemas.api.webhooks.webhook import WebHookStatusResponseRegosObjectResult


ConnectedIntegrationCheckRequest: TypeAlias = ConnectedIntegrationID
ConnectedIntegrationCheckResponse: TypeAlias = BooleanRegosObjectResult
ConnectedIntegrationDisconnectRequest: TypeAlias = IntegrationDisconnect
ConnectedIntegrationDisconnectResponse: TypeAlias = SingleObjectResult
ConnectedIntegrationEditRequest: TypeAlias = ConnectedIntegrationEdit
ConnectedIntegrationEditResponse: TypeAlias = SingleObjectResult
ConnectedIntegrationGetRequest: TypeAlias = IntegrationConnectedGet
ConnectedIntegrationGetResponse: TypeAlias = IntegrationConnectedRegosArrayResult
ConnectedIntegrationGetWebhookInfoRequest: TypeAlias = ConnectedIntegrationWebhookInfoGet
ConnectedIntegrationGetWebhookInfoResponse: TypeAlias = WebHookStatusResponseRegosObjectResult
ConnectedIntegrationReconnectRequest: TypeAlias = IntegrationReconnect
ConnectedIntegrationReconnectResponse: TypeAlias = SingleObjectResult


_MODEL_NAMES = ['ConnectedIntegrationEdit', 'ConnectedIntegrationID', 'ConnectedIntegrationWebhookInfoGet']


__all__ = [
    'ConnectedIntegrationEdit',
    'ConnectedIntegrationID',
    'ConnectedIntegrationWebhookInfoGet',
    'ConnectedIntegrationGetRequest',
    'ConnectedIntegrationGetResponse',
    'ConnectedIntegrationEditRequest',
    'ConnectedIntegrationEditResponse',
    'ConnectedIntegrationCheckRequest',
    'ConnectedIntegrationCheckResponse',
    'ConnectedIntegrationReconnectRequest',
    'ConnectedIntegrationReconnectResponse',
    'ConnectedIntegrationDisconnectRequest',
    'ConnectedIntegrationDisconnectResponse',
    'ConnectedIntegrationGetWebhookInfoRequest',
    'ConnectedIntegrationGetWebhookInfoResponse'
]
