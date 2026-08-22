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
│   ├── CLITimeoutError         # Command exceeded timeout
│   └── PartialWriteError       # A several-command write failed part-way
└── APIError                    # Base exception for REST errors
    ├── APIStatusError          # The server answered with status >= 400
    │   ├── AuthenticationError # 401 Unauthorized
    │   └── APINotFoundError    # 404 Not Found
    └── APIRequestError         # No usable response came back
        ├── APIConnectionError  # The server could not be reached
        ├── APITimeoutError     # The request took too long
        └── APIProtocolError    # The exchange broke down
```

`CLIError` and `APIError` are the two transport roots: catching either one
covers every failure of an operation on that transport, whether or not the
request or command reached Obsidian.

Misusing the library is not one of those failures and stays a plain builtin, as
elsewhere in Python: a bad argument raises `TypeError` or `ValueError`, and
using a client after `aclose()` raises `RuntimeError`.

`CLINotFoundError` and `APINotFoundError` also inherit from `NotFoundError`, so a
missing note can be handled the same way on both transports:

```python
from aiobsidian import NotFoundError

try:
    content = await cli.vault.read("note.md")   # client.vault.read() is the same call
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

The Obsidian CLI exits with status `0` even when a command fails, and prints most
failures as `Error: ...` on standard output. aiobsidian therefore treats output
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

Three failures arrive without that prefix, and are recognised anyway:

- `command`, `history:restore` and `workspace:save` report a parameter they cannot do
  without by returning their usage instead of raising it. That starts with
  `Missing required parameter: `, and is read the same way, by the prefix
- `Vault not found.` — the `vault=` name reached no vault Obsidian knows. It is decided
  before the command reaches a vault, so it carries no prefix, and raises `CommandError`
  rather than `CLINotFoundError`: a vault you cannot reach would otherwise answer
  "the note does not exist" for every note in it
- `Command line interface is not enabled. Please turn it on in Settings > General >
  Advanced.` — likewise `CommandError`

These two sentences are matched as the whole of the output rather than as a prefix, so
only a note whose entire content is one of them is mistaken for the failure it spells.

A command may also succeed and still print something the library cannot interpret. In
that case parsing raises `CLIParseError`, which carries the raw `output`, instead of
letting a `json.JSONDecodeError` escape the `ObsidianError` hierarchy.

### When a write fails part-way

The CLI reads `\n` and `\t` inside a content value as escapes and gives a backslash no
way to hide from it, so content spelling them literally is written as several commands
(the docstrings of `vault.write()` and the other writing methods say so). A failure
between those commands leaves the file holding what already landed, and arrives as
`PartialWriteError`: the underlying failure is its `__cause__`, `path` names the file —
for `create_unique()` that is the path the exception would otherwise have cost the
caller — and `written` of `total` says how much of the content is in place. The
periodic-note commands find their own file, so their `path` is `None`. A failure of
the first command raises itself instead, since nothing has landed yet — save when
that command was also told to `open` what it wrote, which it does after the
writing, so a failure to open leaves the file created behind a plain
`CommandError` that names no path. And only a command failing is a write failing:
cancellation, and a client closed while the write ran, propagate as
`CancelledError` and `RuntimeError`, as everywhere else in the library.

### CLIError attributes

| Exception | Attributes |
|-----------|-----------|
| `BinaryNotFoundError` | `message` |
| `CommandError` | `command`, `exit_code`, `stderr`, `stdout` |
| `CLINotFoundError` | `command`, `exit_code`, `stderr`, `stdout` |
| `CLIParseError` | `command`, `output` |
| `CLITimeoutError` | `command`, `timeout` |
| `PartialWriteError` | `command`, `path`, `written`, `total` |

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
        content = await client.vault.read("nonexistent.md")
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

### When no usable response comes back

`APIRequestError` and its three subclasses cover the failures that produce no
response to inspect, and they are kept apart because they point at different
things to fix:

| Exception | Meaning | Typical cause |
|-----------|---------|---------------|
| `APIConnectionError` | The server was never reached | Obsidian closed, plugin disabled, wrong port, unreachable host |
| `APITimeoutError` | It did not answer in time | A slow or wedged request |
| `APIProtocolError` | It answered, and the exchange broke | Malformed HTTP, a body that belied its headers, a redirect loop |

Only `APIConnectionError` suggests checking whether Obsidian is running. The
other two happen while it plainly is.

A request that could not be sent at all never gets that far: an unparseable
`host`, a `scheme` that is not HTTP, a path that will not form a URL or a header
the HTTP layer refuses raises `ValueError`, because the argument is what needs
fixing.

The underlying `httpx` exception is available as `__cause__` and never escapes
on its own — `httpx` is an optional dependency, so catching it would mean
importing a package the caller may not have installed.

### Attributes

| Exception | Attributes |
|-----------|-----------|
| `APIStatusError` | `status_code`, `message`, `error_code` |
| `AuthenticationError` | `status_code`, `message`, `error_code` |
| `APINotFoundError` | `status_code`, `message`, `error_code` |
| `APIRequestError` | `method`, `url`, `detail` |
| `APIConnectionError` | `method`, `url`, `detail` |
| `APITimeoutError` | `method`, `url`, `detail` |
| `APIProtocolError` | `method`, `url`, `detail` |

### Upgrading from 0.4.0

`APIError` used to be the status-carrying class and is now the REST root. Code
that reads a status code off it must catch `APIStatusError` instead:

```python
except APIError as e:        # still catches status errors, but also
    print(e.status_code)     # connection ones, which have no status_code

except APIStatusError as e:  # what that code meant
    print(e.status_code)
```

`APIError(404, "Not found")` still constructs, because `Exception` accepts any
arguments — it just produces a useless message and no attributes. Search for it
rather than relying on a `TypeError`.

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
