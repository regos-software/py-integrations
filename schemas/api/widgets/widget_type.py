"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class WidgetType(RegosModel):
    "Модель, описывающая WidgetType"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID типа виджета")
    name: str | None = PydField(default=None, description="Наименование типа виджета")
    name_key: str | None = PydField(default=None, description="Ключ наименования")
    description: str | None = PydField(default=None, description="Описание")
    last_update: int | None = PydField(default=None, description="Дата последнего обновления в unix time")


class WidgetTypeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[WidgetType] | Error | None = PydField(default=None, description="Массив результата.")


class WidgetTypesEnum(str, Enum):
    "Перечисление типов виджетов"
    Default = "Default"
    PersonalTargets = "PersonalTargets"
    GlobalTargets = "GlobalTargets"
    Accounts = "Accounts"
    RetailOrders = "RetailOrders"
    OperatingCashes = "OperatingCashes"
    RetailSaleStats = "RetailSaleStats"
    RetailPaymentStats = "RetailPaymentStats"
    RetailSalesDynamics = "RetailSalesDynamics"
    RetailTop10Quantity = "RetailTop10Quantity"
    RetailTop10ItemsAmount = "RetailTop10ItemsAmount"
    RetailCustomersComingBirthdays = "RetailCustomersComingBirthdays"
    RetailCustomersPreferredPurchasesTop10 = "RetailCustomersPreferredPurchasesTop10"
    PartnersDebtTop10 = "PartnersDebtTop10"
    RetailCustomersAgeDistribution = "RetailCustomersAgeDistribution"
    RetailCustomersSexDistribution = "RetailCustomersSexDistribution"
    TariffInfo = "TariffInfo"
    RetailCustomersDebtTop10 = "RetailCustomersDebtTop10"
    RetailSalesActivity = "RetailSalesActivity"
    Integration = "Integration"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error


WidgetTypeGetResponse: TypeAlias = WidgetTypeRegosArrayResult


_MODEL_NAMES = ['WidgetType', 'WidgetTypeRegosArrayResult']


__all__ = [
    'WidgetType',
    'WidgetTypeRegosArrayResult',
    'WidgetTypesEnum',
    'WidgetTypeGetResponse'
]
