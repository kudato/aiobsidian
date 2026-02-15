# CLAUDE.md

## Project overview

`aiobsidian` — async Python client for the [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin.

## Tech stack

- **Runtime**: Python 3.13+, httpx >=0.28, pydantic >=2.0
- **Build**: hatchling, uv (package manager)
- **Lint/Format**: ruff (rules: E, F, I, UP; line-length 88; target py313)
- **Tests**: pytest >=8.0, pytest-asyncio >=0.25 (`asyncio_mode = "auto"`), respx >=0.22
- **Docs**: mkdocs + mkdocs-material + mkdocstrings[python]

## Project structure

```
src/aiobsidian/
├── __init__.py            # public API — all exports in __all__
├── _client.py             # ObsidianClient (entry point, resource properties, request/error dispatch)
├── _base_resource.py      # BaseResource (__slots__, _client ref) + ContentResource (_get/_append/_patch helpers)
├── _constants.py          # DEFAULT_HOST/PORT/SCHEME/TIMEOUT
├── _types.py              # StrEnum types: Period, PatchOperation, TargetType, ContentType
├── _exceptions.py         # ObsidianError → APIError → AuthenticationError / NotFoundError
├── models/
│   ├── vault.py           # FileStat, NoteJson, DocumentMap, VaultDirectory
│   ├── system.py          # ServerStatus, Versions (Field alias "self" → self_)
│   ├── search.py          # MatchSpan, SearchMatch, SearchResult
│   └── commands.py        # Command
└── resources/
    ├── vault.py           # VaultResource — file CRUD + list (ContentResource)
    ├── active.py          # ActiveFileResource — active file ops (ContentResource)
    ├── periodic.py        # PeriodicNotesResource — periodic note ops (ContentResource)
    ├── commands.py        # CommandsResource — list/execute commands (BaseResource)
    ├── search.py          # SearchResource — simple/dataview/jsonlogic (BaseResource)
    ├── open.py            # OpenResource — open file in UI (BaseResource)
    └── system.py          # SystemResource — server status, OpenAPI spec (BaseResource)

tests/
├── conftest.py            # mock_api (respx router) + client (ObsidianClient with mocked transport) fixtures
├── test_client.py         # ObsidianClient unit tests
├── test_vault.py          # VaultResource tests
├── test_active.py         # ActiveFileResource tests
├── test_periodic.py       # PeriodicNotesResource tests
├── test_commands.py       # CommandsResource tests
├── test_search.py         # SearchResource tests
├── test_open.py           # OpenResource tests
└── test_system.py         # SystemResource tests
```

## Commands

```bash
uv sync                                # install all deps (dev + docs)
uv run ruff check src/ tests/          # lint
uv run ruff format --check src/ tests/ # format check
uv run ruff format src/ tests/         # auto-format
uv run pytest                          # run tests (70 tests)
uv run pytest -v                       # verbose test output
uv run mkdocs serve                    # local docs server
uv run mkdocs build                    # build static docs
```

## Architecture patterns

### Client lifecycle

`ObsidianClient` is the single entry point. It builds an internal `httpx.AsyncClient` with base URL, Bearer auth, timeout, and SSL settings. Used as an async context manager:

```python
async with ObsidianClient(api_key="key") as client:
    status = await client.system.status()
```

### External httpx client

When `http_client=` is passed, `ObsidianClient` wraps it without owning it — `aclose()` becomes a no-op. The `_external_client` flag tracks this. The caller is responsible for closing the external client.

### Resource access via `@cached_property`

Each resource (`vault`, `active`, `periodic`, `commands`, `search`, `open`, `system`) is a `@cached_property` on `ObsidianClient`. The resource class is imported **inside** the property getter to avoid circular imports.

### `TYPE_CHECKING` for type hints

`_client.py` imports resource classes under `TYPE_CHECKING` for return-type annotations. `_base_resource.py` imports `ObsidianClient` under `TYPE_CHECKING` for the `_client` parameter type. This breaks the circular dependency cycle: client → resources → base_resource → client.

### Resource class hierarchy

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

### Fixtures (in `conftest.py`)

```python
@pytest.fixture()
def mock_api():
    with respx.mock(base_url="https://127.0.0.1:27124") as api:
        yield api

@pytest.fixture()
async def client(mock_api):
    http = httpx.AsyncClient(
        base_url="https://127.0.0.1:27124",
        headers={"Authorization": "Bearer test-key"},
    )
    async with ObsidianClient("test-key", http_client=http) as c:
        yield c
```

The `client` fixture creates an `httpx.AsyncClient` manually (no SSL verification issues in tests) and passes it via `http_client=` to `ObsidianClient`. This pairs with `respx.mock(base_url=...)` for route matching.

### Test structure

- One test file per resource: `test_vault.py`, `test_active.py`, etc. Plus `test_client.py` for the client itself
- Test naming: `test_<method>_<scenario>` (e.g., `test_get_markdown`, `test_get_not_found`, `test_patch_prepend_to_block`)
- No `async def` markers needed — `asyncio_mode = "auto"` handles it
- Response data constants at module top (e.g., `NOTE_JSON`, `DOC_MAP_JSON`)

### Mocking routes

```python
# Simple response
mock_api.get("/vault/hello.md").respond(200, text="# Hello")

# JSON response
mock_api.get("/vault/hello.md").respond(200, json=NOTE_JSON)

# Verify request details
route = mock_api.patch("/vault/note.md").respond(200)
await client.vault.patch(...)
request = route.calls[0].request
assert request.headers["operation"] == "replace"
```

### Exception testing

```python
async def test_get_not_found(mock_api, client):
    mock_api.get("/vault/missing.md").respond(404, json={"message": "File not found"})
    with pytest.raises(NotFoundError) as exc_info:
        await client.vault.get("missing.md")
    assert exc_info.value.status_code == 404
```

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

Never import resource classes at the top level of `_client.py` or `ObsidianClient` at the top level of resource modules.

### PATCH frontmatter Content-Type

When `target_type == TargetType.FRONTMATTER`, the Content-Type must be `application/json`, not `text/markdown`. This is handled in `ContentResource._patch_content()` — see `_base_resource.py:85-86`.

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

### Adding a new resource

1. Create `src/aiobsidian/resources/<name>.py`
   - Extend `BaseResource` (or `ContentResource` if it needs get/append/patch)
   - Define `_BASE_URL` class variable
   - Add async methods with docstrings
2. Add `@cached_property` in `_client.py`
   - Import resource class inside the property body (not at top level)
   - Add `TYPE_CHECKING` import at the top for the return type annotation
3. Export the resource in `__init__.py` if it should be part of the public API
4. Create `tests/test_<name>.py` with route mocking

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
