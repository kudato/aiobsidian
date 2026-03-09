from __future__ import annotations

import json


async def test_query(cli):
    results = [{"file": "note.md", "score": 1.0}]
    cli._execute.return_value = json.dumps(results)
    result = await cli.search.query("test query")
    assert result == results
    cli._execute.assert_awaited_once_with("search", params={"query": "test query"})


async def test_query_empty(cli):
    cli._execute.return_value = json.dumps([])
    result = await cli.search.query("nothing")
    assert result == []
