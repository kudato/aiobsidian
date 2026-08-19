# Contributing to aiobsidian

Thank you for your interest in contributing! This guide will help you get started.

## Development setup

1. Clone the repository:

   ```bash
   git clone https://github.com/kudato/aiobsidian.git
   cd aiobsidian
   ```

2. Install dependencies with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

## Development workflow

### Running checks

```bash
uv run ruff check src/ tests/ tools/          # lint
uv run ruff format --check src/ tests/ tools/ # format check
uv run mypy src/ tools/                       # type check
uv run pytest -v                              # tests
```

### Auto-formatting

```bash
uv run ruff format src/ tests/ tools/
```

### Refreshing the CLI grammar

`tests/data/cli_grammar.json` lists every command an Obsidian release
registers, with the parameters and flags each declares. The CLI tests
check the command lines they build against it, so a parameter the app
does not take fails a test rather than being silently ignored by the app.

It is read out of an installed Obsidian, and CI has none, so refreshing
it is a local step — run it when a new Obsidian release comes out, and
commit the result with the version it names:

```bash
uv run python tools/extract_cli_grammar.py > tests/data/cli_grammar.json
```

A command line the app no longer accepts then shows up as a failing test
instead of as a bug report.

### Running docs locally

```bash
uv sync --group docs
uv run mkdocs serve
```

## Making changes

1. [Fork](https://github.com/kudato/aiobsidian/fork) this repository
2. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature
   ```

3. Make your changes
4. Ensure all checks pass:

   ```bash
   uv run ruff check src/ tests/ tools/
   uv run ruff format --check src/ tests/ tools/
   uv run mypy src/ tools/
   uv run pytest -v
   ```

5. Commit using [Conventional Commits](https://www.conventionalcommits.org/):

   ```
   feat: add new feature
   fix: fix bug in vault resource
   docs: update README
   refactor: extract helper method
   test: add search tests
   chore: update dependencies
   ```

6. Push and open a Pull Request:

   ```bash
   git push origin feature/your-feature
   ```

## Code style

- **Imports**: always `from __future__ import annotations` at the top of modules
- **Type hints**: use `X | Y` union syntax, `TYPE_CHECKING` guard for circular imports
- **Docstrings**: Google-style with `Args:`, `Returns:`, `Raises:` sections
- **Naming**: Python `snake_case` everywhere; API `camelCase` mapped via Pydantic `Field(alias=...)`
- **Linting**: ruff with rules `E`, `F`, `I`, `UP`; line length 88; target Python 3.13

## Project structure

```
src/aiobsidian/
├── _cli.py             # ObsidianCLI entry point (CLI, primary)
├── _client.py          # ObsidianClient entry point (REST, optional)
├── _constants.py       # Default configuration
├── _types.py           # StrEnum types
├── _exceptions.py      # Exception hierarchy (CLIError + APIError)
├── cli/                # CLI resource classes (primary)
│   ├── _base.py        # BaseCLIResource
│   ├── vault.py        # File operations
│   ├── daily.py        # Daily notes
│   ├── search.py       # Full-text search
│   ├── properties.py   # YAML frontmatter properties
│   ├── tags.py         # Tag operations
│   ├── links.py        # Links and backlinks
│   ├── tasks.py        # Task operations
│   ├── commands.py     # Command execution
│   ├── templates.py    # Template operations
│   ├── bookmarks.py    # Bookmark operations
│   ├── plugins.py      # Plugin management
│   ├── themes.py       # Theme management
│   ├── snippets.py     # CSS snippet management
│   ├── sync.py         # Obsidian Sync operations
│   ├── publish.py      # Obsidian Publish operations
│   ├── history.py      # Local file history
│   ├── workspaces.py   # Workspace management
│   ├── hotkeys.py      # Hotkey operations
│   ├── outline.py      # Document outline
│   ├── random_note.py  # Random note operations
│   ├── aliases.py      # Note alias operations
│   └── bases.py        # Bases (database) operations
├── rest/               # REST resource classes (optional, requires httpx)
│   ├── _base.py        # BaseResource + ContentResource
│   ├── vault.py        # File CRUD + list
│   ├── active.py       # Active file operations
│   ├── periodic.py     # Periodic notes
│   ├── commands.py     # Command execution
│   ├── search.py       # Search (simple, Dataview, JsonLogic)
│   ├── open.py         # Open files in UI
│   └── system.py       # Server status
└── models/             # Pydantic response models

tools/
└── extract_cli_grammar.py  # Reads the CLI grammar out of obsidian.asar
```

## Releasing (maintainers)

1. Update version in `pyproject.toml`
2. Commit and tag:

   ```bash
   git commit -m "chore: release vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

CI will automatically create a GitHub Release and publish to PyPI.
