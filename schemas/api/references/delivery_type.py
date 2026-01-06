from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema


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


__all__ = ["DeliveryType"]
