from __future__ import annotations


class ObsidianError(Exception):
    """Base exception for all aiobsidian errors."""


class APIError(ObsidianError):
    """Error returned by the Obsidian REST API.

    Attributes:
        status_code: HTTP status code of the response.
        message: Error message from the API.
        error_code: Optional numeric error code from the API.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        msg = f"[{status_code}] {message}"
        if error_code is not None:
            msg += f" (error_code={error_code})"
        super().__init__(msg)


class AuthenticationError(APIError):
    """HTTP 401 Unauthorized — invalid or missing API key."""


class NotFoundError(APIError):
    """HTTP 404 Not Found — the requested resource does not exist."""
