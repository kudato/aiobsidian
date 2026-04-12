# Installation

## Choose your interface

aiobsidian supports two interfaces for interacting with Obsidian:

| Interface | Requirements | Install |
|-----------|-------------|---------|
| **CLI** (primary) | [Obsidian CLI](https://obsidian.md/cli) v1.12+ | `pip install aiobsidian` |
| **REST** (optional) | [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin + httpx | `pip install aiobsidian[rest]` |

## CLI setup

1. **Obsidian** — download from [obsidian.md](https://obsidian.md)
2. **Enable the CLI** (v1.12+) — open Obsidian → Settings → General → enable "Command line interface"

    !!! note
        On macOS, creating the CLI symlink at `/usr/local/bin/obsidian` requires administrator privileges. On Linux, the binary is placed at `~/.local/bin/obsidian` — ensure this directory is in your `PATH`.

3. **Install aiobsidian**:

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

### Verify CLI setup

```python
import asyncio
from aiobsidian import ObsidianCLI

async def main():
    async with ObsidianCLI("MyVault") as cli:
        files = await cli.vault.list()
        print(f"Found {len(files)} files")

asyncio.run(main())
```

!!! note
    Obsidian must be running in the background for the CLI to work — it communicates with the desktop app via IPC.

## REST setup

1. **Obsidian** — download from [obsidian.md](https://obsidian.md)
2. **Local REST API plugin** — install from the Obsidian Community Plugins:
    - Open Obsidian Settings → Community Plugins → Browse
    - Search for "Local REST API"
    - Install and enable the plugin
    - Copy the API key from the plugin settings

3. **Install aiobsidian with REST support**:

=== "pip"

    ```bash
    pip install aiobsidian[rest]
    ```

=== "uv"

    ```bash
    uv add aiobsidian[rest]
    ```

=== "Poetry"

    ```bash
    poetry add aiobsidian[rest]
    ```

### SSL certificates

The Local REST API plugin uses **self-signed HTTPS certificates** by default. aiobsidian disables SSL verification (`verify_ssl=False`) to handle this automatically.

!!! warning
    If you need strict SSL verification (e.g. behind a reverse proxy with real certificates), pass `verify_ssl=True` when creating the client:

    ```python
    client = ObsidianClient(api_key="...", verify_ssl=True)
    ```

### Verify REST setup

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient(api_key="your-api-key") as client:
        status = await client.system.status()
        print(f"Connected! Obsidian v{status.versions.obsidian}")

asyncio.run(main())
```
