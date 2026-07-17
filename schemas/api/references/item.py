"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import Enum, IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class GetWithoutICPSRequest(RegosModel):
    "Модель данных для запроса номенклатуры без ИКПУ"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ImageSize(str, Enum):
    "Перечисление для размеров ихображений"
    Default = "Default"
    Large = "Large"
    Medium = "Medium"
    Small = "Small"


class ImportItems(RegosModel):
    "модель для импорта данных"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    comparation_value: ItemImportComparationValue | None = PydField(default=None, description="Сопоставление: Default - не задано (будут добавляться все), Code - по полю код, Name - по полю имя, Articul - по полю\nартикул, Barcode - по штрихкоду. Предназначен для предотвращения добавления дубликатов, будет происходить проверка\nдобавляемой номенклатуры по указанному параметру, номенклатура с совпадающим значением указанного параметра не будет\nдобавлена")
    group_separator: str | None = PydField(default=None, description="Разделитель групп: символ, которым разделяются вложенные группы, по принципу Группа/Подгруппа")
    barcode_separator: str | None = PydField(default=None, description="Разделитель штрихкодов: символ, которым разделяются несколько штрих-кодов в одной строке")
    group_id: int | None = PydField(default=None, description="ID группы номенклатуры по умолчанию, в которую будет импортирована номенклатура с пустым значением параметра group_path")
    unit_id: int | None = PydField(default=None, description="ID единицы измерения по умолчанию, которая будет присвоена импортируемой номенклатуре с пустым значением параметра unit_name")
    vat_value_id: int | None = PydField(default=None, description="ID ставки НДС по умолчанию, которая будет назначена импортируемой номенклатуре с пустым значением парвметра vat_name")
    data: list[ItemImportData] | None = PydField(default=None, description="Массив импортируемой номенклатуры")


class Int64ArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[int] | Error | None = PydField(default=None, description="Объект результата.")


