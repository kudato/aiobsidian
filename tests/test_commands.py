import pytest

from aiobsidian._exceptions import APIParseError, NotFoundError
from aiobsidian.models.commands import Command


async def test_list_commands(mock_api, client):
    mock_api.get("/commands/").respond(
        200,
        json={
            "commands": [
                {"id": "global-search:open", "name": "Search: Search in all files"},
                {"id": "graph:open", "name": "Graph view: Open graph view"},
            ]
        },
    )

    result = await client.commands.list()

    assert len(result) == 2
    assert isinstance(result[0], Command)
    assert result[0].id == "global-search:open"


async def test_list_commands_without_the_envelope(mock_api, client):
    # A wrapper, but not the documented one: reading `commands` off it
    # used to escape as a bare KeyError.
    mock_api.get("/commands/").respond(200, json={"items": []})

    with pytest.raises(APIParseError) as exc_info:
        await client.commands.list()

    error = exc_info.value
    assert error.method == "GET"
    assert error.url.endswith("/commands/")
    assert "items" in error.body


async def test_list_commands_that_are_not_json(mock_api, client):
    mock_api.get("/commands/").respond(200, text="<html>maintenance</html>")

    with pytest.raises(APIParseError):
        await client.commands.list()


async def test_execute_command(mock_api, client):
    route = mock_api.post("/commands/graph:open/").respond(204)

    await client.commands.execute("graph:open")

    assert route.called


async def test_execute_not_found(mock_api, client):
    mock_api.post("/commands/nonexistent/").respond(
        404, json={"message": "Command not found"}
    )

    with pytest.raises(NotFoundError) as exc_info:
        await client.commands.execute("nonexistent")

    assert exc_info.value.status_code == 404
