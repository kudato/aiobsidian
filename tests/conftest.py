from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from aiobsidian._cli import ObsidianCLI
from aiobsidian._client import ObsidianClient


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


@pytest.fixture()
def cli():
    instance = ObsidianCLI.__new__(ObsidianCLI)
    instance._vault = "TestVault"
    instance._binary = "/usr/local/bin/obsidian"
    instance._timeout = 30.0
    instance._execute = AsyncMock()
    return instance
