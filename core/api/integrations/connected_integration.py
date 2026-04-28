"""ConnectedIntegration service."""

from schemas.api.integrations.connected_integration import (
    ConnectedIntegrationEditRequest,
    ConnectedIntegrationEditResponse,
    ConnectedIntegrationGetRequest,
    ConnectedIntegrationGetResponse,
)


class ConnectedIntegrationService:
    PATH_GET = "ConnectedIntegration/Get"
    PATH_EDIT = "ConnectedIntegration/Edit"

    def __init__(self, api):
        self.api = api

    async def get(self, req: ConnectedIntegrationGetRequest) -> ConnectedIntegrationGetResponse:
        return await self.api.call(self.PATH_GET, req, ConnectedIntegrationGetResponse)

    async def edit(self, req: ConnectedIntegrationEditRequest) -> ConnectedIntegrationEditResponse:
        return await self.api.call(self.PATH_EDIT, req, ConnectedIntegrationEditResponse)

