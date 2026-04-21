"""CRM project task service."""

from schemas.api.crm.project_task import (
    ProjectTaskEditRequest,
    ProjectTaskEditResponse,
    ProjectTaskGetRequest,
    ProjectTaskGetResponse,
)


class ProjectTaskService:
    PATH_GET = "ProjectTask/Get"
    PATH_EDIT = "ProjectTask/Edit"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ProjectTaskGetRequest) -> ProjectTaskGetResponse:
        return await self.api.call(self.PATH_GET, req, ProjectTaskGetResponse)

    async def edit(self, req: ProjectTaskEditRequest) -> ProjectTaskEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ProjectTaskEditResponse)
