import asyncio
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional, Sequence, Tuple

from config.settings import settings


_mariadb_pool = None
_POOL_LOCK = asyncio.Lock()
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class MariaDBResult:
    rowcount: int
    lastrowid: Optional[int]


def mariadb_is_enabled() -> bool:
    return bool(settings.mariadb_enabled)


def _require_enabled() -> None:
    if not mariadb_is_enabled():
        raise RuntimeError("MariaDB is not enabled")


def mariadb_quote_identifier(identifier: str) -> str:
    value = str(identifier or "").strip()
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Unsafe MariaDB identifier: {identifier!r}")
    return f"`{value}`"


def mariadb_table_name(*parts: Any) -> str:
    tokens = [str(part or "").strip("_") for part in parts if str(part or "").strip("_")]
    if not tokens:
        raise ValueError("MariaDB table name parts are required")
    return mariadb_quote_identifier("_".join(tokens))


def _normalize_params(params: Optional[Any]) -> Any:
    if params is None:
        return ()
    return params


async def _commit_if_needed(connection: Any) -> None:
    if not bool(connection.get_autocommit()):
        await connection.commit()


async def init_mariadb_pool():
    global _mariadb_pool
    if _mariadb_pool is not None:
        return _mariadb_pool
    _require_enabled()
    async with _POOL_LOCK:
        if _mariadb_pool is not None:
            return _mariadb_pool
        import asyncmy

        min_size = max(int(settings.mariadb_pool_min_size or 1), 1)
        max_size = max(int(settings.mariadb_pool_max_size or min_size), min_size)
        _mariadb_pool = await asyncmy.create_pool(
            host=settings.mariadb_host,
            port=int(settings.mariadb_port or 3306),
            user=settings.mariadb_user,
            password=settings.mariadb_password or None,
            db=settings.mariadb_database,
            charset="utf8mb4",
            autocommit=True,
            minsize=min_size,
            maxsize=max_size,
            connect_timeout=max(int(settings.mariadb_connect_timeout or 10), 1),
        )
        return _mariadb_pool


async def close_mariadb_pool() -> None:
    global _mariadb_pool
    pool = _mariadb_pool
    _mariadb_pool = None
    if pool is None:
        return
    pool.close()
    await pool.wait_closed()


async def _require_pool():
    if _mariadb_pool is None:
        return await init_mariadb_pool()
    return _mariadb_pool


@asynccontextmanager
async def mariadb_connection() -> AsyncIterator[Any]:
    pool = await _require_pool()
    async with pool.acquire() as connection:
        yield connection


@asynccontextmanager
async def mariadb_transaction() -> AsyncIterator[Any]:
    async with mariadb_connection() as connection:
        previous_autocommit = bool(connection.get_autocommit())
        if previous_autocommit:
            await connection.autocommit(False)
        try:
            yield connection
            await connection.commit()
        except Exception:
            await connection.rollback()
            raise
        finally:
            if previous_autocommit:
                await connection.autocommit(True)


async def mariadb_execute(sql: str, params: Optional[Any] = None) -> MariaDBResult:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, _normalize_params(params))
            result = MariaDBResult(
                rowcount=int(cursor.rowcount or 0),
                lastrowid=getattr(cursor, "lastrowid", None),
            )
            await _commit_if_needed(connection)
            return result


async def mariadb_executemany(sql: str, params: Iterable[Any]) -> MariaDBResult:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.executemany(sql, list(params))
            result = MariaDBResult(
                rowcount=int(cursor.rowcount or 0),
                lastrowid=getattr(cursor, "lastrowid", None),
            )
            await _commit_if_needed(connection)
            return result


async def mariadb_fetchone(sql: str, params: Optional[Any] = None) -> Optional[Tuple[Any, ...]]:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, _normalize_params(params))
            return await cursor.fetchone()


async def mariadb_fetchall(sql: str, params: Optional[Any] = None) -> List[Tuple[Any, ...]]:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, _normalize_params(params))
            rows = await cursor.fetchall()
            return list(rows or [])


async def mariadb_fetchone_dict(sql: str, params: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, _normalize_params(params))
            row = await cursor.fetchone()
            if row is None:
                return None
            columns = [column[0] for column in (cursor.description or [])]
            return dict(zip(columns, row))


async def mariadb_fetchall_dict(sql: str, params: Optional[Any] = None) -> List[Dict[str, Any]]:
    async with mariadb_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, _normalize_params(params))
            rows = await cursor.fetchall()
            columns = [column[0] for column in (cursor.description or [])]
            return [dict(zip(columns, row)) for row in (rows or [])]


async def mariadb_ping() -> bool:
    if not mariadb_is_enabled():
        return False
    try:
        async with mariadb_connection() as connection:
            await connection.ping(reconnect=True)
        return True
    except Exception:
        return False


class MariaDBOps:
    def __bool__(self) -> bool:
        return mariadb_is_enabled()

    async def init_pool(self):
        return await init_mariadb_pool()

    async def close_pool(self) -> None:
        await close_mariadb_pool()

    def quote_identifier(self, identifier: str) -> str:
        return mariadb_quote_identifier(identifier)

    def table_name(self, *parts: Any) -> str:
        return mariadb_table_name(*parts)

    def connection(self):
        return mariadb_connection()

    def transaction(self):
        return mariadb_transaction()

    async def execute(self, sql: str, params: Optional[Any] = None) -> MariaDBResult:
        return await mariadb_execute(sql, params)

    async def executemany(self, sql: str, params: Iterable[Any]) -> MariaDBResult:
        return await mariadb_executemany(sql, params)

    async def fetchone(self, sql: str, params: Optional[Any] = None) -> Optional[Tuple[Any, ...]]:
        return await mariadb_fetchone(sql, params)

    async def fetchall(self, sql: str, params: Optional[Any] = None) -> List[Tuple[Any, ...]]:
        return await mariadb_fetchall(sql, params)

    async def fetchone_dict(self, sql: str, params: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        return await mariadb_fetchone_dict(sql, params)

    async def fetchall_dict(self, sql: str, params: Optional[Any] = None) -> List[Dict[str, Any]]:
        return await mariadb_fetchall_dict(sql, params)

    async def ping(self) -> bool:
        return await mariadb_ping()


mariadb_ops = MariaDBOps()
