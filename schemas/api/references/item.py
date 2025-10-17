# schemas/api/references/item.py
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import Field as PydField, field_validator
from pydantic.config import ConfigDict

from schemas.api.base import APIBaseResponse, BaseSchema
from schemas.api.references.brand import Brand
from schemas.api.references.price_type import PriceType
from schemas.api.references.stock import Stock
from schemas.api.references.unit import Unit


# ---------- Плейсхолдеры справочников ----------
# (оставлены как есть для обратной совместимости с текущими импортами)
class ItemGroup(BaseSchema):  # BC: прежнее имя и пустая структура сохранены
    model_config = ConfigDict(extra="ignore")


class Department(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


class TaxVat(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


class Color(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


class SizeChart(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


class Producer(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


class Country(BaseSchema):  # BC
    model_config = ConfigDict(extra="ignore")


# ---------- Общие enum ----------
class ItemType(str, Enum):
    """Тип номенклатуры."""

    Item = "Item"
    Service = "Service"


class SortDirection(str, Enum):
    """Направление сортировки."""

    ASC = "ASC"
    DESC = "DESC"


# ---------- Базовая номенклатура (рид-модель) ----------
class Item(BaseSchema):
    """
    Номенклатурная позиция.
    """

    model_config = ConfigDict(extra="ignore")

    id: int = PydField(..., description="ID номенклатуры.")
    group: ItemGroup = PydField(None, description="Группа номенклатуры.")
    department: Optional[Department] = PydField(None, description="Подразделение.")
    vat: Optional[TaxVat] = PydField(None, description="Ставка НДС.")
    barcode_list: Optional[str] = PydField(
        None, description="Список штрихкодов (строка)."
    )
    base_barcode: Optional[str] = PydField(None, description="Базовый штрихкод.")
    unit: Optional[Unit] = PydField(None, description="Единица измерения (основная).")
    unit2: Optional[Unit] = PydField(
        None, description="Единица измерения (дополнительная)."
    )
    color: Optional[Color] = PydField(None, description="Цвет.")
    size: Optional[SizeChart] = PydField(None, description="Размер.")
    brand: Optional[Brand] = PydField(None, description="Бренд.")
    producer: Optional[Producer] = PydField(None, description="Производитель.")
    country: Optional[Country] = PydField(None, description="Страна происхождения.")
    compound: Optional[bool] = PydField(None, description="Составной товар.")
    deleted_mark: Optional[bool] = PydField(None, description="Метка удаления.")
    image_url: Optional[str] = PydField(None, description="URL изображения.")
    parent_id: Optional[int] = PydField(None, description="ID родителя (для иерархии).")
    has_child: Optional[bool] = PydField(None, description="Есть дочерние элементы.")
    last_update: int = PydField(
        ..., description="Unix time (сек) последнего изменения."
    )

    # BC: поле type оставляем строкой с дефолтом "none" (исторически); позволяем подавать Enum и приводим к str валидатором
    type: str = PydField(
        "none", description='Тип позиции (исторически строка, "none" по умолчанию).'
    )
    code: Optional[int] = PydField(None, description="Внутренний код.")
    name: Optional[str] = PydField(None, description="Краткое наименование.")
    fullname: Optional[str] = PydField(None, description="Полное наименование.")
    description: Optional[str] = PydField(None, description="Описание.")
    articul: Optional[str] = PydField(None, description="Артикул.")
    kdt: Optional[int] = PydField(None, description="КДТ (если применимо).")
    min_quantity: Optional[int] = PydField(None, description="Минимальное количество.")
    icps: Optional[str] = PydField(None, description="ICPS (если применимо).")
    assemblable: Optional[bool] = PydField(
        None, description="Можно собирать (комплектовать)."
    )
    disassemblable: Optional[bool] = PydField(
        None, description="Можно разукомплектовать."
    )
    is_labeled: Optional[bool] = PydField(None, description="Маркируемый товар.")
    comission_tin: Optional[str] = PydField(
        None, description="ИНН комитента (для комиссионной торговли)."
    )
    package_code: Optional[str] = PydField(None, description="Код упаковки.")
    # BC: origin оставляем строкой с дефолтом "none" (исторически); можно было бы ввести Enum, но не меняем тип
    origin: str = PydField(
        "none", description='Происхождение (исторически строка, "none" по умолчанию).'
    )
    partner_id: Optional[int] = PydField(
        None, description="ID партнёра-поставщика (если связан)."
    )

    @field_validator(
        "barcode_list",
        "base_barcode",
        "image_url",
        "name",
        "fullname",
        "description",
        "articul",
        "icps",
        "comission_tin",
        "package_code",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("type", mode="before")
    @classmethod
    def _normalize_type(cls, v):
        # BC: принимаем как str, так и ItemType и сохраняем строку
        if isinstance(v, ItemType):
            return v.value
        return v


# ---------- Search ----------
class ItemSearchRequest(BaseSchema):
    """
    Поиск номенклатуры по полям: code, name, articul, barcode.
    """

    model_config = ConfigDict(extra="forbid")

    code: Optional[str] = PydField(None, description="Код (частичное совпадение).")
    name: Optional[str] = PydField(
        None, description="Наименование (частичное совпадение)."
    )
    articul: Optional[str] = PydField(
        None, description="Артикул (частичное совпадение)."
    )
    barcode: Optional[str] = PydField(
        None, description="Штрихкод (частичное совпадение)."
    )

    deleted_mark: Optional[bool] = PydField(None, description="Метка удаления.")
    assemblable: Optional[bool] = PydField(
        None, description="Фильтр по признаку сборки."
    )
    disassemblable: Optional[bool] = PydField(
        None, description="Фильтр по признаку разборки."
    )
    compound: Optional[bool] = PydField(
        None, description="Фильтр по составным товарам."
    )
    has_child: Optional[bool] = PydField(
        None, description="Фильтр по наличию дочерних."
    )
    type: Optional[ItemType] = PydField(None, description="Тип номенклатуры.")

    @field_validator("code", "name", "articul", "barcode", mode="before")
    @classmethod
    def _strip_search(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- Get ----------
class RedefinitionOption(BaseSchema):
    """Опции переопределений (локализация и пр.)."""

    model_config = ConfigDict(extra="forbid")

    language: Optional[str] = PydField(None, description='Код языка, напр. "RUS".')
    app_id: Optional[int] = PydField(
        None, ge=1, description="ID приложения (если применимо)."
    )


class ItemGetRequest(BaseSchema):
    """
    Получение списка номенклатуры по фильтрам.
    """

    model_config = ConfigDict(extra="forbid")

    ids: Optional[List[int]] = PydField(None, description="ID позиций.")
    group_ids: Optional[List[int]] = PydField(None, description="ID групп.")
    type: Optional[ItemType] = PydField(None, description="Тип номенклатуры.")
    parent_ids: Optional[List[int]] = PydField(
        None, description="ID родительских элементов."
    )
    codes: Optional[List[int]] = PydField(None, description="Коды позиций.")
    redefinition_option: Optional[RedefinitionOption] = PydField(
        None, description="Опции переопределения."
    )
    department_ids: Optional[List[int]] = PydField(
        None, description="ID подразделений."
    )
    deleted_mark: Optional[bool] = PydField(None, description="Метка удаления.")
    assemblable: Optional[bool] = PydField(None, description="Признак собираемости.")
    disassemblable: Optional[bool] = PydField(
        None, description="Признак разукомплектования."
    )
    compound: Optional[bool] = PydField(None, description="Составной товар.")
    has_child: Optional[bool] = PydField(None, description="Есть дочерние.")
    is_labeled: Optional[bool] = PydField(None, description="Маркируемый товар.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Лимит.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Смещение.")


# ---------- GetExt ----------
class ItemGetExtSortColumn(str, Enum):
    """Колонки сортировки для GetExt."""

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


class ItemGetExtSortOrder(BaseSchema):
    """Ступень сортировки для GetExt."""

    model_config = ConfigDict(extra="forbid")

    column: ItemGetExtSortColumn = PydField(..., description="Колонка сортировки.")
    direction: SortDirection = PydField(..., description="Направление: ASC|DESC.")

    @field_validator("direction", mode="before")
    @classmethod
    def _normalize_dir(cls, v):
        # BC: принимаем 'asc'/'desc' в любом регистре и приводим к Enum
        if isinstance(v, str):
            up = v.strip().upper()
            if up in {"ASC", "DESC"}:
                return SortDirection[up]
        return v


class ItemGetExtImageSize(str, Enum):
    """Размер изображения в выдаче GetExt."""

    Large = "Large"
    Medium = "Medium"
    Small = "Small"


class ItemGetExtRequest(BaseSchema):
    """
    Получение расширенной информации о номенклатуре с ценой/остатками/изображением.
    """

    model_config = ConfigDict(extra="forbid")

    stock_id: Optional[int] = PydField(None, ge=1, description="ID склада.")
    price_type_id: Optional[int] = PydField(None, ge=1, description="ID типа цены.")
    sort_orders: Optional[List[ItemGetExtSortOrder]] = PydField(
        None, description="Сортировка."
    )
    search: Optional[str] = PydField(None, description="Строка поиска.")
    zero_quantity: Optional[bool] = PydField(
        None, description="Включать позиции с нулевым остатком."
    )
    zero_price: Optional[bool] = PydField(
        None, description="Включать позиции с нулевой ценой."
    )
    image_size: Optional[ItemGetExtImageSize] = PydField(
        None, description="Размер изображения."
    )

    ids: Optional[List[int]] = PydField(None, description="ID позиций.")
    group_ids: Optional[List[int]] = PydField(None, description="ID групп.")
    type: Optional[ItemType] = PydField(None, description="Тип номенклатуры.")
    parent_ids: Optional[List[int]] = PydField(None, description="ID родителей.")
    codes: Optional[List[int]] = PydField(None, description="Коды позиций.")
    redefinition_option: Optional[RedefinitionOption] = PydField(
        None, description="Опции переопределения."
    )
    department_ids: Optional[List[int]] = PydField(
        None, description="ID подразделений."
    )
    deleted_mark: Optional[bool] = PydField(None, description="Метка удаления.")
    assemblable: Optional[bool] = PydField(None, description="Собираемый.")
    disassemblable: Optional[bool] = PydField(None, description="Разукомплектуемый.")
    compound: Optional[bool] = PydField(None, description="Составной.")
    has_child: Optional[bool] = PydField(None, description="Есть дочерние.")
    has_image: Optional[bool] = PydField(None, description="Только с изображением.")
    is_labeled: Optional[bool] = PydField(None, description="Маркируемый товар.")
    limit: Optional[int] = PydField(default=None, ge=1, description="Лимит.")
    offset: Optional[int] = PydField(default=None, ge=0, description="Смещение.")

    @field_validator("search", mode="before")
    @classmethod
    def _strip_search(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- Расширенная структура для GetExt ----------
class ItemQuantity(BaseSchema):
    """Остатки по складам/разрезам."""

    model_config = ConfigDict(extra="ignore")

    stock: Optional[Stock] = PydField(None, description="Склад.")
    common: Optional[Decimal] = PydField(None, description="Доступно всего.")
    allowed: Optional[Decimal] = PydField(None, description="Разрешено к продаже.")
    booked: Optional[Decimal] = PydField(None, description="Зарезервировано.")


# ---------- GetQuantity ----------
class ItemGetQuantityRequest(BaseSchema):
    """Параметры запроса количества номенклатуры."""

    model_config = ConfigDict(extra="forbid")

    item_id: int = PydField(..., ge=1, description="ID номенклатуры.")
    stock_ids: Optional[List[int]] = PydField(
        None, description="Список ID складов для выборки остатков."
    )
    date: Optional[int] = PydField(
        None,
        ge=0,
        description="Дата, на которую требуется остаток (Unix time, секунд).",
    )


class ItemGetQuantityResponse(APIBaseResponse[List[ItemQuantity]]):
    """Ответ на запрос /v1/Item/GetQuantity."""

    model_config = ConfigDict(extra="ignore")


class ItemExt(BaseSchema):
    """Элемент расширенной выдачи."""

    model_config = ConfigDict(extra="ignore")

    item: Item = PydField(..., description="Основная карточка товара.")
    quantity: Optional[ItemQuantity] = PydField(None, description="Остатки/резервы.")
    pricetype: Optional[PriceType] = PydField(None, description="Тип цены.")
    price: Optional[Decimal] = PydField(None, description="Цена.")
    last_purchase_cost: Optional[Decimal] = PydField(
        None, description="Последняя закупочная цена."
    )
    image_url: Optional[str] = PydField(
        None, description="URL изображения (с учётом image_size)."
    )

    @field_validator("image_url", mode="before")
    @classmethod
    def _strip_img(cls, v):
        return v.strip() if isinstance(v, str) else v


# ---------- Импорт ----------
class ItemImportData(BaseSchema):
    """Строка данных импорта номенклатуры."""

    model_config = ConfigDict(extra="forbid")

    index: Optional[str] = PydField(
        None, description="Индекс записи (идентификатор в исходных данных)."
    )
    name: str = PydField(..., description="Наименование.")
    fullname: Optional[str] = PydField(None, description="Полное наименование.")
    code: Optional[str] = PydField(None, description="Код.")
    articul: Optional[str] = PydField(None, description="Артикул.")
    group_path: Optional[str] = PydField(
        None, description='Путь группы, разделитель в request: "group_separator".'
    )
    barcodes: Optional[str] = PydField(
        None,
        description='Список штрихкодов, разделитель в request: "barcode_separator".',
    )
    color_name: Optional[str] = PydField(None, description="Цвет (наименование).")
    brand_name: Optional[str] = PydField(None, description="Бренд (наименование).")
    producer_name: Optional[str] = PydField(
        None, description="Производитель (наименование)."
    )
    size_name: Optional[str] = PydField(None, description="Размер (наименование).")
    unit_name: Optional[str] = PydField(
        None, description="Единица измерения (наименование)."
    )
    department_name: Optional[str] = PydField(
        None, description="Подразделение (наименование)."
    )
    description: Optional[str] = PydField(None, description="Описание.")
    vat_name: Optional[str] = PydField(None, description="Ставка НДС (наименование).")
    icps: Optional[str] = PydField(None, description="ICPS.")
    labeled: Optional[int] = PydField(
        None, description="Маркируемый (0/1)."
    )  # BC: тип int сохранён
    package_code: Optional[int] = PydField(
        None, description="Код упаковки."
    )  # BC: тип int сохранён
    parent_code: Optional[int] = PydField(
        None, description="Код родителя."
    )  # BC: тип int сохранён

    @field_validator(
        "index",
        "name",
        "fullname",
        "code",
        "articul",
        "group_path",
        "barcodes",
        "color_name",
        "brand_name",
        "producer_name",
        "size_name",
        "unit_name",
        "department_name",
        "description",
        "vat_name",
        "icps",
        mode="before",
    )
    @classmethod
    def _strip_import(cls, v):
        return v.strip() if isinstance(v, str) else v


class ItemImportRequest(BaseSchema):
    """
    Пакет на импорт номенклатуры.
    """

    model_config = ConfigDict(extra="forbid")

    comparation_value: str = PydField(
        ..., description="Поле сравнения для поиска существующих записей."
    )
    # BC: поля с '= None' были типизированы как 'str = None'; переводим в Optional[str] = None без смены имени/значения по умолчанию
    group_separator: Optional[str] = PydField(
        None, description="Разделитель групп в пути (напр. '/')."
    )  # BC
    barcode_separator: Optional[str] = PydField(
        None, description="Разделитель штрихкодов (напр. ',')."
    )  # BC
    group_id: Optional[int] = PydField(
        None, ge=1, description="Группа по умолчанию для импорта."
    )  # BC
    unit_id: Optional[int] = PydField(
        None, ge=1, description="Ед. измерения по умолчанию."
    )  # BC
    vat_value_id: Optional[int] = PydField(
        None, ge=1, description="Ставка НДС по умолчанию."
    )  # BC
    # BC: раньше было data: List[ItemImportData] = [] — заменено на default_factory=list (та же семантика пустого списка)
    data: List[ItemImportData] = PydField(
        default_factory=list, description="Массив строк импорта."
    )  # BC

    @field_validator(
        "comparation_value", "group_separator", "barcode_separator", mode="before"
    )
    @classmethod
    def _strip_req(cls, v):
        return v.strip() if isinstance(v, str) else v


__all__ = [
    "ItemType",
    "SortDirection",
    "Item",
    "ItemSearchRequest",
    "RedefinitionOption",
    "ItemGetRequest",
    "ItemGetExtSortColumn",
    "ItemGetExtSortOrder",
    "ItemGetExtImageSize",
    "ItemGetExtRequest",
    "ItemQuantity",
    "ItemGetQuantityRequest",
    "ItemGetQuantityResponse",
    "ItemExt",
    "ItemImportData",
    "ItemImportRequest",
    # Плейсхолдеры (для текущей обратной совместимости импортов):
    "ItemGroup",
    "Department",
    "TaxVat",
    "Color",
    "SizeChart",
    "Producer",
    "Country",
]
