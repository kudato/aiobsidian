import httpx
import pytest
import respx

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
