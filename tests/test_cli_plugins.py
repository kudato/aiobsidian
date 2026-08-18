from __future__ import annotations

import json

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.plugins import Plugin, PluginInfo

from .helpers import drop_field

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

# A community plugin is described from its manifest, so it names an author
# and a version. Obsidian keeps the description last and leaves it out when
# the manifest has none.
COMMUNITY_INFO = (
    "type\tcommunity\n"
    "name\tLocal REST API with MCP\n"
    "version\t5.1.0\n"
    "author\tAdam Coddington\n"
    "enabled\ttrue\n"
    "description\tA secure REST API and Model Context Protocol (MCP) server "
    "for your vault.\n"
)

# A core plugin has no manifest, and its name is translated.
CORE_INFO = "type\tcore\nname\tЕжедневные заметки\nenabled\ttrue\n"


async def test_info(cli):
    cli._execute.return_value = COMMUNITY_INFO
    result = await cli.plugins.info("obsidian-local-rest-api")
    assert result == PluginInfo(
        type="community",
        name="Local REST API with MCP",
        version="5.1.0",
        author="Adam Coddington",
        enabled=True,
        description=(
            "A secure REST API and Model Context Protocol (MCP) server for your vault."
        ),
    )
    cli._execute.assert_awaited_once_with(
        "plugin", params={"id": "obsidian-local-rest-api"}
    )


async def test_info_of_a_core_plugin(cli):
    cli._execute.return_value = CORE_INFO
    result = await cli.plugins.info("daily-notes")
    assert result == PluginInfo(type="core", name="Ежедневные заметки", enabled=True)
    assert result.version is None
    assert result.author is None
    assert result.description is None


async def test_info_of_a_disabled_plugin(cli):
    cli._execute.return_value = CORE_INFO.replace("true", "false")
    result = await cli.plugins.info("daily-notes")
    assert result.enabled is False


@pytest.mark.parametrize("field", ["type", "name", "enabled"])
async def test_info_without_a_required_field(cli, field):
    cli._execute.return_value = drop_field(CORE_INFO, field)
    with pytest.raises(CLIParseError) as exc_info:
        await cli.plugins.info("daily-notes")
    assert exc_info.value.command == "plugin"


async def test_info_without_a_description(cli):
    cli._execute.return_value = drop_field(COMMUNITY_INFO, "description")
    result = await cli.plugins.info("obsidian-local-rest-api")
    assert result.description is None
    assert result.version == "5.1.0"


async def test_info_without_an_author(cli):
    # Obsidian empties the field itself for a manifest that names nobody,
    # and for one that credits Obsidian.
    cli._execute.return_value = COMMUNITY_INFO.replace("Adam Coddington", "")
    result = await cli.plugins.info("obsidian-local-rest-api")
    assert result.author is None


async def test_info_with_a_description_that_ends_in_a_space(cli):
    # Obsidian prints the description last and takes it from the manifest
    # untrimmed, so the blank space a manifest ends with is the last thing
    # in the output.
    cli._execute.return_value = COMMUNITY_INFO.replace("vault.\n", "vault.  \n")
    result = await cli.plugins.info("obsidian-local-rest-api")
    assert result.description is not None
    assert result.description.endswith("vault.  ")


async def test_info_with_a_description_that_names_a_field_again(cli):
    # A newline in the description is where Obsidian would start another
    # field, so a manifest could otherwise answer for `enabled` itself.
    cli._execute.return_value = COMMUNITY_INFO.replace(
        "vault.\n", "vault.\nenabled\tfalse\n"
    )
    with pytest.raises(CLIParseError):
        await cli.plugins.info("obsidian-local-rest-api")


async def test_info_of_a_core_plugin_that_names_a_version(cli):
    # A core plugin has no manifest to take one from, so the two records
    # Obsidian prints do not overlap.
    cli._execute.return_value = CORE_INFO + "version\t1.0.0\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.plugins.info("daily-notes")
    assert exc_info.value.command == "plugin"


async def test_info_of_a_community_plugin_without_a_version(cli):
    # The manifest gives one and Obsidian prints it unconditionally.
    cli._execute.return_value = drop_field(COMMUNITY_INFO, "version")
    with pytest.raises(CLIParseError):
        await cli.plugins.info("obsidian-local-rest-api")


async def test_info_with_a_stray_line(cli):
    cli._execute.return_value = CORE_INFO + "and one more thing\n"
    with pytest.raises(CLIParseError):
        await cli.plugins.info("daily-notes")


async def test_is_restricted_when_on(cli):
    # The one switch that answers a read in a word rather than a
    # sentence.
    cli._execute.return_value = "on\n"
    assert await cli.plugins.is_restricted() is True
    cli._execute.assert_awaited_once_with("plugins:restrict")


async def test_is_restricted_when_off(cli):
    cli._execute.return_value = "off\n"
    assert await cli.plugins.is_restricted() is False


async def test_set_restricted_true(cli):
    cli._execute.return_value = "Restricted mode enabled. Reloading...\n"
    assert await cli.plugins.set_restricted(True) is True
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["on"])


async def test_set_restricted_true_when_already_restricted(cli):
    # Nothing changed, so nothing reloads either — which is the whole
    # reason a caller needs to be told apart from the line above.
    cli._execute.return_value = "Restricted mode is already enabled.\n"
    assert await cli.plugins.set_restricted(True) is False


async def test_set_restricted_false(cli):
    cli._execute.return_value = "Restricted mode disabled. Reloading...\n"
    assert await cli.plugins.set_restricted(False) is True
    cli._execute.assert_awaited_once_with("plugins:restrict", flags=["off"])


async def test_set_restricted_false_when_already_unrestricted(cli):
    cli._execute.return_value = "Restricted mode is already disabled.\n"
    assert await cli.plugins.set_restricted(False) is False


async def test_set_restricted_with_an_unknown_reply(cli):
    cli._execute.return_value = "Restricted mode enabled.\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.plugins.set_restricted(True)
    assert exc_info.value.command == "plugins:restrict"


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


async def test_list_without_a_string_version(cli):
    cli._execute.return_value = json.dumps([{"id": "backlink", "version": 0}])
    with pytest.raises(CLIParseError):
        await cli.plugins.list()


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
