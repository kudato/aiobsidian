from __future__ import annotations

import json

TABS = [
    {"file": "note.md", "active": True},
    {"file": "todo.md", "active": False},
]

RECENTS = [
    {"file": "note.md", "lastOpened": "2026-03-28T10:00:00Z"},
    {"file": "old.md", "lastOpened": "2026-03-27T09:00:00Z"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TABS)
    result = await cli.tabs.list()
    assert result == TABS
    cli._execute.assert_awaited_once_with("tabs")


async def test_open_file(cli):
    cli._execute.return_value = ""
    await cli.tabs.open(file="note.md")
    cli._execute.assert_awaited_once_with("tab:open", params={"file": "note.md"})


async def test_open_view(cli):
    cli._execute.return_value = ""
    await cli.tabs.open(view="graph")
    cli._execute.assert_awaited_once_with("tab:open", params={"view": "graph"})


async def test_open_no_params(cli):
    cli._execute.return_value = ""
    await cli.tabs.open()
    cli._execute.assert_awaited_once_with("tab:open", params=None)


async def test_recents(cli):
    cli._execute.return_value = json.dumps(RECENTS)
    result = await cli.tabs.recents()
    assert result == RECENTS
    cli._execute.assert_awaited_once_with("recents")
