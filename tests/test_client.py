import httpx
import pytest
import respx

from aiobsidian._client import ObsidianClient
from aiobsidian._exceptions import (
    APIConnectionError,
    APIError,
    APINotFoundError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    ObsidianError,
)


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
    with pytest.raises(APINotFoundError) as exc_info:
        await client.request("GET", "/vault/missing.md")
    assert exc_info.value.error_code == 40401
    assert isinstance(exc_info.value, NotFoundError)
    assert isinstance(exc_info.value, APIError)


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


async def test_client_bearer_token_with_external_http_client(mock_api):
    route = mock_api.get("/vault/").respond(200, json={"files": []})
    http = httpx.AsyncClient(base_url="https://127.0.0.1:27124")

    async with ObsidianClient("my-secret-key", http_client=http) as client:
        await client.vault.list()

    assert route.calls[0].request.headers["authorization"] == "Bearer my-secret-key"
    await http.aclose()


async def test_client_external_http_client_without_base_url(mock_api):
    route = mock_api.get("/vault/").respond(200, json={"files": []})
    http = httpx.AsyncClient()

    async with ObsidianClient("key", http_client=http) as client:
        await client.vault.list()

    assert route.calls[0].request.url == "https://127.0.0.1:27124/vault/"
    await http.aclose()


async def test_client_external_http_client_keeps_its_base_url(mock_api):
    with respx.mock(base_url="http://proxy.local:8080") as api:
        route = api.get("/vault/").respond(200, json={"files": []})
        http = httpx.AsyncClient(base_url="http://proxy.local:8080")

        async with ObsidianClient("key", http_client=http) as client:
            await client.vault.list()

        assert route.called
        await http.aclose()


async def test_client_request_headers_override_authorization(mock_api, client):
    route = mock_api.get("/").respond(200, json={"ok": "OK"})

    await client.request("GET", "/", headers={"Authorization": "Bearer other"})

    assert route.calls[0].request.headers["authorization"] == "Bearer other"


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


async def test_raise_for_status_json_array_body(mock_api, client):
    """A JSON array body must not leak AttributeError; APIError is raised instead."""
    mock_api.get("/x").respond(500, json=[{"error": "boom"}])
    with pytest.raises(APIError) as exc_info:
        await client.request("GET", "/x")
    assert exc_info.value.status_code == 500


async def test_api_error_str_with_error_code():
    err = APIStatusError(404, "Not found", 40401)
    assert str(err) == "[404] Not found (error_code=40401)"
    assert err.error_code == 40401


async def test_api_error_str_without_error_code():
    err = APIStatusError(500, "Internal error")
    assert str(err) == "[500] Internal error"
    assert err.error_code is None


class TestTransportErrors:
    """httpx failures must not reach the caller as httpx exceptions.

    httpx is an optional dependency, so catching one of its exceptions
    means importing a package the caller may not have installed, and it
    sits outside the ObsidianError hierarchy the docs promise.
    """

    async def test_unreachable_server_raises_api_connection_error(
        self, mock_api, client
    ):
        mock_api.get("/vault/note.md").mock(
            side_effect=httpx.ConnectError("[Errno 61] Connection refused")
        )

        with pytest.raises(APIConnectionError) as exc_info:
            await client.request("GET", "/vault/note.md")

        error = exc_info.value
        assert error.method == "GET"
        assert error.url == "https://127.0.0.1:27124/vault/note.md"
        assert error.detail == "[Errno 61] Connection refused"
        assert "Is Obsidian running" in str(error)

    async def test_slow_server_raises_api_timeout_error(self, mock_api, client):
        mock_api.get("/vault/note.md").mock(side_effect=httpx.ReadTimeout("timed out"))

        with pytest.raises(APITimeoutError) as exc_info:
            await client.request("GET", "/vault/note.md")

        assert exc_info.value.method == "GET"
        assert exc_info.value.detail == "timed out"

    async def test_a_timeout_is_not_reported_as_a_connection_failure(
        self, mock_api, client
    ):
        # httpx.TimeoutException derives from RequestError, so the order
        # of the two except clauses is what keeps these apart.
        mock_api.get("/x").mock(side_effect=httpx.ConnectTimeout("timed out"))

        with pytest.raises(APITimeoutError):
            await client.request("GET", "/x")

    async def test_transport_errors_are_obsidian_errors(self, mock_api, client):
        mock_api.get("/x").mock(side_effect=httpx.ConnectError("refused"))

        with pytest.raises(ObsidianError):
            await client.request("GET", "/x")

    async def test_an_error_without_a_message_still_names_itself(
        self, mock_api, client
    ):
        mock_api.get("/x").mock(side_effect=httpx.ReadError(""))

        with pytest.raises(APIConnectionError) as exc_info:
            await client.request("GET", "/x")

        assert exc_info.value.detail == "ReadError"


async def test_repr_does_not_contain_api_key():
    client = ObsidianClient("super-secret-key", host="myhost", port=9999, scheme="http")
    r = repr(client)
    assert "super-secret-key" not in r
    assert "myhost" in r
    assert "9999" in r
    assert "http" in r
    await client.aclose()
