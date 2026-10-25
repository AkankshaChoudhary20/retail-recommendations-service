import asyncio
import pytest
from app import consumer

@pytest.mark.asyncio
async def test_start_is_idempotent_and_can_restart(monkeypatch):
    async def consume():
        await asyncio.Future()
    monkeypatch.setattr(consumer.settings, 'messaging_provider', 'rabbitmq')
    monkeypatch.setattr(consumer, '_run', consume)
    monkeypatch.setattr(consumer, '_task', None)
    try:
        consumer.start()
        first = consumer._task
        consumer.start()
        assert consumer._task is first
        await consumer.stop()
        consumer.start()
        assert consumer._task is not first
    finally:
        await consumer.stop()
