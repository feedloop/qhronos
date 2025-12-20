"""
Events Resource
"""

from datetime import datetime
from typing import Any

from qhronos.resources.base import BaseResource, AsyncBaseResource
from qhronos.models import Event, EventCreateParams, EventUpdateParams


class EventsResource(BaseResource):
    """Synchronous Events resource."""

    def create(
        self,
        params: EventCreateParams,
        idempotency_key: str | None = None,
    ) -> Event:
        """Create a new event."""
        data = params.model_dump(exclude_none=True)
        if isinstance(data.get("start_time"), datetime):
            data["start_time"] = data["start_time"].isoformat()
        response = self._post("/events", json=data, idempotency_key=idempotency_key)
        return Event.model_validate(response)

    def get(self, event_id: str) -> Event:
        """Get an event by ID."""
        response = self._get(f"/events/{event_id}")
        return Event.model_validate(response)

    def update(self, event_id: str, params: EventUpdateParams) -> Event:
        """Update an event."""
        data = params.model_dump(exclude_none=True)
        if isinstance(data.get("start_time"), datetime):
            data["start_time"] = data["start_time"].isoformat()
        response = self._put(f"/events/{event_id}", json=data)
        return Event.model_validate(response)

    def delete(self, event_id: str) -> None:
        """Delete an event."""
        self._delete(f"/events/{event_id}")

    def list(
        self,
        page: int | None = None,
        limit: int | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List events with optional filtering."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if tags:
            params["tags"] = tags
        if status:
            params["status"] = status
        return self._get("/events", params=params)

    def pause(self, event_id: str) -> Event:
        """Pause an event."""
        response = self._post(f"/events/{event_id}/pause")
        return Event.model_validate(response)

    def resume(self, event_id: str) -> Event:
        """Resume a paused event."""
        response = self._post(f"/events/{event_id}/resume")
        return Event.model_validate(response)

    def trigger(self, event_id: str) -> dict[str, str]:
        """Trigger an event immediately."""
        return self._post(f"/events/{event_id}/trigger")


class AsyncEventsResource(AsyncBaseResource):
    """Asynchronous Events resource."""

    async def create(
        self,
        params: EventCreateParams,
        idempotency_key: str | None = None,
    ) -> Event:
        """Create a new event."""
        data = params.model_dump(exclude_none=True)
        if isinstance(data.get("start_time"), datetime):
            data["start_time"] = data["start_time"].isoformat()
        response = await self._post("/events", json=data, idempotency_key=idempotency_key)
        return Event.model_validate(response)

    async def get(self, event_id: str) -> Event:
        """Get an event by ID."""
        response = await self._get(f"/events/{event_id}")
        return Event.model_validate(response)

    async def update(self, event_id: str, params: EventUpdateParams) -> Event:
        """Update an event."""
        data = params.model_dump(exclude_none=True)
        if isinstance(data.get("start_time"), datetime):
            data["start_time"] = data["start_time"].isoformat()
        response = await self._put(f"/events/{event_id}", json=data)
        return Event.model_validate(response)

    async def delete(self, event_id: str) -> None:
        """Delete an event."""
        await self._delete(f"/events/{event_id}")

    async def list(
        self,
        page: int | None = None,
        limit: int | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List events with optional filtering."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if tags:
            params["tags"] = tags
        if status:
            params["status"] = status
        return await self._get("/events", params=params)

    async def pause(self, event_id: str) -> Event:
        """Pause an event."""
        response = await self._post(f"/events/{event_id}/pause")
        return Event.model_validate(response)

    async def resume(self, event_id: str) -> Event:
        """Resume a paused event."""
        response = await self._post(f"/events/{event_id}/resume")
        return Event.model_validate(response)

    async def trigger(self, event_id: str) -> dict[str, str]:
        """Trigger an event immediately."""
        return await self._post(f"/events/{event_id}/trigger")

