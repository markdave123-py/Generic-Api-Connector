import pytest
import pytest_asyncio
from httpx import AsyncClient
from simapi.main import app as fastapi_app
from connector.client import APIClient
from httpx._transports.asgi import ASGITransport
from connector.registry import get_connector


@pytest.fixture()
async def api_client():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def live_client():
    """
    Returns an APIClient whose internal httpx client is wired
    to the in-process FastAPI sim (no real TCP).
    """
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        Connector = get_connector("sim")
        client = Connector(base_url="http://testserver")
        client._client = ac
        client._oauth._client = ac  # keep auth in sync
        yield client
        await client.close()
