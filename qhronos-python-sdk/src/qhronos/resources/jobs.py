"""
Jobs Resource
"""

from typing import Any

from qhronos.resources.base import BaseResource, AsyncBaseResource
from qhronos.models import Job, JobType, JobStatus


class JobsResource(BaseResource):
    """Synchronous Jobs resource."""

    def get(self, job_id: str) -> Job:
        """Get a job by ID."""
        response = self._get(f"/jobs/{job_id}")
        return Job.model_validate(response)

    def list(
        self,
        page: int | None = None,
        limit: int | None = None,
        type: JobType | None = None,
        status: JobStatus | None = None,
        event_id: str | None = None,
        workflow_id: str | None = None,
        parent_job_id: str | None = None,
    ) -> dict[str, Any]:
        """List jobs with optional filtering."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if type:
            params["type"] = type.value if isinstance(type, JobType) else type
        if status:
            params["status"] = status.value if isinstance(status, JobStatus) else status
        if event_id:
            params["event_id"] = event_id
        if workflow_id:
            params["workflow_id"] = workflow_id
        if parent_job_id:
            params["parent_job_id"] = parent_job_id
        return self._get("/jobs", params=params)

    def cancel(self, job_id: str) -> Job:
        """Cancel a pending or running job."""
        response = self._post(f"/jobs/{job_id}/cancel")
        return Job.model_validate(response)

    def retry(self, job_id: str) -> Job:
        """Retry a failed job."""
        response = self._post(f"/jobs/{job_id}/retry")
        return Job.model_validate(response)

    def children(
        self,
        job_id: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Get child jobs for a workflow job."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get(f"/jobs/{job_id}/children", params=params)


class AsyncJobsResource(AsyncBaseResource):
    """Asynchronous Jobs resource."""

    async def get(self, job_id: str) -> Job:
        """Get a job by ID."""
        response = await self._get(f"/jobs/{job_id}")
        return Job.model_validate(response)

    async def list(
        self,
        page: int | None = None,
        limit: int | None = None,
        type: JobType | None = None,
        status: JobStatus | None = None,
        event_id: str | None = None,
        workflow_id: str | None = None,
        parent_job_id: str | None = None,
    ) -> dict[str, Any]:
        """List jobs with optional filtering."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if type:
            params["type"] = type.value if isinstance(type, JobType) else type
        if status:
            params["status"] = status.value if isinstance(status, JobStatus) else status
        if event_id:
            params["event_id"] = event_id
        if workflow_id:
            params["workflow_id"] = workflow_id
        if parent_job_id:
            params["parent_job_id"] = parent_job_id
        return await self._get("/jobs", params=params)

    async def cancel(self, job_id: str) -> Job:
        """Cancel a pending or running job."""
        response = await self._post(f"/jobs/{job_id}/cancel")
        return Job.model_validate(response)

    async def retry(self, job_id: str) -> Job:
        """Retry a failed job."""
        response = await self._post(f"/jobs/{job_id}/retry")
        return Job.model_validate(response)

    async def children(
        self,
        job_id: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Get child jobs for a workflow job."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self._get(f"/jobs/{job_id}/children", params=params)

