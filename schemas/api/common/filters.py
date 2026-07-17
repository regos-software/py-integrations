"""Backward-compatible helpers for REGOS API filters."""

from __future__ import annotations

from typing import Any, List

from pydantic import model_validator

from schemas.api.common.filter import Filter as SwaggerFilter
from schemas.api.common.filter import FilterOperatorEnum


FilterOperator = FilterOperatorEnum


class Filter(SwaggerFilter):
    """Legacy lowercase constructor wrapper around the Swagger Filter model."""

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        for legacy_key, swagger_key in (
            ("field", "Field"),
            ("operator", "Operator"),
            ("value", "Value"),
        ):
            if legacy_key in normalized and swagger_key not in normalized:
                normalized[swagger_key] = normalized.pop(legacy_key)
        return normalized

    @model_validator(mode="after")
    def _check_value_presence(self):
        if self.Operator in {FilterOperator.Exists, FilterOperator.NotExists}:
            return self
        if self.Value is None or str(self.Value).strip() == "":
            raise ValueError(
                "A non-empty 'value' is required for the selected filter operator."
            )
        return self


Filters = List[Filter]


__all__ = ["Filter", "FilterOperator", "Filters"]
