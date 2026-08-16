from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from aiobsidian._cli import ObsidianCLI
from aiobsidian._client import ObsidianClient


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
