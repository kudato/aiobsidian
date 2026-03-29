from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIDevResource(BaseCLIResource):
    """CLI resource for developer/debugging tools.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def devtools(self) -> None:
        """Toggle Electron DevTools."""
        await self._cli._execute("devtools")

    async def eval(self, code: str) -> str:
        """Execute JavaScript in the Obsidian API context.

        Args:
            code: JavaScript code to evaluate.

        Returns:
            Evaluation result as a string.
        """
        return await self._cli._execute("eval", params={"code": code})

    async def console(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Show console messages.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of console message objects.
        """
        params: dict[str, str] = {}
        if limit is not None:
            params["limit"] = str(limit)
        output = await self._cli._execute("dev:console", params=params or None)
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def errors(self) -> list[dict[str, Any]]:
        """Show JavaScript errors.

        Returns:
            List of error objects.
        """
        output = await self._cli._execute("dev:errors")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def screenshot(self, path: str) -> str:
        """Capture a screenshot (base64 PNG).

        Args:
            path: File path for the screenshot.

        Returns:
            Base64-encoded PNG data.
        """
        return await self._cli._execute("dev:screenshot", params={"path": path})

    async def dom(
        self,
        selector: str,
        *,
        match_all: bool = False,
        text: bool = False,
        attr: str | None = None,
        css: str | None = None,
    ) -> str:
        """Inspect DOM elements.

        Args:
            selector: CSS selector for the element(s).
            match_all: If ``True``, match all elements instead of just the first.
            text: If ``True``, return text content only.
            attr: Return this attribute value from matched elements.
            css: Return this CSS property value from matched elements.

        Returns:
            DOM inspection result.
        """
        params: dict[str, str] = {"selector": selector}
        if attr is not None:
            params["attr"] = attr
        if css is not None:
            params["css"] = css
        flags: list[str] = []
        if match_all:
            flags.append("--all")
        if text:
            flags.append("--text")
        return await self._cli._execute("dev:dom", params=params, flags=flags or None)

    async def css(self, selector: str, *, prop: str | None = None) -> str:
        """Inspect CSS styles.

        Args:
            selector: CSS selector for the element.
            prop: Specific CSS property to retrieve.

        Returns:
            CSS inspection result.
        """
        params: dict[str, str] = {"selector": selector}
        if prop is not None:
            params["prop"] = prop
        return await self._cli._execute("dev:css", params=params)

    async def mobile(self, *, on: bool) -> None:
        """Toggle mobile emulation.

        Args:
            on: ``True`` to enable, ``False`` to disable.
        """
        flags = ["--on"] if on else ["--off"]
        await self._cli._execute("dev:mobile", flags=flags)

    async def debug(self, *, on: bool) -> None:
        """Start or stop console capture.

        Args:
            on: ``True`` to start, ``False`` to stop capture.
        """
        flags = ["--on"] if on else ["--off"]
        await self._cli._execute("dev:debug", flags=flags)

    async def cdp(self, method: str, params: str) -> str:
        """Execute a Chrome DevTools Protocol command.

        Args:
            method: CDP method name.
            params: JSON-encoded parameters.

        Returns:
            CDP command result.
        """
        return await self._cli._execute(
            "dev:cdp", params={"method": method, "params": params}
        )
