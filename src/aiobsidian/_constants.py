from __future__ import annotations

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 27124
DEFAULT_SCHEME = "https"
DEFAULT_TIMEOUT = 30.0
DEFAULT_CLI_TIMEOUT = 30.0

PATCH_VERSION = "1"
"""Markdown-patch format this library speaks.

Local REST API 5.x defaults to the 2.0 format, whose instruction travels
as a JSON body and whose targets are URL path elements, and rejects the
header-driven form unless the version is stated explicitly. Until the
library moves to 2.0 it pins the 1.x format, which the plugin serves
until its 6.0 release.
"""
