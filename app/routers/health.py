from fastapi import APIRouter, Response

from app.redis_store import ping

router = APIRouter(tags=["health"])


@router.get("/health/liveness")
async def liveness():
    return {"status": "UP"}


@router.get("/health/readiness")
async def readiness(response: Response):
    try:
        ok = await ping()
    except Exception:
        ok = False
    if not ok:
        response.status_code = 503
        return {"status": "DOWN"}
    return {"status": "UP"}
