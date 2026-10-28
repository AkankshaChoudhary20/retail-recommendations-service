"""Redis-backed item-item co-purchase store.

Two structures are maintained per Redis DB:
  - cooccur:{productId}  (sorted set)  member=otherProductId, score=co-purchase count
  - popularity:global     (sorted set)  member=productId,      score=total purchase count

This is a simple, explainable form of item-based collaborative filtering:
products that are frequently bought together in the same order end up with
a high mutual score, so "people who bought X also bought Y" falls out of a
single ZINCRBY per pair, with no offline training step required.
"""
import itertools

import redis.asyncio as redis

from app.config import settings

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def record_order(product_ids: list[str]) -> None:
    """Update co-occurrence and popularity counts for one completed order."""
    distinct = sorted(set(product_ids))
    if not distinct:
        return

    client = get_client()
    # Publish popularity and both directions of every pair atomically.
    pipe = client.pipeline(transaction=True)

    for product_id in distinct:
        pipe.zincrby("popularity:global", 1, product_id)

    for a, b in itertools.permutations(distinct, 2):
        pipe.zincrby(f"cooccur:{a}", 1, b)

    await pipe.execute()


async def get_related(product_id: str, limit: int) -> list[tuple[str, float]]:
    if limit <= 0:
        return []
    client = get_client()
    pairs = await client.zrevrange(f"cooccur:{product_id}", 0, limit - 1, withscores=True)
    return [(member, score) for member, score in pairs]


async def get_popular(limit: int, exclude: set[str] | None = None) -> list[tuple[str, float]]:
    if limit <= 0:
        return []
    client = get_client()
    # Over-fetch a little so we can drop excluded ids without a second round trip.
    fetch = limit + len(exclude or [])
    pairs = await client.zrevrange("popularity:global", 0, fetch - 1, withscores=True)
    if exclude:
        pairs = [(m, s) for m, s in pairs if m not in exclude]
    return pairs[:limit]


async def ping() -> bool:
    client = get_client()
    return await client.ping()

