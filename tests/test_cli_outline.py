from __future__ import annotations

import json

OUTLINE = [
    {"level": 1, "heading": "Introduction", "line": 1},
    {"level": 2, "heading": "Setup", "line": 12},
]


async def test_get(cli):
    cli._execute.return_value = json.dumps(OUTLINE)
    result = await cli.outline.get("notes/guide.md")
    assert result == OUTLINE
    cli._execute.assert_awaited_once_with(
        "outline", params={"path": "notes/guide.md"}, output_format="json"
    )


async def test_get_no_headings(cli):
    cli._execute.return_value = "No headings found.\n"
    result = await cli.outline.get("notes/plain.md")
    assert result == []
