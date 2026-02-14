from aiobsidian.models.system import ServerStatus

STATUS_JSON = {
    "ok": "OK",
    "service": "Obsidian Local REST API",
    "authenticated": True,
    "versions": {"obsidian": "1.7.7", "self": "3.2.0"},
}


async def test_status(mock_api, client):
    mock_api.get("/").respond(200, json=STATUS_JSON)

    result = await client.system.status()

    assert isinstance(result, ServerStatus)
    assert result.authenticated is True
    assert result.versions.obsidian == "1.7.7"
    assert result.versions.self_ == "3.2.0"


async def test_openapi(mock_api, client):
    mock_api.get("/openapi.yaml").respond(200, text="openapi: 3.0.2")

    result = await client.system.openapi()

    assert result == "openapi: 3.0.2"
