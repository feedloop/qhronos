"""
Qhronos SDK Errors
"""

from typing import Any


class QhronosError(Exception):
    """Base exception for Qhronos SDK errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QhronosAPIError(QhronosError):
    """Exception raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        parts = [f"[{self.status_code}]"]
        if self.code:
            parts.append(f"({self.code})")
        parts.append(self.message)
        return " ".join(parts)


class QhronosNetworkError(QhronosError):
    """Exception raised when a network error occurs."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class QhronosTimeoutError(QhronosNetworkError):
    """Exception raised when a request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)

