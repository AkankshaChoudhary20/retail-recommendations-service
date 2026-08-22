from fastapi import APIRouter, Query

from app.config import settings
from app.models import RecommendationItem, RecommendationResponse
from app.redis_store import get_popular, get_related

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations/products/{product_id}", response_model=RecommendationResponse)
async def related_products(
    product_id: str,
    limit: int = Query(default=settings.default_limit, ge=1, le=settings.max_limit),
):
    """"Customers who bought this also bought" for a single product.

    Falls back to global popularity when there isn't yet enough co-purchase
    data for this product (cold start), so the endpoint always returns
    something useful.
    """
    related = await get_related(product_id, limit)
    strategy = "item-cooccurrence"

    if not related:
        popular = await get_popular(limit, exclude={product_id})
        related = popular
        strategy = "popular-fallback"

    return RecommendationResponse(
        productId=product_id,
        strategy=strategy,
        recommendations=[RecommendationItem(productId=p, score=s) for p, s in related],
    )


@router.get("/recommendations/popular", response_model=RecommendationResponse)
async def popular_products(
    limit: int = Query(default=settings.default_limit, ge=1, le=settings.max_limit),
):
    """Store-wide trending products, e.g. for a homepage "Popular right now" rail."""
    popular = await get_popular(limit)
    return RecommendationResponse(
        strategy="popular",
        recommendations=[RecommendationItem(productId=p, score=s) for p, s in popular],
    )