class Item(RegosModel):
    "Модель, описывающая номенклатуру"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID номенклатуры")
    group: ItemGroup | None = PydField(default=None, description="Группа номенклатуры")
    department: Department | None = PydField(default=None, description="Отдел, к которому принадлежит номенклатура")
    vat: TaxVat | None = PydField(default=None, description="Ставка НДС (%)")
    barcode_list: str | None = PydField(default=None, description="Список штрих-кодов номенклатуры, разделенных символом ,")
    base_barcode: str | None = PydField(default=None, description="Штрих-код номенклатуры")
    unit: Unit | None = PydField(default=None, description="Единица измерения номенклатуры")
    unit2: Unit | None = PydField(default=None, description="Единица измерения номенклатуры для КДТ")
    color: Color | None = PydField(default=None, description="Цвет номенклатуры")
    size: SizeChart | None = PydField(default=None, description="Размер номенклатуры")
    brand: Brand | None = PydField(default=None, description="Бренд номенклатуры")
    producer: Producer | None = PydField(default=None, description="Производитель номенклатуры")
    country: Country | None = PydField(default=None, description="Страна производства номенклатуры")
    compound: bool | None = PydField(default=None, description="Метка о том, что номенклатура составная")
    deleted_mark: bool | None = PydField(default=None, description="Метка на удаление")
    image_url: str | None = PydField(default=None, description="URL изображения номенклатуры")
    parent_id: int | None = PydField(default=None, description="ID родительской номенклатуры (используется для создания вариаций)")
    has_child: bool | None = PydField(default=None, description="Метка о наличии дочерних элементов (используется для создания вариаций)")
    min_quantity: int | None = PydField(default=None, description="Минимальное количество номенклатуры")
    fields: list[FieldValue] | None = PydField(default=None, description="Массив значений дополнительных полей")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")
    type: ItemType | None = PydField(default=None)
    code: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    articul: str | None = PydField(default=None)
    kdt: int | None = PydField(default=None)
    icps: str | None = PydField(default=None, description="Ввести поле идентификационных кодов продукции и услуг (ИКПУ)")
    assemblable: bool | None = PydField(default=None, description="Товар можно произвести через производство \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    disassemblable: bool | None = PydField(default=None, description="Товар можно разобрать. Относится только к товарам, которые можно произвести \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    is_labeled: bool | None = PydField(default=None, description="учёт маркировки")
    comission_tin: str | None = PydField(default=None, description="ИНН (ПИНФЛ) владельца коммисионного товара")
    package_code: str | None = PydField(default=None, description="Код упаковки")
    origin: ItemOriginEnum | None = PydField(default=None, description="Происхождение товара")
    partner_id: int | None = PydField(default=None)


class ItemAdd(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    group_id: int | None = PydField(default=None)
    department_id: int | None = PydField(default=None)
    vat_id: int | None = PydField(default=None)
    unit_id: int | None = PydField(default=None)
    unit2_id: int | None = PydField(default=None)
    color_id: int | None = PydField(default=None)
    size_id: int | None = PydField(default=None)
    brand_id: int | None = PydField(default=None)
    producer_id: int | None = PydField(default=None)
    country_id: int | None = PydField(default=None)
    compound: bool | None = PydField(default=None, description="составной товар или нет")
    parent_id: int | None = PydField(default=None, description="ID родительской номеклатуры (для вариационного товара)")
    min_quantity: int | None = PydField(default=None)
    fields: list[FieldValueAdd] | None = PydField(default=None, description="значения доп полей для добавления")
    type: ItemType | None = PydField(default=None)
    code: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    articul: str | None = PydField(default=None)
    kdt: int | None = PydField(default=None)
    icps: str | None = PydField(default=None, description="Ввести поле идентификационных кодов продукции и услуг (ИКПУ)")
    assemblable: bool | None = PydField(default=None, description="Товар можно произвести через производство \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    disassemblable: bool | None = PydField(default=None, description="Товар можно разобрать. Относится только к товарам, которые можно произвести \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    is_labeled: bool | None = PydField(default=None, description="учёт маркировки")
    comission_tin: str | None = PydField(default=None, description="ИНН (ПИНФЛ) владельца коммисионного товара")
    package_code: str | None = PydField(default=None, description="Код упаковки")
    origin: ItemOriginEnum | None = PydField(default=None, description="Происхождение товара")
    partner_id: int | None = PydField(default=None)


class ItemAddCopy(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id номенклатуры")


class ItemAddToCompound(RegosModel):
    "Модель добавления номенклатуры к составной номенклатуре"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    compound_id: int | None = PydField(default=None, description="ID составной номенклатуры")
    item_id: int | None = PydField(default=None, description="ID добавляемой номенклатуры")
    quantity: _Decimal | None = PydField(default=None, description="Количество добавляемой номенклатуры (по умолчанию 1)")


class ItemCodeCheckIn(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: int | None = PydField(default=None, description="Код номенклатуры")


class ItemCodeCheckOut(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    enable: bool | None = PydField(default=None)


class ItemCodeCheckOutRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: ItemCodeCheckOut | Error | None = PydField(default=None, description="Объект результата.")


class ItemCodeGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: int | None = PydField(default=None)


class ItemCodeGetRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: ItemCodeGet | Error | None = PydField(default=None, description="Объект результата.")


class ItemCompound(RegosModel):
    "Модель элемента составной номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item: Item | None = PydField(default=None, description="Номенклатура")
    quantity: _Decimal | None = PydField(default=None, description="количество")
    image_url: str | None = PydField(default=None, description="URL изображения")


class ItemCompoundGet(RegosModel):
    "Модель для запроса состава составной номенклатуры"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="ID составной номенклатуры")
    image_size: ImageSize | None = PydField(default=None, description="Размер изображения: Small (100х100), Medium (300х300), Large (900х900). По умолчанию: Small")


class ItemCompoundRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemCompound] | Error | None = PydField(default=None, description="Массив результата.")


class ItemCurrentQuantity(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="id номенклатуры")
    stock_id: int | None = PydField(default=None, description="id склада")
    quantity: _Decimal | None = PydField(default=None, description="Количество")


class ItemCurrentQuantityGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_ids: list[int] | None = PydField(default=None, description="Массив ID номенклатуры. Количество передаваемых элементов в массиве не должно превышать 250")
    stock_ids: list[int] | None = PydField(default=None, description="Массив ID складов")


class ItemCurrentQuantityRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemCurrentQuantity] | Error | None = PydField(default=None, description="Массив результата.")


class ItemDelete(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id номенклатуры")


class ItemDeleteFromCompound(RegosModel):
    "Модель удаления номенклатуры из составной номенклатуры"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    compound_id: int | None = PydField(default=None, description="ID составной номенклатуры")
    item_id: int | None = PydField(default=None, description="ID удаляемой номенклатуры")


class ItemDeleteMark(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id номенклатуры")


class ItemEdit(RegosModel):
    "Модель редактирвоания номенклатуры"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID номенклатуры")
    group_id: int | None = PydField(default=None, description="ID группы номенклатуры. По умолчанию 0 - корневая группа")
    department_id: int | None = PydField(default=None, description="ID отдела, к которому принадлежит номенклатура")
    vat_id: int | None = PydField(default=None, description="ID ставки НДС")
    unit_id: int | None = PydField(default=None, description="ID единицы измерения номенклатуры")
    unit2_id: int | None = PydField(default=None, description="ID единицы измерения номенклатуры для КДТ")
    color_id: int | None = PydField(default=None, description="ID цвета номенклатуры")
    size_id: int | None = PydField(default=None, description="ID размера номенклатуры")
    brand_id: int | None = PydField(default=None, description="ID бренда номенклатуры")
    producer_id: int | None = PydField(default=None, description="ID производителя номенклатуры")
    country_id: int | None = PydField(default=None, description="ID страны производства номенклатуры")
    parent_id: int | None = PydField(default=None, description="ID родительской номенклатуры (используется для создания размерной сетки)")
    min_quantity: int | None = PydField(default=None, description="Минимальное количество номенклатуры")
    fields: list[FieldValueEdit] | None = PydField(default=None, description="Массив значений дополнительных полей")
    type: ItemType | None = PydField(default=None)
    code: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    articul: str | None = PydField(default=None)
    kdt: int | None = PydField(default=None)
    icps: str | None = PydField(default=None, description="Ввести поле идентификационных кодов продукции и услуг (ИКПУ)")
    assemblable: bool | None = PydField(default=None, description="Товар можно произвести через производство \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    disassemblable: bool | None = PydField(default=None, description="Товар можно разобрать. Относится только к товарам, которые можно произвести \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    is_labeled: bool | None = PydField(default=None, description="учёт маркировки")
    comission_tin: str | None = PydField(default=None, description="ИНН (ПИНФЛ) владельца коммисионного товара")
    package_code: str | None = PydField(default=None, description="Код упаковки")
    origin: ItemOriginEnum | None = PydField(default=None, description="Происхождение товара")
    partner_id: int | None = PydField(default=None)


class ItemExt(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item: Item | None = PydField(default=None, description="Модель, описывающая номенклатуру")
    quantity: ItemQuantity | None = PydField(default=None)
    pricetype: PriceType | None = PydField(default=None, description="Модель, описывающая виды цен")
    price: _Decimal | None = PydField(default=None)
    last_purchase_cost: _Decimal | None = PydField(default=None, description="последняя закупочная стоимость")
    image_url: str | None = PydField(default=None, description="URL изображения")


class ItemExtGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    stock_id: int | None = PydField(default=None, description="ID склада")
    price_type_id: int | None = PydField(default=None, description="ID типа цены")
    sort_orders: list[ItemOrder] | None = PydField(default=None, description="Сортировка выходных параметров")
    search: str | None = PydField(default=None, description="Строка поиска по полям: name - наименование, articul - артикул, code - код, barcode - штрих-код")
    zero_quantity: bool | None = PydField(default=None, description="Флаг, указывающий, выводить ли товары с 0 Количеством")
    zero_price: bool | None = PydField(default=None, description="Флаг, указывающий, выводить ли товары с 0 Ценой")
    has_image: bool | None = PydField(default=None, description="Флаг, указывающий, есть ли изображение у номенклатуры: null - вся номенклатура, true - только с изображениями, false - только без изображений")
    image_size: ImageSize | None = PydField(default=None, description="Размер изображения: <Large | 1> - 900х900px, <Medium | 2> - 300х300px, <Small | 3> - 100х100px")
    ids: list[int] | None = PydField(default=None, description="Массив id номенклатур")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп номенклатур")
    type: ItemType | None = PydField(default=None, description="Тип номенклатуры: <Item | 1> - Товар, <Service | 2> - Услуга")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительской номенклатуры")
    codes: list[int] | None = PydField(default=None, description="Массив кодов номенклатуры")
    department_ids: list[int] | None = PydField(default=None, description="Массив id отделов")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    assemblable: bool | None = PydField(default=None, description="Метка о том, что товар можно произвести")
    disassemblable: bool | None = PydField(default=None, description="Метка о том, что товар можно разобрать")
    compound: bool | None = PydField(default=None, description="Метка о том, что товар составной")
    has_child: bool | None = PydField(default=None, description="Имеет ли дочернюю номенклатуру: true - имеет, false - не имеет")
    is_labeled: bool | None = PydField(default=None, description="Метка о том, что товар подлежит маркировке")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ItemExtRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemExt] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ItemGet(RegosModel):
    "модель для получения номенклатуры"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    ids: list[int] | None = PydField(default=None, description="Массив id номенклатур")
    group_ids: list[int] | None = PydField(default=None, description="Массив id групп номенклатур")
    type: ItemType | None = PydField(default=None, description="Тип номенклатуры: <Item | 1> - Товар, <Service | 2> - Услуга")
    parent_ids: list[int] | None = PydField(default=None, description="Массив id родительской номенклатуры")
    codes: list[int] | None = PydField(default=None, description="Массив кодов номенклатуры")
    department_ids: list[int] | None = PydField(default=None, description="Массив id отделов")
    deleted_mark: bool | None = PydField(default=None, description="Метка об удалении")
    assemblable: bool | None = PydField(default=None, description="Метка о том, что товар можно произвести")
    disassemblable: bool | None = PydField(default=None, description="Метка о том, что товар можно разобрать")
    compound: bool | None = PydField(default=None, description="Метка о том, что товар составной")
    has_child: bool | None = PydField(default=None, description="Имеет ли дочернюю номенклатуру: true - имеет, false - не имеет")
    is_labeled: bool | None = PydField(default=None, description="Метка о том, что товар подлежит маркировке")
    filters: list[Filter] | None = PydField(default=None, description="Фильтры по основным и дополнительным полям")
    limit: int | None = PydField(default=None, description="Количество возвращаемых элементов при запросе")
    offset: int | None = PydField(default=None, description="Смещение от начала выборки")


class ItemGetQuantityIncome(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_id: int | None = PydField(default=None, description="Id номенклатуры")
    stock_ids: list[int] | None = PydField(default=None, description="Массив id складов")
    date: int | None = PydField(default=None, description="Дата в unix time, на которую необходимо вернуть количество")


class ItemGetQuantityOutcome(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    stock: Stock | None = PydField(default=None, description="Модель, описывающая склады")
    common: _Decimal | None = PydField(default=None, description="Общее кол-во")
    allowed: _Decimal | None = PydField(default=None, description="Доступное кол-во (common - booked)")
    booked: _Decimal | None = PydField(default=None, description="Забронированное кол-во")


class ItemGetQuantityOutcomeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemGetQuantityOutcome] | Error | None = PydField(default=None, description="Массив результата.")


class ItemGetQuantityPosIncome(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user_id: int | None = PydField(default=None, description="ID кассира")
    item_id: int | None = PydField(default=None, description="Id номенклатуры")
    stock_ids: list[int] | None = PydField(default=None, description="Массив id складов")
    date: int | None = PydField(default=None, description="Дата в unix time, на которую необходимо вернуть количество")


class ItemGetQuantityPosOutcome(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    stock_name: str | None = PydField(default=None)
    firm_name: str | None = PydField(default=None)
    common: _Decimal | None = PydField(default=None, description="Общее кол-во")
    allowed: _Decimal | None = PydField(default=None, description="Доступное кол-во (common - booked)")
    booked: _Decimal | None = PydField(default=None, description="Забронированное кол-во")


class ItemGetQuantityPosOutcomeRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemGetQuantityPosOutcome] | Error | None = PydField(default=None, description="Массив результата.")


class ItemImportComparationValue(str, Enum):
    "перечесление настроек по импорт"
    Default = "Default"
    Code = "Code"
    Name = "Name"
    Articul = "Articul"
    Barcode = "Barcode"
    ICPS = "ICPS"
    ICPSBarcode = "ICPSBarcode"


class ItemImportData(RegosModel):
    "модель для описание нмоенклатуры для импорта"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    index: str | None = PydField(default=None, description="индекс строки в файле, необязательное")
    name: str | None = PydField(default=None, description="наименование")
    fullname: str | None = PydField(default=None, description="полное наименование")
    code: str | None = PydField(default=None, description="код номенклатуры")
    articul: str | None = PydField(default=None, description="артикул")
    group_path: str | None = PydField(default=None, description="группа (path)")
    barcodes: str | None = PydField(default=None, description="штрихкод(ы)")
    color_name: str | None = PydField(default=None, description="цвет")
    brand_name: str | None = PydField(default=None, description="бренд")
    producer_name: str | None = PydField(default=None, description="производитель")
    size_name: str | None = PydField(default=None, description="размер")
    unit_name: str | None = PydField(default=None, description="единица измерения")
    department_name: str | None = PydField(default=None, description="отдел")
    description: str | None = PydField(default=None, description="описание")
    vat_name: str | None = PydField(default=None, description="ставка НДС")
    icps: str | None = PydField(default=None, description="код ИКПУ")
    icpsbarcode: str | None = PydField(default=None, description="код ИКПУ+barcode")
    labeled: int | None = PydField(default=None, description="Метка обязательной маркировки")
    package_code: int | None = PydField(default=None, description="код упаковки")
    parent_code: int | None = PydField(default=None, description="родитель (код)")


class ItemImportDataResponse(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    success: bool | None = PydField(default=None, description="Успешность выполнения импорта позиции")
    index: str | None = PydField(default=None, description="индекс строки в файле, если было")
    item_id: int | None = PydField(default=None, description="id номенклатуры (если добавлена или найдена)")


class ItemImportDataResponseArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemImportDataResponse] | Error | None = PydField(default=None, description="Объект результата.")


class ItemMatchingRequest(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: MatchingType | None = PydField(default=None, description="Тип сопоставления: , Code - По коду, Name - По наименованию, Articul - По артиклу, Barcode - По штрих-коду")
    data: list[ItemMatchingRequestData] | None = PydField(default=None, description="Массив данных")


class ItemMatchingRequestData(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    index: str | None = PydField(default=None)
    value: str | None = PydField(default=None)


class ItemMatchingResponse(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    index: str | None = PydField(default=None)
    item_id: int | None = PydField(default=None)
    value: str | None = PydField(default=None)


class ItemMatchingResponseArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemMatchingResponse] | Error | None = PydField(default=None, description="Объект результата.")


class ItemOFDPackage(RegosModel):
    "модель для отображения packages (упаковок) OFD"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    code: str | None = PydField(default=None)
    nameUz: str | None = PydField(default=None)
    nameRu: str | None = PydField(default=None)
    nameLat: str | None = PydField(default=None)


class ItemOFDPackageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemOFDPackage] | Error | None = PydField(default=None, description="Массив результата.")


class ItemOFDPackagesGet(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    icps: str | None = PydField(default=None, description="ИКПУ")


class ItemOprOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: ItemOprOrderColumn | None = PydField(default=None)
    direction: ItemOprOrderDirection | None = PydField(default=None)


class ItemOprOrderColumn(str, Enum):
    Default = "Default"
    stock_name = "stock_name"
    firm_name = "firm_name"
    quantity = "quantity"
    date = "date"
    doc_type = "doc_type"


class ItemOprOrderDirection(str, Enum):
    Default = "Default"
    ASC = "ASC"
    DESC = "DESC"


class ItemOrder(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    column: ItemOrderColumn | None = PydField(default=None)
    direction: ColumnSortOrderDirection | None = PydField(default=None, description="enum для перечесление сортировок колонок")


class ItemOrderColumn(str, Enum):
    default = "default"
    name = "name"
    articul = "articul"
    code = "code"
    unit_name = "unit.name"
    color_name = "color.name"
    size_name = "size.name"
    brand_name = "brand.name"
    producer_name = "producer.name"
    country_name = "country.name"
    vat_name = "vat.name"
    department_name = "department.name"


class ItemOriginEnum(str, Enum):
    "Перечисление происхождение товара"
    BuyingAndSelling = "BuyingAndSelling"
    Produced = "Produced"
    Service = "Service"
    NotSpecified = "NotSpecified"


class ItemPreCost(RegosModel):
    "модель ответа по себестоимости номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    item_id: int | None = PydField(default=None)
    value: _Decimal | None = PydField(default=None)
    cost_date: int | None = PydField(default=None)


class ItemPreCostArrayRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemPreCost] | Error | None = PydField(default=None, description="Объект результата.")


class ItemPreCostGet(RegosModel):
    "модель для получения себестоимости номенклатры"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item_ids: list[int] | None = PydField(default=None, description="Массив id номенклатуры")
    firm_id: int | None = PydField(default=None, description="ID предприятия")
    cost_date: int | None = PydField(default=None)


class ItemQuantity(RegosModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    common: _Decimal | None = PydField(default=None, description="Общее кол-во")
    allowed: _Decimal | None = PydField(default=None, description="Доступное кол-во (common - booked)")
    booked: _Decimal | None = PydField(default=None, description="Забронированное кол-во")


class ItemRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Item] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ItemReplaceICPS(RegosModel):
    "модель для установки ИКПУ для номенклатуры (массовое)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    old_icps: str | None = PydField(default=None, description="Старый ИКПУ")
    new_icps: str | None = PydField(default=None, description="Новый ИКПУ")


class ItemSearch(RegosModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    code: str | None = PydField(default=None, description="Код номенклатуры")
    name: str | None = PydField(default=None, description="Наименование номенклатуры")
    articul: str | None = PydField(default=None, description="Артикул номенклатуры")
    barcode: str | None = PydField(default=None, description="Штрих-код номенклатуры")
    deleted_mark: bool | None = PydField(default=None, description="Помечен на удаление")
    assemblable: bool | None = PydField(default=None, description="Сборный. Может участвовать в сбрке на произвостве")
    disassemblable: bool | None = PydField(default=None, description="Разборный. Может участвовать в разборке на произвостве")
    compound: bool | None = PydField(default=None, description="Метка о том, что товар составной")
    has_child: bool | None = PydField(default=None, description="Вариативный - имеет дочернюю номенклатуру")
    type: ItemType | None = PydField(default=None, description="Тип номенклатуры, если null - то все типы")


class ItemSetICPS(RegosModel):
    "модель для установки ИКПУ для номенклатуры (массовое)"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    icps: str | None = PydField(default=None, description="ИКПУ")
    group_id: int | None = PydField(default=None, description="ID группы номенклатуры")


class ItemShort(RegosModel):
    "модель короткой записи номенклатуры"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None)
    group_id: int | None = PydField(default=None)
    department_id: int | None = PydField(default=None)
    vat_id: int | None = PydField(default=None)
    unit_id: int | None = PydField(default=None)
    unit2_id: int | None = PydField(default=None)
    color_id: int | None = PydField(default=None)
    size_id: int | None = PydField(default=None)
    brand_id: int | None = PydField(default=None)
    producer_id: int | None = PydField(default=None)
    country_id: int | None = PydField(default=None)
    compound: bool | None = PydField(default=None, description="составной товар или нет")
    parent_id: int | None = PydField(default=None, description="ID родительской номеклатуры (для вариационного товара), 0 - нет родительской номенклатуры")
    has_child: bool | None = PydField(default=None, description="Метка о наличии дочерних номенклатур (для вариационного товара)")
    min_quantity: int | None = PydField(default=None)
    deleted_mark: bool | None = PydField(default=None)
    last_update: int | None = PydField(default=None)
    base_barcode: str | None = PydField(default=None, description="Основной штрих-код")
    type: ItemType | None = PydField(default=None)
    code: int | None = PydField(default=None)
    name: str | None = PydField(default=None)
    fullname: str | None = PydField(default=None)
    description: str | None = PydField(default=None)
    articul: str | None = PydField(default=None)
    kdt: int | None = PydField(default=None)
    icps: str | None = PydField(default=None, description="Ввести поле идентификационных кодов продукции и услуг (ИКПУ)")
    assemblable: bool | None = PydField(default=None, description="Товар можно произвести через производство \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    disassemblable: bool | None = PydField(default=None, description="Товар можно разобрать. Относится только к товарам, которые можно произвести \n           nullable сделан чтобы можно использовать и в Add и в Edit")
    is_labeled: bool | None = PydField(default=None, description="учёт маркировки")
    comission_tin: str | None = PydField(default=None, description="ИНН (ПИНФЛ) владельца коммисионного товара")
    package_code: str | None = PydField(default=None, description="Код упаковки")
    origin: ItemOriginEnum | None = PydField(default=None, description="Происхождение товара")
    partner_id: int | None = PydField(default=None)


class ItemShortRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemShort] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class ItemType(str, Enum):
    Item = "Item"
    Service = "Service"


class ItemWithoutICPS(RegosModel):
    "Модель ответа номенклатуры без ИКПУ с наименованием товара"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    name: str | None = PydField(default=None)
    id: int | None = PydField(default=None, description="ID номенклатуры")
    barcode: str | None = PydField(default=None, description="Штрих-код")


class ItemWithoutICPSRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemWithoutICPS] | Error | None = PydField(default=None, description="Массив результата.")


class ItemWithoutICPSShort(RegosModel):
    "Модель ответа номенклатуры без ИКПУ"
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: int | None = PydField(default=None, description="ID номенклатуры")
    barcode: str | None = PydField(default=None, description="Штрих-код")


class ItemWithoutICPSShortRegosOffsettedArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayOffsettedResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[ItemWithoutICPSShort] | Error | None = PydField(default=None, description="Массив результата.")
    next_offset: int | None = PydField(default=None, description="Смещение для следующей выборки данных.")
    total: int | None = PydField(default=None, description="Общее количество элементов выборки.")


class MatchingType(str, Enum):
    Default = "Default"
    Code = "Code"
    Name = "Name"
    Articul = "Articul"
    Barcode = "Barcode"
    ICPS = "ICPS"
    ICPSBarcode = "ICPSBarcode"


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import BooleanRegosObjectResult, ColumnSortOrderDirection, Error, InsertResult, UpdateResult
from schemas.api.common.filter import Filter
from schemas.api.references.brand import Brand
from schemas.api.references.color import Color
from schemas.api.references.country import Country
from schemas.api.references.department import Department
from schemas.api.references.field import FieldValue, FieldValueAdd, FieldValueEdit
from schemas.api.references.item_group import ItemGroup
from schemas.api.references.price_type import PriceType
from schemas.api.references.producer import Producer
from schemas.api.references.size_chart import SizeChart
from schemas.api.references.stock import Stock
from schemas.api.references.tax_vat import TaxVat
from schemas.api.references.unit import Unit


ItemAddRequest: TypeAlias = ItemAdd
ItemAddResponse: TypeAlias = InsertResult
ItemAddToCompoundRequest: TypeAlias = ItemAddToCompound
ItemAddToCompoundResponse: TypeAlias = UpdateResult
ItemCheckCodeRequest: TypeAlias = ItemCodeCheckIn
ItemCheckCodeResponse: TypeAlias = ItemCodeCheckOutRegosObjectResult
ItemCopyRequest: TypeAlias = ItemAddCopy
ItemCopyResponse: TypeAlias = InsertResult
ItemDeleteFromCompoundRequest: TypeAlias = ItemDeleteFromCompound
ItemDeleteFromCompoundResponse: TypeAlias = UpdateResult
ItemDeleteMarkRequest: TypeAlias = ItemDeleteMark
ItemDeleteMarkResponse: TypeAlias = UpdateResult
ItemDeleteRequest: TypeAlias = ItemDelete
ItemDeleteResponse: TypeAlias = UpdateResult
ItemEditRequest: TypeAlias = ItemEdit
ItemEditResponse: TypeAlias = UpdateResult
ItemFillIcpsByBarcodeRequest: TypeAlias = list[ItemWithoutICPSShort]
ItemFillIcpsByBarcodeResponse: TypeAlias = ItemWithoutICPSRegosArrayResult
ItemGetCodeRequest: TypeAlias = ItemCodeGet
ItemGetCodeResponse: TypeAlias = ItemCodeGetRegosObjectResult
ItemGetCompoundRequest: TypeAlias = ItemCompoundGet
ItemGetCompoundResponse: TypeAlias = ItemCompoundRegosArrayResult
ItemGetCurrentQuantityRequest: TypeAlias = ItemCurrentQuantityGet
ItemGetCurrentQuantityResponse: TypeAlias = ItemCurrentQuantityRegosArrayResult
ItemGetExtImageSize: TypeAlias = ImageSize
ItemGetExtRequest: TypeAlias = ItemExtGet
ItemGetExtResponse: TypeAlias = ItemExtRegosOffsettedArrayResult
ItemGetPackagesByIcpsRequest: TypeAlias = ItemOFDPackagesGet
ItemGetPackagesByIcpsResponse: TypeAlias = ItemOFDPackageRegosArrayResult
ItemGetQuantityPosRequest: TypeAlias = ItemGetQuantityPosIncome
ItemGetQuantityPosResponse: TypeAlias = ItemGetQuantityPosOutcomeRegosArrayResult
ItemGetQuantityRequest: TypeAlias = ItemGetQuantityIncome
ItemGetQuantityResponse: TypeAlias = ItemGetQuantityOutcomeRegosArrayResult
ItemGetRequest: TypeAlias = ItemGet
ItemGetResponse: TypeAlias = ItemRegosOffsettedArrayResult
ItemGetShortRequest: TypeAlias = ItemGet
ItemGetShortResponse: TypeAlias = ItemShortRegosOffsettedArrayResult
ItemGetWithoutIcpsRequest: TypeAlias = GetWithoutICPSRequest
ItemGetWithoutIcpsResponse: TypeAlias = ItemWithoutICPSShortRegosOffsettedArrayResult
ItemImportRequest: TypeAlias = ImportItems
ItemImportResponse: TypeAlias = ItemImportDataResponseArrayRegosObjectResult
ItemMatchRequest: TypeAlias = ItemMatchingRequest
ItemMatchResponse: TypeAlias = ItemMatchingResponseArrayRegosObjectResult
ItemMatchingData: TypeAlias = ItemMatchingRequestData
ItemMatchingType: TypeAlias = MatchingType
ItemReplaceIcpsRequest: TypeAlias = ItemReplaceICPS
ItemReplaceIcpsResponse: TypeAlias = BooleanRegosObjectResult
ItemSearchRequest: TypeAlias = ItemSearch
ItemSearchResponse: TypeAlias = Int64ArrayRegosObjectResult
ItemSetIcpsFromServerRequest: TypeAlias = list[ItemWithoutICPSShort]
ItemSetIcpsFromServerResponse: TypeAlias = ItemWithoutICPSRegosArrayResult
ItemSetIcpsRequest: TypeAlias = ItemSetICPS
ItemSetIcpsResponse: TypeAlias = BooleanRegosObjectResult
ItemSetLabeledMarkResponse: TypeAlias = BooleanRegosObjectResult


_MODEL_NAMES = ['GetWithoutICPSRequest', 'ImportItems', 'Int64ArrayRegosObjectResult', 'Item', 'ItemAdd', 'ItemAddCopy', 'ItemAddToCompound', 'ItemCodeCheckIn', 'ItemCodeCheckOut', 'ItemCodeCheckOutRegosObjectResult', 'ItemCodeGet', 'ItemCodeGetRegosObjectResult', 'ItemCompound', 'ItemCompoundGet', 'ItemCompoundRegosArrayResult', 'ItemCurrentQuantity', 'ItemCurrentQuantityGet', 'ItemCurrentQuantityRegosArrayResult', 'ItemDelete', 'ItemDeleteFromCompound', 'ItemDeleteMark', 'ItemEdit', 'ItemExt', 'ItemExtGet', 'ItemExtRegosOffsettedArrayResult', 'ItemGet', 'ItemGetQuantityIncome', 'ItemGetQuantityOutcome', 'ItemGetQuantityOutcomeRegosArrayResult', 'ItemGetQuantityPosIncome', 'ItemGetQuantityPosOutcome', 'ItemGetQuantityPosOutcomeRegosArrayResult', 'ItemImportData', 'ItemImportDataResponse', 'ItemImportDataResponseArrayRegosObjectResult', 'ItemMatchingRequest', 'ItemMatchingRequestData', 'ItemMatchingResponse', 'ItemMatchingResponseArrayRegosObjectResult', 'ItemOFDPackage', 'ItemOFDPackageRegosArrayResult', 'ItemOFDPackagesGet', 'ItemOprOrder', 'ItemOrder', 'ItemPreCost', 'ItemPreCostArrayRegosObjectResult', 'ItemPreCostGet', 'ItemQuantity', 'ItemRegosOffsettedArrayResult', 'ItemReplaceICPS', 'ItemSearch', 'ItemSetICPS', 'ItemShort', 'ItemShortRegosOffsettedArrayResult', 'ItemWithoutICPS', 'ItemWithoutICPSRegosArrayResult', 'ItemWithoutICPSShort', 'ItemWithoutICPSShortRegosOffsettedArrayResult']


__all__ = [
    'GetWithoutICPSRequest',
    'ImageSize',
    'ImportItems',
    'Int64ArrayRegosObjectResult',
    'Item',
    'ItemAdd',
    'ItemAddCopy',
    'ItemAddToCompound',
    'ItemCodeCheckIn',
    'ItemCodeCheckOut',
    'ItemCodeCheckOutRegosObjectResult',
    'ItemCodeGet',
    'ItemCodeGetRegosObjectResult',
    'ItemCompound',
    'ItemCompoundGet',
    'ItemCompoundRegosArrayResult',
    'ItemCurrentQuantity',
    'ItemCurrentQuantityGet',
    'ItemCurrentQuantityRegosArrayResult',
    'ItemDelete',
    'ItemDeleteFromCompound',
    'ItemDeleteMark',
    'ItemEdit',
    'ItemExt',
    'ItemExtGet',
    'ItemExtRegosOffsettedArrayResult',
    'ItemGet',
    'ItemGetQuantityIncome',
    'ItemGetQuantityOutcome',
    'ItemGetQuantityOutcomeRegosArrayResult',
    'ItemGetQuantityPosIncome',
    'ItemGetQuantityPosOutcome',
    'ItemGetQuantityPosOutcomeRegosArrayResult',
    'ItemImportComparationValue',
    'ItemImportData',
    'ItemImportDataResponse',
    'ItemImportDataResponseArrayRegosObjectResult',
    'ItemMatchingRequest',
    'ItemMatchingRequestData',
    'ItemMatchingResponse',
    'ItemMatchingResponseArrayRegosObjectResult',
    'ItemOFDPackage',
    'ItemOFDPackageRegosArrayResult',
    'ItemOFDPackagesGet',
    'ItemOprOrder',
    'ItemOprOrderColumn',
    'ItemOprOrderDirection',
    'ItemOrder',
    'ItemOrderColumn',
    'ItemOriginEnum',
    'ItemPreCost',
    'ItemPreCostArrayRegosObjectResult',
    'ItemPreCostGet',
    'ItemQuantity',
    'ItemRegosOffsettedArrayResult',
    'ItemReplaceICPS',
    'ItemSearch',
    'ItemSetICPS',
    'ItemShort',
    'ItemShortRegosOffsettedArrayResult',
    'ItemType',
    'ItemWithoutICPS',
    'ItemWithoutICPSRegosArrayResult',
    'ItemWithoutICPSShort',
    'ItemWithoutICPSShortRegosOffsettedArrayResult',
    'MatchingType',
    'ItemGetRequest',
    'ItemGetResponse',
    'ItemGetShortRequest',
    'ItemGetShortResponse',
    'ItemGetExtRequest',
    'ItemGetExtResponse',
    'ItemAddRequest',
    'ItemAddResponse',
    'ItemCopyRequest',
    'ItemCopyResponse',
    'ItemEditRequest',
    'ItemEditResponse',
    'ItemDeleteMarkRequest',
    'ItemDeleteMarkResponse',
    'ItemDeleteRequest',
    'ItemDeleteResponse',
    'ItemCheckCodeRequest',
    'ItemCheckCodeResponse',
    'ItemGetCodeRequest',
    'ItemGetCodeResponse',
    'ItemSearchRequest',
    'ItemSearchResponse',
    'ItemGetQuantityRequest',
    'ItemGetQuantityResponse',
    'ItemGetQuantityPosRequest',
    'ItemGetQuantityPosResponse',
    'ItemGetCurrentQuantityRequest',
    'ItemGetCurrentQuantityResponse',
    'ItemMatchRequest',
    'ItemMatchResponse',
    'ItemImportRequest',
    'ItemImportResponse',
    'ItemSetIcpsRequest',
    'ItemSetIcpsResponse',
    'ItemReplaceIcpsRequest',
    'ItemReplaceIcpsResponse',
    'ItemGetWithoutIcpsRequest',
    'ItemGetWithoutIcpsResponse',
    'ItemSetIcpsFromServerRequest',
    'ItemSetIcpsFromServerResponse',
    'ItemSetLabeledMarkResponse',
    'ItemFillIcpsByBarcodeRequest',
    'ItemFillIcpsByBarcodeResponse',
    'ItemGetPackagesByIcpsRequest',
    'ItemGetPackagesByIcpsResponse',
    'ItemGetCompoundRequest',
    'ItemGetCompoundResponse',
    'ItemAddToCompoundRequest',
    'ItemAddToCompoundResponse',
    'ItemDeleteFromCompoundRequest',
    'ItemDeleteFromCompoundResponse',
    'ItemGetExtImageSize',
    'ItemMatchingData',
    'ItemMatchingType'
]
