import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

import app.redis_store as redis_store
from app.main import app


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_store, "_client", fake)
    yield fake


@pytest.mark.asyncio
async def test_popular_is_empty_with_no_data(fake_redis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/recommendations/popular")
    assert resp.status_code == 200
    assert resp.json()["recommendations"] == []


@pytest.mark.asyncio
async def test_related_products_falls_back_to_popular(fake_redis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Two orders: {A, B}, {A, C} -> A is popular, B/C co-occur with A only.
        await client.post("/internal/events/order-created", json={
            "order": {"id": "o1", "orderItems": [{"productId": "A"}, {"productId": "B"}]}
        })
        await client.post("/internal/events/order-created", json={
            "order": {"id": "o2", "orderItems": [{"productId": "A"}, {"productId": "C"}]}
        })

        related = await client.get("/recommendations/products/A")
        assert related.status_code == 200
        body = related.json()
        assert body["strategy"] == "item-cooccurrence"
        related_ids = {r["productId"] for r in body["recommendations"]}
        assert related_ids == {"B", "C"}

        # D was never purchased, so it has no co-occurrence data -> falls back to popularity.
        fallback = await client.get("/recommendations/products/D")
        assert fallback.status_code == 200
        assert fallback.json()["strategy"] == "popular-fallback"

        popular = await client.get("/recommendations/popular")
        assert popular.json()["recommendations"][0]["productId"] == "A"


@pytest.mark.asyncio
async def test_liveness_and_readiness(fake_redis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        live = await client.get("/health/liveness")
        ready = await client.get("/health/readiness")
    assert live.status_code == 200
    assert ready.status_code == 200
