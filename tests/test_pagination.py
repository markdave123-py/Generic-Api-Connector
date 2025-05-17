import pytest

@pytest.mark.asyncio
async def test_pagination(live_client):
    items = await live_client.list_all_items(concurrent=False)
    assert [i.id for i in items] == [1, 2, 3, 4, 5]
