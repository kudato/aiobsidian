import httpx
import pytest

from aiobsidian._exceptions import AuthenticationError, NotFoundError
from aiobsidian._types import ContentType, PatchOperation, TargetType
from aiobsidian.models.vault import DocumentMap, NoteJson, VaultDirectory

NOTE_JSON = {
    "content": "# Hello\nWorld",
    "frontmatter": {"title": "Hello"},
    "tags": ["greeting"],
    "path": "notes/hello.md",
    "stat": {"ctime": 1700000000, "mtime": 1700000100, "size": 42},
}

DOC_MAP_JSON = {
    "headings": ["# Hello"],
    "blocks": ["^abc123"],
    "frontmatterFields": ["title"],
}


async def test_get_markdown(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, text="# Hello")

    result = await client.vault.get("hello.md")

    assert result == "# Hello"


async def test_get_note_json(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, json=NOTE_JSON)

    result = await client.vault.get("hello.md", content_type=ContentType.NOTE_JSON)

    assert isinstance(result, NoteJson)
    assert result.path == "notes/hello.md"
    assert result.stat.size == 42


async def test_get_document_map(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, json=DOC_MAP_JSON)

    result = await client.vault.get("hello.md", content_type=ContentType.DOCUMENT_MAP)

    assert isinstance(result, DocumentMap)
    assert result.headings == ["# Hello"]


async def test_create(mock_api, client):
    route = mock_api.put("/vault/new.md").respond(204)

    await client.vault.create("new.md", "# New note")

    assert route.called
    request: httpx.Request = route.calls[0].request
    assert request.content == b"# New note"


async def test_append(mock_api, client):
    route = mock_api.post("/vault/note.md").respond(204)

    await client.vault.append("note.md", "appended text")

    assert route.called


async def test_patch(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)

    await client.vault.patch(
        "note.md",
        "new content",
        operation=PatchOperation.REPLACE,
        target_type=TargetType.HEADING,
        target="Section 1",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["operation"] == "replace"
    assert request.headers["target-type"] == "heading"
    assert request.headers["target"] == "Section 1"


async def test_delete(mock_api, client):
    route = mock_api.delete("/vault/old.md").respond(204)

    await client.vault.delete("old.md")

    assert route.called


async def test_list_root(mock_api, client):
    mock_api.get("/vault/").respond(200, json={"files": ["note.md", "folder/"]})

    result = await client.vault.list()

    assert isinstance(result, VaultDirectory)
    assert "note.md" in result.files


async def test_list_subdirectory(mock_api, client):
    mock_api.get("/vault/folder/").respond(200, json={"files": ["sub.md"]})

    result = await client.vault.list("folder")

    assert result.files == ["sub.md"]


async def test_get_json(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, json=NOTE_JSON)

    result = await client.vault.get_json("hello.md")

    assert isinstance(result, NoteJson)
    assert result.path == "notes/hello.md"
    assert result.stat.size == 42


async def test_get_document_map_convenience(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, json=DOC_MAP_JSON)

    result = await client.vault.get_document_map("hello.md")

    assert isinstance(result, DocumentMap)
    assert result.headings == ["# Hello"]


async def test_get_not_found(mock_api, client):
    mock_api.get("/vault/missing.md").respond(404, json={"message": "File not found"})

    with pytest.raises(NotFoundError) as exc_info:
        await client.vault.get("missing.md")

    assert exc_info.value.status_code == 404


async def test_create_unauthorized(mock_api, client):
    mock_api.put("/vault/secret.md").respond(401, json={"message": "Unauthorized"})

    with pytest.raises(AuthenticationError) as exc_info:
        await client.vault.create("secret.md", "content")

    assert exc_info.value.status_code == 401


async def test_patch_prepend_to_block(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)

    await client.vault.patch(
        "note.md",
        "prepended text",
        operation=PatchOperation.PREPEND,
        target_type=TargetType.BLOCK,
        target="^abc123",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["operation"] == "prepend"
    assert request.headers["target-type"] == "block"
    assert request.headers["target"] == "^abc123"
