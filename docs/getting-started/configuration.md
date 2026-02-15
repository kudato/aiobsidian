# Configuration

## Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | *required* | API key from the Local REST API plugin settings |
| `host` | `str` | `"127.0.0.1"` | Hostname of the REST API server |
| `port` | `int` | `27124` | Port number |
| `scheme` | `str` | `"https"` | URL scheme (`"https"` or `"http"`) |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `verify_ssl` | `bool` | `False` | Whether to verify SSL certificates |
| `http_client` | `httpx.AsyncClient \| None` | `None` | Optional pre-configured HTTP client |

## Basic usage

```python
from aiobsidian import ObsidianClient

client = ObsidianClient(api_key="your-api-key")
```

## Custom host and port

If the REST API plugin is configured to use a different host or port:

```python
client = ObsidianClient(
    api_key="your-api-key",
    host="192.168.1.100",
    port=8080,
)
```

## Using HTTP instead of HTTPS

```python
client = ObsidianClient(
    api_key="your-api-key",
    scheme="http",
)
```

## Custom httpx client

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

### Context manager (recommended)

```python
async with ObsidianClient(api_key="your-api-key") as client:
    status = await client.system.status()
# Client is automatically closed here
```

### Manual close

```python
client = ObsidianClient(api_key="your-api-key")
try:
    status = await client.system.status()
finally:
    await client.aclose()
```
