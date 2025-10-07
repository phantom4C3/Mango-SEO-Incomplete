# backend/src/clients/redis_client.py

import logging
import json
import hashlib
from typing import Optional, Dict, Any
from upstash_redis.asyncio import Redis
from redis.exceptions import RedisError
from ..core.config import settings

logger = logging.getLogger(__name__)

# ----------------------------
# Singleton Upstash Redis client
# ----------------------------
redis_client = Redis(
url=settings.redis_url,
    token=settings.redis_token )

# ----------------------------
# Low-level helper functions
# ----------------------------
async def close_redis():
    """Close Redis connection gracefully."""
    try:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
        logger.info("Redis connection closed.")
    except RedisError as e:
        logger.warning(f"Failed to close Redis: {e}")


async def ping_redis() -> bool:
    """Check Redis connectivity."""
    try:
        return await redis_client.ping()
    except RedisError as e:
        logger.error(f"Redis ping failed: {e}")
        return False


# ----------------------------
# High-level cache utilities
# ----------------------------
class RedisCache:
    """High-impact, short-lived cache for expensive operations (tasks, scrape results, etc.)."""

    @staticmethod
    def _generate_url_hash(url: str) -> str:
        """Generate consistent hash for URL-based keys."""
        return hashlib.md5(url.encode()).hexdigest()

    # --- TASK STATUS (60 seconds) ---
    @staticmethod
    async def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        key = f"task:{task_id}:status"
        value = await redis_client.get(key)
        return json.loads(value) if value else None

    @staticmethod
    async def set_task_status(task_id: str, status_data: Dict[str, Any], ttl: int = 60):
        key = f"task:{task_id}:status"
        await redis_client.setex(key, ttl, json.dumps(status_data))

    @staticmethod
    async def clear_task_status(task_id: str):
        key = f"task:{task_id}:status"
        await redis_client.delete(key)

    # --- SCRAPE RESULTS (5 minutes) ---
    @staticmethod
    async def get_scrape_result(url: str) -> Optional[Dict[str, Any]]:
        url_hash = RedisCache._generate_url_hash(url)
        key = f"scrape:{url_hash}"
        value = await redis_client.get(key)
        return json.loads(value) if value else None

    @staticmethod
    async def set_scrape_result(url: str, scrape_data: Dict[str, Any], ttl: int = 300):
        url_hash = RedisCache._generate_url_hash(url)
        key = f"scrape:{url_hash}"
        await redis_client.setex(key, ttl, json.dumps(scrape_data))

    @staticmethod
    async def clear_scrape_result(url: str):
        url_hash = RedisCache._generate_url_hash(url)
        key = f"scrape:{url_hash}"
        await redis_client.delete(key)

    # --- UTILITY METHODS ---
    @staticmethod
    async def delete_key(key: str):
        await redis_client.delete(key)

    @staticmethod
    async def flush_all():
        """Clear all cache (mainly for dev/testing)."""
        await redis_client.flushall()

 
    @staticmethod
    async def cache_set(key: str, value: Any, ttl: int = 300):
        """Generic cache setter"""
        try:
            await redis_client.setex(key, ttl, json.dumps(value))
        except RedisError as e:
            logger.warning(f"Redis set failed for {key}: {str(e)}")

    @staticmethod
    async def cache_get(key: str) -> Optional[Any]:
        """Generic cache getter"""
        try:
            value = await redis_client.get(key)
            return json.loads(value) if value else None
        except RedisError as e:
            logger.warning(f"Redis get failed for {key}: {str(e)}")
            return None
 




# Redis is **not mandatory** for all backend operations. Its main purposes are:

# 1. **Celery broker & result backend**

#    * Celery needs a **message broker** to queue tasks and optionally store results.
#    * Common brokers: **Redis**, RabbitMQ.
#    * Without a broker, Celery **cannot schedule or run async tasks reliably**.

# 2. **Caching / Rate limiting / Concurrency control**

#    * Redis is very fast for temporary data, counters, and locks.
#    * Example: rate-limiting API requests, storing ephemeral job states, caching expensive queries.

# ---

# ## 2️⃣ How Celery uses Redis

# * **Broker**: Celery pushes tasks to Redis (list/queue). Workers pull tasks from Redis.
# * **Result backend** (optional): Celery can store task results in Redis so you can check later.

# Example:

# ```python
# # celery config
# broker_url = "redis://localhost:6379/0"
# result_backend = "redis://localhost:6379/1"
# ```

# * Task push → Redis list → Worker pops task → Executes → Stores result in Redis.

# ✅ So, if your backend needs **async task processing**, you either need Redis or another broker.
# ❌ If you are not using Celery in the backend yet, Redis is not required.

# ---

# ## 3️⃣ Can you just use Supabase?

# * Supabase is **Postgres + Realtime + Auth**, not a message broker.
# * Celery **cannot use Supabase as a broker**.
# * Supabase can store **persistent results**, but it’s **not suitable for high-throughput async queues**.

# So **for Celery in backend**, Redis is necessary.

# ---

# ## 4️⃣ Do you copy the blogwriter Redis client?

# * Blogwriter uses **Upstash Redis async client**, fully featured with JSON handling, TTL, atomic increments, etc.
# * Your backend example uses `aioredis.from_url` — simpler but works for Celery.

# **Recommendation:**

# * If backend just needs **Celery**, you don’t need the full RedisClient from blogwriter.
# * If backend also needs **rate limiting, caching, or counters**, you can copy blogwriter’s `RedisClient` class for consistency.

# ---

# ### ✅ TL;DR Recommendations

# | Question                              | Answer                                                                                                            |
# | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
# | Do we need Redis in backend?          | Only if you plan to run **Celery tasks** or need **caching/rate-limiting**.                                       |
# | Can we use Supabase instead of Redis? | No, Supabase is not a task broker.                                                                                |
# | How does Celery use Redis?            | As **broker** (task queue) and optional **result backend**.                                                       |
# | Copy blogwriter RedisClient?          | Only if you need advanced Redis features (TTL, counters, JSON). For Celery, simple `aioredis.from_url` is enough. |

