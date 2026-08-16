import json

import httpx
import pytest

from aiobsidian._exceptions import APIError
from aiobsidian.models.search import SearchResult

SIMPLE_RESULTS = [
    {
        "filename": "notes/hello.md",
        "score": 0.95,
        "matches": [
            {"match": {"start": 0, "end": 5}, "context": "Hello world"},
        ],
    }
]

JSONLOGIC_RESULTS = [{"filename": "games/elden-ring.md", "result": {"rating": 10}}]

JSONLOGIC_BOOL_RESULTS = [
    {"filename": "scratch/lib.md", "result": True},
    {"filename": "scratch/fm.md", "result": True},
]


async def test_simple_search(mock_api, client):
    mock_api.post("/search/simple/").respond(200, json=SIMPLE_RESULTS)

    results = await client.search.simple("hello")

    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].score == 0.95
    assert results[0].matches[0].context == "Hello world"


async def test_simple_search_params(mock_api, client):
    route = mock_api.post("/search/simple/").respond(200, json=[])

    await client.search.simple("test", context_length=200)

    request: httpx.Request = route.calls[0].request
    assert "contextLength=200" in str(request.url)


async def test_jsonlogic_search(mock_api, client):
    route = mock_api.post("/search/").respond(200, json=JSONLOGIC_RESULTS)
    query = {"===": [{"var": "frontmatter.url"}, "https://example.com"]}

    results = await client.search.jsonlogic(query)

    assert len(results) == 1
    assert results[0].result == {"rating": 10}
    request: httpx.Request = route.calls[0].request
    assert request.headers["content-type"] == "application/vnd.olrapi.jsonlogic+json"


async def test_jsonlogic_boolean_result(mock_api, client):
    mock_api.post("/search/").respond(200, json=JSONLOGIC_BOOL_RESULTS)

    results = await client.search.jsonlogic(
        {"==": [{"var": "frontmatter.title"}, "Welcome"]}
    )

    assert [r.result for r in results] == [True, True]
    assert all(isinstance(r.result, bool) for r in results)


async def test_jsonlogic_string_result(mock_api, client):
    mock_api.post("/search/").respond(
        200, json=[{"filename": "notes/a.md", "result": "My Title"}]
    )

    results = await client.search.jsonlogic({"var": "frontmatter.title"})

    assert results[0].result == "My Title"


async def test_jsonlogic_number_result(mock_api, client):
    mock_api.post("/search/").respond(
        200, json=[{"filename": "notes/a.md", "result": 113}]
    )

    results = await client.search.jsonlogic({"var": "stat.size"})

    assert results[0].result == 113
    assert isinstance(results[0].result, int)


async def test_jsonlogic_array_result(mock_api, client):
    mock_api.post("/search/").respond(
        200, json=[{"filename": "notes/a.md", "result": ["x", "y"]}]
    )

    results = await client.search.jsonlogic({"var": "tags"})

    assert results[0].result == ["x", "y"]


async def test_jsonlogic_null_result(mock_api, client):
    mock_api.post("/search/").respond(
        200, json=[{"filename": "notes/a.md", "result": None}]
    )

    results = await client.search.jsonlogic({"var": "frontmatter.missing"})

    assert results[0].result is None


async def test_simple_search_server_error(mock_api, client):
    mock_api.post("/search/simple/").respond(
        500, json={"message": "Internal server error"}
    )

    with pytest.raises(APIError) as exc_info:
        await client.search.simple("query")

    assert exc_info.value.status_code == 500


async def test_jsonlogic_sends_json_body(mock_api, client):
    route = mock_api.post("/search/").respond(200, json=[])
    query = {"glob": ["*.md"]}
    await client.search.jsonlogic(query)
    assert json.loads(route.calls[0].request.content) == {"glob": ["*.md"]}
