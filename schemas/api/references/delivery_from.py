from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field as PydField

from schemas.api.base import BaseSchema


class DeliveryFrom(BaseSchema):
    """Справочник источников розничных заказов."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(
        default=None, ge=1, description="ID источника розничных заказов."
    )
    name: Optional[str] = PydField(
        default=None, description="Наименование источника розничных заказов."
    )
    deleted: Optional[bool] = PydField(
        default=None, description="Метка об удалении."
    )
    last_update: Optional[int] = PydField(
        default=None,
        ge=0,
        description="Дата последнего изменения записи (unix time, сек).",
    )


__all__ = ["DeliveryFrom"]
