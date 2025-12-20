"""
Scripts Resource
"""

from typing import Any

from qhronos.resources.base import BaseResource, AsyncBaseResource
from qhronos.models import Script, ScriptCreateParams, ScriptUpdateParams, Job


class ScriptsResource(BaseResource):
    """Synchronous Scripts resource."""

    def create(
        self,
        params: ScriptCreateParams,
        idempotency_key: str | None = None,
    ) -> Script:
        """Create a new script."""
        data = params.model_dump(exclude_none=True)
        response = self._post("/scripts", json=data, idempotency_key=idempotency_key)
        return Script.model_validate(response)

    def get(self, script_id: str) -> Script:
        """Get a script by ID."""
        response = self._get(f"/scripts/{script_id}")
        return Script.model_validate(response)

    def update(self, script_id: str, params: ScriptUpdateParams) -> Script:
        """Update a script."""
        data = params.model_dump(exclude_none=True)
        response = self._put(f"/scripts/{script_id}", json=data)
        return Script.model_validate(response)

    def delete(self, script_id: str) -> None:
        """Delete a script."""
        self._delete(f"/scripts/{script_id}")

    def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List scripts with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get("/scripts", params=params)

    def execute(
        self,
        script_id: str,
        params: dict[str, Any] | None = None,
    ) -> Job:
        """Execute a script immediately."""
        data = {"params": params} if params else {}
        response = self._post(f"/scripts/{script_id}/execute", json=data)
        return Job.model_validate(response)


class AsyncScriptsResource(AsyncBaseResource):
    """Asynchronous Scripts resource."""

    async def create(
        self,
        params: ScriptCreateParams,
        idempotency_key: str | None = None,
    ) -> Script:
        """Create a new script."""
        data = params.model_dump(exclude_none=True)
        response = await self._post("/scripts", json=data, idempotency_key=idempotency_key)
        return Script.model_validate(response)

    async def get(self, script_id: str) -> Script:
        """Get a script by ID."""
        response = await self._get(f"/scripts/{script_id}")
        return Script.model_validate(response)

    async def update(self, script_id: str, params: ScriptUpdateParams) -> Script:
        """Update a script."""
        data = params.model_dump(exclude_none=True)
        response = await self._put(f"/scripts/{script_id}", json=data)
        return Script.model_validate(response)

    async def delete(self, script_id: str) -> None:
        """Delete a script."""
        await self._delete(f"/scripts/{script_id}")

    async def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List scripts with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self._get("/scripts", params=params)

    async def execute(
        self,
        script_id: str,
        params: dict[str, Any] | None = None,
    ) -> Job:
        """Execute a script immediately."""
        data = {"params": params} if params else {}
        response = await self._post(f"/scripts/{script_id}/execute", json=data)
        return Job.model_validate(response)

