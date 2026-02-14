import httpx
import pytest

from aiobsidian._exceptions import NotFoundError
from aiobsidian._types import ContentType, PatchOperation, Period, TargetType
from aiobsidian.models.vault import NoteJson

NOTE_JSON = {
    "content": "# Daily",
    "frontmatter": {},
    "tags": [],
    "path": "daily/2026-02-14.md",
    "stat": {"ctime": 1700000000, "mtime": 1700000100, "size": 10},
}


async def test_get_markdown(mock_api, client):
    mock_api.get("/periodic/daily/").respond(200, text="# Daily note")

    result = await client.periodic.get(Period.DAILY)

    assert result == "# Daily note"


async def test_get_note_json(mock_api, client):
    mock_api.get("/periodic/weekly/").respond(200, json=NOTE_JSON)

    result = await client.periodic.get(
        Period.WEEKLY, content_type=ContentType.NOTE_JSON
    )

    assert isinstance(result, NoteJson)


async def test_update(mock_api, client):
    route = mock_api.put("/periodic/monthly/").respond(204)

    await client.periodic.update(Period.MONTHLY, "# Month")

    assert route.called


async def test_append(mock_api, client):
    route = mock_api.post("/periodic/daily/").respond(204)

    await client.periodic.append(Period.DAILY, "new entry")

    assert route.called


async def test_patch(mock_api, client):
    route = mock_api.patch("/periodic/daily/").respond(200)

    await client.periodic.patch(
        Period.DAILY,
        "patched",
        operation=PatchOperation.APPEND,
        target_type=TargetType.HEADING,
        target="Tasks",
    )

    request: httpx.Request = route.calls[0].request
    assert request.headers["operation"] == "append"


async def test_delete(mock_api, client):
    route = mock_api.delete("/periodic/yearly/").respond(204)

    await client.periodic.delete(Period.YEARLY)

    assert route.called


async def test_get_not_found(mock_api, client):
    mock_api.get("/periodic/daily/").respond(
        404, json={"message": "No daily note found"}
    )

    with pytest.raises(NotFoundError) as exc_info:
        await client.periodic.get(Period.DAILY)

    assert exc_info.value.status_code == 404


async def test_get_quarterly(mock_api, client):
    mock_api.get("/periodic/quarterly/").respond(200, text="# Q1 2026")

    result = await client.periodic.get(Period.QUARTERLY)

    assert result == "# Q1 2026"
