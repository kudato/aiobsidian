# aiobsidian

**Async Python client for [Obsidian](https://obsidian.md).**

CLI-first: works out of the box with the [Obsidian CLI](https://obsidian.md/cli) (v1.12+). Optional REST support via the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin.

## Features

- **CLI-first** — works directly with the Obsidian CLI binary, no plugins required
- **Optional REST** — full REST API support via `pip install aiobsidian[rest]`
- **Async/await** — built for modern async Python
- **Fully typed** — complete type annotations and a `py.typed` marker
- **Resource-based API** — intuitive access through `cli.vault`, `cli.tags`, `client.search`, etc.
- **Pydantic v2 models** — structured, validated response objects

## Quick example

=== "CLI"

    ```python
    import asyncio
    from aiobsidian import ObsidianCLI

    async def main():
        async with ObsidianCLI("MyVault") as cli:
            content = await cli.vault.read("notes/hello.md")
            print(content)

            tags = await cli.tags.list()
            results = await cli.search.query("python")

    asyncio.run(main())
    ```

=== "REST"

    ```python
    import asyncio
    from aiobsidian import ObsidianClient

    async def main():
        async with ObsidianClient(api_key="your-api-key") as client:
            status = await client.system.status()
            print(f"Obsidian v{status.versions.obsidian}")

            content = await client.vault.get("Notes/hello.md")
            print(content)

    asyncio.run(main())
    ```

## Next steps

- [Installation](getting-started/installation.md) — install aiobsidian and set up Obsidian CLI or the REST plugin
- [Quick Start](getting-started/quickstart.md) — get up and running in minutes
- [User Guide](guide/vault.md) — learn all the operations available
- [API Reference](reference/cli.md) — full API documentation
