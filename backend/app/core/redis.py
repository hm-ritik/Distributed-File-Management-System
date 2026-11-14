from redis.asyncio import Redis
from app.core.config import settings


async def create_redis_client() -> Redis:
    redis_client = Redis.from_url(settings.REDIS_URL,decode_responses=True)

    await redis_client.ping()
    return redis_client
