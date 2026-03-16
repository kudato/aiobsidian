from __future__ import annotations

import json

THEMES = [
    {"name": "Default", "active": True},
    {"name": "Minimal", "active": False},
]

CURRENT_THEME = {"name": "Default", "mode": "dark"}


async def test_list(cli):
    cli._execute.return_value = json.dumps(THEMES)
    result = await cli.themes.list()
    assert result == THEMES
    cli._execute.assert_awaited_once_with("themes")


async def test_current(cli):
    cli._execute.return_value = json.dumps(CURRENT_THEME)
    result = await cli.themes.current()
    assert result == CURRENT_THEME
    cli._execute.assert_awaited_once_with("theme")


async def test_set(cli):
    cli._execute.return_value = ""
    await cli.themes.set("Minimal")
    cli._execute.assert_awaited_once_with("theme:set", params={"name": "Minimal"})


async def test_install(cli):
    cli._execute.return_value = ""
    await cli.themes.install("Minimal")
    cli._execute.assert_awaited_once_with("theme:install", params={"name": "Minimal"})


async def test_uninstall(cli):
    cli._execute.return_value = ""
    await cli.themes.uninstall("Minimal")
    cli._execute.assert_awaited_once_with("theme:uninstall", params={"name": "Minimal"})
