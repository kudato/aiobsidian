from __future__ import annotations

import json

PLUGINS = [
    {"id": "dataview", "name": "Dataview", "enabled": True},
    {"id": "templater", "name": "Templater", "enabled": False},
]

ENABLED_PLUGINS = [
    {"id": "dataview", "name": "Dataview"},
]


async def test_info(cli):
    plugin_info = {"id": "dataview", "name": "Dataview", "version": "0.5.66"}
    cli._execute.return_value = json.dumps(plugin_info)
    result = await cli.plugins.info("dataview")
    assert result == plugin_info
    cli._execute.assert_awaited_once_with("plugin", params={"id": "dataview"})


async def test_restrict_on(cli):
    cli._execute.return_value = ""
    await cli.plugins.restrict(on=True)
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["--on"])


async def test_restrict_off(cli):
    cli._execute.return_value = ""
    await cli.plugins.restrict(on=False)
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["--off"])


async def test_list(cli):
    cli._execute.return_value = json.dumps(PLUGINS)
    result = await cli.plugins.list()
    assert result == PLUGINS
    cli._execute.assert_awaited_once_with("plugins", flags=None)


async def test_list_with_versions(cli):
    cli._execute.return_value = json.dumps(PLUGINS)
    result = await cli.plugins.list(versions=True)
    assert result == PLUGINS
    cli._execute.assert_awaited_once_with("plugins", flags=["--versions"])


async def test_enabled(cli):
    cli._execute.return_value = json.dumps(ENABLED_PLUGINS)
    result = await cli.plugins.enabled()
    assert result == ENABLED_PLUGINS
    cli._execute.assert_awaited_once_with("plugins:enabled")


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
