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
        custom_domain: Custom domain the site also answers to. Obsidian
            stores the setting as it was typed and checks nothing, and
            the example it offers is a bare host — `"notes.example.com"`
            — so this need not be a URL the way `url` is. Whether `url`
            still serves the site or redirects here is a setting of its
            own that the CLI does not print. `None` when no custom
            domain is set up.
    """

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    url: str
    custom_domain: str | None = Field(default=None, alias="custom")
