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
        custom_domain: Custom domain the site also answers to, as a
            bare host. Obsidian names the setting a custom URL but
            offers `example.com` for it, and puts `https://` in front
            of what it stored when it serves the site — nothing checks
            the value on the way in, so one typed with a scheme of its
            own is served from `https://https://`. Whether `url` still
            serves the site or redirects here is a setting of its own
            that the CLI does not print. `None` when no custom domain
            is set up.
    """

    model_config = ConfigDict(populate_by_name=True)

    slug: str
    url: str
    custom_domain: str | None = Field(default=None, alias="custom")
