import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture
async def client():
    # Use ASGITransport to properly handle ASGI apps with httpx
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
