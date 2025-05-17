import httpx
import pytest
from connector.client import APIClient

class _DummyTransport(httpx.AsyncBaseTransport):
    def __init__(self, fail_times=2):
        self._fail_times = fail_times
    async def handle_async_request(self, request):
        if self._fail_times > 0:
            self._fail_times -= 1
            raise httpx.ConnectTimeout("boom")
        return httpx.Response(200, json={"page": 1, "total_pages": 1, "items": []})

@pytest.mark.asyncio
async def test_retry_logic():
    client = APIClient(base_url="http://example")
    client._client._transport = _DummyTransport()
    # Skip hitting /oauth2/token
    client._oauth._token = "dummy"
    client._oauth._expires_at = 9999999999
    items = await client.list_all_items(concurrent=False)
    assert items == []
    await client.close()
