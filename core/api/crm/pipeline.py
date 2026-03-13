"""CRM pipeline service."""

from schemas.api.crm.pipeline import PipelineGetRequest, PipelineGetResponse


class PipelineService:
    PATH_GET = "Pipeline/Get"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PipelineGetRequest) -> PipelineGetResponse:
        return await self.api.call(self.PATH_GET, req, PipelineGetResponse)
