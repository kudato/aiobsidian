import httpx

from aiobsidian._types import ContentType, PatchOperation, TargetType
from aiobsidian.models.vault import DocumentMap, NoteJson

NOTE_JSON = {
    "content": "# Active",
    "frontmatter": {},
    "tags": [],
    "path": "active.md",
    "stat": {"ctime": 1700000000, "mtime": 1700000100, "size": 10},
}

DOC_MAP_JSON = {
    "headings": ["# Active"],
    "blocks": ["^def456"],
    "frontmatterFields": [],
}


async def test_get_markdown(mock_api, client):
    mock_api.get("/active/").respond(200, text="# Active note")

    result = await client.active.get()

    assert result == "# Active note"


async def test_get_note_json(mock_api, client):
    mock_api.get("/active/").respond(200, json=NOTE_JSON)

    result = await client.active.get(content_type=ContentType.NOTE_JSON)

    assert isinstance(result, NoteJson)
    assert result.path == "active.md"


async def test_update(mock_api, client):
    route = mock_api.put("/active/").respond(204)

    await client.active.update("# Updated")

    request: httpx.Request = route.calls[0].request
    assert request.content == b"# Updated"


async def test_append(mock_api, client):
    route = mock_api.post("/active/").respond(204)

    await client.active.append("extra text")

    assert route.called


async def test_patch(mock_api, client):
    route = mock_api.patch("/active/").respond(200)

    await client.active.patch(
        "value",
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="title",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["content-type"] == "application/json"
    assert request.headers["target-type"] == "frontmatter"


async def test_delete(mock_api, client):
    route = mock_api.delete("/active/").respond(204)

    await client.active.delete()

    assert route.called


async def test_get_document_map(mock_api, client):
    mock_api.get("/active/").respond(200, json=DOC_MAP_JSON)

    result = await client.active.get(content_type=ContentType.DOCUMENT_MAP)

    assert isinstance(result, DocumentMap)
    assert result.headings == ["# Active"]


async def test_get_json_convenience(mock_api, client):
    mock_api.get("/active/").respond(200, json=NOTE_JSON)

    result = await client.active.get_json()

    assert isinstance(result, NoteJson)
    assert result.path == "active.md"


async def test_get_document_map_convenience(mock_api, client):
    mock_api.get("/active/").respond(200, json=DOC_MAP_JSON)

    result = await client.active.get_document_map()

    assert isinstance(result, DocumentMap)
    assert result.headings == ["# Active"]
