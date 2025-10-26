# core/regos_oauth.py
from __future__ import annotations

import asyncio
import json
import hashlib
from typing import Optional

import httpx

from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("regos_oauth")

try:
    from core.redis import redis_client as shared_redis  
except Exception:
    shared_redis = None


class RedisClientCredentialsProvider:
    """
    OAuth2 Client Credentials c кэшированием access_token в Redis.
    Минимальный протокол: grant_type=client_credentials, client_id, client_secret.
    """

    def __init__(
        self,
        token_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        http_timeout: int = 30,
        redis_client=None,  # redis.asyncio.Redis | None
    ):
        # Собираем URL эндпоинта токена как <oauth_endpoint>/oauth/token
        self.token_url = token_url or f"{settings.oauth_endpoint.rstrip('/')}/oauth/token"
        self.client_id = client_id or settings.oauth_client_id
        self.client_secret = client_secret or settings.oauth_secret
        self.http_timeout = http_timeout

        self._redis = redis_client or shared_redis
        if not self._redis and settings.redis_enabled:
            # fallback: создадим клиент, если общий не подключён
            import redis.asyncio as redis
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password or None,
                decode_responses=True,
            )

        # Ключи в Redis: из token_url и client_id
        digest = hashlib.sha1(f"{self.token_url}|{self.client_id}".encode()).hexdigest()
        self._token_key = f"oauth:cc:{settings.environment}:{digest}:token"
        self._lock_key = f"oauth:cc:{settings.environment}:{digest}:lock"

        # Процессный лок на случай отсутствия Redis
        self._process_lock = asyncio.Lock()

        self._http = httpx.AsyncClient(timeout=self.http_timeout)

    async def _get_cached_token(self) -> Optional[str]:
        if not self._redis:
            return None
        return await self._redis.get(self._token_key)

    async def _set_cached_token(self, token: str, expires_in: int):
        if not self._redis:
            return
        # небольшой запас TTL: 10% или 60с (что меньше)
        skew = min(60, max(0, int(expires_in * 0.1)))
        ttl = max(1, expires_in - skew)
        await self._redis.set(self._token_key, token, ex=ttl)

    async def _acquire_lock(self, timeout: int = 30, wait: int = 10):
        """
        Берём Redis-лок; если Redis недоступен — используем процессный лок.
        """
        if not self._redis:
            await self._process_lock.acquire()
            return ("process", None)

        lock = self._redis.lock(self._lock_key, timeout=timeout, blocking_timeout=wait)
        ok = await lock.acquire()
        if not ok:
            raise TimeoutError("Не удалось получить Redis-лок для получения токена")
        return ("redis", lock)

    async def _release_lock(self, token):
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

    async def _fetch_token(self) -> tuple[str, int]:
        """
        Минимальный client_credentials:
        POST x-www-form-urlencoded: grant_type, client_id, client_secret
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        logger.info(f"OAuth CC: POST {self.token_url}")
        resp = await self._http.post(self.token_url, data=data, headers=headers)
        resp.raise_for_status()

        payload = resp.json()
        access_token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not access_token:
            raise ValueError(f"В ответе нет access_token: {json.dumps(payload, ensure_ascii=False)[:300]}")
        return access_token, expires_in

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        1) читаем из Redis
        2) если пусто/force — под локом берём новый у провайдера и кладём в Redis
        """
        if not force_refresh:
            cached = await self._get_cached_token()
            if cached:
                return cached

        lock_token = await self._acquire_lock()
        try:
            if not force_refresh:
                cached = await self._get_cached_token()
                if cached:
                    return cached

            access_token, expires_in = await self._fetch_token()
            await self._set_cached_token(access_token, expires_in)
            return access_token
        finally:
            await self._release_lock(lock_token)

    async def aclose(self):
        await self._http.aclose()
