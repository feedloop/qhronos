"""
Workflows Resource
"""

from typing import Any

from qhronos.resources.base import BaseResource, AsyncBaseResource
from qhronos.models import Workflow, WorkflowCreateParams, WorkflowUpdateParams, Job


class WorkflowsResource(BaseResource):
    """Synchronous Workflows resource."""

    def create(
        self,
        params: WorkflowCreateParams,
        idempotency_key: str | None = None,
    ) -> Workflow:
        """Create a new workflow."""
        data = params.model_dump(exclude_none=True)
        response = self._post("/workflows", json=data, idempotency_key=idempotency_key)
        return Workflow.model_validate(response)

    def get(self, workflow_id: str) -> Workflow:
        """Get a workflow by ID."""
        response = self._get(f"/workflows/{workflow_id}")
        return Workflow.model_validate(response)

    def update(self, workflow_id: str, params: WorkflowUpdateParams) -> Workflow:
        """Update a workflow."""
        data = params.model_dump(exclude_none=True)
        response = self._put(f"/workflows/{workflow_id}", json=data)
        return Workflow.model_validate(response)

    def delete(self, workflow_id: str) -> None:
        """Delete a workflow."""
        self._delete(f"/workflows/{workflow_id}")

    def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List workflows with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get("/workflows", params=params)

    def execute(
        self,
        workflow_id: str,
        params: dict[str, Any] | None = None,
    ) -> Job:
        """Execute a workflow immediately."""
        data = {"params": params} if params else {}
        response = self._post(f"/workflows/{workflow_id}/execute", json=data)
        return Job.model_validate(response)

    def jobs(
        self,
        workflow_id: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List jobs for a workflow."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get(f"/workflows/{workflow_id}/jobs", params=params)

    def job(self, workflow_id: str, job_id: str) -> Job:
        """Get a specific job for a workflow."""
        response = self._get(f"/workflows/{workflow_id}/jobs/{job_id}")
        return Job.model_validate(response)


class AsyncWorkflowsResource(AsyncBaseResource):
    """Asynchronous Workflows resource."""

    async def create(
        self,
        params: WorkflowCreateParams,
        idempotency_key: str | None = None,
    ) -> Workflow:
        """Create a new workflow."""
        data = params.model_dump(exclude_none=True)
        response = await self._post("/workflows", json=data, idempotency_key=idempotency_key)
        return Workflow.model_validate(response)

    async def get(self, workflow_id: str) -> Workflow:
        """Get a workflow by ID."""
        response = await self._get(f"/workflows/{workflow_id}")
        return Workflow.model_validate(response)

    async def update(self, workflow_id: str, params: WorkflowUpdateParams) -> Workflow:
        """Update a workflow."""
        data = params.model_dump(exclude_none=True)
        response = await self._put(f"/workflows/{workflow_id}", json=data)
        return Workflow.model_validate(response)

    async def delete(self, workflow_id: str) -> None:
        """Delete a workflow."""
        await self._delete(f"/workflows/{workflow_id}")

    async def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List workflows with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self._get("/workflows", params=params)

    async def execute(
        self,
        workflow_id: str,
        params: dict[str, Any] | None = None,
    ) -> Job:
        """Execute a workflow immediately."""
        data = {"params": params} if params else {}
        response = await self._post(f"/workflows/{workflow_id}/execute", json=data)
        return Job.model_validate(response)

    async def jobs(
        self,
        workflow_id: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List jobs for a workflow."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self._get(f"/workflows/{workflow_id}/jobs", params=params)

    async def job(self, workflow_id: str, job_id: str) -> Job:
        """Get a specific job for a workflow."""
        response = await self._get(f"/workflows/{workflow_id}/jobs/{job_id}")
        return Job.model_validate(response)

