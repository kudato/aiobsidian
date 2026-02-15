from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

import httpx

from ._constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SCHEME, DEFAULT_TIMEOUT
from ._exceptions import APIError, AuthenticationError, NotFoundError

if TYPE_CHECKING:
    from .resources.active import ActiveFileResource
    from .resources.commands import CommandsResource
    from .resources.open import OpenResource
    from .resources.periodic import PeriodicNotesResource
    from .resources.search import SearchResource
    from .resources.system import SystemResource
    from .resources.vault import VaultResource


class ObsidianClient:
    """Async client for the Obsidian Local REST API.

    Provides access to vault files, the active file, periodic notes,
    commands, search, and system information through resource properties.

    Can be used as an async context manager:

    ```python
    async with ObsidianClient(api_key="your-key") as client:
        status = await client.system.status()
    ```

    Args:
        api_key: API key from the Local REST API plugin settings.
        host: Hostname of the Obsidian REST API server.
        port: Port number of the Obsidian REST API server.
        scheme: URL scheme (`"https"` or `"http"`).
        timeout: Request timeout in seconds.
        verify_ssl: Whether to verify SSL certificates. Defaults to
            `False` because the plugin uses self-signed certificates.
        http_client: Optional pre-configured `httpx.AsyncClient`. When
            provided, the client will **not** be closed on `aclose()`.
    """

    def __init__(
        self,
        api_key: str,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        scheme: str = DEFAULT_SCHEME,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = False,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = f"{scheme}://{host}:{port}"
        self._api_key = api_key
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._external_client = http_client is not None
        self._http = http_client or self._build_http_client()

    def _build_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout,
            verify=self._verify_ssl,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        content: str | bytes | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send an HTTP request to the Obsidian REST API.

        This is a low-level method used internally by resource classes.
        Prefer using the resource methods (e.g. `client.vault.get()`)
        for typical operations.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API endpoint path (e.g. `"/vault/note.md"`).
            content: Raw request body.
            json: JSON-serializable request body.
            headers: Additional HTTP headers.
            params: URL query parameters.

        Returns:
            The `httpx.Response` object.

        Raises:
            AuthenticationError: If the API key is invalid (HTTP 401).
            NotFoundError: If the resource is not found (HTTP 404).
            APIError: For any other HTTP error (status >= 400).
        """
        response = await self._http.request(
            method,
            path,
            content=content,
            json=json,
            headers=headers,
            params=params,
        )
        if response.status_code >= 400:
            self._raise_for_status(response)
        return response

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        message = response.text
        error_code = None
        try:
            data = response.json()
            message = data.get("message", message)
            error_code = data.get("errorCode")
        except (ValueError, KeyError):
            pass

        status = response.status_code
        if status == 401:
            raise AuthenticationError(status, message, error_code)
        if status == 404:
            raise NotFoundError(status, message, error_code)
        raise APIError(status, message, error_code)

    # -- resources ---------------------------------------------------------

    @cached_property
    def vault(self) -> VaultResource:
        """Access vault file operations (read, create, append, patch, delete, list)."""
        from .resources.vault import VaultResource

        return VaultResource(self)

    @cached_property
    def active(self) -> ActiveFileResource:
        """Access the currently active file in Obsidian."""
        from .resources.active import ActiveFileResource

        return ActiveFileResource(self)

    @cached_property
    def periodic(self) -> PeriodicNotesResource:
        """Access periodic notes (daily, weekly, monthly, quarterly, yearly)."""
        from .resources.periodic import PeriodicNotesResource

        return PeriodicNotesResource(self)

    @cached_property
    def commands(self) -> CommandsResource:
        """List and execute Obsidian commands."""
        from .resources.commands import CommandsResource

        return CommandsResource(self)

    @cached_property
    def search(self) -> SearchResource:
        """Search vault content (simple text, Dataview DQL, JsonLogic)."""
        from .resources.search import SearchResource

        return SearchResource(self)

    @cached_property
    def open(self) -> OpenResource:
        """Open files in the Obsidian UI."""
        from .resources.open import OpenResource

        return OpenResource(self)

    @cached_property
    def system(self) -> SystemResource:
        """Access server status and OpenAPI specification."""
        from .resources.system import SystemResource

        return SystemResource(self)

    # -- lifecycle ---------------------------------------------------------

    async def __aenter__(self) -> ObsidianClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client.

        If an external `httpx.AsyncClient` was provided to the
        constructor, this method is a no-op — the caller is
        responsible for closing it.
        """
        if not self._external_client:
            await self._http.aclose()
