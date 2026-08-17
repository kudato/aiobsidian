from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PublishChange(BaseModel):
    """A file whose state differs from the published site.

    Attributes:
        type: What the change is: `"new"`, `"changed"` or `"deleted"`.
        path: Path to the file relative to the vault root.
    """

    type: str
    path: str


class PublishSite(BaseModel):
    """The Publish site this vault is published to.

    Attributes:
        slug: Site ID, the last part of the Publish URL.
        url: Where the site is served from,
            `https://publish.obsidian.md/` followed by the slug.
        custom_domain: Domain serving the site instead of `url`, or
            `None` when none is set up.
    """

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    url: str
    custom_domain: str | None = Field(default=None, alias="custom")
