from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

# ---------- вспомогательные модели (плейсхолдеры, чтобы не тянуть все справочники) ----------
from schemas.api.refrences.brand import Brand
from schemas.api.refrences.price_type import PriceType
from schemas.api.refrences.stock import Stock
from schemas.api.refrences.unit import Unit  
# Если есть полноценные схемы ниже — замени импорты.
class ItemGroup(BaseModel): pass
class Department(BaseModel): pass
class TaxVat(BaseModel): pass
class Color(BaseModel): pass
class SizeChart(BaseModel): pass
class Producer(BaseModel): pass
class Country(BaseModel): pass

# ---------- базовая номенклатура ----------
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

# ---------- общие enum/сортировки ----------
class ItemType(str, Enum):
    Item = "Item"
    Service = "Service"

class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

# ---------- Search ----------
class ItemSearchRequest(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    articul: Optional[str] = None
    barcode: Optional[str] = None

    deleted_mark: Optional[bool] = None
    assemblable: Optional[bool] = None
    disassemblable: Optional[bool] = None
    compound: Optional[bool] = None
    has_child: Optional[bool] = None
    type: Optional[ItemType] = None

# ---------- Get ----------
class RedefinitionOption(BaseModel):
    language: Optional[str] = None  # например, "RUS"
    app_id: Optional[int] = None

class ItemGetRequest(BaseModel):
    ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    type: Optional[ItemType] = None
    parent_ids: Optional[List[int]] = None
    codes: Optional[List[int]] = None
    redefinition_option: Optional[RedefinitionOption] = None
    department_ids: Optional[List[int]] = None
    deleted_mark: Optional[bool] = None
    assemblable: Optional[bool] = None
    disassemblable: Optional[bool] = None
    compound: Optional[bool] = None
    has_child: Optional[bool] = None
    is_labeled: Optional[bool] = None
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)

# ---------- GetExt ----------
class ItemGetExtSortColumn(str, Enum):
    Name = "Name"
    Articul = "Articul"
    Code = "Code"
    Unit = "Unit"
    Color = "Color"
    Size = "Size"
    Brand = "Brand"
    Producer = "Producer"
    Country = "Country"
    TaxVat = "TaxVat"
    Department = "Department"

class ItemGetExtSortOrder(BaseModel):
    column: ItemGetExtSortColumn
    direction: SortDirection

class ItemGetExtImageSize(str, Enum):
    Large = "Large"
    Medium = "Medium"
    Small = "Small"

class ItemGetExtRequest(BaseModel):
    stock_id: Optional[int] = None
    price_type_id: Optional[int] = None
    sort_orders: Optional[List[ItemGetExtSortOrder]] = None
    search: Optional[str] = None
    zero_quantity: Optional[bool] = None
    zero_price: Optional[bool] = None
    image_size: Optional[ItemGetExtImageSize] = None

    ids: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    type: Optional[ItemType] = None
    parent_ids: Optional[List[int]] = None
    codes: Optional[List[int]] = None
    redefinition_option: Optional[RedefinitionOption] = None
    department_ids: Optional[List[int]] = None
    deleted_mark: Optional[bool] = None
    assemblable: Optional[bool] = None
    disassemblable: Optional[bool] = None
    compound: Optional[bool] = None
    has_child: Optional[bool] = None
    has_image: Optional[bool] = None
    is_labeled: Optional[bool] = None
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)

class ItemQuantity(BaseModel):
    stock: Optional[Stock] = None   
    common: Optional[Decimal] = None
    allowed: Optional[Decimal] = None
    booked: Optional[Decimal] = None

class ItemExt(BaseModel):
    item: Item
    quantity: Optional[ItemQuantity] = None
    pricetype: Optional[PriceType] = None  
    price: Optional[Decimal] = None
    last_purchase_cost: Optional[Decimal] = None
    image_url: Optional[str] = None

class ItemImportData(BaseModel):
    index: Optional[str] = None
    name: str
    fullname: Optional[str] = None
    code: Optional[str] = None
    articul: Optional[str] = None
    group_path: Optional[str] = None
    barcodes: Optional[str] = None
    color_name: Optional[str] = None
    brand_name: Optional[str] = None
    producer_name: Optional[str] = None
    size_name: Optional[str] = None
    unit_name: Optional[str] = None
    department_name: Optional[str] = None
    description: Optional[str] = None
    vat_name: Optional[str] = None
    icps: Optional[str] = None
    labeled: Optional[int] = None
    package_code: Optional[int] = None
    parent_code: Optional[int] = None

class ItemImportRequest(BaseModel):
    comparation_value: Optional[str] = None
    group_separator: Optional[str] = None
    barcode_separator: Optional[str] = None
    group_id: Optional[int] = None
    unit_id: Optional[int] = None
    vat_value_id: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None