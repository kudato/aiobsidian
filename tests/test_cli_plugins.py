from __future__ import annotations

import json

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.plugins import Plugin

# `plugins` lists everything installed. Core plugins ship with the app and
# report no version; only community ones carry a number.
PLUGINS = [
    {"id": "backlink", "version": ""},
    {"id": "bookmarks", "version": ""},
    {"id": "obsidian-local-rest-api", "version": "5.1.0"},
]

# The community plugin is installed but switched off.
ENABLED_PLUGINS = [
    {"id": "backlink"},
    {"id": "bookmarks"},
]


async def test_info(cli):
    cli._execute.return_value = "type\tcommunity\nname\tDataview\nenabled\ttrue\n"
    result = await cli.plugins.info("dataview")
    assert result == {"type": "community", "name": "Dataview", "enabled": "true"}
    cli._execute.assert_awaited_once_with("plugin", params={"id": "dataview"})


async def test_set_restricted_true(cli):
    cli._execute.return_value = ""
    await cli.plugins.set_restricted(True)
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["on"])


async def test_set_restricted_false(cli):
    cli._execute.return_value = ""
    await cli.plugins.set_restricted(False)
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["off"])


async def test_list(cli):
    cli._execute.return_value = json.dumps(PLUGINS)
    result = await cli.plugins.list()
    assert result == [
        Plugin(id="backlink", version=None),
        Plugin(id="bookmarks", version=None),
        Plugin(id="obsidian-local-rest-api", version="5.1.0"),
    ]
    cli._execute.assert_awaited_once_with(
        "plugins", flags=["versions"], output_format="json"
    )


async def test_list_without_the_version_column(cli):
    cli._execute.return_value = json.dumps([{"id": "backlink"}])
    with pytest.raises(CLIParseError) as exc_info:
        await cli.plugins.list()
    assert exc_info.value.command == "plugins"


async def test_enabled(cli):
    cli._execute.return_value = json.dumps(ENABLED_PLUGINS)
    result = await cli.plugins.enabled()
    assert result == ["backlink", "bookmarks"]
    cli._execute.assert_awaited_once_with("plugins:enabled", output_format="json")


async def test_enable(cli):
    cli._execute.return_value = ""
    await cli.plugins.enable("dataview")
    cli._execute.assert_awaited_once_with("plugin:enable", params={"id": "dataview"})


async def test_disable(cli):
    cli._execute.return_value = ""
    await cli.plugins.disable("dataview")
    cli._execute.assert_awaited_once_with("plugin:disable", params={"id": "dataview"})


async def test_install(cli):
    cli._execute.return_value = ""
    await cli.plugins.install("dataview")
    cli._execute.assert_awaited_once_with("plugin:install", params={"id": "dataview"})


async def test_uninstall(cli):
    cli._execute.return_value = ""
    await cli.plugins.uninstall("dataview")
    cli._execute.assert_awaited_once_with("plugin:uninstall", params={"id": "dataview"})


async def test_reload(cli):
    cli._execute.return_value = ""
    await cli.plugins.reload("dataview")
    cli._execute.assert_awaited_once_with("plugin:reload", params={"id": "dataview"})
