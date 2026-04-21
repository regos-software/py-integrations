"""Field service."""

from schemas.api.references.field import (
    FieldAddRequest,
    FieldAddResponse,
    FieldGetRequest,
    FieldGetResponse,
)


class FieldService:
    PATH_GET = "Field/Get"
    PATH_ADD = "Field/Add"

    def __init__(self, api):
        self.api = api

    async def get(self, req: FieldGetRequest) -> FieldGetResponse:
        return await self.api.call(self.PATH_GET, req, FieldGetResponse)

    async def add(self, req: FieldAddRequest) -> FieldAddResponse:
        return await self.api.call(self.PATH_ADD, req, FieldAddResponse)
