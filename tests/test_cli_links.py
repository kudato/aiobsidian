from __future__ import annotations

import json

INCOMING = [
    {"file": "projects/main.md"},
]

UNRESOLVED = [
    {"link": "missing-note"},
]


async def test_outgoing(cli):
    cli._execute.return_value = "notes/setup.md\nnotes/config.md\n"
    result = await cli.links.outgoing("note.md")
    assert result == ["notes/setup.md", "notes/config.md"]
    cli._execute.assert_awaited_once_with("links", params={"path": "note.md"})


async def test_outgoing_without_links(cli):
    cli._execute.return_value = "No links found.\n"
    result = await cli.links.outgoing("note.md")
    assert result == []


async def test_incoming(cli):
    cli._execute.return_value = json.dumps(INCOMING)
    result = await cli.links.incoming("note.md")
    assert result == INCOMING
    cli._execute.assert_awaited_once_with(
        "backlinks", params={"path": "note.md"}, flags=None, output_format="json"
    )


async def test_incoming_with_counts(cli):
    cli._execute.return_value = json.dumps(INCOMING)
    result = await cli.links.incoming("note.md", counts=True)
    assert result == INCOMING
    cli._execute.assert_awaited_once_with(
        "backlinks",
        params={"path": "note.md"},
        flags=["counts"],
        output_format="json",
    )


async def test_incoming_without_backlinks(cli):
    cli._execute.return_value = "No backlinks found.\n"
    result = await cli.links.incoming("note.md")
    assert result == []


async def test_unresolved(cli):
    cli._execute.return_value = json.dumps(UNRESOLVED)
    result = await cli.links.unresolved()
    assert result == UNRESOLVED
    cli._execute.assert_awaited_once_with("unresolved", output_format="json")


async def test_orphans(cli):
    cli._execute.return_value = "archive/old.md\nnotes/orphan.md\n"
    result = await cli.links.orphans()
    assert result == ["archive/old.md", "notes/orphan.md"]
    cli._execute.assert_awaited_once_with("orphans")


async def test_deadends(cli):
    cli._execute.return_value = "notes/leaf.md\n"
    result = await cli.links.deadends()
    assert result == ["notes/leaf.md"]
    cli._execute.assert_awaited_once_with("deadends")
