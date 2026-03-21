from __future__ import annotations

import json

SNIPPETS = [
    {"name": "custom-styles", "enabled": True},
    {"name": "hide-sidebar", "enabled": False},
]

ENABLED_SNIPPETS = [
    {"name": "custom-styles"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(SNIPPETS)
    result = await cli.snippets.list()
    assert result == SNIPPETS
    cli._execute.assert_awaited_once_with("snippets")


async def test_enabled(cli):
    cli._execute.return_value = json.dumps(ENABLED_SNIPPETS)
    result = await cli.snippets.enabled()
    assert result == ENABLED_SNIPPETS
    cli._execute.assert_awaited_once_with("snippets:enabled")


async def test_enable(cli):
    cli._execute.return_value = ""
    await cli.snippets.enable("custom-styles")
    cli._execute.assert_awaited_once_with(
        "snippet:enable", params={"name": "custom-styles"}
    )


async def test_disable(cli):
    cli._execute.return_value = ""
    await cli.snippets.disable("custom-styles")
    cli._execute.assert_awaited_once_with(
        "snippet:disable", params={"name": "custom-styles"}
    )
