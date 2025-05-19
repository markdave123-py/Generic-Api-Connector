from typing import List
from connector.base import BaseConnector
from connector.models import Item


class SimConnector(BaseConnector):
    # re-use BASE_URL from env; ENDPOINTS map logical names to HTTP verb + path
    ENDPOINTS = {
        "list_users": ("GET", "/items"),  # the mock returns items that look like users
        "get_user": ("GET", "/items/{id}"),
    }

    async def list_users(self, **kw) -> List[Item]:
        data = await self._call("list_users")
        return [Item.model_validate(d) for d in data["items"]]
