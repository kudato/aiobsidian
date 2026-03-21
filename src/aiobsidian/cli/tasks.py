from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLITasksResource(BaseCLIResource):
    """CLI resource for task operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def list(self) -> list[dict[str, Any]]:
        """List all tasks across the vault.

        Returns:
            List of task objects.
        """
        output = await self._cli._execute("tasks")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def create(self, content: str, *, tags: str | None = None) -> None:
        """Create a new task.

        Args:
            content: Task text content.
            tags: Comma-separated tag names to attach to the task.
        """
        params: dict[str, str] = {"content": content}
        if tags:
            params["tags"] = tags
        await self._cli._execute("task:create", params=params)

    async def complete(self, task_id: str) -> None:
        """Mark a task as complete.

        Args:
            task_id: Identifier of the task to complete.
        """
        await self._cli._execute("task:complete", params={"task": task_id})
