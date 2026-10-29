import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from app import redis_store
from app.main import app

@pytest.mark.asyncio
async def test_sparse_related_results_are_filled_without_duplicates(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_store, '_client', fake)
    await redis_store.record_order(['A', 'B'])
    await redis_store.record_order(['C'])
    await redis_store.record_order(['D'])
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/recommendations/products/A?limit=3')
        items = response.json()['recommendations']
        assert response.status_code == 200
        assert response.json()['strategy'] == 'item-cooccurrence'
        assert items[0]['productId'] == 'B'
        assert {item['productId'] for item in items} == {'B', 'C', 'D'}
        limited = await client.get('/recommendations/products/A?limit=1')
        assert [x['productId'] for x in limited.json()['recommendations']] == ['B']
    await fake.aclose()
