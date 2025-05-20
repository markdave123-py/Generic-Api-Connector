import asyncio
from typing import List, Optional

import httpx

from .anomaly import AnomalyDetector
from .auth import OAuth2Manager
from .config import get_settings
from .exceptions import (
    APIClientError,
    AuthenticationError,
    NotFoundError,
)
from .logger import logger, redact_headers
from .models import Item, ItemPage
from .utils import gather_limited


class APIClient:
    """High‑level async client for the third‑party API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        *,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        concurrency_limit: Optional[int] = None,
    ):
        s = get_settings()
        self.base_url = (base_url or s.base_url).rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10)
        self._oauth = OAuth2Manager(self._client, s)
        self._max_retries = max_retries or s.max_retries
        self._backoff_factor = backoff_factor or s.backoff_factor
        self._concurrency_limit = concurrency_limit or s.concurrency_limit
        self._detector = AnomalyDetector()

    # ------------- Low‑level request helper -------------
    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Authenticated request with retry, logging, error handling."""
        self._detector.record_request()
        token = await self._oauth.get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        # redact before logging
        logger.debug("Request: %s %s headers=%s", method, path, redact_headers(headers))
        last_exc: Optional[Exception] = None
        url = path if path.startswith("http") else self.base_url + path

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await self._client.request(
                    method, url, headers=headers, **kwargs
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "Network error (%s) attempt %s/%s", exc, attempt, self._max_retries
                )
            else:
                if resp.status_code < 400:
                    logger.debug("Response %s %s", resp.status_code, url)
                    return resp
                if resp.status_code == 401:
                    # maybe token expired – refresh once automatically
                    self._detector.record_401()
                    try:
                        await self._oauth._refresh()
                    except AuthenticationError:
                        raise
                    continue  # retry with fresh token
                if resp.status_code == 404:
                    raise NotFoundError(path)
                if resp.status_code == 429:
                    logger.warning("429 Too Many Requests – backing off")
                    await asyncio.sleep(self._backoff_factor * (2 ** (attempt - 1)))
                    continue  # retry
                if 500 <= resp.status_code < 600:
                    logger.warning(
                        "Server error %s, attempt %s", resp.status_code, attempt
                    )
                    await asyncio.sleep(self._backoff_factor * (2 ** (attempt - 1)))
                    continue
                # for other 4xx errors, no retry
                raise APIClientError(f"HTTP {resp.status_code}: {resp.text}")
            # network error path
            await asyncio.sleep(self._backoff_factor * (2 ** (attempt - 1)))
        if last_exc:
            raise APIClientError("Max retries exceeded", last_exc)
        raise APIClientError("Request failed after retries")

    # High‑level helpers
    async def list_items_page(self, page: int = 1) -> ItemPage:
        resp = await self._request("GET", f"/items?page={page}")
        return ItemPage.parse_obj(resp.json())

    async def list_all_items(self, concurrent: bool = True) -> List[Item]:
        """Fetch every item across pages – optionally concurrent."""
        first = await self.list_items_page(1)
        items: List[Item] = list(first.items)
        if first.total_pages <= 1:
            return items

        pages = range(2, first.total_pages + 1)
        if concurrent:
            coros = [self.list_items_page(p) for p in pages]
            results: List[ItemPage] = await gather_limited(
                coros, self._concurrency_limit
            )
            for page_obj in results:
                items.extend(page_obj.items)
        else:
            for p in pages:
                ip = await self.list_items_page(p)
                items.extend(ip.items)
        return items

    async def close(self):
        await self._client.aclose()


# Convenience singleton for quick import
_default_client: Optional[APIClient] = None


def default_client() -> APIClient:
    global _default_client
    if _default_client is None:
        _default_client = APIClient()
    return _default_client
