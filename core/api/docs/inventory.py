"""Compatibility facade for the generated DocInventory service."""

from __future__ import annotations

from typing import Any

from core.api.docs.doc_inventory import (
    DocInventoryService as GeneratedDocInventoryService,
)


class DocInventoryService(GeneratedDocInventoryService):
    async def perform(self, req: Any):
        """Compatibility alias used by generic document UI actions."""
        return await self.close(req)

    async def perform_cancel(self, req: Any):
        """Compatibility alias used by generic document UI actions."""
        return await self.open(req)


__all__ = ["DocInventoryService"]
