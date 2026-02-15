import httpx
import pytest

from aiobsidian._exceptions import NotFoundError


async def test_open_file(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.open.open("notes/hello.md")

    assert route.called


async def test_open_file_new_leaf(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.open.open("notes/hello.md", new_leaf=True)

    request: httpx.Request = route.calls[0].request
    assert "newLeaf=true" in str(request.url)


async def test_open_not_found(mock_api, client):
    mock_api.post("/open/missing.md").respond(404, json={"message": "File not found"})
    with pytest.raises(NotFoundError):
        await client.open.open("missing.md")


async def test_open_default_no_new_leaf_param(mock_api, client):
    route = mock_api.post("/open/note.md").respond(200)
    await client.open.open("note.md")
    assert "newLeaf" not in str(route.calls[0].request.url)
