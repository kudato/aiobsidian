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
uv run ruff check src/ tests/          # lint
uv run ruff format --check src/ tests/ # format check
uv run mypy src/                       # type check
uv run pytest -v                       # tests
```

### Auto-formatting

```bash
uv run ruff format src/ tests/
```

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
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   uv run mypy src/
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
├── _client.py          # ObsidianClient entry point
├── _base_resource.py   # BaseResource + ContentResource
├── _constants.py       # Default configuration
├── _types.py           # StrEnum types
├── _exceptions.py      # Exception hierarchy
├── models/             # Pydantic response models
└── resources/          # API resource classes
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
