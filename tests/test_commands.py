import pytest

from aiobsidian._exceptions import NotFoundError
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
