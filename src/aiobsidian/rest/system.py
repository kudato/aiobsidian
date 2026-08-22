from __future__ import annotations

from ..models.system import ServerStatus
from ._base import BaseResource


class SystemResource(BaseResource):
    """Access server status and the OpenAPI specification."""

    __slots__ = ()

    async def status(self) -> ServerStatus:
        """Get the current server status.

        Returns:
            A `ServerStatus` object with authentication state and
            version information.

        Raises:
            APIParseError: If the body is not a status record.
        """
        response = await self._client.request("GET", "/")
        return self._parse_as(response, ServerStatus)

    async def openapi(self) -> str:
        """Get the OpenAPI specification of the REST API.

        Returns:
            The OpenAPI spec as a YAML string.
        """
        response = await self._client.request("GET", "/openapi.yaml")
        return response.text
