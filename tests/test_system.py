import pytest

from aiobsidian._exceptions import APIError, AuthenticationError
from aiobsidian.models.system import ServerStatus

STATUS_JSON = {
    "status": "OK",
    "service": "Obsidian Local REST API",
    "authenticated": True,
    "versions": {"obsidian": "1.7.7", "self": "3.2.0"},
    "manifest": {"id": "obsidian-local-rest-api", "name": "Local REST API"},
    "certificateInfo": {"validFrom": "2024-01-01"},
    "apiExtensions": [],
}


async def test_status(mock_api, client):
    mock_api.get("/").respond(200, json=STATUS_JSON)

    result = await client.system.status()

    assert isinstance(result, ServerStatus)
    assert result.status == "OK"
    assert result.authenticated is True
    assert result.versions.obsidian == "1.7.7"
    assert result.versions.self_ == "3.2.0"


async def test_openapi(mock_api, client):
    mock_api.get("/openapi.yaml").respond(200, text="openapi: 3.0.2")

    result = await client.system.openapi()

    assert result == "openapi: 3.0.2"


async def test_status_authentication_error(mock_api, client):
    mock_api.get("/").respond(401, json={"message": "Unauthorized"})
    with pytest.raises(AuthenticationError):
        await client.system.status()


async def test_openapi_server_error(mock_api, client):
    mock_api.get("/openapi.yaml").respond(500, json={"message": "Internal error"})
    with pytest.raises(APIError):
        await client.system.openapi()
