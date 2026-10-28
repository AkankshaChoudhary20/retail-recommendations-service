from unittest.mock import AsyncMock, Mock
import pytest
from app import redis_store


@pytest.mark.asyncio
async def test_all_order_counters_are_committed_in_one_transaction(monkeypatch):
    pipe = Mock()
    pipe.execute = AsyncMock()
    client = Mock()
    client.pipeline.return_value = pipe
    monkeypatch.setattr(redis_store, '_client', client)
    await redis_store.record_order(['B', 'A', 'A'])
    client.pipeline.assert_called_once_with(transaction=True)
    assert pipe.zincrby.call_count == 4
    pipe.execute.assert_awaited_once()
