from __future__ import annotations

TABS_OUTPUT = "[markdown] welcome\n[search] Search\n"
RECENTS_OUTPUT = "notes/note.md\nnotes/old.md\n"


async def test_list(cli):
    cli._execute.return_value = TABS_OUTPUT
    result = await cli.tabs.list()
    assert result == ["[markdown] welcome", "[search] Search"]
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
    cli._execute.return_value = RECENTS_OUTPUT
    result = await cli.tabs.recents()
    assert result == ["notes/note.md", "notes/old.md"]
    cli._execute.assert_awaited_once_with("recents")


async def test_recent_count(cli):
    cli._execute.return_value = "2\n"
    result = await cli.tabs.recent_count()
    assert result == 2
    cli._execute.assert_awaited_once_with("recents", flags=["total"])


async def test_recent_count_when_there_are_none(cli):
    # Counted, the empty list is a zero rather than the "No recent
    # files." the listing answers with.
    cli._execute.return_value = "0\n"
    result = await cli.tabs.recent_count()
    assert result == 0
