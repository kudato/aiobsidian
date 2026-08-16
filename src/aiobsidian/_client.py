from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from ._constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SCHEME, DEFAULT_TIMEOUT
from ._exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIProtocolError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
)

if TYPE_CHECKING:
    import httpx

    from .rest.active import ActiveFileResource
    from .rest.commands import CommandsResource
    from .rest.open import OpenResource
    from .rest.search import SearchResource
    from .rest.system import SystemResource
    from .rest.vault import VaultResource


class ObsidianClient:
    """Async client for the Obsidian Local REST API.

    Provides access to vault files, the active file, commands, search,
    and system information through resource properties. Requires the
    Local REST API plugin 5.0 or newer.

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
        http_client: Optional pre-configured `httpx.AsyncClient`. The
            `api_key` is applied to every request either way. If the
            client carries no `base_url`, `host`/`port`/`scheme` supply
            one. It is **not** closed on `aclose()`.
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
        if not 0 <= port <= 65535:
            # Out of range, the OS rejects the connect() with an
            # OverflowError that anyio wraps in an ExceptionGroup, so
            # nothing the caller could reasonably catch ever sees it.
            raise ValueError(f"port must be between 0 and 65535, got {port}")

        self._host = host
        self._port = port
        self._scheme = scheme
        self._base_url = f"{scheme}://{host}:{port}"
        self._api_key = api_key
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._external_client = http_client is not None
        self._httpx = self._import_httpx()
        self._http = http_client or self._build_http_client()
        self._url_prefix = "" if str(self._http.base_url) else self._base_url

    @staticmethod
    def _import_httpx() -> Any:
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for REST API support. "
                "Install with: pip install aiobsidian[rest]"
            ) from None
        return httpx

    def __repr__(self) -> str:
        return (
            f"ObsidianClient(host={self._host!r}, port={self._port!r}, "
            f"scheme={self._scheme!r})"
        )

    def _build_http_client(self) -> httpx.AsyncClient:
        httpx = self._import_httpx()
        try:
            return httpx.AsyncClient(  # type: ignore[no-any-return]
                base_url=self._base_url,
                timeout=self._timeout,
                verify=self._verify_ssl,
            )
        except httpx.InvalidURL as exc:
            # host, port and scheme are public parameters, and httpx
            # parses the URL they make while the client is being built.
            raise ValueError(
                f"host, port and scheme make no valid URL: {self._base_url!r} — {exc}"
            ) from exc

    async def request(
        self,
        method: str,
        path: str,
        *,
        content: str | bytes | None = None,
        json: Any = None,
        headers: dict[str, Any] | None = None,
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
            headers: Additional HTTP headers. The `Authorization` header
                is added from `api_key` and can be overridden here.
            params: URL query parameters.

        Returns:
            The `httpx.Response` object.

        Raises:
            ValueError: If the request cannot be built — an unparseable
                URL, a scheme that is not HTTP, an illegal header. A
                lone surrogate in `path` raises `UnicodeEncodeError`,
                which is a `ValueError` too.
            APIConnectionError: If the server cannot be reached.
            APITimeoutError: If the request exceeds the timeout.
            APIProtocolError: If the exchange with the server breaks down.
            AuthenticationError: If the API key is invalid (HTTP 401).
            APINotFoundError: If the resource is not found (HTTP 404).
            APIStatusError: For any other HTTP error (status >= 400).
        """
        request_headers: dict[str, Any] = {"Authorization": f"Bearer {self._api_key}"}
        if headers:
            request_headers.update(headers)

        url = f"{self._url_prefix}{path}"
        httpx = self._httpx
        try:
            response = await self._http.request(
                method,
                url,
                content=content,
                json=json,
                headers=request_headers,
                params=params,
            )
        except (
            httpx.InvalidURL,
            httpx.UnsupportedProtocol,
            httpx.LocalProtocolError,
        ) as exc:
            # None of these three reach the server: the URL will not
            # parse, its scheme is not HTTP, or the headers are not
            # legal. They are bad arguments, and this library reports
            # those as ValueError rather than as a transport failure.
            raise ValueError(f"{method} {url} cannot be sent: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise APITimeoutError(*self._failure(method, url, exc)) from exc
        except (httpx.NetworkError, httpx.ProxyError) as exc:
            raise APIConnectionError(*self._failure(method, url, exc)) from exc
        except httpx.RequestError as exc:
            # What is left answered, or half-answered, and the exchange
            # broke: bad framing, a body that belied its own headers, a
            # redirect loop. Reporting those as unreachable would send
            # the caller to restart an Obsidian that is plainly running.
            raise APIProtocolError(*self._failure(method, url, exc)) from exc

        if response.status_code >= 400:
            self._raise_for_status(response)
        return response

    @staticmethod
    def _failure(
        method: str, fallback_url: str, exc: httpx.RequestError
    ) -> tuple[str, str, str]:
        """Describe a failed request for the exception that reports it.

        Args:
            method: HTTP method of the request.
            fallback_url: URL to name when httpx attached no request to
                the error. It is what the caller passed, so it may be
                relative.
            exc: The error the HTTP transport raised.

        Returns:
            The method, the URL and what the transport reported.
        """
        try:
            url = str(exc.request.url)
        except RuntimeError:
            url = fallback_url
        return method, url, str(exc) or type(exc).__name__

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        message = response.text
        error_code = None
        try:
            data = response.json()
            message = data.get("message", message)
            error_code = data.get("errorCode")
        except (ValueError, AttributeError):
            pass

        status = response.status_code
        if status == 401:
            raise AuthenticationError(status, message, error_code)
        if status == 404:
            raise APINotFoundError(status, message, error_code)
        raise APIStatusError(status, message, error_code)

    # -- resources ---------------------------------------------------------

    @cached_property
    def vault(self) -> VaultResource:
        """Access vault file operations (read, create, append, patch, delete, list)."""
        from .rest.vault import VaultResource

        return VaultResource(self)

    @cached_property
    def active(self) -> ActiveFileResource:
        """Access the currently active file in Obsidian."""
        from .rest.active import ActiveFileResource

        return ActiveFileResource(self)

    @cached_property
    def commands(self) -> CommandsResource:
        """List and execute Obsidian commands."""
        from .rest.commands import CommandsResource

        return CommandsResource(self)

    @cached_property
    def search(self) -> SearchResource:
        """Search vault content (simple text, JsonLogic)."""
        from .rest.search import SearchResource

        return SearchResource(self)

    @cached_property
    def open(self) -> OpenResource:
        """Open files in the Obsidian UI."""
        from .rest.open import OpenResource

        return OpenResource(self)

    @cached_property
    def system(self) -> SystemResource:
        """Access server status and OpenAPI specification."""
        from .rest.system import SystemResource

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
