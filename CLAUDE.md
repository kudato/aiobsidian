# CLAUDE.md

## Git

- Open every pull request against `main`, never against another branch; keep dependent work local until what it needs is merged
- Write commits and pull request titles as Conventional Commits, `!` included; the title becomes the squash commit subject on `main`
- Update a branch from `main` by merging, never by rebasing
- Never rewrite pushed history — no force push, rebase, amend or hard reset on a published branch
- Squash-merge every pull request; `main` stays linear

## Commands

```bash
uv sync --all-groups                   # install all deps (dev + docs); plain `uv sync` drops docs
uv run ruff check src/ tests/ tools/   # lint
uv run ruff format src/ tests/ tools/  # auto-format
uv run mypy src/ tools/ tests/typing_examples.py   # type check
uv run pytest                          # run tests
uv run mkdocs build                    # build static docs

# Refresh the CLI grammar the tests check against, from an installed Obsidian
uv run python tools/extract_cli_grammar.py > tests/data/cli_grammar.json
```

## Code style

- **Always** `from __future__ import annotations` (except `_types.py`, which needs `StrEnum` at runtime, and `__init__.py`)
- Use `X | Y` unions, never `Union[X, Y]` or `Optional[X]`
- Break circular imports with `TYPE_CHECKING` guards, and import resource classes lazily inside the `@cached_property` getter
- Every resource declares its own `__slots__`, `__slots__ = ()` included; the clients are not slotted, `@cached_property` needs `__dict__`
- Every `__init__` parameter after the first positional one is keyword-only
- Deserialize with `Model.model_validate(data)`, never `Model(**data)`; map API camelCase with `Field(alias=...)`
- Google-style docstrings with `Args:`, `Returns:` and `Raises:` sections
- Failure detection for CLI commands belongs to `_execute()`: the CLI exits `0` on failure, so resource methods parse successful output only
- Parse CLI output with the `_parse_*` helpers of `BaseCLIResource`, never with bare `json.loads()`; pass `output_format=` only for commands that document `format=`

## Tests

- One test file per resource; name tests `test_<method>_<scenario>`
- `asyncio_mode = "auto"` — no async markers needed
- REST: `respx.mock` with the `client` fixture; CLI: the `cli` fixture with `AsyncMock` on `_execute`
- CLI test data must reproduce real `obsidian` output, not what the code happens to send
- The `cli` fixture checks every command line against `tests/data/cli_grammar.json`, the grammar of the shipped app; a new command or parameter has to be one Obsidian registers
- Every public CLI method needs an entry in `CALLS` in `tests/test_cli_contract.py`, which is what checks its command line, its empty answer and its error propagation
