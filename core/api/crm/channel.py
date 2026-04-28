"""CRM channel service."""

from schemas.api.crm.channel import (
    ChannelAddRequest,
    ChannelAddResponse,
    ChannelDeleteRequest,
    ChannelDeleteResponse,
    ChannelEditRequest,
    ChannelEditResponse,
    ChannelGetRequest,
    ChannelGetResponse,
    ChannelSetIntervalsRequest,
    ChannelSetIntervalsResponse,
    ChannelSetOperatorsRequest,
    ChannelSetOperatorsResponse,
)


class ChannelService:
    PATH_GET = "Channel/Get"
    PATH_ADD = "Channel/Add"
    PATH_EDIT = "Channel/Edit"
    PATH_DELETE = "Channel/Delete"
    PATH_SET_OPERATORS = "Channel/SetOperators"
    PATH_SET_INTERVALS = "Channel/SetIntervals"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ChannelGetRequest) -> ChannelGetResponse:
        return await self.api.call(self.PATH_GET, req, ChannelGetResponse)

    async def add(self, req: ChannelAddRequest) -> ChannelAddResponse:
        return await self.api.call(self.PATH_ADD, req, ChannelAddResponse)

    async def edit(self, req: ChannelEditRequest) -> ChannelEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ChannelEditResponse)

    async def delete(self, req: ChannelDeleteRequest) -> ChannelDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, ChannelDeleteResponse)

    async def set_operators(
        self, req: ChannelSetOperatorsRequest
    ) -> ChannelSetOperatorsResponse:
        return await self.api.call(
            self.PATH_SET_OPERATORS,
            req,
            ChannelSetOperatorsResponse,
        )

    async def set_intervals(
        self, req: ChannelSetIntervalsRequest
    ) -> ChannelSetIntervalsResponse:
        return await self.api.call(
            self.PATH_SET_INTERVALS,
            req,
            ChannelSetIntervalsResponse,
        )
