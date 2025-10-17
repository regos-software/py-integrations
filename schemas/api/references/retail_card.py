from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class RetailCardGroup(BaseModel):
    pass


class RetailCustomer(BaseModel):
    pass


class BarcodeType(BaseModel):
    pass


class PromoProgram(BaseModel):
    pass


class RetailCard(BaseModel):
    id: int
    group: Optional[RetailCardGroup] = None
    customer: Optional[RetailCustomer] = None
    barcode_value: str
    barcode_type: Optional[BarcodeType] = None
    promo: Optional[PromoProgram] = None
    bonus_amount: Decimal
    date: int
    unlimited: bool
    expiry_date: Optional[str] = None
    last_purchase: Optional[int] = None
    enabled: bool
    last_update: int
