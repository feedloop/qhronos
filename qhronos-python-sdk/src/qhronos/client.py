"""
Qhronos SDK Client
"""

from typing import Any, TypeVar

import httpx

from qhronos.errors import (
    QhronosAPIError,
    QhronosNetworkError,
    QhronosTimeoutError,
)
from qhronos.resources import (
    EventsResource,
    JobsResource,
    WorkflowsResource,
    ScriptsResource,
    IntegrationsResource,
    AsyncEventsResource,
    AsyncJobsResource,
    AsyncWorkflowsResource,
    AsyncScriptsResource,
    AsyncIntegrationsResource,
)

T = TypeVar("T")


class BaseClient:
    """Base client with common functionality."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        debug: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.debug = debug
        self._default_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            **(headers or {}),
        }

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _build_query_params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code >= 400:
            error = data.get("error", {})
            raise QhronosAPIError(
                message=error.get("message", "Unknown API error"),
                status_code=response.status_code,
                code=error.get("code"),
                details=error.get("details"),
            )

        return data


class QhronosClient(BaseClient):
    """
    Synchronous Qhronos API client.

    Example:
        >>> client = QhronosClient(
        ...     base_url="https://api.qhronos.io",
        ...     token="your-api-token",
        ... )
        >>> event = client.events.create(
        ...     EventCreateParams(
        ...         name="Daily Report",
        ...         start_time=datetime.now(),
        ...     )
        ... )
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__(base_url, token, timeout, headers, debug)
        self._client = httpx.Client(
            timeout=timeout,
            headers=self._default_headers,
        )

        # Initialize resources
        self.events = EventsResource(self)
        self.jobs = JobsResource(self)
        self.workflows = WorkflowsResource(self)
        self.scripts = ScriptsResource(self)
        self.integrations = IntegrationsResource(self)

    def __enter__(self) -> "QhronosClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API."""
        url = self._build_url(path)
        query_params = self._build_query_params(params)

        request_headers = {**self._default_headers}
        if headers:
            request_headers.update(headers)
        if idempotency_key:
            request_headers["Idempotency-Key"] = idempotency_key

        if self.debug:
            print(f"[Qhronos] {method} {url}")
            if json:
                print(f"[Qhronos] Body: {json}")

        try:
            response = self._client.request(
                method=method,
                url=url,
                json=json,
                params=query_params,
                headers=request_headers,
            )
        except httpx.TimeoutException as e:
            raise QhronosTimeoutError() from e
        except httpx.RequestError as e:
            raise QhronosNetworkError(str(e), e) from e

        return self._handle_response(response)

    def health(self) -> dict[str, Any]:
        """Check the health of the Qhronos API."""
        return self.request("GET", "/health")

    def status(self) -> dict[str, Any]:
        """Get the status of the Qhronos API."""
        return self.request("GET", "/status")


class AsyncQhronosClient(BaseClient):
    """
    Asynchronous Qhronos API client.

    Example:
        >>> async with AsyncQhronosClient(
        ...     base_url="https://api.qhronos.io",
        ...     token="your-api-token",
        ... ) as client:
        ...     event = await client.events.create(
        ...         EventCreateParams(
        ...             name="Daily Report",
        ...             start_time=datetime.now(),
        ...         )
        ...     )
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__(base_url, token, timeout, headers, debug)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._default_headers,
        )

        # Initialize resources
        self.events = AsyncEventsResource(self)
        self.jobs = AsyncJobsResource(self)
        self.workflows = AsyncWorkflowsResource(self)
        self.scripts = AsyncScriptsResource(self)
        self.integrations = AsyncIntegrationsResource(self)

    async def __aenter__(self) -> "AsyncQhronosClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API."""
        url = self._build_url(path)
        query_params = self._build_query_params(params)

        request_headers = {**self._default_headers}
        if headers:
            request_headers.update(headers)
        if idempotency_key:
            request_headers["Idempotency-Key"] = idempotency_key

        if self.debug:
            print(f"[Qhronos] {method} {url}")
            if json:
                print(f"[Qhronos] Body: {json}")

        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=json,
                params=query_params,
                headers=request_headers,
            )
        except httpx.TimeoutException as e:
            raise QhronosTimeoutError() from e
        except httpx.RequestError as e:
            raise QhronosNetworkError(str(e), e) from e

        return self._handle_response(response)

    async def health(self) -> dict[str, Any]:
        """Check the health of the Qhronos API."""
        return await self.request("GET", "/health")

    async def status(self) -> dict[str, Any]:
        """Get the status of the Qhronos API."""
        return await self.request("GET", "/status")

