"""REGOS API filter schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

from pydantic import AliasChoices, ConfigDict, Field as PydField

from schemas.api.common.base import RegosModel


class FilterOperatorEnum(str, Enum):
    """REGOS filter operators."""

    Default = "Default"
    Equal = "Equal"
    NotEqual = "NotEqual"
    Greater = "Greater"
    Less = "Less"
    GreaterOrEqual = "GreaterOrEqual"
    LessOrEqual = "LessOrEqual"
    Like = "Like"
    Exists = "Exists"
    NotExists = "NotExists"
    In = "In"
    NotIn = "NotIn"


class Filter(RegosModel):
    """Additional REGOS API filter.

    Swagger exposes PascalCase keys (Field, Operator, Value). Existing
    integrations historically used lowercase constructor names, so both input
    shapes are accepted while serialization still follows the public contract.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    Field: str | None = PydField(
        default=None,
        validation_alias=AliasChoices("Field", "field"),
        description="Filter field name.",
    )
    Operator: FilterOperatorEnum | None = PydField(
        default=None,
        validation_alias=AliasChoices("Operator", "operator"),
        description="Filter operator.",
    )
    Value: str | None = PydField(
        default=None,
        validation_alias=AliasChoices("Value", "value"),
        description="Filter value.",
    )

    @property
    def field(self) -> str | None:
        return self.Field

    @field.setter
    def field(self, value: str | None) -> None:
        self.Field = value

    @property
    def operator(self) -> FilterOperatorEnum | None:
        return self.Operator

    @operator.setter
    def operator(self, value: FilterOperatorEnum | None) -> None:
        self.Operator = value

    @property
    def value(self) -> str | None:
        return self.Value

    @value.setter
    def value(self, value: str | None) -> None:
        self.Value = value


class FilterFieldInfo(RegosModel):
    """Field available for filtering."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    field: str | None = PydField(default=None)
    datatype: str | None = PydField(default=None)


class FilterFieldInfoRegosArrayResult(RegosModel):
    """OpenAPI-only typed equivalent of SingleArrayResult."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ok: bool | None = PydField(default=None, description="Request success flag.")
    result: list[FilterFieldInfo] | Error | None = PydField(
        default=None,
        description="Result array.",
    )


class FilterGetFields(RegosModel):
    """Request model for filterable fields."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    entity_type: FieldEntityTypeEnum | None = PydField(
        default=None,
        description="Entity type.",
    )


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.references.field import FieldEntityTypeEnum


FilterGetFieldsRequest: TypeAlias = FilterGetFields
FilterGetFieldsResponse: TypeAlias = FilterFieldInfoRegosArrayResult


_MODEL_NAMES = [
    "Filter",
    "FilterFieldInfo",
    "FilterFieldInfoRegosArrayResult",
    "FilterGetFields",
]


__all__ = [
    "Filter",
    "FilterFieldInfo",
    "FilterFieldInfoRegosArrayResult",
    "FilterGetFields",
    "FilterOperatorEnum",
    "FilterGetFieldsRequest",
    "FilterGetFieldsResponse",
]
