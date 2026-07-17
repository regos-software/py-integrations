from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from core.mariadb import mariadb_is_enabled, mariadb_ops


logger = setup_logger("meta_leadgen_crm_channel.storage")

_SCHEMA_LOCK = asyncio.Lock()
_SCHEMA_READY = False
_MIGRATIONS_DIR = Path(__file__).with_name("migrations")
_PAGE_MAP_TABLE = mariadb_ops.table_name("mlg", "page", "map")


class PageMapConflictError(RuntimeError):
    def __init__(self, *, page_id: str, connected_integration_id: str) -> None:
        self.page_id = page_id
        self.connected_integration_id = connected_integration_id
        super().__init__("Meta page is already connected to another integration")


def meta_leadgen_mariadb_enabled() -> bool:
    return mariadb_is_enabled()


def _require_meta_leadgen_mariadb() -> None:
    if not meta_leadgen_mariadb_enabled():
        raise RuntimeError("MariaDB is required for meta_leadgen_crm_channel")


def _page_map_from_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "page_id": str(row.get("page_id") or "").strip(),
        "connected_integration_id": str(row.get("connected_integration_id") or "").strip(),
        "is_active": str(row.get("is_active") or "").strip().lower()
        not in {"", "0", "false", "none"},
        "updated_at": row.get("updated_at"),
    }


async def ensure_schema(*, force: bool = False) -> bool:
    global _SCHEMA_READY
    _require_meta_leadgen_mariadb()
    if _SCHEMA_READY and not force:
        return True

    async with _SCHEMA_LOCK:
        if _SCHEMA_READY and not force:
            return True

        for migration_path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            sql = migration_path.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            await mariadb_ops.execute(sql)
            logger.info("Applied Meta Leadgen MariaDB migration: %s", migration_path.name)

        _SCHEMA_READY = True
        return True


async def upsert_page_map(
    *,
    connected_integration_id: str,
    page_id: str,
    is_active: bool = True,
    allow_reassign: bool = False,
) -> bool:
    ci = str(connected_integration_id or "").strip()
    page = str(page_id or "").strip()
    if not ci or not page:
        return False

    try:
        await ensure_schema()
        async with mariadb_ops.transaction() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT `connected_integration_id`, `is_active`
                    FROM {_PAGE_MAP_TABLE}
                    WHERE `page_id` = %s
                    FOR UPDATE
                    """,
                    (page,),
                )
                row = await cursor.fetchone()
                if row:
                    existing_ci = str(row[0] or "").strip()
                    existing_active = str(row[1] or "").strip().lower() not in {"", "0", "false", "none"}
                    if existing_active and existing_ci and existing_ci != ci and not allow_reassign:
                        raise PageMapConflictError(
                            page_id=page,
                            connected_integration_id=existing_ci,
                        )

                if is_active:
                    await cursor.execute(
                        f"""
                        UPDATE {_PAGE_MAP_TABLE}
                        SET `is_active` = 0,
                            `updated_at` = CURRENT_TIMESTAMP
                        WHERE `connected_integration_id` = %s AND `page_id` <> %s
                        """,
                        (ci, page),
                    )

                await cursor.execute(
                    f"""
                    INSERT INTO {_PAGE_MAP_TABLE}
                        (`page_id`, `connected_integration_id`, `is_active`)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        `connected_integration_id` = VALUES(`connected_integration_id`),
                        `is_active` = VALUES(`is_active`),
                        `updated_at` = CURRENT_TIMESTAMP
                    """,
                    (
                        page,
                        ci,
                        1 if is_active else 0,
                    ),
                )
    except PageMapConflictError:
        logger.warning(
            "Meta Leadgen page mapping conflict: ci=%s page_id=%s",
            ci,
            page,
        )
        raise
    except Exception:
        logger.exception(
            "Failed to write Meta Leadgen page mapping: ci=%s page_id=%s",
            ci,
            page,
        )
        raise
    return True


async def reassign_page_map(
    *,
    connected_integration_id: str,
    page_id: str,
) -> Optional[str]:
    ci = str(connected_integration_id or "").strip()
    page = str(page_id or "").strip()
    if not ci or not page:
        return None

    previous_ci: Optional[str] = None
    try:
        await ensure_schema()
        async with mariadb_ops.transaction() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT `connected_integration_id`, `is_active`
                    FROM {_PAGE_MAP_TABLE}
                    WHERE `page_id` = %s
                    FOR UPDATE
                    """,
                    (page,),
                )
                row = await cursor.fetchone()
                if row:
                    existing_ci = str(row[0] or "").strip()
                    existing_active = str(row[1] or "").strip().lower() not in {"", "0", "false", "none"}
                    if existing_active and existing_ci and existing_ci != ci:
                        previous_ci = existing_ci

                await cursor.execute(
                    f"""
                    UPDATE {_PAGE_MAP_TABLE}
                    SET `is_active` = 0,
                        `updated_at` = CURRENT_TIMESTAMP
                    WHERE `connected_integration_id` = %s AND `page_id` <> %s
                    """,
                    (ci, page),
                )

                await cursor.execute(
                    f"""
                    INSERT INTO {_PAGE_MAP_TABLE}
                        (`page_id`, `connected_integration_id`, `is_active`)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        `connected_integration_id` = VALUES(`connected_integration_id`),
                        `is_active` = 1,
                        `updated_at` = CURRENT_TIMESTAMP
                    """,
                    (
                        page,
                        ci,
                    ),
                )
    except Exception:
        logger.exception(
            "Failed to reassign Meta Leadgen page mapping: ci=%s page_id=%s",
            ci,
            page,
        )
        raise
    return previous_ci


