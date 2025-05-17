"""OAuth2 Client‑Credentials token handling."""

import asyncio
import time
from typing import Optional
import httpx
from .models import TokenResponse
from .exceptions import AuthenticationError
from .logger import logger, redact_headers

_TOKEN_ENDPOINT = "/oauth2/token"


class OAuth2Manager:
    def __init__(self, client: httpx.AsyncClient, client_id: str, client_secret: str):
        self._client = client
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: Optional[str] = None
        self._expires_at: Optional[float] = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        async with self._lock:
            if not self._token or (
                self._expires_at and time.time() >= self._expires_at
            ):
                await self._refresh()
            return self._token  # type: ignore

    async def _refresh(self):
        logger.info("Refreshing OAuth2 token …")
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        # Never log secrets
        logger.debug("Token request: POST %s", _TOKEN_ENDPOINT)
        resp = await self._client.post(_TOKEN_ENDPOINT, data=data)
        if resp.status_code != 200:
            raise AuthenticationError(
                f"Token endpoint failed ({resp.status_code}) – {resp.text}"
            )
        tr = TokenResponse.parse_obj(resp.json())
        self._token = tr.access_token
        self._expires_at = time.time() + tr.expires_in - 60  # refresh 60s early
        logger.info("Obtained new token (valid %ss)", tr.expires_in)
