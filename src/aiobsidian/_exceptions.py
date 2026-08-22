from __future__ import annotations

from functools import partial


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


class APIRequestError(APIError):
    """A request that produced no usable response.

    The other half of `APIError`: `APIStatusError` means the server
    answered and refused, this means nothing came back that could be
    read as an answer — whether or not the server sent bytes.

    Attributes:
        method: HTTP method of the request that failed.
        url: URL the request was sent to.
        detail: What the HTTP transport reported.
    """

    _problem = "failed"
    _hint = ""

    def __init__(self, method: str, url: str, detail: str) -> None:
        self.method = method
        self.url = url
        self.detail = detail
        message = f"{method} {url} {self._problem}: {detail}"
        if self._hint:
            message = f"{message}. {self._hint}"
        super().__init__(message)

    def __reduce__(self) -> tuple[type[APIRequestError], tuple[str, str, str]]:
        return type(self), (self.method, self.url, self.detail)


class APIConnectionError(APIRequestError):
    """The REST API server could not be reached.

    A refused connection, a dropped one, an unreachable host or a proxy
    that would not forward.
    """

    _problem = "could not be reached"
    _hint = "Is Obsidian running with the Local REST API plugin enabled?"


class APITimeoutError(APIRequestError):
    """A request to the REST API exceeded its timeout."""

    _problem = "timed out"


class APIProtocolError(APIRequestError):
    """The exchange with the REST API server broke down.

    The connection was made and the server responded, but its response
    could not be used: malformed HTTP, a body that did not match its
    declared encoding or length, or a redirect loop. It says nothing
    about whether Obsidian is running — it plainly is.

    A request that could not be sent in the first place is a bad
    argument, and raises `ValueError` instead.
    """

    _problem = "did not complete"


class APIParseError(APIError):
    """The body of a REST API response could not be read as promised.

    The server answered success and the exchange held, so this is
    neither an `APIStatusError` nor an `APIRequestError`: what arrived
    is not what the endpoint documents — not JSON, or JSON of another
    shape. The counterpart of `CLIParseError`, and it carries the raw
    body the same way.

    Attributes:
        method: HTTP method of the request.
        url: URL the request was sent to.
        body: Raw text of the response body.
    """

    def __init__(self, method: str, url: str, body: str) -> None:
        self.method = method
        self.url = url
        self.body = body
        excerpt = body.strip()[:200]
        super().__init__(f"Could not read the answer of {method} {url}: {excerpt!r}")

    def __reduce__(self) -> tuple[type[APIParseError], tuple[str, str, str]]:
        return type(self), (self.method, self.url, self.body)


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


class PartialWriteError(CLIError):
    """A write that takes several commands failed with some already run.

    The CLI reads `\\n` and `\\t` inside a content value as escapes and
    gives a backslash no way to hide from it, so content spelling them
    literally is written one part per command. A failure between those
    commands leaves the file holding what already landed. The failure
    itself is the `__cause__`; this names the file, so a caller knows
    what to look at, and counts the parts, so it knows how much of the
    content is there. A failure of the first command raises itself
    instead, since nothing has landed yet — save when that command was
    also told to `open` what it wrote, which it does after the writing,
    so a failure to open leaves the file created behind a plain
    `CommandError` that names no path. And only a command failing is a
    write failing: cancellation, and the client being closed while the
    write ran, propagate as themselves, as everywhere else.

    Attributes:
        command: The CLI command the failed part was sent with.
        path: Path of the file left holding part of the content,
            relative to the vault root, or `None` when the command
            finds its own file, as the periodic-note commands do.
        written: How many parts landed, the opening write included.
        total: How many parts the content was split into.
    """

    def __init__(
        self,
        command: str,
        *,
        path: str | None,
        written: int,
        total: int,
    ) -> None:
        self.command = command
        self.path = path
        self.written = written
        self.total = total
        placed = "" if path is None else f" to {path!r}"
        super().__init__(
            f"Command {command!r} wrote {written} of {total} content parts"
            f"{placed} before failing"
        )

    def __reduce__(self) -> tuple[partial[PartialWriteError], tuple[()]]:
        rebuild = partial(
            type(self),
            self.command,
            path=self.path,
            written=self.written,
            total=self.total,
        )
        return rebuild, ()
