from __future__ import annotations

import json

from aiobsidian.models.search import MatchedFile, MatchedLine

RESULTS = ["welcome.md", "notes/linked.md"]

# `search:context` really serialises, so the line numbers arrive as
# numbers. A file can match without any line matching, which is what the
# CLI prints when the query hit the name or the frontmatter.
CONTEXT_RESULTS = [
    {"file": "welcome.md", "matches": [{"line": 2, "text": "title: Welcome"}]},
    {
        "file": "notes/linked.md",
        "matches": [{"line": 7, "text": "Back to [[welcome]]."}],
    },
    {"file": "notes/empty-match.md", "matches": []},
]

PARSED_CONTEXT = [
    MatchedFile(
        file="welcome.md", matches=[MatchedLine(line=2, text="title: Welcome")]
    ),
    MatchedFile(
        file="notes/linked.md",
        matches=[MatchedLine(line=7, text="Back to [[welcome]].")],
    ),
    MatchedFile(file="notes/empty-match.md", matches=[]),
]


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.search.open("test query")
    cli._execute.assert_awaited_once_with("search:open", params={"query": "test query"})


async def test_query_returns_paths(cli):
    cli._execute.return_value = json.dumps(RESULTS)
    result = await cli.search.query("test query")
    assert result == RESULTS
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "test query"}, flags=None, output_format="json"
    )


async def test_query_no_matches(cli):
    cli._execute.return_value = "No matches found.\n"
    result = await cli.search.query("nothing")
    assert result == []


async def test_query_with_path(cli):
    cli._execute.return_value = json.dumps(RESULTS)
    result = await cli.search.query("test", path="notes")
    assert result == RESULTS
    cli._execute.assert_awaited_once_with(
        "search",
        params={"query": "test", "path": "notes"},
        flags=None,
        output_format="json",
    )


async def test_query_with_limit(cli):
    cli._execute.return_value = json.dumps(RESULTS)
    result = await cli.search.query("test", limit=5)
    assert result == RESULTS
    cli._execute.assert_awaited_once_with(
        "search",
        params={"query": "test", "limit": "5"},
        flags=None,
        output_format="json",
    )


async def test_query_case_sensitive(cli):
    cli._execute.return_value = json.dumps(RESULTS)
    result = await cli.search.query("Test", case=True)
    assert result == RESULTS
    cli._execute.assert_awaited_once_with(
        "search", params={"query": "Test"}, flags=["case"], output_format="json"
    )


async def test_query_all_params(cli):
    cli._execute.return_value = json.dumps(RESULTS)
    result = await cli.search.query("test", path="notes", limit=10, case=True)
    assert result == RESULTS
    cli._execute.assert_awaited_once_with(
        "search",
        params={"query": "test", "path": "notes", "limit": "10"},
        flags=["case"],
        output_format="json",
    )


async def test_context(cli):
    cli._execute.return_value = json.dumps(CONTEXT_RESULTS)
    result = await cli.search.context("test query")
    assert result == PARSED_CONTEXT
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test query"},
        flags=None,
        output_format="json",
    )


async def test_context_no_matches(cli):
    cli._execute.return_value = "No matches found.\n"
    result = await cli.search.context("nothing")
    assert result == []


async def test_context_with_path(cli):
    cli._execute.return_value = json.dumps(CONTEXT_RESULTS)
    result = await cli.search.context("test", path="notes")
    assert result == PARSED_CONTEXT
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "path": "notes"},
        flags=None,
        output_format="json",
    )


async def test_context_with_limit(cli):
    cli._execute.return_value = json.dumps(CONTEXT_RESULTS)
    result = await cli.search.context("test", limit=5)
    assert result == PARSED_CONTEXT
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "limit": "5"},
        flags=None,
        output_format="json",
    )


async def test_context_case_sensitive(cli):
    cli._execute.return_value = json.dumps(CONTEXT_RESULTS)
    result = await cli.search.context("Test", case=True)
    assert result == PARSED_CONTEXT
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "Test"},
        flags=["case"],
        output_format="json",
    )


async def test_context_all_params(cli):
    cli._execute.return_value = json.dumps(CONTEXT_RESULTS)
    result = await cli.search.context("test", path="notes", limit=10, case=True)
    assert result == PARSED_CONTEXT
    cli._execute.assert_awaited_once_with(
        "search:context",
        params={"query": "test", "path": "notes", "limit": "10"},
        flags=["case"],
        output_format="json",
    )
