"""
Integrations Resource
"""

from typing import Any

from qhronos.resources.base import BaseResource, AsyncBaseResource
from qhronos.models import Integration, IntegrationCreateParams, IntegrationUpdateParams


class IntegrationsResource(BaseResource):
    """Synchronous Integrations resource."""

    def create(
        self,
        params: IntegrationCreateParams,
        idempotency_key: str | None = None,
    ) -> Integration:
        """Create a new integration."""
        data = params.model_dump(exclude_none=True)
        # Convert enums to values
        if "type" in data:
            data["type"] = data["type"].value if hasattr(data["type"], "value") else data["type"]
        if "provider" in data:
            data["provider"] = data["provider"].value if hasattr(data["provider"], "value") else data["provider"]
        response = self._post("/integrations", json=data, idempotency_key=idempotency_key)
        return Integration.model_validate(response)

    def get(self, integration_id: str) -> Integration:
        """Get an integration by ID."""
        response = self._get(f"/integrations/{integration_id}")
        return Integration.model_validate(response)

    def update(self, integration_id: str, params: IntegrationUpdateParams) -> Integration:
        """Update an integration."""
        data = params.model_dump(exclude_none=True)
        response = self._put(f"/integrations/{integration_id}", json=data)
        return Integration.model_validate(response)

    def delete(self, integration_id: str) -> None:
        """Delete an integration."""
        self._delete(f"/integrations/{integration_id}")

    def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List integrations with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._get("/integrations", params=params)

    def test(self, integration_id: str) -> dict[str, Any]:
        """Test an integration connection."""
        return self._post(f"/integrations/{integration_id}/test")


class AsyncIntegrationsResource(AsyncBaseResource):
    """Asynchronous Integrations resource."""

    async def create(
        self,
        params: IntegrationCreateParams,
        idempotency_key: str | None = None,
    ) -> Integration:
        """Create a new integration."""
        data = params.model_dump(exclude_none=True)
        # Convert enums to values
        if "type" in data:
            data["type"] = data["type"].value if hasattr(data["type"], "value") else data["type"]
        if "provider" in data:
            data["provider"] = data["provider"].value if hasattr(data["provider"], "value") else data["provider"]
        response = await self._post("/integrations", json=data, idempotency_key=idempotency_key)
        return Integration.model_validate(response)

    async def get(self, integration_id: str) -> Integration:
        """Get an integration by ID."""
        response = await self._get(f"/integrations/{integration_id}")
        return Integration.model_validate(response)

    async def update(self, integration_id: str, params: IntegrationUpdateParams) -> Integration:
        """Update an integration."""
        data = params.model_dump(exclude_none=True)
        response = await self._put(f"/integrations/{integration_id}", json=data)
        return Integration.model_validate(response)

    async def delete(self, integration_id: str) -> None:
        """Delete an integration."""
        await self._delete(f"/integrations/{integration_id}")

    async def list(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """List integrations with optional pagination."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self._get("/integrations", params=params)

    async def test(self, integration_id: str) -> dict[str, Any]:
        """Test an integration connection."""
        return await self._post(f"/integrations/{integration_id}/test")

