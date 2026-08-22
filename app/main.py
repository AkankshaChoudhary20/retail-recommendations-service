import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app import consumer
from app.routers import health, internal, recommendations

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer.start()
    yield
    await consumer.stop()


app = FastAPI(
    title="retail-store-sample-recommendations",
    description="Item-based product recommendations for the retail-store-sample-app",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(health.router)
app.include_router(recommendations.router)
app.include_router(internal.router)
