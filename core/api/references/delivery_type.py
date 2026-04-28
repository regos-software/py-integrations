"""DeliveryType service."""

from schemas.api.references.delivery_type import (
    DeliveryTypeGetRequest,
    DeliveryTypeGetResponse,
)


class DeliveryTypeService:
    PATH_GET = "DeliveryType/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: DeliveryTypeGetRequest) -> DeliveryTypeGetResponse:
        return await self.api.call(self.PATH_GET, req, DeliveryTypeGetResponse)
