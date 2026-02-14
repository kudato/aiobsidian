from .._base_resource import BaseResource


class OpenResource(BaseResource):
    async def __call__(
        self,
        filename: str,
        *,
        new_leaf: bool = False,
    ) -> None:
        params: dict[str, str] = {}
        if new_leaf:
            params["newLeaf"] = "true"
        await self._client.request(
            "POST",
            f"/open/{filename}",
            params=params,
        )
