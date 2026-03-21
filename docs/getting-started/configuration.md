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

Per-command timeout override is also available via the `_execute` method internally.

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
    base_url="https://127.0.0.1:27124",
    headers={"Authorization": "Bearer your-api-key"},
    timeout=60.0,
    verify=False,
    limits=httpx.Limits(max_connections=10),
)

client = ObsidianClient(
    api_key="your-api-key",
    http_client=custom_http,
)
```

!!! note
    When you provide an external `httpx.AsyncClient`, aiobsidian will **not** close it when `aclose()` is called. You are responsible for managing its lifecycle.

## Lifecycle management

Both `ObsidianCLI` and `ObsidianClient` support async context managers:

### Context manager (recommended)

```python
async with ObsidianCLI("MyVault") as cli:
    files = await cli.vault.list()
# CLI instance is cleaned up here

async with ObsidianClient(api_key="your-api-key") as client:
    status = await client.system.status()
# HTTP client is automatically closed here
```

### Manual close (REST only)

```python
client = ObsidianClient(api_key="your-api-key")
try:
    status = await client.system.status()
finally:
    await client.aclose()
```
