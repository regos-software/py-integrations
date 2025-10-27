# core/api/regos_oauth.py
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Optional

import httpx

from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("regos_oauth")


try:
    # ваш общий Redis-клиент, если есть
    from core.redis import redis_client as SHARED_REDIS  # type: ignore
except Exception:
    SHARED_REDIS = None


class RegosOAuthProvider:
    """
    OAuth2 Client Credentials для REGOS c кэшированием access_token:
    - In-memory кэш (всегда)
    - Redis кэш (если включён)
    - Защита от догоняющего запроса через Redis-лок или процессный лок.

    Протокол получения токена минимальный:
    POST x-www-form-urlencoded: grant_type, client_id, client_secret
    """

    def __init__(
        self,
        *,
        token_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        http_timeout: int = 30,
        redis_client=None,
    ) -> None:
        # Где брать токен
        self._token_url = token_url or f"{settings.oauth_endpoint.rstrip('/')}/oauth/token"
        self._client_id = client_id or settings.oauth_client_id
        self._client_secret = client_secret or settings.oauth_secret

        # HTTP-клиент: реюзаем внешний, чтобы не плодить соединения
        self._http = http_client or httpx.AsyncClient(timeout=http_timeout)
        self._owns_http = http_client is None

        # Redis (опционально)
        self._redis = redis_client or SHARED_REDIS
        if not self._redis and settings.redis_enabled:
            import redis.asyncio as redis  # локальный импорт
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password or None,
                decode_responses=True,
            )

        # Ключи в Redis зависят от token_url + client_id
        digest = hashlib.sha1(f"{self._token_url}|{self._client_id}".encode()).hexdigest()
        self._redis_key_token = f"oauth:cc:{settings.environment}:{digest}:token"
        self._redis_key_lock = f"oauth:cc:{settings.environment}:{digest}:lock"

        # Лок на процесс на случай отсутствия Redis
        self._process_lock = asyncio.Lock()

        # In-memory кэш
        self._mem_token: Optional[str] = None
        self._mem_expire_at: float = 0.0

    # ---------- in-memory кэш ----------

    def _mem_get(self) -> Optional[str]:
        if self._mem_token and time.time() < self._mem_expire_at:
            return self._mem_token
        return None

    def _mem_set(self, token: str, expires_in: int) -> None:
        # небольшой запас по времени
        skew = min(60, max(0, int(expires_in * 0.1)))
        self._mem_token = token
        self._mem_expire_at = time.time() + max(1, expires_in - skew)

    # ---------- redis кэш ----------

    async def _redis_get(self) -> Optional[str]:
        if not self._redis:
            return None
        try:
            return await self._redis.get(self._redis_key_token)
        except Exception:
            return None

    async def _redis_set(self, token: str, expires_in: int) -> None:
        if not self._redis:
            return
        skew = min(60, max(0, int(expires_in * 0.1)))
        ttl = max(1, expires_in - skew)
        try:
            await self._redis.set(self._redis_key_token, token, ex=ttl)
        except Exception:
            pass

    # ---------- лок ----------

    async def _acquire_lock(self):
        if not self._redis:
            await self._process_lock.acquire()
            return ("process", None)

        lock = self._redis.lock(self._redis_key_lock, timeout=30, blocking_timeout=10)
        ok = await lock.acquire()
        if not ok:
            raise TimeoutError("Не удалось получить блокировку при запросе токена")
        return ("redis", lock)

    async def _release_lock(self, token) -> None:
        kind, lock = token
        if kind == "redis" and lock:
            try:
                await lock.release()
            except Exception:
                pass
        elif kind == "process":
            try:
                self._process_lock.release()
            except Exception:
                pass

    # ---------- сетевой запрос токена ----------

    async def _fetch_token(self) -> tuple[str, int]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        form = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        logger.info("OAuth CC: POST %s", self._token_url)
        resp = await self._http.post(self._token_url, headers=headers, data=form)
        resp.raise_for_status()

        payload = resp.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not token:
            raise ValueError(f"В ответе нет access_token: {json.dumps(payload, ensure_ascii=False)[:300]}")
        return token, expires_in

    # ---------- публичный API ----------

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        # 1) память
        if not force_refresh:
            t = self._mem_get()
            if t:
                return t

        # 2) redis
        if not force_refresh:
            t = await self._redis_get()
            if t:
                # мы не знаем точный остаток TTL, но сохраним в память на короткий срок
                self._mem_set(t, expires_in=300)
                return t

        # 3) сетевой фетч под локом
        lk = await self._acquire_lock()
        try:
            if not force_refresh:
                t = await self._redis_get()
                if t:
                    self._mem_set(t, expires_in=300)
                    return t

            token, expires_in = await self._fetch_token()
            self._mem_set(token, expires_in)
            await self._redis_set(token, expires_in)
            return token
        finally:
            await self._release_lock(lk)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()
