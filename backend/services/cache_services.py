import hashlib
import json
from upstash_redis import Redis
from datetime import datetime

from config import (
    UPSTASH_REDIS_REST_URL,
    UPSTASH_REDIS_REST_TOKEN
)

redis = Redis(
    url=UPSTASH_REDIS_REST_URL,
    token=UPSTASH_REDIS_REST_TOKEN
)

def generate_cache_key(
    processed_image_bytes: bytes,
    base_prompt: str,
    click_x: int | None,
    click_y: int | None
) -> str:
    """
    Generate a unique cache key based on the processed image
    and all parameters that affect the generated output.
    """

    hasher = hashlib.sha256()

    hasher.update(processed_image_bytes)
    hasher.update(base_prompt.encode())

    hasher.update(str(click_x).encode())
    hasher.update(str(click_y).encode())

    return hasher.hexdigest()

async def get_from_cache(
    cache_key: str
) -> dict | None:
    """
    Retrieve cached generation metadata from Redis.
    Returns None if no cache entry exists.
    """

    try:
        cached_data = redis.get(cache_key)

        if cached_data is None:
            return None

        return json.loads(cached_data)

    except Exception as e:
        print(f"Redis GET failed: {e}")
        return None

async def save_to_cache(
    cache_key: str,
    cache_data: dict,
    ttl: int = 3600
) -> bool:
    """
    Save generation metadata to Redis with a TTL.
    """

    try:
        cache_data["cached_at"] = datetime.utcnow().isoformat()

        redis.set(
            cache_key,
            json.dumps(cache_data),
            ex=ttl
        )

        return True

    except Exception as e:
        print(f"Redis SET failed: {e}")
        return False
    
async def get_cache_stats() -> dict:
    """
    Placeholder cache statistics.
    Can be expanded later with application-level metrics.
    """

    return {
        "provider": "Upstash Redis",
        "ttl_seconds": 3600,
        "status": "connected"
    }