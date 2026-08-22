"""RabbitMQ consumer that ingests order-created events.

Binds to the same fanout exchange ("orders-exchange") that the orders
service's RabbitMQMessagingConfig already publishes OrderCreatedEvent to, so
this service learns about new orders without the orders service knowing
recommendations exists at all.
"""
import asyncio
import json
import logging

import aio_pika

from app.config import settings
from app.models import OrderCreatedEvent
from app.redis_store import record_order

logger = logging.getLogger("recommendations.consumer")

_task: asyncio.Task | None = None


async def _handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            payload = json.loads(message.body)
            event = OrderCreatedEvent.model_validate(payload)
        except Exception:
            logger.exception("Discarding unparseable order-created message")
            return

        product_ids = [item.productId for item in event.order.orderItems]
        await record_order(product_ids)
        logger.info("Recorded order %s with %d items", event.order.id, len(product_ids))


async def _run() -> None:
    url = f"amqp://{settings.rabbitmq_username}:{settings.rabbitmq_password}@{settings.rabbitmq_addresses}/"
    while True:
        try:
            connection = await aio_pika.connect_robust(url)
            async with connection:
                channel = await connection.channel()
                # non-durable, matching the orders service's FanoutExchange declaration
                exchange = await channel.declare_exchange(
                    settings.rabbitmq_exchange, aio_pika.ExchangeType.FANOUT, durable=False
                )
                queue = await channel.declare_queue(settings.rabbitmq_queue, durable=False)
                await queue.bind(exchange)
                logger.info("Consuming order events from exchange=%s queue=%s", exchange.name, queue.name)
                await queue.consume(_handle_message)
                await asyncio.Future()  # run until the connection drops
        except Exception:
            logger.exception("RabbitMQ consumer error, retrying in 5s")
            await asyncio.sleep(5)


def start() -> None:
    global _task
    if settings.messaging_provider != "rabbitmq":
        logger.info("Messaging provider is %r, order event consumer disabled", settings.messaging_provider)
        return
    _task = asyncio.create_task(_run())


async def stop() -> None:
    if _task is not None:
        _task.cancel()
