"""Schemas for retail order delivery documents (DocOrderDelivery)."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import ConfigDict, Field as PydField, model_validator

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.common.sort_orders import SortOrders
from schemas.api.references.delivery_courier import DeliveryCourier
from schemas.api.references.delivery_from import DeliveryFrom
from schemas.api.references.delivery_type import DeliveryType
from schemas.api.references.payment_type import PaymentType
from schemas.api.references.price_type import PriceType
from schemas.api.references.retail_card import RetailCard
from schemas.api.references.retail_customer import RetailCustomer
from schemas.api.references.stock import Stock


class DocumentStatus(BaseSchema):
    """Статус документа."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = PydField(default=None, ge=1, description="ID статуса.")
    name: Optional[str] = PydField(default=None, description="Наименование статуса.")


class Location(BaseSchema):
    """Delivery location (coordinates)."""

    model_config = ConfigDict(extra="ignore")

    longitude: Optional[Decimal] = PydField(
        default=None,
        ge=-180,
        le=180,
        description="Longitude (from -180 to +180).",
    )
    latitude: Optional[Decimal] = PydField(
        default=None,
        ge=-90,
        le=90,
        description="Latitude (from -90 to +90).",
    )


class DocOrderDelivery(BaseSchema):
    """Retail order delivery document (read model)."""

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., ge=1, description="Document id.")
    date: int = PydField(..., ge=0, description="Document date (unix time).")
    code: str = PydField(..., description="Document code.")
    stock: Optional[Stock] = PydField(default=None, description="Stock.")
    customer: Optional[RetailCustomer] = PydField(default=None, description="Customer.")
    card: Optional[RetailCard] = PydField(default=None, description="Customer card.")
    operating_cash_id: Optional[int] = PydField(
        default=None, ge=1, description="Operating cash id."
    )
    amount: Optional[Decimal] = PydField(default=None, description="Total amount.")
    status: Optional[DocumentStatus] = PydField(default=None, description="Status.")
    delivery_date: Optional[int] = PydField(
        default=None, ge=0, description="Delivery date (unix time)."
    )
    description: Optional[str] = PydField(default=None, description="Description.")
    address: Optional[str] = PydField(default=None, description="Delivery address.")
    phone: Optional[str] = PydField(default=None, description="Phone.")
    external_code: Optional[str] = PydField(default=None, description="External code.")
    from_: Optional[DeliveryFrom] = PydField(
        default=None, alias="from", description="Order source."
    )
    location: Optional[Location] = PydField(default=None, description="Location.")
    delivery_type: Optional[DeliveryType] = PydField(
        default=None, description="Delivery type."
    )
    courier: Optional[DeliveryCourier] = PydField(default=None, description="Courier.")
    price_type: Optional[PriceType] = PydField(
        default=None, description="Price type."
    )
    qrcodeurl: Optional[str] = PydField(
        default=None, description="OFD receipt URL (qr code)."
    )
    payment_type: Optional[PaymentType] = PydField(
        default=None, description="Payment type."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Document blocked flag."
    )
    current_user_blocked: Optional[bool] = PydField(
        default=None, description="Blocked for current user."
    )
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Deleted mark."
    )
    last_update: Optional[int] = PydField(
        default=None, ge=0, description="Last update (unix time)."
    )


class DocOrderDeliveryOperation(BaseSchema):
    """Order delivery operation (line)."""

    model_config = ConfigDict(extra="forbid")

    item_id: Optional[int] = PydField(
        default=None, ge=1, description="Item id."
    )
    item_code: Optional[int] = PydField(
        default=None, ge=1, description="Item code."
    )
    quantity: Decimal = PydField(..., description="Quantity.")
    price: Decimal = PydField(..., description="Price.")

    @model_validator(mode="after")
    def _validate_item_ref(self) -> "DocOrderDeliveryOperation":
        if self.item_id is None and self.item_code is None:
            raise ValueError("item_id or item_code is required")
        return self


