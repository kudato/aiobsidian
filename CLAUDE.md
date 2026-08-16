# CLAUDE.md

## Commands

```bash
uv sync                                # install all deps (dev + docs)
uv run ruff check src/ tests/          # lint
uv run ruff format src/ tests/         # auto-format
uv run mypy src/                       # type check
uv run pytest                          # run tests
uv run mkdocs build                    # build static docs
```

## Code style

- **Always** `from __future__ import annotations` (except `_types.py`, which needs `StrEnum` at runtime, and `__init__.py`)
- Use `X | Y` unions, never `Union[X, Y]` or `Optional[X]`
- Break circular imports with `TYPE_CHECKING` guards, and import resource classes lazily inside the `@cached_property` getter
- Resources use `__slots__`; every `__init__` parameter after the first positional one is keyword-only
- Deserialize with `Model.model_validate(data)`, never `Model(**data)`; map API camelCase with `Field(alias=...)`
- Google-style docstrings with `Args:`, `Returns:` and `Raises:` sections
- Failure detection for CLI commands belongs to `_execute()`: the CLI exits `0` on failure, so resource methods parse successful output only
- Parse CLI output with the `_parse_*` helpers of `BaseCLIResource`, never with bare `json.loads()`; pass `output_format=` only for commands that document `format=`

## Tests

- One test file per resource; name tests `test_<method>_<scenario>`
- `asyncio_mode = "auto"` — no async markers needed
- REST: `respx.mock` with the `client` fixture; CLI: the `cli` fixture with `AsyncMock` on `_execute`
- CLI test data must reproduce real `obsidian` output, not what the code happens to send
