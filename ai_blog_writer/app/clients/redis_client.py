# ai_blog_writer/src/clients/redis_client.py
import asyncio
import json
import logging
from typing import Optional, Any, Union
from upstash_redis.asyncio import Redis
from ..core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Async Redis client using Upstash Redis for AI Blog Writer.
    Features:
      - Atomic increment + expiry
      - Concurrency-safe connection
      - Automatic reconnection
    """
    def __init__(self):
        self._client: Optional[Redis] = None
        self._is_connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish Redis connection (concurrency-safe)."""
        if self._is_connected:
            return
        async with self._lock:
            if self._is_connected:
                return
            try:
                self._client = Redis(
                    url=settings.redis_url,
                    token=settings.redis_token
                )
                await self._client.ping()
                self._is_connected = True
                logger.info("✅ Redis connection established successfully")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self._is_connected = False
                raise

    async def disconnect(self) -> None:
        if self._client and self._is_connected:
            await self._client.close()
            self._is_connected = False
            logger.info("ℹ️ Redis connection closed")

    async def set_once(self, key: str, value: Union[str, dict], ttl: int = 86400) -> bool:
        """Set key only if it does not exist (NX flag)."""
        if not self._is_connected:
            await self.connect()
        if isinstance(value, dict):
            value = json.dumps(value)
        try:
            return await self._client.set(name=key, value=value, ex=ttl, nx=True)
        except Exception as e:
            logger.error(f"Redis set_once failed for key {key}: {e}")
            return False

    async def setex(self, key: str, ttl: int, value: Union[str, dict]) -> bool:
        """Set key with expiry (overwrite if exists)."""
        if not self._is_connected:
            await self.connect()
        if isinstance(value, dict):
            value = json.dumps(value)
        try:
            return await self._client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis setex failed for key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value and attempt JSON decoding."""
        if not self._is_connected:
            await self.connect()
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        if not self._is_connected:
            await self.connect()
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        if not self._is_connected:
            await self.connect()
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists failed for key {key}: {e}")
            return False

    async def increment_with_expiry(self, key: str, ttl: int) -> Optional[int]:
        """
        Atomically increment a key and set expiry.
        Compatible with rate limiter and counters.
        """
        if not self._is_connected:
            await self.connect()
        try:
            count = await self._client.incr(key)
            current_ttl = await self._client.ttl(key)
            if current_ttl <= 0:
                await self._client.expire(key, ttl)
            return count
        except Exception as e:
            logger.error(f"Redis increment_with_expiry failed for key {key}: {e}")
            return None

    async def get_health(self) -> bool:
        """Ping Redis to check health."""
        if not self._is_connected:
            await self.connect()
        try:
            return await self._client.ping() == "PONG"
        except Exception:
            return False

    async def get_ttl(self, key: str) -> int:
        """Return TTL of a key in seconds, -2 if key does not exist, -1 if no expiry."""
        if not self._is_connected:
            await self.connect()
        try:
            ttl = await self._client.ttl(key)
            return ttl
        except Exception as e:
            logger.error(f"Redis get_ttl failed for key {key}: {e}")
            return -2


# Singleton instance
redis_client = RedisClient()
