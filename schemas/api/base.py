"""Base API schemas used across integration modules."""

from __future__ import annotations

from decimal import Decimal
from typing import Generic, Optional, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field as PydField


class BaseSchema(BaseModel):
    """Base model with shared JSON encoders."""

    model_config = ConfigDict(json_encoders={Decimal: float})


T = TypeVar("T")


class APIBaseResponse(BaseSchema, Generic[T]):
    """Generic REGOS REST response envelope."""

    model_config = ConfigDict(extra="ignore")

    ok: bool = PydField(..., description="Success flag.")
    result: Optional[T] = PydField(default=None, description="Response payload.")
    next_offset: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Next page offset.",
    )
    total: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Total record count.",
    )


class APIErrorResult(BaseSchema):
    """Error payload returned by API."""

    model_config = ConfigDict(extra="ignore")

    error: int = PydField(..., description="Error code.")
    description: str = PydField(..., description="Error description.")


class ArrayResult(BaseSchema):
    """Result payload for update/delete-like operations."""

    model_config = ConfigDict(extra="ignore")

    row_affected: int = PydField(
        ...,
        ge=0,
        validation_alias=AliasChoices("row_affected", "affected"),
        description="Affected rows count.",
    )
    ids: Optional[list[int]] = PydField(
        default_factory=list,
        description="Affected entity ids.",
    )


class AddResult(BaseSchema):
    """Result payload for create operations."""

    model_config = ConfigDict(extra="ignore")

    new_id: int = PydField(..., ge=1, description="Created entity id.")


class IDRequest(BaseSchema):
    """Simple request with single positive identifier."""

    model_config = ConfigDict(extra="forbid")

    id: int = PydField(..., ge=1, description="Record id.")


__all__ = [
    "APIBaseResponse",
    "APIErrorResult",
    "ArrayResult",
    "BaseSchema",
    "IDRequest",
]
