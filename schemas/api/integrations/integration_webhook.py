"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class IntegrationWebhook(RegosModel):
    "Модель, описывающая вебхук интеграции"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str | None = PydField(default=None, description="Название вебхука интеграции")
    order: int | None = PydField(default=None, description="Порядок вебхука интеграции")


class IntegrationWebhookRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[IntegrationWebhook] | Error | None = PydField(default=None, description="Массив результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


IntegrationWebhookGetResponse: TypeAlias = IntegrationWebhookRegosArrayResult


_MODEL_NAMES = ['IntegrationWebhook', 'IntegrationWebhookRegosArrayResult']


__all__ = [
    'IntegrationWebhook',
    'IntegrationWebhookRegosArrayResult',
    'IntegrationWebhookGetResponse'
]
