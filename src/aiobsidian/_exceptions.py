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


class CLIError(ObsidianError):
    """Base exception for Obsidian CLI errors."""


class BinaryNotFoundError(CLIError):
    """The Obsidian CLI binary could not be found.

    Attributes:
        message: Description of the error.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CommandError(CLIError):
    """A CLI command exited with a non-zero status.

    Attributes:
        command: The CLI command that failed.
        exit_code: Process exit code.
        stderr: Standard error output.
    """

    def __init__(self, command: str, exit_code: int, stderr: str) -> None:
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(
            f"Command {command!r} failed (exit_code={exit_code}): {stderr}"
        )


class CLITimeoutError(CLIError):
    """A CLI command exceeded the timeout limit.

    Attributes:
        command: The CLI command that timed out.
        timeout: Timeout value in seconds.
    """

    def __init__(self, command: str, timeout: float) -> None:
        self.command = command
        self.timeout = timeout
        super().__init__(f"Command {command!r} timed out after {timeout}s")
