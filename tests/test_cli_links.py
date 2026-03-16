from __future__ import annotations

import json

OUTGOING = [
    {"path": "notes/setup.md", "display": "setup"},
    {"path": "notes/config.md", "display": "config"},
]

INCOMING = [
    {"path": "projects/main.md", "display": "main"},
]

UNRESOLVED = [
    {"source": "notes/draft.md", "target": "missing-note"},
]

ORPHANS = [
    {"path": "archive/old.md", "name": "old"},
]


async def test_outgoing(cli):
    cli._execute.return_value = json.dumps(OUTGOING)
    result = await cli.links.outgoing("note.md")
    assert result == OUTGOING
    cli._execute.assert_awaited_once_with("links", params={"file": "note.md"})


async def test_incoming(cli):
    cli._execute.return_value = json.dumps(INCOMING)
    result = await cli.links.incoming("note.md")
    assert result == INCOMING
    cli._execute.assert_awaited_once_with("backlinks", params={"file": "note.md"})


async def test_unresolved(cli):
    cli._execute.return_value = json.dumps(UNRESOLVED)
    result = await cli.links.unresolved()
    assert result == UNRESOLVED
    cli._execute.assert_awaited_once_with("unresolved")


async def test_orphans(cli):
    cli._execute.return_value = json.dumps(ORPHANS)
    result = await cli.links.orphans()
    assert result == ORPHANS
    cli._execute.assert_awaited_once_with("orphans")
