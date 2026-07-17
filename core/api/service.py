"""Shared base service for REGOS API wrappers."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RegosAPIService:
    REQUEST_MODELS: dict[str, type[BaseModel]] = {}

    def __init__(self, api):
        self.api = api

    @classmethod
    def _payload(cls, data: Any) -> Any:
        if isinstance(data, BaseModel):
            return data.model_dump(mode='json', exclude_none=True, by_alias=True)
        if isinstance(data, list):
            return [cls._payload(item) for item in data]
        if isinstance(data, dict):
            return {key: cls._payload(value) for key, value in data.items()}
        return data

    async def _call(self, path: str, body: Any, response_model):
        return await self.api.call(path, self._payload(body), response_model)

    def _request_model(self, method_name: str):
        model = self.REQUEST_MODELS.get(method_name)
        if model is None:
            raise AttributeError(f'Request model is not registered for {method_name!r}')
        return model

    async def get_by_id(self, id_: int):
        req_model = self._request_model('get')
        response = await self.get(req_model(ids=[id_], limit=1))
        result = getattr(response, 'result', None) or []
        return result[0] if result else None

    async def get_short_by_id(self, id_: int):
        req_model = self._request_model('get_short')
        response = await self.get_short(req_model(ids=[id_], limit=1))
        result = getattr(response, 'result', None) or []
        return result[0] if result else None


__all__ = ['RegosAPIService']
