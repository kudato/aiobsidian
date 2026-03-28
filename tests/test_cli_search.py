from __future__ import annotations

import json


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.search.open("test query")
    cli._execute.assert_awaited_once_with("search:open", params={"query": "test query"})


async def test_query(cli):
    results = [{"file": "note.md", "score": 1.0}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("test query")
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "test query"}, flags=None
    )


async def test_query_empty(cli):
    cli._execute.return_value = json.dumps([])
    result = await cli.search.query("nothing")
    assert result == []


async def test_query_with_path(cli):
    results = [{"file": "notes/a.md", "score": 0.8}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("test", path="notes")
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "test", "path": "notes"}, flags=None
    )


async def test_query_with_limit(cli):
    results = [{"file": "note.md", "score": 1.0}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("test", limit=5)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "test", "limit": "5"}, flags=None
    )


async def test_query_case_sensitive(cli):
    results = [{"file": "note.md", "score": 1.0}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("Test", case=True)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "Test"}, flags=["--case"]
    )


async def test_query_with_matches(cli):
    results = [{"file": "note.md", "score": 1.0, "matches": []}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("test", matches=True)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "test"}, flags=["--matches"]
    )


async def test_query_all_params(cli):
    results = [{"file": "note.md", "score": 1.0}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query(
        "test", path="notes", limit=10, case=True, matches=True
    )
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search",
        params={"query": "test", "path": "notes", "limit": "10"},
        flags=["--case", "--matches"],
    )


async def test_context(cli):
    results = [{"file": "note.md", "line": 5, "context": ["line4", "match", "line6"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context("test query")
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context", params={"query": "test query"}, flags=None
    )


async def test_context_with_lines(cli):
    results = [{"file": "note.md", "line": 5, "context": ["match"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context("test query", lines=3)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context", params={"query": "test query", "lines": "3"}, flags=None
    )


async def test_context_with_path(cli):
    results = [{"file": "notes/a.md", "line": 1, "context": ["match"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context("test", path="notes")
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "path": "notes"},
        flags=None,
    )


async def test_context_with_limit(cli):
    results = [{"file": "note.md", "line": 1, "context": ["match"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context("test", limit=5)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "limit": "5"},
        flags=None,
    )


async def test_context_case_sensitive(cli):
    results = [{"file": "note.md", "line": 1, "context": ["match"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context("Test", case=True)
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context", params={"query": "Test"}, flags=["--case"]
    )


async def test_context_all_params(cli):
    results = [{"file": "note.md", "line": 1, "context": ["match"]}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.context(
        "test", lines=2, path="notes", limit=10, case=True
    )
    assert result == results
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "lines": "2", "path": "notes", "limit": "10"},
        flags=["--case"],
    )
