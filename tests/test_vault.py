from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError

from aiobsidian._exceptions import AuthenticationError, NotFoundError
from aiobsidian._types import ContentType, PatchOperation, TargetType
from aiobsidian.models.vault import DocumentMap, NoteJson

NOTE_JSON = {
    "content": "# Hello\nWorld",
    "frontmatter": {"title": "Hello"},
    "tags": ["greeting"],
    "path": "notes/hello.md",
    # The plugin passes Obsidian's own record on untouched, and Obsidian
    # keeps the two moments as whole milliseconds since the epoch.
    "stat": {"ctime": 1786836399339, "mtime": 1786922799339, "size": 42},
}

DOC_MAP_JSON = {
    "headings": ["Hello", "Hello::Details"],
    "blocks": ["abc123"],
    "frontmatterFields": ["title"],
}


async def test_read_markdown(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, text="# Hello")

    result = await client.vault.read("hello.md")

    assert result == "# Hello"


async def test_read_note_json(mock_api, client):
    mock_api.get("/vault/hello.md").respond(200, json=NOTE_JSON)

    result = await client.vault.read("hello.md", content_type=ContentType.NOTE_JSON)

    assert isinstance(result, NoteJson)
    assert result.path == "notes/hello.md"
    assert result.stat.size == 42
    assert result.stat.created == datetime(2026, 8, 15, 23, 26, 39, 339000, tzinfo=UTC)
    assert result.stat.modified == datetime(2026, 8, 16, 23, 26, 39, 339000, tzinfo=UTC)


async def test_read_note_json_with_a_fraction_of_a_millisecond(mock_api, client):
    # Obsidian rounds the file system record before the plugin ever sees
    # it, so a fraction is not a moment it keeps.
    stat = {**NOTE_JSON["stat"], "ctime": 1786836399339.5}
    mock_api.get("/vault/hello.md").respond(200, json={**NOTE_JSON, "stat": stat})

    with pytest.raises(ValidationError):
        await client.vault.read("hello.md", content_type=ContentType.NOTE_JSON)


async def test_read_note_json_with_a_moment_that_names_no_zone(mock_api, client):
    # The rule the CLI's record is held to, which this one shares: a
    # moment written without a zone leaves no telling which one it was
    # written in, so it is refused rather than read as UTC.
    stat = {**NOTE_JSON["stat"], "ctime": "2026-08-15T23:26:39"}
    mock_api.get("/vault/hello.md").respond(200, json={**NOTE_JSON, "stat": stat})

    with pytest.raises(ValidationError):
        await client.vault.read("hello.md", content_type=ContentType.NOTE_JSON)


async def test_read_document_map(mock_api, client):
    route = mock_api.get("/vault/hello.md").respond(200, json=DOC_MAP_JSON)

    result = await client.vault.read("hello.md", content_type=ContentType.DOCUMENT_MAP)

    assert isinstance(result, DocumentMap)
    assert result.headings == ["Hello", "Hello::Details"]
    assert result.blocks == ["abc123"]
    assert result.frontmatter_fields == ["title"]
    assert route.calls[0].request.headers["markdown-patch-version"] == "1"


async def test_read_markdown_omits_patch_version(mock_api, client):
    route = mock_api.get("/vault/hello.md").respond(200, text="# Hello")

    await client.vault.read("hello.md")

    assert "markdown-patch-version" not in route.calls[0].request.headers


def test_document_map_populate_by_name():
    result = DocumentMap(headings=[], blocks=[], frontmatter_fields=["title"])

    assert result.frontmatter_fields == ["title"]


async def test_write(mock_api, client):
    route = mock_api.put("/vault/new.md").respond(204)

    await client.vault.write("new.md", "# New note")

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
    assert request.headers["markdown-patch-version"] == "1"
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

    assert result == ["note.md", "folder/"]


async def test_list_subdirectory(mock_api, client):
    mock_api.get("/vault/folder/").respond(200, json={"files": ["sub.md"]})

    result = await client.vault.list("folder")

    assert result == ["sub.md"]


