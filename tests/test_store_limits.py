import fakeredis.aioredis
import pytest
from app import redis_store
@pytest.mark.asyncio
@pytest.mark.parametrize('limit',[0,-1,-10])
async def test_nonpositive_limits_return_no_recommendations(monkeypatch,limit):
 client=fakeredis.aioredis.FakeRedis(decode_responses=True)
 monkeypatch.setattr(redis_store,'_client',client)
 try:
  await redis_store.record_order(['A','B','C'])
  assert await redis_store.get_related('A',limit)==[]
  assert await redis_store.get_popular(limit)==[]
  assert await redis_store.get_popular(limit,exclude={'A'})==[]
  assert len(await redis_store.get_related('A',1))==1
  assert len(await redis_store.get_popular(1,exclude={'A'}))==1
 finally:
  await client.aclose()
