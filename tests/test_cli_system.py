from __future__ import annotations

import json

COMMANDS = [
    {"name": "read", "description": "Read a file"},
    {"name": "create", "description": "Create a file"},
]

VAULTS = [
    {"name": "MyVault", "path": "/vaults/MyVault"},
    {"name": "Work", "path": "/vaults/Work"},
]


async def test_version(cli):
    cli._execute.return_value = "1.8.0"
    result = await cli.system.version()
    assert result == "1.8.0"
    cli._execute.assert_awaited_once_with("version")


async def test_help(cli):
    cli._execute.return_value = json.dumps(COMMANDS)
    result = await cli.system.help()
    assert result == COMMANDS
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
    cli._execute.return_value = json.dumps(VAULTS)
    result = await cli.system.vaults()
    assert result == VAULTS
    cli._execute.assert_awaited_once_with("vaults")
