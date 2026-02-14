import httpx
import pytest
import respx

from aiobsidian._client import ObsidianClient
from aiobsidian._exceptions import APIError, AuthenticationError, NotFoundError


async def test_client_default_base_url():
    client = ObsidianClient("key")
    assert client._base_url == "https://127.0.0.1:27124"
    await client.aclose()


async def test_client_custom_url():
    client = ObsidianClient("key", host="localhost", port=8080, scheme="http")
    assert client._base_url == "http://localhost:8080"
    await client.aclose()


async def test_client_context_manager():
    async with ObsidianClient("key") as client:
        assert client._http is not None


async def test_client_external_http_client_not_closed():
    http = httpx.AsyncClient()
    client = ObsidianClient("key", http_client=http)
    await client.aclose()
    assert not http.is_closed
    await http.aclose()


async def test_client_raises_authentication_error(mock_api, client):
    mock_api.get("/").respond(401, json={"message": "Unauthorized"})
    with pytest.raises(AuthenticationError) as exc_info:
        await client.request("GET", "/")
    assert exc_info.value.status_code == 401


async def test_client_raises_not_found_error(mock_api, client):
    mock_api.get("/vault/missing.md").respond(
        404, json={"message": "Not found", "errorCode": 40401}
    )
    with pytest.raises(NotFoundError) as exc_info:
        await client.request("GET", "/vault/missing.md")
    assert exc_info.value.error_code == 40401


async def test_client_raises_api_error(mock_api, client):
    mock_api.post("/commands/bad/").respond(500, json={"message": "Internal error"})
    with pytest.raises(APIError):
        await client.request("POST", "/commands/bad/")


async def test_client_bearer_token():
    with respx.mock(base_url="https://127.0.0.1:27124") as api:
        route = api.get("/").respond(200, json={"ok": "OK"})
        client = ObsidianClient("my-secret-key")
        await client.request("GET", "/")
        assert route.calls[0].request.headers["authorization"] == "Bearer my-secret-key"
        await client.aclose()


async def test_client_raises_api_error_non_json_response(mock_api, client):
    mock_api.get("/bad").respond(500, text="Internal Server Error")
    with pytest.raises(APIError) as exc_info:
        await client.request("GET", "/bad")
    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "Internal Server Error"
