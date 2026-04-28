"""CRM pipeline service."""

from schemas.api.crm.pipeline import (
    PipelineAddRequest,
    PipelineAddResponse,
    PipelineDeleteRequest,
    PipelineDeleteResponse,
    PipelineEditRequest,
    PipelineEditResponse,
    PipelineGetRequest,
    PipelineGetResponse,
    PipelineSetAccessRequest,
    PipelineSetAccessResponse,
    PipelineSetStagesRequest,
    PipelineSetStagesResponse,
)


class PipelineService:
    PATH_GET = "Pipeline/Get"
    PATH_ADD = "Pipeline/Add"
    PATH_EDIT = "Pipeline/Edit"
    PATH_DELETE = "Pipeline/Delete"
    PATH_SET_ACCESS = "Pipeline/SetAccess"
    PATH_SET_STAGES = "Pipeline/SetStages"

    def __init__(self, api):
        self.api = api

    async def get(self, req: PipelineGetRequest) -> PipelineGetResponse:
        return await self.api.call(self.PATH_GET, req, PipelineGetResponse)

    async def add(self, req: PipelineAddRequest) -> PipelineAddResponse:
        return await self.api.call(self.PATH_ADD, req, PipelineAddResponse)

    async def edit(self, req: PipelineEditRequest) -> PipelineEditResponse:
        return await self.api.call(self.PATH_EDIT, req, PipelineEditResponse)

    async def delete(self, req: PipelineDeleteRequest) -> PipelineDeleteResponse:
        return await self.api.call(self.PATH_DELETE, req, PipelineDeleteResponse)

    async def set_access(self, req: PipelineSetAccessRequest) -> PipelineSetAccessResponse:
        return await self.api.call(self.PATH_SET_ACCESS, req, PipelineSetAccessResponse)

    async def set_stages(self, req: PipelineSetStagesRequest) -> PipelineSetStagesResponse:
        return await self.api.call(self.PATH_SET_STAGES, req, PipelineSetStagesResponse)
