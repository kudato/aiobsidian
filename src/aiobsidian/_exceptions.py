from __future__ import annotations


class ObsidianError(Exception):
    """Base exception for aiobsidian."""


class APIError(ObsidianError):
    """Error returned by the Obsidian REST API."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{status_code}] {message}")


class AuthenticationError(APIError):
    """401 Unauthorized."""


class NotFoundError(APIError):
    """404 Not Found."""
