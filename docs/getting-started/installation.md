# Installation

## Prerequisites

1. **Obsidian** — download from [obsidian.md](https://obsidian.md)
2. **Local REST API plugin** — install from the Obsidian Community Plugins:
    - Open Obsidian Settings → Community Plugins → Browse
    - Search for "Local REST API"
    - Install and enable the plugin
    - Copy the API key from the plugin settings

## Install aiobsidian

=== "pip"

    ```bash
    pip install aiobsidian
    ```

=== "uv"

    ```bash
    uv add aiobsidian
    ```

=== "Poetry"

    ```bash
    poetry add aiobsidian
    ```

## SSL certificates

The Local REST API plugin uses **self-signed HTTPS certificates** by default. aiobsidian disables SSL verification (`verify_ssl=False`) to handle this automatically.

!!! warning
    If you need strict SSL verification (e.g. behind a reverse proxy with real certificates), pass `verify_ssl=True` when creating the client:

    ```python
    client = ObsidianClient(api_key="...", verify_ssl=True)
    ```

## Verify the installation

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient(api_key="your-api-key") as client:
        status = await client.system.status()
        print(f"Connected! Obsidian v{status.versions.obsidian}")

asyncio.run(main())
```

If you see the Obsidian version printed, you're all set!
