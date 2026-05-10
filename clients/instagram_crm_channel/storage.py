from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import setup_logger
from core.mariadb import mariadb_is_enabled, mariadb_ops


logger = setup_logger("instagram_crm_channel.storage")

_SCHEMA_LOCK = asyncio.Lock()
_SCHEMA_READY = False
_MIGRATIONS_DIR = Path(__file__).with_name("migrations")
_BUSINESS_MAP_TABLE = mariadb_ops.table_name("igc", "business", "map")


class BusinessMapConflictError(RuntimeError):
    def __init__(self, *, business_id: str, connected_integration_id: str) -> None:
        self.business_id = business_id
        self.connected_integration_id = connected_integration_id
        super().__init__("Instagram business account is already connected to another integration")


def instagram_mariadb_enabled() -> bool:
    return mariadb_is_enabled()


def _require_instagram_mariadb() -> None:
    if not instagram_mariadb_enabled():
        raise RuntimeError("MariaDB is required for instagram_crm_channel")


async def ensure_schema(*, force: bool = False) -> bool:
    global _SCHEMA_READY
    _require_instagram_mariadb()
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
            logger.info("Applied Instagram MariaDB migration: %s", migration_path.name)

        _SCHEMA_READY = True
        return True


async def upsert_business_map(
    *,
    connected_integration_id: str,
    business_id: str,
    username: Optional[str] = None,
    is_active: bool = True,
    allow_reassign: bool = False,
) -> bool:
    ci = str(connected_integration_id or "").strip()
    business = str(business_id or "").strip()
    if not ci or not business:
        return False

    try:
        await ensure_schema()
        async with mariadb_ops.transaction() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT `connected_integration_id`, `is_active`
                    FROM {_BUSINESS_MAP_TABLE}
                    WHERE `business_id` = %s
                    FOR UPDATE
                    """,
                    (business,),
                )
                row = await cursor.fetchone()
                if row:
                    existing_ci = str(row[0] or "").strip()
                    existing_active = str(row[1] or "").strip().lower() not in {"", "0", "false", "none"}
                    if existing_active and existing_ci and existing_ci != ci and not allow_reassign:
                        raise BusinessMapConflictError(
                            business_id=business,
                            connected_integration_id=existing_ci,
                        )

                await cursor.execute(
                    f"""
                    INSERT INTO {_BUSINESS_MAP_TABLE}
                        (`business_id`, `connected_integration_id`, `username`, `is_active`)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        `connected_integration_id` = VALUES(`connected_integration_id`),
                        `username` = VALUES(`username`),
                        `is_active` = VALUES(`is_active`),
                        `updated_at` = CURRENT_TIMESTAMP
                    """,
                    (business, ci, str(username or "").strip() or None, 1 if is_active else 0),
                )
    except BusinessMapConflictError:
        logger.warning(
            "Instagram business mapping conflict: ci=%s business_id=%s",
            ci,
            business,
        )
        raise
    except Exception:
        logger.exception(
            "Failed to write Instagram business mapping: ci=%s business_id=%s",
            ci,
            business,
        )
        raise
    return True


async def reassign_business_map(
    *,
    connected_integration_id: str,
    business_id: str,
    username: Optional[str] = None,
) -> Optional[str]:
    ci = str(connected_integration_id or "").strip()
    business = str(business_id or "").strip()
    if not ci or not business:
        return None

    previous_ci: Optional[str] = None
    try:
        await ensure_schema()
        async with mariadb_ops.transaction() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT `connected_integration_id`, `is_active`
                    FROM {_BUSINESS_MAP_TABLE}
                    WHERE `business_id` = %s
                    FOR UPDATE
                    """,
                    (business,),
                )
                row = await cursor.fetchone()
                if row:
                    existing_ci = str(row[0] or "").strip()
                    existing_active = str(row[1] or "").strip().lower() not in {"", "0", "false", "none"}
                    if existing_active and existing_ci and existing_ci != ci:
                        previous_ci = existing_ci

                await cursor.execute(
                    f"""
                    INSERT INTO {_BUSINESS_MAP_TABLE}
                        (`business_id`, `connected_integration_id`, `username`, `is_active`)
                    VALUES (%s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        `connected_integration_id` = VALUES(`connected_integration_id`),
                        `username` = VALUES(`username`),
                        `is_active` = 1,
                        `updated_at` = CURRENT_TIMESTAMP
                    """,
                    (business, ci, str(username or "").strip() or None),
                )
    except Exception:
        logger.exception(
            "Failed to reassign Instagram business mapping: ci=%s business_id=%s",
            ci,
            business,
        )
        raise
    return previous_ci


async def get_business_map(business_id: str) -> Optional[Dict[str, Any]]:
    business = str(business_id or "").strip()
    if not business:
        return None

    await ensure_schema()
    row = await mariadb_ops.fetchone_dict(
        f"""
        SELECT `business_id`, `connected_integration_id`, `username`, `is_active`, `updated_at`
        FROM {_BUSINESS_MAP_TABLE}
        WHERE `business_id` = %s
        LIMIT 1
        """,
        (business,),
    )
    if not row:
        return None
    return {
        "business_id": str(row.get("business_id") or "").strip(),
        "connected_integration_id": str(row.get("connected_integration_id") or "").strip(),
        "username": str(row.get("username") or "").strip(),
        "is_active": str(row.get("is_active") or "").strip().lower() not in {"", "0", "false", "none"},
        "updated_at": row.get("updated_at"),
    }


async def resolve_ci_by_business_id(business_id: str) -> Optional[str]:
    business = str(business_id or "").strip()
    if not business:
        return None

    row = await get_business_map(business)
    if not row or not row.get("is_active"):
        return None
    return str(row.get("connected_integration_id") or "").strip() or None


async def mark_business_map_inactive(
    *,
    connected_integration_id: str,
    business_id: Optional[str] = None,
) -> bool:
    ci = str(connected_integration_id or "").strip()
    business = str(business_id or "").strip()
    if not ci:
        return False

    try:
        await ensure_schema()
        if business:
            await mariadb_ops.execute(
                f"""
                UPDATE {_BUSINESS_MAP_TABLE}
                SET `is_active` = 0, `updated_at` = CURRENT_TIMESTAMP
                WHERE `connected_integration_id` = %s AND `business_id` = %s
                """,
                (ci, business),
            )
        else:
            await mariadb_ops.execute(
                f"""
                UPDATE {_BUSINESS_MAP_TABLE}
                SET `is_active` = 0, `updated_at` = CURRENT_TIMESTAMP
                WHERE `connected_integration_id` = %s
                """,
                (ci,),
            )
    except Exception:
        logger.exception(
            "Failed to mark Instagram business mapping inactive: ci=%s business_id=%s",
            ci,
            business or "",
        )
        raise
    return True
