from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

_USAGE_KEY = "account usage"
_USAGE_SEPARATOR = " / "
_SIZES = ("vault_size", "account_used", "account_limit")


class SyncStatus(BaseModel):
    """What Obsidian Sync is doing with this vault.

    Only `status` is always there. A vault Sync was never set up for
    answers with that field alone; the vault and the device are named
    once Sync knows them; and the three sizes arrive together or not at
    all, because they all come of the account quota, which Obsidian asks
    its server for and does without when the request fails. A record
    holding some of the three and not the rest is refused, since it is
    one Sync cannot report.

    Attributes:
        status: What Sync is doing: `"uninitialized"` before it starts
            up, then `"disconnected"` for a vault it is not set up for,
            and `"synced"`, `"syncing"`, `"paused"` or `"error"` for one
            it is.
        vault: Name of the vault on Sync, which need not be the name of
            the folder it lives in.
        device: Name this device is known by on Sync.
        vault_size: How much of the quota this vault takes up, as the
            CLI prints it — rounded to two decimals and carrying its
            unit, as in `"4.06 KB"`, and a comma too once it reaches a
            thousand of that unit, as in `"1,023.44 KB"`. Only a size
            below a kilobyte is printed whole, as in `"431 B"`.
        account_used: How much of the quota the whole account takes up,
            in the same rounded form.
        account_limit: How much the account is allowed, in the same
            rounded form.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: str
    vault: str | None = None
    device: str | None = None
    vault_size: str | None = Field(default=None, alias="vault size")
    account_used: str | None = None
    account_limit: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _split_usage(cls, data: Any) -> Any:
        """Take apart the line that reports the quota twice over.

        The CLI prints what the account uses and what it is allowed on
        one line, joined by ` / `. The join is safe to undo: each side
        is a size Obsidian rounds and spells out itself, and no size it
        spells can hold a slash.

        Args:
            data: Fields as the CLI printed them.

        Returns:
            The same fields with the usage line replaced by the two
            sizes it holds, or the data untouched when the line is
            absent or is not a string.

        Raises:
            ValueError: If the line holds one size rather than two.
        """
        if not isinstance(data, dict) or not isinstance(data.get(_USAGE_KEY), str):
            return data
        fields = dict(data)
        printed = fields.pop(_USAGE_KEY)
        used, found, limit = printed.partition(_USAGE_SEPARATOR)
        if not found:
            raise ValueError(f"account usage names one size, not two: {printed!r}")
        return {**fields, "account_used": used, "account_limit": limit}

    @model_validator(mode="after")
    def _sizes_arrive_together(self) -> SyncStatus:
        """Refuse a record that reports the quota by halves.

        One test on the size Sync fetched decides all three: either
        Obsidian prints the vault size and the usage line both, or it
        prints neither and reports what it does know.

        Returns:
            The record, when it reports every size or none.

        Raises:
            ValueError: If it reports some of the three and not the rest.
        """
        reported = [name for name in _SIZES if getattr(self, name) is not None]
        if reported and len(reported) != len(_SIZES):
            raise ValueError(
                "the quota is reported whole or not at all, "
                f"and this reports {', '.join(reported)} alone"
            )
        return self
