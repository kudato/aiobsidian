# aiobsidian

Async Python client for [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin.

## Installation

```bash
pip install aiobsidian
```

## Quick start

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient("your-api-key") as client:
        # Get server status
        status = await client.system.status()
        print(status.versions.obsidian)

        # Read a note
        content = await client.vault.get("notes/hello.md")
        print(content)

        # Create a note
        await client.vault.update("notes/new.md", "# New Note\n\nContent here.")

        # Search
        results = await client.search.simple("hello")
        for r in results:
            print(r.filename, r.score)

        # Execute a command
        commands = await client.commands.list()
        await client.commands.execute("daily-notes")

asyncio.run(main())
```

## Features

- Full async/await support via `httpx`
- All Obsidian Local REST API endpoints covered:
  - **Vault** — CRUD operations on any file
  - **Active** — operations on the currently open file
  - **Periodic** — daily, weekly, monthly, quarterly, yearly notes
  - **Commands** — list and execute Obsidian commands
  - **Search** — simple text search, Dataview DQL, JsonLogic
  - **Open** — open files in Obsidian UI
  - **System** — server status, OpenAPI spec
- Pydantic v2 models for all responses
- Custom exception hierarchy with error codes
- Context manager lifecycle management
- Bring-your-own `httpx.AsyncClient` support

## Configuration

```python
client = ObsidianClient(
    "your-api-key",
    host="127.0.0.1",      # default
    port=27124,             # default (HTTPS)
    scheme="https",         # default
    timeout=30.0,           # default
    verify_ssl=False,       # default (self-signed cert)
)
```

## Contributing

### For contributors

1. [Fork](https://github.com/kudato/aiobsidian/fork) this repository
2. Clone your fork and create a branch:

   ```bash
   git clone https://github.com/YOUR_USERNAME/aiobsidian.git
   cd aiobsidian
   git checkout -b feature/your-feature
   ```

3. Make changes and commit using [Conventional Commits](https://www.conventionalcommits.org/):

   ```
   feat: add new feature
   fix: fix bug in vault resource
   docs: update README
   refactor: extract helper method
   test: add search tests
   chore: update dependencies
   ```

4. Push to your fork and open a Pull Request:

   ```bash
   git push origin feature/your-feature
   gh pr create  # or use GitHub UI
   ```

### For maintainers

```bash
# Update version in pyproject.toml
sed -i '' 's/version = ".*/version = "X.Y.Z"/' pyproject.toml
git add pyproject.toml
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

CI will automatically create a GitHub Release and publish to PyPI.

## License

MIT
