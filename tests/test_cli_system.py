from __future__ import annotations

HELP_OUTPUT = """Obsidian CLI

Usage: obsidian <command> [options]

Commands:
  read                  Read file contents
"""


async def test_version(cli):
    cli._execute.return_value = "1.13.7 (installer 1.13.7)\n"
    result = await cli.system.version()
    assert result == "1.13.7 (installer 1.13.7)"
    cli._execute.assert_awaited_once_with("version")


async def test_help(cli):
    cli._execute.return_value = HELP_OUTPUT
    result = await cli.system.help()
    assert result == HELP_OUTPUT.strip()
    cli._execute.assert_awaited_once_with("help")


async def test_reload(cli):
    cli._execute.return_value = ""
    await cli.system.reload()
    cli._execute.assert_awaited_once_with("reload")


async def test_restart(cli):
    cli._execute.return_value = ""
    await cli.system.restart()
    cli._execute.assert_awaited_once_with("restart")


async def test_vaults(cli):
    cli._execute.return_value = "MyVault\nWork\n"
    result = await cli.system.vaults()
    assert result == ["MyVault", "Work"]
    cli._execute.assert_awaited_once_with("vaults")
