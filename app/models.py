from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    productId: str
    quantity: int = 1


class Order(BaseModel):
    id: str
    orderItems: list[OrderItem] = Field(default_factory=list)


class OrderCreatedEvent(BaseModel):
    """Mirrors orders/events/order-created-event.schema.json."""
    order: Order


class RecommendationItem(BaseModel):
    productId: str
    score: float


class RecommendationResponse(BaseModel):
    productId: str | None = None
    strategy: str
    recommendations: list[RecommendationItem]
