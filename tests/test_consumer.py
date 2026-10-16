import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aio_pika.message import IncomingMessage
from app import consumer


class Delivery:
    # Use aio-pika's real processing context and acknowledgment policy.
    process = IncomingMessage.process

    def __init__(self, body):
        self.body = body
        self.processed = False
        self.redelivered = False
        self.channel = SimpleNamespace(is_closed=False)
        self.ack = AsyncMock()
        self.reject = AsyncMock()


def valid_delivery():
    return Delivery(json.dumps({"order": {"id": "o1", "orderItems": [{"productId": "A"}]}}).encode())


@pytest.mark.asyncio
async def test_storage_failure_is_requeued_not_acknowledged(monkeypatch):
    record = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    monkeypatch.setattr(consumer, "record_order", record)
    delivery = valid_delivery()
    with pytest.raises(ConnectionError, match="Redis unavailable"):
        await consumer._handle_message(delivery)
    delivery.ack.assert_not_awaited()
    delivery.reject.assert_awaited_once_with(requeue=True)


@pytest.mark.asyncio
async def test_successful_storage_is_acknowledged(monkeypatch):
    record = AsyncMock()
    monkeypatch.setattr(consumer, "record_order", record)
    delivery = valid_delivery()
    await consumer._handle_message(delivery)
    record.assert_awaited_once_with(["A"])
    delivery.ack.assert_awaited_once_with()
    delivery.reject.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"not json", b'{"order": {"id": "o", "orderItems": [{"productId": "A", "quantity": 0}]}}'])
async def test_poison_payload_is_discarded_without_retry(monkeypatch, body):
    record = AsyncMock()
    monkeypatch.setattr(consumer, "record_order", record)
    delivery = Delivery(body)
    await consumer._handle_message(delivery)
    record.assert_not_awaited()
    delivery.ack.assert_awaited_once_with()
    delivery.reject.assert_not_awaited()
