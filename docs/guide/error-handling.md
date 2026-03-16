# Error Handling

aiobsidian uses a structured exception hierarchy for both CLI and REST errors.

## Exception hierarchy

```
ObsidianError              # Base exception for all aiobsidian errors
├── CLIError               # Base exception for CLI errors
│   ├── BinaryNotFoundError    # CLI binary not found on PATH
│   ├── CommandError           # Command exited with non-zero status
│   └── CLITimeoutError        # Command exceeded timeout
└── APIError               # HTTP error from the REST API
    ├── AuthenticationError    # 401 Unauthorized
    └── NotFoundError          # 404 Not Found
```

## CLI errors

```python
from aiobsidian import (
    ObsidianCLI,
    BinaryNotFoundError,
    CommandError,
    CLITimeoutError,
)

try:
    async with ObsidianCLI("MyVault") as cli:
        content = await cli.vault.read("note.md")
except BinaryNotFoundError:
    print("Obsidian CLI binary not found. Install Obsidian v1.12+ or pass binary= explicitly.")
except CommandError as e:
    print(f"Command {e.command!r} failed (exit code {e.exit_code}): {e.stderr}")
except CLITimeoutError as e:
    print(f"Command {e.command!r} timed out after {e.timeout}s")
```

### CLIError attributes

| Exception | Attributes |
|-----------|-----------|
| `BinaryNotFoundError` | `message` |
| `CommandError` | `command`, `exit_code`, `stderr` |
| `CLITimeoutError` | `command`, `timeout` |

## REST API errors

```python
from aiobsidian import (
    ObsidianClient,
    APIError,
    AuthenticationError,
    NotFoundError,
)

async with ObsidianClient(api_key="your-api-key") as client:
    try:
        content = await client.vault.get("nonexistent.md")
    except NotFoundError:
        print("File not found")
    except AuthenticationError:
        print("Invalid API key")
    except APIError as e:
        print(f"API error [{e.status_code}]: {e.message}")
```

### APIError attributes

All API exceptions (`APIError`, `AuthenticationError`, `NotFoundError`) have these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` | HTTP status code (e.g. 401, 404, 500) |
| `message` | `str` | Error message from the API response |
| `error_code` | `int \| None` | Optional numeric error code from the API |

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
