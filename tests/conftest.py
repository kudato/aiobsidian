from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from aiobsidian._cli import ObsidianCLI
from aiobsidian._client import ObsidianClient


def drop_field(output: str, field: str, separator: str = "\t") -> str:
    """Print a field block the way the CLI would without one field.

    The record commands print a field per line, and which of those lines
    Obsidian may leave out is what the models say. Removing one is how a
    test asks whether a field is really required.

    Args:
        output: Field block as the CLI prints it.
        field: Name of the field to leave out.
        separator: Separator between key and value.

    Returns:
        The same block without that field's line.
    """
    prefix = f"{field}{separator}"
    return "".join(
        line for line in output.splitlines(keepends=True) if not line.startswith(prefix)
    )


@pytest.fixture(autouse=True)
def guard_killpg(request):
    """Keep os.killpg away from process groups the tests do not own.

    A mocked process answers `.pid` with a MagicMock, and MagicMock
    coerces to 1 through `__index__`, so an unguarded `_kill` would ask
    the OS to SIGKILL process group 1. A desktop refuses that; a
    container running as root would not.

    Autouse across the whole suite, not one file: any test that patches
    `asyncio.create_subprocess_exec` can reach `_kill`.
    """
    if "real_processes" in request.keywords:
        yield None
        return
    with patch("aiobsidian._cli.os.killpg") as killpg:
        yield killpg


@pytest.fixture()
def mock_api():
    with respx.mock(base_url="https://127.0.0.1:27124") as api:
        yield api


@pytest.fixture()
async def client(mock_api):
    # No Authorization header here on purpose: the client must install it
    # itself, whoever built the transport.
    http = httpx.AsyncClient(base_url="https://127.0.0.1:27124")
    async with ObsidianClient("test-key", http_client=http) as c:
        yield c


@pytest.fixture()
def cli():
    instance = ObsidianCLI("TestVault", binary="/usr/local/bin/obsidian")
    instance._execute = AsyncMock()
    return instance
