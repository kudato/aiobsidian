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
        custom_url: Where the site also answers, as Obsidian's Custom
            URL setting holds it: a domain or subdomain with `www.`
            left off, and the path behind it when the site is served
            from one — `example.com`, or `mysite.com/my-notes`. It
            carries no scheme the way `url` does, since the published
            site puts `https://` in front of it itself. Whether `url`
            still serves the site or redirects here is a setting of its
            own that the CLI does not print. `None` when the site
            answers at `url` alone.
    """

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    url: str
    custom_url: str | None = Field(default=None, alias="custom")
