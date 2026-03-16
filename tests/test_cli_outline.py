from __future__ import annotations

import json

OUTLINE = [
    {"level": 1, "text": "Introduction", "position": 0},
    {"level": 2, "text": "Setup", "position": 50},
    {"level": 2, "text": "Usage", "position": 120},
]


async def test_get(cli):
    cli._execute.return_value = json.dumps(OUTLINE)
    result = await cli.outline.get("notes/guide.md")
    assert result == OUTLINE
    cli._execute.assert_awaited_once_with("outline", params={"file": "notes/guide.md"})
