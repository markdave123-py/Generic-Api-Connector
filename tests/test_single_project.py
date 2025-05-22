# tests/test_single_project.py

import pytest


@pytest.mark.asyncio
async def test_get_project(live_client):
    project = await live_client.get_project(3)
    assert project.id == 3
    assert project.name == "Item 3"
    assert project.value == 4.5
