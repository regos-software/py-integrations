from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import APIBaseResponse, BaseSchema


class DeliveryType(BaseSchema):
    """Справочник способов доставки."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(
        default=None, ge=1, description="ID способа доставки."
    )
    name: Optional[str] = PydField(
        default=None, description="Наименование способа доставки."
    )
    last_update: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Дата последнего изменения записи (unix time, сек).",
    ) 


class DeliveryTypeGetRequest(BaseSchema):
    """Request for DeliveryType/Get."""

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(default=None, description="Delivery type ids.")
    search: Optional[str] = PydField(default=None, description="Search string.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Page size.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Page offset.")


class DeliveryTypeGetResponse(APIBaseResponse[List[DeliveryType] | Dict[str, Any]]):
    """Response for DeliveryType/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "DeliveryType",
    "DeliveryTypeGetRequest",
    "DeliveryTypeGetResponse",
]
