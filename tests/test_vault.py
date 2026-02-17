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
    assert result.frontmatter_fields == ["title"]


async def test_update(mock_api, client):
    route = mock_api.put("/vault/new.md").respond(204)

    await client.vault.update("new.md", "# New note")

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
    assert request.headers["target"] == "Section%201"
    assert request.headers["content-type"] == "text/markdown"
    assert request.headers["target-delimiter"] == "::"


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


async def test_get_not_found(mock_api, client):
    mock_api.get("/vault/missing.md").respond(404, json={"message": "File not found"})

    with pytest.raises(NotFoundError) as exc_info:
        await client.vault.get("missing.md")

    assert exc_info.value.status_code == 404


async def test_update_unauthorized(mock_api, client):
    mock_api.put("/vault/secret.md").respond(401, json={"message": "Unauthorized"})

    with pytest.raises(AuthenticationError) as exc_info:
        await client.vault.update("secret.md", "content")

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
    assert request.headers["target"] == "%5Eabc123"


async def test_get_sends_accept_header(mock_api, client):
    route = mock_api.get("/vault/note.md").respond(200, text="# Hello")
    await client.vault.get("note.md")
    assert route.calls[0].request.headers["accept"] == "text/markdown"


async def test_append_sends_content_and_header(mock_api, client):
    route = mock_api.post("/vault/note.md").respond(204)
    await client.vault.append("note.md", "appended text")
    request: httpx.Request = route.calls[0].request
    assert request.content == b"appended text"
    assert request.headers["content-type"] == "text/markdown"


async def test_patch_frontmatter_content_type(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        '{"title": "New"}',
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="title",
    )
    request: httpx.Request = route.calls[0].request
    assert request.headers["content-type"] == "application/json"
    assert request.headers["target-type"] == "frontmatter"


async def test_patch_custom_delimiter(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        "content",
        operation=PatchOperation.APPEND,
        target_type=TargetType.HEADING,
        target="A > B",
        target_delimiter=">",
    )
    request: httpx.Request = route.calls[0].request
    assert request.headers["target-delimiter"] == ">"
    assert request.headers["operation"] == "append"


async def test_list_strips_trailing_slashes(mock_api, client):
    mock_api.get("/vault/folder/").respond(200, json={"files": ["a.md"]})
    result = await client.vault.list("/folder/")
    assert result.files == ["a.md"]


async def test_get_path_with_spaces(mock_api, client):
    route = mock_api.get("/vault/notes/my%20note.md").respond(200, text="# Spaced")

    result = await client.vault.get("notes/my note.md")

    assert result == "# Spaced"
    assert route.called


async def test_get_path_with_unicode(mock_api, client):
    encoded = (
        "/vault/%D0%B7%D0%B0%D0%BC%D0%B5%D1%82%D0%BA%D0%B8"
        "/%D0%B7%D0%B0%D0%BC%D0%B5%D1%82%D0%BA%D0%B0.md"
    )
    route = mock_api.get(encoded).respond(200, text="# Кириллица")

    result = await client.vault.get("заметки/заметка.md")

    assert result == "# Кириллица"
    assert route.called


async def test_get_deep_nested_path(mock_api, client):
    route = mock_api.get("/vault/a/b/c/d/file.md").respond(200, text="# Deep")

    result = await client.vault.get("a/b/c/d/file.md")

    assert result == "# Deep"
    assert route.called


async def test_patch_non_ascii_target(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)

    await client.vault.patch(
        "note.md",
        "content",
        operation=PatchOperation.REPLACE,
        target_type=TargetType.HEADING,
        target="Заметки",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["target"] == "%D0%97%D0%B0%D0%BC%D0%B5%D1%82%D0%BA%D0%B8"
