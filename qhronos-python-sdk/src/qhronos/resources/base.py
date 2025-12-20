"""
Base Resource Classes
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from qhronos.client import QhronosClient, AsyncQhronosClient


class BaseResource:
    """Base class for synchronous resources."""

    def __init__(self, client: "QhronosClient") -> None:
        self._client = client

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._client.request("GET", path, params=params)

    def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self._client.request("POST", path, json=json, idempotency_key=idempotency_key)

    def _put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._client.request("PUT", path, json=json)

    def _delete(self, path: str) -> dict[str, Any]:
        return self._client.request("DELETE", path)


class AsyncBaseResource:
    """Base class for asynchronous resources."""

    def __init__(self, client: "AsyncQhronosClient") -> None:
        self._client = client

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._client.request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return await self._client.request("POST", path, json=json, idempotency_key=idempotency_key)

    async def _put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._client.request("PUT", path, json=json)

    async def _delete(self, path: str) -> dict[str, Any]:
        return await self._client.request("DELETE", path)

