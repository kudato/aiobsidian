from __future__ import annotations

from ..models.system import ServerStatus
from ._base import BaseResource


class SystemResource(BaseResource):
    """Access server status and the OpenAPI specification."""

    async def status(self) -> ServerStatus:
        """Get the current server status.

        Returns:
            A `ServerStatus` object with authentication state and
            version information.
        """
        response = await self._client.request("GET", "/")
        return ServerStatus.model_validate(response.json())

    async def openapi(self) -> str:
        """Get the OpenAPI specification of the REST API.

        Returns:
            The OpenAPI spec as a YAML string.
        """
        response = await self._client.request("GET", "/openapi.yaml")
        return response.text
