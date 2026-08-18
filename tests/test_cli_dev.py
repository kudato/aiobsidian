from __future__ import annotations

import pytest

from aiobsidian._exceptions import CLIParseError

CONSOLE_OUTPUT = "08:38:02 Received CLI command\n08:38:03 Plugin loaded\n"
CONSOLE_MSGS = ["08:38:02 Received CLI command", "08:38:03 Plugin loaded"]


async def test_devtools(cli):
    cli._execute.return_value = ""
    await cli.dev.devtools()
    cli._execute.assert_awaited_once_with("devtools")


async def test_eval(cli):
    cli._execute.return_value = "42\n"
    result = await cli.dev.eval("1+1")
    assert result == "42"
    cli._execute.assert_awaited_once_with("eval", params={"code": "1+1"})


async def test_console(cli):
    cli._execute.return_value = CONSOLE_OUTPUT
    result = await cli.dev.console()
    assert result == CONSOLE_MSGS
    cli._execute.assert_awaited_once_with("dev:console", params=None)


async def test_console_with_limit(cli):
    cli._execute.return_value = "08:38:02 Received CLI command\n"
    result = await cli.dev.console(limit=1)
    assert result == CONSOLE_MSGS[:1]
    cli._execute.assert_awaited_once_with("dev:console", params={"limit": "1"})


async def test_errors(cli):
    cli._execute.return_value = "TypeError: undefined is not a function\n"
    result = await cli.dev.errors()
    assert result == ["TypeError: undefined is not a function"]
    cli._execute.assert_awaited_once_with("dev:errors")


async def test_errors_none_captured(cli):
    cli._execute.return_value = "No errors captured.\n"
    result = await cli.dev.errors()
    assert result == []


async def test_screenshot(cli):
    cli._execute.return_value = ""
    result = await cli.dev.screenshot("/tmp/shot.png")
    assert result is None
    cli._execute.assert_awaited_once_with(
        "dev:screenshot", params={"path": "/tmp/shot.png"}
    )


async def test_dom(cli):
    cli._execute.return_value = "<div>hello</div>\n"
    result = await cli.dev.dom(".my-class")
    assert result == "<div>hello</div>"
    cli._execute.assert_awaited_once_with(
        "dev:dom", params={"selector": ".my-class"}, flags=None
    )


async def test_dom_text(cli):
    cli._execute.return_value = "hello\n"
    result = await cli.dev.dom("#app", match_all=True, text=True)
    assert result == "hello"
    cli._execute.assert_awaited_once_with(
        "dev:dom", params={"selector": "#app"}, flags=["all", "text"]
    )


async def test_dom_attr(cli):
    cli._execute.return_value = "workspace-leaf\n"
    result = await cli.dev.dom("#app", attr="class")
    assert result == "workspace-leaf"
    cli._execute.assert_awaited_once_with(
        "dev:dom", params={"selector": "#app", "attr": "class"}, flags=None
    )


async def test_dom_css(cli):
    cli._execute.return_value = "display: flex\n"
    result = await cli.dev.dom("#app", css="display")
    assert result == "display: flex"
    cli._execute.assert_awaited_once_with(
        "dev:dom", params={"selector": "#app", "css": "display"}, flags=None
    )


async def test_dom_rejects_several_answers(cli):
    with pytest.raises(TypeError, match="text, attr, css"):
        await cli.dev.dom("#app", text=True, attr="class", css="display")
    cli._execute.assert_not_awaited()


async def test_css(cli):
    cli._execute.return_value = "rgb(0, 0, 0)\n"
    result = await cli.dev.css(".el")
    assert result == "rgb(0, 0, 0)"
    cli._execute.assert_awaited_once_with("dev:css", params={"selector": ".el"})


async def test_css_with_prop(cli):
    cli._execute.return_value = "16px"
    result = await cli.dev.css(".el", prop="font-size")
    assert result == "16px"
    cli._execute.assert_awaited_once_with(
        "dev:css", params={"selector": ".el", "prop": "font-size"}
    )


async def test_set_mobile_true(cli):
    cli._execute.return_value = "Mobile emulation enabled. Reloading...\n"
    assert await cli.dev.set_mobile(True) is True
    cli._execute.assert_awaited_once_with("dev:mobile", flags=["on"])


async def test_set_mobile_true_when_already_emulating(cli):
    cli._execute.return_value = "Mobile emulation is already enabled.\n"
    assert await cli.dev.set_mobile(True) is False


async def test_set_mobile_false(cli):
    cli._execute.return_value = "Mobile emulation disabled. Reloading...\n"
    assert await cli.dev.set_mobile(False) is True
    cli._execute.assert_awaited_once_with("dev:mobile", flags=["off"])


async def test_set_mobile_false_when_not_emulating(cli):
    cli._execute.return_value = "Mobile emulation is already disabled.\n"
    assert await cli.dev.set_mobile(False) is False


async def test_is_attached_when_attached(cli):
    cli._execute.return_value = "Debugger is attached.\n"
    assert await cli.dev.is_attached() is True
    cli._execute.assert_awaited_once_with("dev:debug")


async def test_is_attached_when_detached(cli):
    cli._execute.return_value = "Debugger is detached.\n"
    assert await cli.dev.is_attached() is False


async def test_is_attached_with_the_answer_to_a_flag(cli):
    cli._execute.return_value = "Debugger attached. Console capture started.\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.dev.is_attached()
    assert exc_info.value.command == "dev:debug"


async def test_set_debugger_true(cli):
    cli._execute.return_value = "Debugger attached. Console capture started.\n"
    assert await cli.dev.set_debugger(True) is True
    cli._execute.assert_awaited_once_with("dev:debug", flags=["on"])


async def test_set_debugger_true_when_already_attached(cli):
    cli._execute.return_value = "Debugger is already attached.\n"
    assert await cli.dev.set_debugger(True) is False


async def test_set_debugger_false(cli):
    cli._execute.return_value = "Debugger detached. Console capture stopped.\n"
    assert await cli.dev.set_debugger(False) is True
    cli._execute.assert_awaited_once_with("dev:debug", flags=["off"])


async def test_set_debugger_false_when_not_attached(cli):
    # Detaching what was never attached is the one no-op that does not
    # say "already", so nothing about the wording can be assumed.
    cli._execute.return_value = "Debugger is not attached.\n"
    assert await cli.dev.set_debugger(False) is False


async def test_cdp(cli):
    cli._execute.return_value = '{"result": {}}\n'
    result = await cli.dev.cdp("Page.navigate", '{"url": "https://example.com"}')
    assert result == '{"result": {}}'
    cli._execute.assert_awaited_once_with(
        "dev:cdp",
        params={"method": "Page.navigate", "params": '{"url": "https://example.com"}'},
    )
