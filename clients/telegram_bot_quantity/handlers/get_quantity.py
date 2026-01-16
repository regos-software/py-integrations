from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Dict, List, Optional

from aiogram import types
from aiogram.types import BufferedInputFile

from core.api.regos_api import RegosAPI
from schemas.api.references.item import ItemExt, ItemGetExtRequest


MAX_PAGES_PER_STOCK = 10
DEFAULT_ITEM_GETEXT_PAGE_LIMIT = 10_000


def _safe_decimal(v) -> Decimal:
    try:
        if v is None:
            return Decimal(0)
        return Decimal(str(v))
    except Exception:
        return Decimal(0)


def _should_include(item_ext: ItemExt) -> bool:
    min_qty = item_ext.item.min_quantity
    if min_qty is None:
        return False

    try:
        min_qty_dec = Decimal(int(min_qty))
    except Exception:
        return False

    qty = _safe_decimal(
        getattr(item_ext.quantity, "common", None) if item_ext.quantity else None
    )
    return qty < min_qty_dec


def _item_to_row(stock_id: int, item_ext: ItemExt) -> List[object]:
    qty = _safe_decimal(
        getattr(item_ext.quantity, "common", None) if item_ext.quantity else None
    )
    return [
        stock_id,
        item_ext.item.id,
        item_ext.item.code,
        item_ext.item.name,
        item_ext.item.articul,
        float(qty),
        item_ext.item.min_quantity,
    ]


async def _fetch_all_items_for_stock(
    *, connected_integration_id: str, stock_id: int, search: Optional[str] = None
) -> List[ItemExt]:
    items: List[ItemExt] = []
    offset: Optional[int] = None

    async with RegosAPI(connected_integration_id=connected_integration_id) as api:
        for _ in range(MAX_PAGES_PER_STOCK):
            req = ItemGetExtRequest(
                stock_id=stock_id,
                search=search,
                offset=offset,
                limit=DEFAULT_ITEM_GETEXT_PAGE_LIMIT,
            )
            resp = await api.references.item.get_ext(req)

            if not getattr(resp, "ok", False):
                raise RuntimeError("REGOS API returned ok=false for Item/GetExt")

            page_items = resp.result or []
            items.extend(page_items)

            next_offset = getattr(resp, "next_offset", None)
            if next_offset is None or next_offset == 0:
                break
            if offset == next_offset:
                break
            offset = next_offset

    return items


def _build_excel_bytes(*, stock_id: int, rows: List[List[object]]) -> bytes:
    # openpyxl is intentionally imported here to keep import errors localized
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = f"stock_{stock_id}"

    headers = [
        "stock_id",
        "item_id",
        "code",
        "name",
        "articul",
        "quantity",
        "min_quantity",
    ]

    ws.append(headers)
    for row in rows:
        ws.append(row)

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


async def handle_get_quantity(
    *,
    integration,
    message: types.Message,
    stock_ids: List[int],
    search: Optional[str] = None,
) -> None:
    """Fetch items via Item/GetExt, filter < min_quantity, send Excel to the requesting user."""

    if not integration.connected_integration_id:
        await message.answer("Не задан connected_integration_id")
        return

    if not stock_ids:
        await message.answer("Не настроены STOCK_IDS для выгрузки.")
        return

    await message.answer("Формируем отчет по минимальным остаткам…")

    for stock_id in stock_ids:
        all_items = await _fetch_all_items_for_stock(
            connected_integration_id=str(integration.connected_integration_id),
            stock_id=int(stock_id),
            search=search,
        )

        less_than_min_qty_records: List[List[object]] = []
        for item_ext in all_items:
            if _should_include(item_ext):
                less_than_min_qty_records.append(_item_to_row(int(stock_id), item_ext))

        xlsx_bytes = _build_excel_bytes(
            stock_id=int(stock_id),
            rows=less_than_min_qty_records,
        )

        filename = f"min_quantity_report_stock_{int(stock_id)}.xlsx"
        await message.answer_document(
            document=BufferedInputFile(xlsx_bytes, filename=filename),
            caption=f"Отчет по товарам с остатком ниже минимального (склад {int(stock_id)})",
        )
