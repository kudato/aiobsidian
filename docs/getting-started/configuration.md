# Configuration

## ObsidianCLI

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vault` | `str` | *required* | Name of the Obsidian vault to operate on |
| `binary` | `str` | `"auto"` | Path to the CLI binary, or `"auto"` for automatic lookup |
| `timeout` | `float` | `30.0` | Default command timeout in seconds |

### Basic usage

```python
from aiobsidian import ObsidianCLI

async with ObsidianCLI("MyVault") as cli:
    content = await cli.vault.read("note.md")
```

### Custom binary path

If the `obsidian` binary is not on your `PATH`, specify it explicitly:

```python
cli = ObsidianCLI("MyVault", binary="/opt/obsidian/bin/obsidian")
```

### Custom timeout

```python
cli = ObsidianCLI("MyVault", timeout=60.0)
```

A single slow command can override it without changing the client:

```python
await cli.run("dev:screenshot", params={"path": "shot.png"}, timeout=120.0)
```

Wrapping a call in `asyncio.timeout` works too — cancelling a command
kills it and everything it started, so nothing is left running against
the vault.

### Running commands the library does not wrap

`run()` sends a command as given and returns its output as printed,
without parsing:

```python
raw = await cli.run("wordcount", params={"path": "note.md"})
# 'words: 3\ncharacters: 24\n'

raw = await cli.run("tags", flags=["total"])
# '8\n'
```

Prefer the resource methods where they exist — they know the shape of
each command's output. `run()` is for the commands they do not cover
yet, and it is the CLI counterpart of `ObsidianClient.request()`.

Failures are detected the same way as everywhere else, so a command that
fails raises instead of returning its error text.

---

## ObsidianClient (REST)

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | API key from the Local REST API plugin settings |
| `host` | `str` | `"127.0.0.1"` | Hostname of the REST API server |
| `port` | `int` | `27124` | Port number |
| `scheme` | `str` | `"https"` | URL scheme (`"https"` or `"http"`) |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `verify_ssl` | `bool` | `False` | Whether to verify SSL certificates |
| `http_client` | `httpx.AsyncClient \| None` | `None` | Optional pre-configured HTTP client |

### Basic usage

```python
from aiobsidian import ObsidianClient

async with ObsidianClient(api_key="your-api-key") as client:
    status = await client.system.status()
```

### Custom host and port

If the REST API plugin is configured to use a different host or port:

```python
client = ObsidianClient(
    api_key="your-api-key",
    host="192.168.1.100",
    port=8080,
)
```

### Using HTTP instead of HTTPS

```python
client = ObsidianClient(
    api_key="your-api-key",
    scheme="http",
)
```

### Custom httpx client

You can provide your own `httpx.AsyncClient` for advanced use cases like custom middleware, proxies, or connection pooling:

```python
import httpx
from aiobsidian import ObsidianClient

custom_http = httpx.AsyncClient(
    timeout=60.0,
    verify=False,
    limits=httpx.Limits(max_connections=10),
)

client = ObsidianClient(
    api_key="your-api-key",
    http_client=custom_http,
)
```

The `api_key` is applied to every request, so the client needs no `Authorization` header of its own. It needs no `base_url` either — `host`, `port` and `scheme` supply one when it has none. Set `base_url` yourself only to route requests elsewhere, e.g. through a proxy; it then wins over `host`/`port`/`scheme`.

!!! note
    When you provide an external `httpx.AsyncClient`, aiobsidian will **not** close it when `aclose()` is called. You are responsible for managing its lifecycle.

## Lifecycle management

Both `ObsidianCLI` and `ObsidianClient` support async context managers:

### Context manager (recommended)

```python
async with ObsidianCLI("MyVault") as cli:
    files = await cli.vault.list()
# any command still running is killed here

async with ObsidianClient(api_key="your-api-key") as client:
    status = await client.system.status()
# HTTP client is automatically closed here
```

### Manual close

Both clients close through `aclose()`, so code holding one does not need
to know which transport it got:

```python
client: ObsidianCLI | ObsidianClient = ObsidianCLI("MyVault")
try:
    ...
finally:
    await client.aclose()
```

Closing an `ObsidianCLI` is final: it kills every command still running,
and any command issued afterwards raises `RuntimeError`.
