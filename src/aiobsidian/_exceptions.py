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
    """Base exception for Obsidian REST API errors.

    The counterpart of `CLIError`: catching it covers a request the
    server refused as well as one that never reached it.
    """


class APIStatusError(APIError):
    """The REST API answered with an error status.

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

    def __reduce__(self) -> tuple[type[APIStatusError], tuple[int, str, int | None]]:
        return type(self), (self.status_code, self.message, self.error_code)


class AuthenticationError(APIStatusError):
    """HTTP 401 Unauthorized — invalid or missing API key."""


class APINotFoundError(APIStatusError, NotFoundError):
    """HTTP 404 Not Found — the requested resource does not exist."""


class APIConnectionError(APIError):
    """The REST API server could not be reached.

    Attributes:
        method: HTTP method of the request that failed.
        url: URL the request was sent to.
        detail: What the HTTP transport reported.
    """

    def __init__(self, method: str, url: str, detail: str) -> None:
        self.method = method
        self.url = url
        self.detail = detail
        super().__init__(
            f"{method} {url} could not be reached: {detail}. Is Obsidian "
            f"running with the Local REST API plugin enabled?"
        )

    def __reduce__(self) -> tuple[type[APIConnectionError], tuple[str, str, str]]:
        return type(self), (self.method, self.url, self.detail)


class APITimeoutError(APIError):
    """A request to the REST API exceeded its timeout.

    Attributes:
        method: HTTP method of the request that timed out.
        url: URL the request was sent to.
        detail: What the HTTP transport reported.
    """

    def __init__(self, method: str, url: str, detail: str) -> None:
        self.method = method
        self.url = url
        self.detail = detail
        super().__init__(f"{method} {url} timed out: {detail}")

    def __reduce__(self) -> tuple[type[APITimeoutError], tuple[str, str, str]]:
        return type(self), (self.method, self.url, self.detail)


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

    def __reduce__(self) -> tuple[type[CommandError], tuple[str, int, str, str]]:
        return type(self), (self.command, self.exit_code, self.stderr, self.stdout)


class CLINotFoundError(CommandError, NotFoundError):
    """A CLI command failed because the requested resource does not exist.

    Raised when the CLI reports a missing file, folder, tag, property or any
    other vault resource. A command that the CLI itself does not know is
    reported as a plain `CommandError`.
    """


class CLIParseError(CLIError):
    """The output of a CLI command could not be parsed.

    Attributes:
        command: The CLI command whose output could not be parsed.
        output: Raw output of the command.
    """

    def __init__(self, command: str, output: str) -> None:
        self.command = command
        self.output = output
        excerpt = output.strip()[:200]
        super().__init__(f"Could not parse the output of {command!r}: {excerpt!r}")

    def __reduce__(self) -> tuple[type[CLIParseError], tuple[str, str]]:
        return type(self), (self.command, self.output)


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

    def __reduce__(self) -> tuple[type[CLITimeoutError], tuple[str, float]]:
        return type(self), (self.command, self.timeout)
