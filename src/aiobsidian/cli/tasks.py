from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLITasksResource(BaseCLIResource):
    """CLI resource for task operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def list(
        self,
        *,
        path: str | None = None,
        daily: bool = False,
        done: bool = False,
    ) -> list[dict[str, Any]]:
        """List tasks across the vault.

        Args:
            path: Restrict to tasks in files under this path.
            daily: If ``True``, only list tasks from the daily note.
            done: If ``True``, include completed tasks.

        Returns:
            List of task objects.
        """
        params = {"path": path} if path is not None else None
        flags: list[str] = []
        if daily:
            flags.append("--daily")
        if done:
            flags.append("--done")
        output = await self._cli._execute("tasks", params=params, flags=flags or None)
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def toggle(self, path: str, line: int) -> None:
        """Toggle a task's completion status.

        Args:
            path: Path to the file containing the task.
            line: Line number of the task in the file.
        """
        await self._cli._execute(
            "task", params={"path": path, "line": str(line)}, flags=["--toggle"]
        )

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
