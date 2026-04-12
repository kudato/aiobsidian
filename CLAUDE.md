# CLAUDE.md

## Project overview

`aiobsidian` — async Python client for Obsidian. CLI-first: works out of the box with the [Obsidian CLI](https://obsidian.md/cli) (v1.12+). Optional REST support via the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin (`pip install aiobsidian[rest]`).

## Tech stack

- **Runtime**: Python 3.13+, pydantic >=2.0, httpx >=0.28 (optional, for REST)
- **Build**: hatchling, uv (package manager)
- **Lint/Format**: ruff (rules: E, F, I, UP; line-length 88; target py313)
- **Audit**: `uv audit` (OSV-based dependency vulnerability scanning)
- **Tests**: pytest >=8.0, pytest-asyncio >=0.25 (`asyncio_mode = "auto"`), respx >=0.22
- **Docs**: mkdocs + mkdocs-material + mkdocstrings[python]

## Commands

```bash
uv sync                                # install all deps (dev + docs)
uv run ruff check src/ tests/          # lint
uv run ruff format --check src/ tests/ # format check
uv run ruff format src/ tests/         # auto-format
uv run pytest                          # run tests
uv run pytest -v                       # verbose test output
uv run mkdocs serve                    # local docs server
uv run mkdocs build                    # build static docs
```

## Architecture patterns

### Two entry points

- `ObsidianCLI(vault)` — primary, CLI-based. Wraps the Obsidian CLI binary via `asyncio.create_subprocess_exec`. No external dependencies beyond stdlib.
- `ObsidianClient(api_key)` — optional, REST-based. Requires `httpx` (`pip install aiobsidian[rest]`). Builds an internal `httpx.AsyncClient` with Bearer auth and SSL settings.

Both are async context managers:

```python
async with ObsidianCLI("MyVault") as cli:
    content = await cli.vault.read("note.md")

async with ObsidianClient(api_key="key") as client:
    status = await client.system.status()
```

### Optional httpx dependency

`httpx` is imported lazily in `_client.py` via `_import_httpx()`. At import time only `TYPE_CHECKING` imports are used. If a user instantiates `ObsidianClient` without httpx installed, they get a clear `ImportError` with install instructions.

### External httpx client

When `http_client=` is passed, `ObsidianClient` wraps it without owning it — `aclose()` becomes a no-op. The `_external_client` flag tracks this. The caller is responsible for closing the external client.

### Resource access via `@cached_property`

Each resource is a `@cached_property` on `ObsidianCLI` or `ObsidianClient`. The resource class is imported **inside** the property getter to avoid circular imports.

### `TYPE_CHECKING` for type hints

`_client.py` imports REST resource classes under `TYPE_CHECKING`. `_cli.py` imports CLI resource classes under `TYPE_CHECKING`. Base resource modules import their parent client under `TYPE_CHECKING`. This breaks all circular dependency cycles.

### Resource class hierarchy

**CLI** (`cli/`):
- `BaseCLIResource` — holds `_cli` reference, uses `__slots__ = ("_cli",)`
- All CLI resources extend `BaseCLIResource` directly

**REST** (`rest/`):
- `BaseResource` — holds `_client` reference, uses `__slots__ = ("_client",)`
- `ContentResource(BaseResource)` — adds `_get_content`, `_append_content`, `_patch_content` helpers with `@overload` for type-safe return types based on `ContentType`
- Vault, Active, Periodic extend `ContentResource`; Commands, Search, Open, System extend `BaseResource`

### Error handling

`ObsidianClient.request()` checks `status_code >= 400` and dispatches to:
- 401 → `AuthenticationError`
- 404 → `NotFoundError`
- Other → `APIError`

All exceptions carry `status_code`, `message`, and optional `error_code` from JSON body. Non-JSON error bodies fall back to `response.text`.

### SSL

`verify_ssl=False` by default because the Obsidian plugin uses self-signed certificates. Passed directly to `httpx.AsyncClient(verify=...)`.

## Code style

### Imports and annotations

- **Always** `from __future__ import annotations` at the top of every module (except `_types.py` which uses `StrEnum` at runtime and `__init__.py` which re-exports)
- Use `X | Y` union syntax (not `Union[X, Y]` or `Optional[X]`)
- Use `TYPE_CHECKING` guard for imports that would create circular dependencies

### Type definitions

- Enums use `StrEnum` (from `enum`, not a third-party lib) — values are lowercase strings matching the API
- Resources use `__slots__` for memory efficiency
- All `__init__` parameters after the first positional arg are keyword-only (enforced with `*`)

### Pydantic models

- Inherit from `BaseModel` (no custom base)
- Deserialization: always `Model.model_validate(data)`, never `Model(**data)`
- Field aliases: `Field(alias="camelCase")` for API fields that differ from Python naming
- `ConfigDict(populate_by_name=True)` when a model needs both alias and Python name access (see `Versions`)
- Default values: `Field(default=...)` for optional fields with defaults

### Docstrings

Google-style with `Args:`, `Returns:`, `Raises:` sections. Class-level docstrings describe the class with an `Attributes:` section. Include `Example:` with code blocks for user-facing classes like `ObsidianClient`.

### `@overload` pattern

Used in `ContentResource` and its subclasses for `get()` methods. The pattern:
1. Multiple `@overload` signatures mapping each `Literal[ContentType.X]` to its return type
2. Implementation signature uses the `ContentType` union and returns `str | NoteJson | DocumentMap`
3. Body dispatches on `content_type` value

### Naming

- Python snake_case for everything: methods, parameters, attributes
- API camelCase mapped via Field aliases (e.g., `frontmatterFields` → `frontmatter_fields`)
- Private modules prefixed with `_` (`_client.py`, `_types.py`, etc.)
- Resource URL constants: `_BASE_URL` class variable

## Testing patterns

- One test file per resource, plus `test_client.py` and `test_cli.py` for entry points
- Test naming: `test_<method>_<scenario>`
- `asyncio_mode = "auto"` — no async markers needed
- REST tests: `respx.mock` + `client` fixture (see `conftest.py`)
- CLI tests: `cli` fixture with `AsyncMock` on `_execute` (see `conftest.py`)

## Gotchas

### Trailing slashes in URLs

The Obsidian REST API is inconsistent with trailing slashes. Some endpoints require them, some don't:
- `/vault/` (list) — trailing slash means directory listing
- `/vault/file.md` (CRUD) — no trailing slash
- `/commands/` (list) — trailing slash required
- `/commands/{id}/` (execute) — trailing slash required
- `/periodic/{period}/` — trailing slash required
- `/active/` — trailing slash required
- `/search/simple/` — trailing slash required
- `/search/` (dataview, jsonlogic) — trailing slash required

Each resource defines `_BASE_URL` accordingly. Check the API spec before adding endpoints.

### Circular imports

The client imports resources, and resources need the client type. Solved with:
1. `TYPE_CHECKING` guards for type hints only
2. Lazy imports inside `@cached_property` getters for runtime

Never import resource classes at the top level of `_client.py`/`_cli.py` or client classes at the top level of resource modules.

### PATCH frontmatter Content-Type

When `target_type == TargetType.FRONTMATTER`, the Content-Type must be `application/json`, not `text/markdown`. This is handled in `ContentResource._patch_content()` — see `rest/_base.py`.

### respx base_url matching

`respx.mock(base_url=...)` must match the `httpx.AsyncClient(base_url=...)` exactly — including scheme and port. Both use `https://127.0.0.1:27124` in tests.

## Commit style

Format: `<type>: <description>` (lowercase, imperative mood, no period)

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples from this repo:
```
feat: add API resource classes
refactor: extract shared get/append/patch logic into BaseResource
test: add negative tests and missing enum coverage
chore: add project configuration and license
```

## Common tasks

### Adding a new CLI resource

1. Create `src/aiobsidian/cli/<name>.py`
   - Extend `BaseCLIResource` from `._base`
   - Add async methods that call `self._cli._execute()`
   - Annotate `json.loads()` return values to satisfy mypy
2. Add `@cached_property` in `_cli.py`
   - Import resource class inside the property body (not at top level)
   - Add `TYPE_CHECKING` import at the top for the return type annotation
3. Create `tests/test_cli_<name>.py` using the `cli` fixture (AsyncMock)

### Adding a new REST resource

1. Create `src/aiobsidian/rest/<name>.py`
   - Extend `BaseResource` (or `ContentResource` if it needs get/append/patch) from `._base`
   - Define `_BASE_URL` class variable
   - Add async methods with docstrings
2. Add `@cached_property` in `_client.py`
   - Import resource class inside the property body (not at top level)
   - Add `TYPE_CHECKING` import at the top for the return type annotation
3. Export the resource in `__init__.py` if it should be part of the public API
4. Create `tests/test_<name>.py` with respx route mocking

### Adding a new model

1. Create or extend a file in `src/aiobsidian/models/`
   - Inherit from `BaseModel`
   - Use `Field(alias=...)` for camelCase API fields
   - Add Google-style docstring with `Attributes:` section
2. Add to `__init__.py` `__all__` list
3. Add test data constants and test cases

### Adding a new enum value

1. Add the value to the appropriate `StrEnum` in `_types.py`
   - Value must match the API string exactly (lowercase)
   - Add a docstring line for the new member
2. Add test coverage for the new value
