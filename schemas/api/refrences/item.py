from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from schemas.api.refrences.unit import Unit


class ItemGroup(BaseModel):
    pass


class Department(BaseModel):
    pass


class TaxVat(BaseModel):
    pass



class Color(BaseModel):
    pass


class SizeChart(BaseModel):
    pass


class Brand(BaseModel):
    pass


class Producer(BaseModel):
    pass


class Country(BaseModel):
    pass



class Item(BaseModel):
    id: int
    group: Optional[ItemGroup] = None
    department: Optional[Department] = None
    vat: Optional[TaxVat] = None
    barcode_list: Optional[str] = None
    base_barcode: Optional[str] = None
    unit: Optional[Unit] = None
    unit2: Optional[Unit] = None
    color: Optional[Color] = None
    size: Optional[SizeChart] = None
    brand: Optional[Brand] = None
    producer: Optional[Producer] = None
    country: Optional[Country] = None
    compound: Optional[bool] = None
    deleted_mark: Optional[bool] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    has_child: Optional[bool] = None
    last_update: int
    type: str = "none"  
    code: Optional[int] = None
    name: Optional[str] = None
    fullname: Optional[str] = None
    description: Optional[str] = None
    articul: Optional[str] = None
    kdt: Optional[int] = None
    min_quantity: Optional[int] = None
    icps: Optional[str] = None
    assemblable: Optional[bool] = None
    disassemblable: Optional[bool] = None
    is_labeled: Optional[bool] = None
    comission_tin: Optional[str] = None
    package_code: Optional[str] = None
    origin: str = "none"  
    partner_id: Optional[int] = None
