from __future__ import annotations


class ObsidianError(Exception):
    """Base exception for all aiobsidian errors."""


class NotFoundError(ObsidianError):
    """The requested resource does not exist.

    Transport-neutral base class: `APINotFoundError` (REST) and
    `CLINotFoundError` (CLI) both inherit from it, so a missing note can be
    handled the same way regardless of the transport in use.
    """


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


class APINotFoundError(APIError, NotFoundError):
    """HTTP 404 Not Found — the requested resource does not exist."""


class CLIError(ObsidianError):
    """Base exception for Obsidian CLI errors."""


class BinaryNotFoundError(CLIError):
    """The Obsidian CLI binary could not be found or executed.

    Attributes:
        message: Description of the error.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CommandError(CLIError):
    """A CLI command failed.

    The Obsidian CLI reports failures by printing `Error: ...` to standard
    output while still exiting with status `0`, so `exit_code` is usually
    `0` and the failure text is carried by `stdout`.

    Attributes:
        command: The CLI command that failed.
        exit_code: Process exit code (`0` for failures reported on stdout).
        stderr: Standard error output.
        stdout: Standard output, which carries the CLI error message.
    """

    def __init__(
        self,
        command: str,
        exit_code: int,
        stderr: str,
        stdout: str = "",
    ) -> None:
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        detail = stderr.strip() or stdout.strip() or "no output"
        super().__init__(
            f"Command {command!r} failed (exit_code={exit_code}): {detail}"
        )


class CLINotFoundError(CommandError, NotFoundError):
    """A CLI command failed because the requested resource does not exist.

    Raised when the CLI reports a missing file, folder, tag, property or any
    other vault resource. A command that the CLI itself does not know is
    reported as a plain `CommandError`.
    """


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
