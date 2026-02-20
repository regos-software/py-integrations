from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import List, Optional

from aiogram import types
from aiogram.types import BufferedInputFile

from core.api.regos_api import RegosAPI
from schemas.api.references.item import ItemExt, ItemGetExtRequest
from schemas.api.references.stock import StockGetRequest


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
        min_qty_dec = Decimal(str(min_qty))
    except Exception:
        return False

    qty = _safe_decimal(
        getattr(item_ext.quantity, "common", None) if item_ext.quantity else None
    )
    return qty < min_qty_dec


def _item_to_row(item_ext: ItemExt) -> List[object]:
    qty = _safe_decimal(
        getattr(item_ext.quantity, "common", None) if item_ext.quantity else None
    )
    return [
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
            if not next_offset:
                break
            offset = next_offset

    return items


async def _get_stock_name(
    *, connected_integration_id: str, stock_id: int
) -> str:
    async with RegosAPI(connected_integration_id=connected_integration_id) as api:
        resp = await api.references.stock.get(
            StockGetRequest(ids=[stock_id], limit=1)
        )

        if not getattr(resp, "ok", False):
            return f"stock_{stock_id}"

        stocks = resp.result or []
        if not stocks:
            return f"stock_{stock_id}"

        return stocks[0].name


def _safe_filename(name: str) -> str:
    return (
        name.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )


def _build_excel_bytes(*, stock_name: str, rows: List[List[object]]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = stock_name[:31]  # лимит Excel

    headers = [
        "Код товара",
        "Наименование",
        "Артикул",
        "Остаток",
        "Минимальный остаток",
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
    if not integration.connected_integration_id:
        await message.answer("Не задан connected_integration_id")
        return

    if not stock_ids:
        await message.answer("Не настроены STOCK_IDS для выгрузки.")
        return

    await message.answer("Формируем отчет по минимальным остаткам…")

    for stock_id in stock_ids:
        stock_name = await _get_stock_name(
            connected_integration_id=str(integration.connected_integration_id),
            stock_id=int(stock_id),
        )

        all_items = await _fetch_all_items_for_stock(
            connected_integration_id=str(integration.connected_integration_id),
            stock_id=int(stock_id),
            search=search,
        )

        rows: List[List[object]] = [
            _item_to_row(item)
            for item in all_items
            if _should_include(item)
        ]

        if not rows:
            await message.answer(
                f"На складе {stock_name} нет товаров ниже минимального остатка."
            )
            continue

        xlsx_bytes = _build_excel_bytes(
            stock_name=stock_name,
            rows=rows,
        )

        filename = f"Минимальные_остатки_{_safe_filename(stock_name)}.xlsx"

        await message.answer_document(
            document=BufferedInputFile(xlsx_bytes, filename=filename),
            caption=f"Отчет по товарам с остатком ниже минимального\nСклад: {stock_name}",
        )
