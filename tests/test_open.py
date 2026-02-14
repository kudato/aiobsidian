import httpx


async def test_open_file(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.open("notes/hello.md")

    assert route.called


async def test_open_file_new_leaf(mock_api, client):
    route = mock_api.post("/open/notes/hello.md").respond(200)

    await client.open("notes/hello.md", new_leaf=True)

    request: httpx.Request = route.calls[0].request
    assert "newLeaf=true" in str(request.url)
