import httpx
import pytest

from aiobsidian._exceptions import NotFoundError
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


async def test_get_not_found(mock_api, client):
    mock_api.get("/active/").respond(404, json={"message": "No active file"})

    with pytest.raises(NotFoundError) as exc_info:
        await client.active.get()

    assert exc_info.value.status_code == 404


async def test_append_sends_content_and_header(mock_api, client):
    route = mock_api.post("/active/").respond(204)
    await client.active.append("extra text")
    request: httpx.Request = route.calls[0].request
    assert request.content == b"extra text"
    assert request.headers["content-type"] == "text/markdown"


async def test_patch_custom_delimiter(mock_api, client):
    route = mock_api.patch("/active/").respond(200)
    await client.active.patch(
        "content",
        operation=PatchOperation.APPEND,
        target_type=TargetType.HEADING,
        target="A > B",
        target_delimiter=">",
    )
    assert route.calls[0].request.headers["target-delimiter"] == ">"


async def test_patch_non_ascii_target(mock_api, client):
    route = mock_api.patch("/active/").respond(200)

    await client.active.patch(
        "content",
        operation=PatchOperation.REPLACE,
        target_type=TargetType.HEADING,
        target="Заголовок",
    )

    request: httpx.Request = route.calls[0].request
    raw_headers = {k.lower(): v for k, v in request.headers.raw}
    assert raw_headers[b"target"] == "Заголовок".encode()
