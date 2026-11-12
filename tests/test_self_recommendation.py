import asyncio
import fakeredis.aioredis
from app import redis_store

def test_related_products_exclude_self_without_losing_results(monkeypatch):
    async def run():
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(redis_store, '_client', client)
        try:
            await client.zadd('cooccur:A', {'A':100, 'B':10, 'C':5})
            assert await redis_store.get_related('A', 2) == [('B',10.0),('C',5.0)]
            assert await redis_store.get_related('A', 1) == [('B',10.0)]
        finally:
            await client.aclose()
    asyncio.run(run())
