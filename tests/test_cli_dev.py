from __future__ import annotations

import json

CONSOLE_MSGS = [
    {"level": "log", "message": "hello"},
    {"level": "warn", "message": "deprecation"},
]

ERRORS = [
    {"message": "TypeError: undefined is not a function", "stack": "at foo:1"},
]


async def test_devtools(cli):
    cli._execute.return_value = ""
    await cli.dev.devtools()
    cli._execute.assert_awaited_once_with("devtools")


async def test_eval(cli):
    cli._execute.return_value = "42"
    result = await cli.dev.eval("1+1")
    assert result == "42"
    cli._execute.assert_awaited_once_with("eval", params={"code": "1+1"})


async def test_console(cli):
    cli._execute.return_value = json.dumps(CONSOLE_MSGS)
    result = await cli.dev.console()
    assert result == CONSOLE_MSGS
    cli._execute.assert_awaited_once_with("dev:console", params=None)


async def test_console_with_limit(cli):
    cli._execute.return_value = json.dumps(CONSOLE_MSGS[:1])
    result = await cli.dev.console(limit=1)
    assert result == CONSOLE_MSGS[:1]
    cli._execute.assert_awaited_once_with("dev:console", params={"limit": "1"})


async def test_errors(cli):
    cli._execute.return_value = json.dumps(ERRORS)
    result = await cli.dev.errors()
    assert result == ERRORS
    cli._execute.assert_awaited_once_with("dev:errors")


async def test_screenshot(cli):
    cli._execute.return_value = "base64data"
    result = await cli.dev.screenshot("/tmp/shot.png")
    assert result == "base64data"
    cli._execute.assert_awaited_once_with(
        "dev:screenshot", params={"path": "/tmp/shot.png"}
    )


async def test_dom(cli):
    cli._execute.return_value = "<div>hello</div>"
    result = await cli.dev.dom(".my-class")
    assert result == "<div>hello</div>"
    cli._execute.assert_awaited_once_with(
        "dev:dom", params={"selector": ".my-class"}, flags=None
    )


async def test_dom_all_flags(cli):
    cli._execute.return_value = "text content"
    result = await cli.dev.dom(
        "#app", all=True, text=True, attr="data-id", css="color"
    )
    assert result == "text content"
    cli._execute.assert_awaited_once_with(
        "dev:dom",
        params={"selector": "#app", "attr": "data-id", "css": "color"},
        flags=["--all", "--text"],
    )


async def test_css(cli):
    cli._execute.return_value = "rgb(0, 0, 0)"
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


async def test_mobile_on(cli):
    cli._execute.return_value = ""
    await cli.dev.mobile(on=True)
    cli._execute.assert_awaited_once_with("dev:mobile", flags=["--on"])


async def test_mobile_off(cli):
    cli._execute.return_value = ""
    await cli.dev.mobile(on=False)
    cli._execute.assert_awaited_once_with("dev:mobile", flags=["--off"])


async def test_debug_on(cli):
    cli._execute.return_value = ""
    await cli.dev.debug(on=True)
    cli._execute.assert_awaited_once_with("dev:debug", flags=["--on"])


async def test_debug_off(cli):
    cli._execute.return_value = ""
    await cli.dev.debug(on=False)
    cli._execute.assert_awaited_once_with("dev:debug", flags=["--off"])


async def test_cdp(cli):
    cli._execute.return_value = '{"result": {}}'
    result = await cli.dev.cdp("Page.navigate", '{"url": "https://example.com"}')
    assert result == '{"result": {}}'
    cli._execute.assert_awaited_once_with(
        "dev:cdp",
        params={"method": "Page.navigate", "params": '{"url": "https://example.com"}'},
    )
