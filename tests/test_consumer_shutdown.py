import asyncio
import pytest
from app import consumer

@pytest.mark.asyncio
async def test_stop_waits_for_resource_cleanup_and_resets_task(monkeypatch):
    started = asyncio.Event()
    cleaned = asyncio.Event()
    async def consume():
        try:
            started.set()
            await asyncio.Future()
        finally:
            await asyncio.sleep(0)
            cleaned.set()
    task = asyncio.create_task(consume())
    monkeypatch.setattr(consumer, '_task', task)
    await started.wait()
    try:
        await consumer.stop()
        assert cleaned.is_set()
        assert task.done()
        assert consumer._task is None
        await consumer.stop()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
