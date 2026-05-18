import httpx

from app.core.config import settings


def trigger_review_analysis_sync(review_id: int) -> None:
    """Gọi AI worker (đồng bộ, best-effort) — dùng với FastAPI BackgroundTasks."""
    url = f"{settings.ai_worker_url.rstrip('/')}/analyze/{review_id}"
    try:
        httpx.post(url, timeout=120.0)
    except httpx.HTTPError:
        pass


async def trigger_review_analysis(review_id: int) -> None:
    """Gọi AI worker bất đồng bộ."""
    url = f"{settings.ai_worker_url.rstrip('/')}/analyze/{review_id}"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            await client.post(url)
    except httpx.HTTPError:
        pass