class DocOrderDeliveryAddRequest(BaseSchema):
    """Payload for DocOrderDelivery/Add (embedded in AddFull)."""

    model_config = ConfigDict(extra="forbid")

    date: Optional[int] = PydField(default=None, ge=0, description="Document date.")
    stock_id: Optional[int] = PydField(default=None, ge=1, description="Stock id.")
    customer_id: Optional[int] = PydField(
        default=None, ge=1, description="Customer id."
    )
    card_id: Optional[int] = PydField(default=None, ge=1, description="Card id.")
    operating_cash_id: Optional[int] = PydField(
        default=None, ge=1, description="Operating cash id."
    )
    amount: Optional[Decimal] = PydField(default=None, description="Total amount.")
    delivery_date: Optional[int] = PydField(
        default=None, ge=0, description="Delivery date (unix time)."
    )
    description: Optional[str] = PydField(default=None, description="Description.")
    address: Optional[str] = PydField(default=None, description="Delivery address.")
    phone: Optional[str] = PydField(default=None, description="Phone.")
    external_code: Optional[str] = PydField(default=None, description="External code.")
    from_id: Optional[int] = PydField(default=None, ge=1, description="Source id.")
    location: Optional[Location] = PydField(default=None, description="Location.")
    delivery_type_id: Optional[int] = PydField(
        default=None, ge=1, description="Delivery type id."
    )
    courier_id: Optional[int] = PydField(
        default=None, ge=1, description="Courier id."
    )
    price_type_id: Optional[int] = PydField(
        default=None, ge=1, description="Price type id."
    )
    payment_type_id: Optional[int] = PydField(
        default=None, ge=1, description="Payment type id."
    )


class DocOrderDeliveryAddFullRequest(BaseSchema):
    """Payload for DocOrderDelivery/AddFull."""

    model_config = ConfigDict(extra="forbid")

    document: DocOrderDeliveryAddRequest = PydField(..., description="Order document.")
    operations: List[DocOrderDeliveryOperation] = PydField(
        ..., description="Order operations."
    )


class DocOrderDeliveryGetRequest(BaseSchema):
    """Request for DocOrderDelivery/Get."""

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[int] = PydField(
        default=None, ge=0, description="Start date (unix time)."
    )
    end_date: Optional[int] = PydField(
        default=None, ge=0, description="End date (unix time)."
    )
    code: Optional[str] = PydField(default=None, description="Document code.")
    ids: Optional[List[int]] = PydField(default=None, description="Document ids.")
    status_ids: Optional[List[int]] = PydField(
        default=None, description="Status ids."
    )
    stock_ids: Optional[List[int]] = PydField(default=None, description="Stock ids.")
    customer_ids: Optional[List[int]] = PydField(
        default=None, description="Customer ids."
    )
    operating_cash_ids: Optional[List[int]] = PydField(
        default=None, description="Operating cash ids."
    )
    from_ids: Optional[List[int]] = PydField(default=None, description="Source ids.")
    external_code: Optional[str] = PydField(
        default=None, description="External code."
    )
    blocked: Optional[bool] = PydField(
        default=None, description="Blocked flag."
    )
    sort_orders: Optional[SortOrders] = PydField(
        default=None, description="Sort orders."
    )
    search: Optional[str] = PydField(default=None, description="Search string.")
    deleted_mark: Optional[bool] = PydField(
        default=None, description="Deleted mark."
    )
    limit: Optional[int] = PydField(
        default=None, ge=1, description="Limit."
    )
    offset: Optional[int] = PydField(
        default=None, ge=0, description="Offset."
    )

    @model_validator(mode="after")
    def _validate_dates(self) -> "DocOrderDeliveryGetRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class DocOrderDeliveryGetResponse(APIBaseResponse[List[DocOrderDelivery]]):
    """Response for DocOrderDelivery/Get."""

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "DocOrderDelivery",
    "DocOrderDeliveryAddFullRequest",
    "DocOrderDeliveryAddRequest",
    "DocOrderDeliveryGetRequest",
    "DocOrderDeliveryGetResponse",
    "DocOrderDeliveryOperation",
    "DocumentStatus",
    "Location",
]
