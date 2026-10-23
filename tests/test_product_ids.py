import json
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app import consumer
from app.models import OrderItem
from app.main import app
from httpx import ASGITransport, AsyncClient
from tests.test_consumer import Delivery


@pytest.mark.parametrize('product_id', ['', ' ', '\t\n'])
def test_blank_product_ids_are_invalid(product_id):
    with pytest.raises(ValidationError, match='productId'):
        OrderItem(productId=product_id)


@pytest.mark.asyncio
@pytest.mark.parametrize('product_id', ['', ' ', '\t\n'])
async def test_invalid_ids_discard_entire_order_before_redis_write(monkeypatch, product_id):
    record = AsyncMock()
    monkeypatch.setattr(consumer, 'record_order', record)
    delivery = Delivery(json.dumps({'order': {'id': 'o1', 'orderItems': [
        {'productId': 'valid'}, {'productId': product_id}
    ]}}).encode())
    await consumer._handle_message(delivery)
    record.assert_not_awaited()
    delivery.ack.assert_awaited_once_with()
    delivery.reject.assert_not_awaited()


def test_nonblank_ids_keep_their_exact_identity():
    for product_id in ['SKU-1', '0', ' SKU-1 ', '商品']:
        assert OrderItem(productId=product_id).productId == product_id


@pytest.mark.asyncio
@pytest.mark.parametrize('product_id', ['', ' ', '\t\n'])
async def test_internal_api_rejects_blank_ids_before_recording(monkeypatch, product_id):
    from app.routers import internal
    record = AsyncMock()
    monkeypatch.setattr(internal, 'record_order', record)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/internal/events/order-created', json={
            'order': {'id': 'o1', 'orderItems': [{'productId': product_id}]}
        })
    assert response.status_code == 422
    record.assert_not_awaited()