async def get_page_map(page_id: str) -> Optional[Dict[str, Any]]:
    page = str(page_id or "").strip()
    if not page:
        return None

    await ensure_schema()
    row = await mariadb_ops.fetchone_dict(
        f"""
        SELECT `page_id`, `connected_integration_id`, `is_active`, `updated_at`
        FROM {_PAGE_MAP_TABLE}
        WHERE `page_id` = %s
        LIMIT 1
        """,
        (page,),
    )
    return _page_map_from_row(row)


async def resolve_ci_by_page_id(page_id: str) -> Optional[str]:
    page = str(page_id or "").strip()
    if not page:
        return None

    row = await get_page_map(page)
    if not row or not row.get("is_active"):
        return None
    return str(row.get("connected_integration_id") or "").strip() or None


async def active_connected_integration_ids() -> List[str]:
    await ensure_schema()
    rows = await mariadb_ops.fetchall_dict(
        f"""
        SELECT DISTINCT `connected_integration_id`
        FROM {_PAGE_MAP_TABLE}
        WHERE `is_active` = 1
        """
    )
    return sorted(
        str(row.get("connected_integration_id") or "").strip()
        for row in rows
        if str(row.get("connected_integration_id") or "").strip()
    )


async def mark_page_map_inactive(
    *,
    connected_integration_id: str,
    page_id: Optional[str] = None,
) -> bool:
    ci = str(connected_integration_id or "").strip()
    page = str(page_id or "").strip()
    if not ci:
        return False

    try:
        await ensure_schema()
        if page:
            await mariadb_ops.execute(
                f"""
                UPDATE {_PAGE_MAP_TABLE}
                SET `is_active` = 0,
                    `updated_at` = CURRENT_TIMESTAMP
                WHERE `connected_integration_id` = %s AND `page_id` = %s
                """,
                (ci, page),
            )
        else:
            await mariadb_ops.execute(
                f"""
                UPDATE {_PAGE_MAP_TABLE}
                SET `is_active` = 0,
                    `updated_at` = CURRENT_TIMESTAMP
                WHERE `connected_integration_id` = %s
                """,
                (ci,),
            )
    except Exception:
        logger.exception(
            "Failed to mark Meta Leadgen page mapping inactive: ci=%s page_id=%s",
            ci,
            page or "",
        )
        raise
    return True
