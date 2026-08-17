from __future__ import annotations

import json

from aiobsidian.models.outline import Heading

# `outline` is one of the few commands that really serialises: asked for
# JSON it prints the level and the line as numbers rather than as text.
OUTLINE = [
    {"level": 1, "heading": "Introduction", "line": 1},
    {"level": 2, "heading": "Setup", "line": 12},
]


async def test_get(cli):
    cli._execute.return_value = json.dumps(OUTLINE)
    result = await cli.outline.get("notes/guide.md")
    assert result == [
        Heading(level=1, text="Introduction", line=1),
        Heading(level=2, text="Setup", line=12),
    ]
    cli._execute.assert_awaited_once_with(
        "outline", params={"path": "notes/guide.md"}, output_format="json"
    )


async def test_get_reports_numbers_as_numbers(cli):
    cli._execute.return_value = json.dumps(OUTLINE)
    result = await cli.outline.get("notes/guide.md")
    assert isinstance(result[0].level, int)
    assert isinstance(result[0].line, int)


async def test_get_no_headings(cli):
    cli._execute.return_value = "No headings found.\n"
    result = await cli.outline.get("notes/plain.md")
    assert result == []
