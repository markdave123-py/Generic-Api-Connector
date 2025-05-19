from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterable
from connector.client import APIClient


class BaseConnector(APIClient, ABC):
    """
    Sub-class this for every provider (Google, Facebook…).
    All auth/retry/logging/anomaly logic lives in APIClient.
    """

    #: map logical names → (method, path_template)
    ENDPOINTS: Dict[str, tuple[str, str]] = {}

    # helpers for subclasses
    async def _call(
        self, name: str, *, path_params: Dict[str, Any] | None = None, **request_kw
    ) -> Any:
        """
        Generic request helper – resolves method & path from ENDPOINTS,
        expands {vars} in the path, then delegates to self._request().
        """
        if name not in self.ENDPOINTS:
            raise ValueError(f"Unknown endpoint {name!r} for {type(self).__name__}")

        method, path_tmpl = self.ENDPOINTS[name]
        path_params = path_params or {}
        path = path_tmpl.format(**path_params)
        resp = await self._request(method, path, **request_kw)
        return resp.json()

    # canonical user API
    @abstractmethod
    async def list_users(self, **kw) -> Iterable[dict]:
        """Every connector must implement this high-level call."""
