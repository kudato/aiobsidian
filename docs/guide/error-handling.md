# Error Handling

aiobsidian uses a structured exception hierarchy for both CLI and REST errors.

## Exception hierarchy

```
ObsidianError                   # Base exception for all aiobsidian errors
├── NotFoundError               # Requested resource does not exist (any transport)
├── CLIError                    # Base exception for CLI errors
│   ├── BinaryNotFoundError     # CLI binary not found or not executable
│   ├── CommandError            # Command failed
│   │   └── CLINotFoundError    # ... because the resource does not exist
│   ├── CLIParseError           # Command output could not be parsed
│   └── CLITimeoutError         # Command exceeded timeout
└── APIError                    # Base exception for REST errors
    ├── APIStatusError          # The server answered with status >= 400
    │   ├── AuthenticationError # 401 Unauthorized
    │   └── APINotFoundError    # 404 Not Found
    ├── APIConnectionError      # The server could not be reached
    └── APITimeoutError         # The request took too long
```

`CLIError` and `APIError` are the two transport roots: catching either one
covers every way that transport can fail, whether or not a request or command
ever reached Obsidian.

`CLINotFoundError` and `APINotFoundError` also inherit from `NotFoundError`, so a
missing note can be handled the same way on both transports:

```python
from aiobsidian import NotFoundError

try:
    content = await cli.vault.read("note.md")   # or client.vault.get("note.md")
except NotFoundError:
    print("Note does not exist")
```

## CLI errors

```python
from aiobsidian import (
    ObsidianCLI,
    BinaryNotFoundError,
    CLINotFoundError,
    CommandError,
    CLITimeoutError,
)

try:
    async with ObsidianCLI("MyVault") as cli:
        content = await cli.vault.read("note.md")
except BinaryNotFoundError:
    print("Obsidian CLI binary not found. Install Obsidian v1.12+ and enable the CLI, or pass binary= explicitly.")
except CLINotFoundError as e:
    print(f"Command {e.command!r} found nothing: {e.stdout}")
except CommandError as e:
    print(f"Command {e.command!r} failed (exit code {e.exit_code}): {e.stdout or e.stderr}")
except CLITimeoutError as e:
    print(f"Command {e.command!r} timed out after {e.timeout}s")
```

### How CLI failures are detected

The Obsidian CLI exits with status `0` even when a command fails, and prints the
failure as `Error: ...` on standard output. aiobsidian therefore treats output
starting with that prefix as a failure:

- `Error: File "note.md" not found.`, `Error: Folder "archive" not found.` and other
  missing resources raise `CLINotFoundError`
- everything else — an unknown command, a missing required parameter, a command of a
  disabled plugin — raises `CommandError`
- `exit_code` is `0` for these failures, and the CLI message is available as `stdout`

Because the detection is based on the message prefix, reading a note whose content
starts with `Error: ` raises instead of returning the text. The prefix only matters at
the very beginning of the output, so `Error: ` further down a note is returned as
normal content.

A command may also succeed and still print something the library cannot interpret. In
that case parsing raises `CLIParseError`, which carries the raw `output`, instead of
letting a `json.JSONDecodeError` escape the `ObsidianError` hierarchy.

### CLIError attributes

| Exception | Attributes |
|-----------|-----------|
| `BinaryNotFoundError` | `message` |
| `CommandError` | `command`, `exit_code`, `stderr`, `stdout` |
| `CLINotFoundError` | `command`, `exit_code`, `stderr`, `stdout` |
| `CLIParseError` | `command`, `output` |
| `CLITimeoutError` | `command`, `timeout` |

## REST API errors

```python
from aiobsidian import (
    ObsidianClient,
    APIConnectionError,
    APINotFoundError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
)

async with ObsidianClient(api_key="your-api-key") as client:
    try:
        content = await client.vault.get("nonexistent.md")
    except APIConnectionError:
        print("Obsidian is not reachable — is it running with the plugin enabled?")
    except APITimeoutError:
        print("The server did not answer in time")
    except APINotFoundError:
        print("File not found")
    except AuthenticationError:
        print("Invalid API key")
    except APIStatusError as e:
        print(f"API error [{e.status_code}]: {e.message}")
```

### The request never reached the server

`APIConnectionError` and `APITimeoutError` cover the failures where no response
came back at all: Obsidian is closed, the plugin is disabled, the port is wrong,
the host is unreachable. The underlying `httpx` exception is the `__cause__` and
never escapes on its own — `httpx` is an optional dependency, so catching it
would mean importing a package the caller may not have installed.

### Attributes

| Exception | Attributes |
|-----------|-----------|
| `APIStatusError` | `status_code`, `message`, `error_code` |
| `AuthenticationError` | `status_code`, `message`, `error_code` |
| `APINotFoundError` | `status_code`, `message`, `error_code` |
| `APIConnectionError` | `method`, `url`, `detail` |
| `APITimeoutError` | `method`, `url`, `detail` |

## Catching all aiobsidian errors

Use `ObsidianError` to catch any exception from the library:

```python
from aiobsidian import ObsidianError

try:
    # CLI or REST operations
    ...
except ObsidianError as e:
    print(f"aiobsidian error: {e}")
```
