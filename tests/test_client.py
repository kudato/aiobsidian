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


async def test_aclose_closes_internal_client():
    client = ObsidianClient("key")
    await client.aclose()
    assert client._http.is_closed is True


async def test_build_http_client_timeout():
    client = ObsidianClient("key", timeout=60.0)
    assert client._http.timeout == httpx.Timeout(60.0)
    await client.aclose()


async def test_raise_for_status_json_without_message_key(mock_api, client):
    mock_api.get("/x").respond(400, json={"detail": "something"})
    with pytest.raises(APIError) as exc_info:
        await client.request("GET", "/x")
    assert "detail" in exc_info.value.message


async def test_api_error_str_with_error_code():
    err = APIError(404, "Not found", 40401)
    assert str(err) == "[404] Not found (error_code=40401)"
    assert err.error_code == 40401


async def test_api_error_str_without_error_code():
    err = APIError(500, "Internal error")
    assert str(err) == "[500] Internal error"
    assert err.error_code is None


async def test_repr_does_not_contain_api_key():
    client = ObsidianClient("super-secret-key", host="myhost", port=9999, scheme="http")
    r = repr(client)
    assert "super-secret-key" not in r
    assert "myhost" in r
    assert "9999" in r
    assert "http" in r
    await client.aclose()