async def test_read_not_found(mock_api, client):
    mock_api.get("/vault/missing.md").respond(404, json={"message": "File not found"})

    with pytest.raises(NotFoundError) as exc_info:
        await client.vault.read("missing.md")

    assert exc_info.value.status_code == 404


async def test_write_unauthorized(mock_api, client):
    mock_api.put("/vault/secret.md").respond(401, json={"message": "Unauthorized"})

    with pytest.raises(AuthenticationError) as exc_info:
        await client.vault.write("secret.md", "content")

    assert exc_info.value.status_code == 401


async def test_patch_prepend_to_block(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)

    await client.vault.patch(
        "note.md",
        "prepended text",
        operation=PatchOperation.PREPEND,
        target_type=TargetType.BLOCK,
        target="abc123",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["operation"] == "prepend"
    assert request.headers["target-type"] == "block"
    assert request.headers["target"] == "abc123"


async def test_read_sends_accept_header(mock_api, client):
    route = mock_api.get("/vault/note.md").respond(200, text="# Hello")
    await client.vault.read("note.md")
    assert route.calls[0].request.headers["accept"] == "text/markdown"


async def test_append_sends_content_and_header(mock_api, client):
    route = mock_api.post("/vault/note.md").respond(204)
    await client.vault.append("note.md", "appended text")
    request: httpx.Request = route.calls[0].request
    assert request.content == b"appended text"
    assert request.headers["content-type"] == "text/markdown"


async def test_patch_frontmatter_string_value(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        "My Title",
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="title",
    )
    request: httpx.Request = route.calls[0].request
    assert request.content == b"My Title"
    assert request.headers["content-type"] == "text/markdown"
    assert request.headers["target-type"] == "frontmatter"


async def test_patch_frontmatter_list_value(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        ["draft", "python"],
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="tags",
    )
    request: httpx.Request = route.calls[0].request
    assert request.content == b'["draft", "python"]'
    assert request.headers["content-type"] == "application/json"


async def test_patch_frontmatter_dict_value(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        {"by": "kudato"},
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="meta",
    )
    assert route.calls[0].request.content == b'{"by": "kudato"}'


async def test_patch_frontmatter_number_value(mock_api, client):
    route = mock_api.patch("/vault/note.md").respond(200)
    await client.vault.patch(
        "note.md",
        42,
        operation=PatchOperation.REPLACE,
        target_type=TargetType.FRONTMATTER,
        target="rating",
    )
    assert route.calls[0].request.content == b"42"


async def test_patch_heading_rejects_non_string(client):
    with pytest.raises(TypeError, match="heading"):
        await client.vault.patch(
            "note.md",
            ["a", "b"],
            operation=PatchOperation.REPLACE,
            target_type=TargetType.HEADING,
            target="Section",
        )


async def test_patch_block_rejects_non_string(client):
    with pytest.raises(TypeError, match="block"):
        await client.vault.patch(
            "note.md",
            {"a": 1},
            operation=PatchOperation.REPLACE,
            target_type=TargetType.BLOCK,
            target="abc123",
        )


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
    assert result == ["a.md"]


async def test_read_path_with_spaces(mock_api, client):
    route = mock_api.get("/vault/notes/my%20note.md").respond(200, text="# Spaced")

    result = await client.vault.read("notes/my note.md")

    assert result == "# Spaced"
    assert route.called


async def test_read_path_with_unicode(mock_api, client):
    encoded = (
        "/vault/%D0%B7%D0%B0%D0%BC%D0%B5%D1%82%D0%BA%D0%B8"
        "/%D0%B7%D0%B0%D0%BC%D0%B5%D1%82%D0%BA%D0%B0.md"
    )
    route = mock_api.get(encoded).respond(200, text="# Кириллица")

    result = await client.vault.read("заметки/заметка.md")

    assert result == "# Кириллица"
    assert route.called


async def test_read_deep_nested_path(mock_api, client):
    route = mock_api.get("/vault/a/b/c/d/file.md").respond(200, text="# Deep")

    result = await client.vault.read("a/b/c/d/file.md")

    assert result == "# Deep"
    assert route.called


async def test_read_path_with_hash(mock_api, client):
    route = mock_api.get("/vault/scratch/note%23hash.md").respond(200, text="# Hash")

    result = await client.vault.read("scratch/note#hash.md")

    assert result == "# Hash"
    assert route.called


async def test_read_path_with_percent(mock_api, client):
    route = mock_api.get("/vault/scratch/note%2050%25.md").respond(200, text="# Half")

    result = await client.vault.read("scratch/note 50%.md")

    assert result == "# Half"
    assert route.called


async def test_read_path_with_question_mark(mock_api, client):
    route = mock_api.get("/vault/scratch/q%3Fmark.md").respond(200, text="# Query")

    result = await client.vault.read("scratch/q?mark.md")

    assert result == "# Query"
    assert route.called


async def test_write_path_with_hash(mock_api, client):
    route = mock_api.put("/vault/scratch/note%23hash.md").respond(204)

    await client.vault.write("scratch/note#hash.md", "OVERWRITTEN")

    assert route.called
    assert route.calls[0].request.url.raw_path == b"/vault/scratch/note%23hash.md"


async def test_delete_path_with_hash(mock_api, client):
    route = mock_api.delete("/vault/scratch/note%23hash.md").respond(204)

    await client.vault.delete("scratch/note#hash.md")

    assert route.called


async def test_read_leading_slash(mock_api, client):
    route = mock_api.get("/vault/notes/a.md").respond(200, text="# A")

    result = await client.vault.read("/notes/a.md")

    assert result == "# A"
    assert route.called


async def test_write_leading_slash(mock_api, client):
    route = mock_api.put("/vault/notes/a.md").respond(204)

    await client.vault.write("/notes/a.md", "content")

    assert route.called


async def test_append_leading_slash(mock_api, client):
    route = mock_api.post("/vault/notes/a.md").respond(204)

    await client.vault.append("/notes/a.md", "content")

    assert route.called


async def test_patch_leading_slash(mock_api, client):
    route = mock_api.patch("/vault/notes/a.md").respond(200)

    await client.vault.patch(
        "/notes/a.md",
        "content",
        operation=PatchOperation.APPEND,
        target_type=TargetType.HEADING,
        target="Section",
    )

    assert route.called


async def test_delete_leading_slash(mock_api, client):
    route = mock_api.delete("/vault/notes/a.md").respond(204)

    await client.vault.delete("/notes/a.md")

    assert route.called


async def test_list_path_with_hash(mock_api, client):
    mock_api.get("/vault/scratch/tag%23folder/").respond(200, json={"files": ["a.md"]})

    result = await client.vault.list("scratch/tag#folder")

    assert result == ["a.md"]


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


async def test_open(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.vault.open("notes/hello.md")

    assert route.called


async def test_open_new_leaf(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.vault.open("notes/hello.md", new_leaf=True)

    request: httpx.Request = route.calls[0].request
    assert "newLeaf=true" in str(request.url)


async def test_open_omits_new_leaf_by_default(mock_api, client):
    route = mock_api.post("/open/note.md").respond(200)

    await client.vault.open("note.md")

    assert "newLeaf" not in str(route.calls[0].request.url)


async def test_open_not_found(mock_api, client):
    mock_api.post("/open/missing.md").respond(404, json={"message": "File not found"})

    with pytest.raises(NotFoundError):
        await client.vault.open("missing.md")


async def test_open_path_with_question_mark(mock_api, client):
    route = mock_api.post("/open/scratch/q%3Fmark.md").respond(200)

    await client.vault.open("scratch/q?mark.md")

    assert route.called
    assert route.calls[0].request.url.raw_path == b"/open/scratch/q%3Fmark.md"


async def test_open_leading_slash(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.vault.open("/notes/hello.md")

    assert route.called
