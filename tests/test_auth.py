import pytest


@pytest.mark.asyncio
async def test_token_refresh_on_expiry(live_client):
    # Pretend the token is already expired
    live_client._oauth._expires_at = 1.0
    items = await live_client.list_all_items(concurrent=False)
    assert items  # refresh succeeded
