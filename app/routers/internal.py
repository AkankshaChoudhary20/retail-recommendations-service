"""Test/manual-only ingestion path.

The primary way this service learns about orders is the RabbitMQ consumer
(app/consumer.py). This endpoint exists so the docker-compose stack and
integration tests can feed it order data without standing up RabbitMQ.
"""
from fastapi import APIRouter

from app.models import OrderCreatedEvent
from app.redis_store import record_order

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events/order-created", status_code=202)
async def ingest_order_created(event: OrderCreatedEvent):
    product_ids = [item.productId for item in event.order.orderItems]
    await record_order(product_ids)
    return {"recorded": len(product_ids)}
