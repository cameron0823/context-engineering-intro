"""
Cache implementation for the Tree Service Estimating application.

Uses Redis for distributed caching with fallback to in-memory cache.
"""
import json
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError
import structlog

from src.core.config import settings


logger = structlog.get_logger()


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class InMemoryCache:
    """Simple in-memory cache fallback when Redis is unavailable."""
    
    def __init__(self):
        self._cache: dict = {}
        self._expiry: dict = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check if key exists and hasn't expired
        if key in self._cache:
            if key in self._expiry:
                if datetime.utcnow() > self._expiry[key]:
                    # Expired, remove it
                    del self._cache[key]
                    del self._expiry[key]
                    return None
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with optional expiration in seconds."""
        self._cache[key] = value
        if expire:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=expire)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self.get(key) is not None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if key in self._cache:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=seconds)
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._expiry.clear()
    
    async def close(self) -> None:
        """Close cache connection (no-op for in-memory)."""
        pass


class RedisCache:
    """Redis-based cache implementation."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = settings.CACHE_TTL_SECONDS
        self._connected = False
    
    async def connect(self):
        """Connect to Redis."""
        if self._connected:
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except RedisError as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise CacheError(f"Redis connection failed: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client and self._connected:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Return as string if not JSON
                    return value
            return None
        except RedisError as e:
            logger.error("Redis get error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration in seconds."""
        if not self._connected:
            await self.connect()
        
        try:
            # Serialize to JSON if not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            # Use default TTL if not specified
            expire = expire or self.default_ttl
            
            return await self.redis_client.set(key, value, ex=expire)
        except RedisError as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._connected:
            await self.connect()
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            await self.connect()
        
        try:
            return await self.redis_client.exists(key) > 0
        except RedisError as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self._connected:
            await self.connect()
        
        try:
            return await self.redis_client.expire(key, seconds)
        except RedisError as e:
            logger.error("Redis expire error", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        if not self._connected:
            await self.connect()
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error("Redis clear pattern error", pattern=pattern, error=str(e))
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        if not self._connected:
            await self.connect()
        
        try:
            return await self.redis_client.incr(key, amount)
        except RedisError as e:
            logger.error("Redis increment error", key=key, error=str(e))
            return None
    
    async def set_hash(self, key: str, field: str, value: Any) -> bool:
        """Set a field in a hash."""
        if not self._connected:
            await self.connect()
        
        try:
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            return await self.redis_client.hset(key, field, value)
        except RedisError as e:
            logger.error("Redis hset error", key=key, field=field, error=str(e))
            return False
    
    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """Get a field from a hash."""
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.redis_client.hget(key, field)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except RedisError as e:
            logger.error("Redis hget error", key=key, field=field, error=str(e))
            return None
    
    async def get_all_hash(self, key: str) -> dict:
        """Get all fields from a hash."""
        if not self._connected:
            await self.connect()
        
        try:
            data = await self.redis_client.hgetall(key)
            result = {}
            for field, value in data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            return result
        except RedisError as e:
            logger.error("Redis hgetall error", key=key, error=str(e))
            return {}
    
    async def close(self) -> None:
        """Close cache connection."""
        await self.disconnect()


class CacheManager:
    """
    Main cache manager that handles Redis with in-memory fallback.
    """
    
    def __init__(self):
        self.redis_cache: Optional[RedisCache] = None
        self.memory_cache = InMemoryCache()
        self.use_redis = True
        self._initialized = False
    
    async def initialize(self):
        """Initialize cache connection."""
        if self._initialized:
            return
        
        # Try to connect to Redis
        if settings.REDIS_URL and self.use_redis:
            try:
                self.redis_cache = RedisCache(settings.REDIS_URL)
                await self.redis_cache.connect()
                self._initialized = True
                logger.info("Cache initialized with Redis")
            except CacheError:
                logger.warning("Redis unavailable, falling back to in-memory cache")
                self.use_redis = False
                self._initialized = True
        else:
            logger.info("Cache initialized with in-memory storage")
            self.use_redis = False
            self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.get(key)
        return await self.memory_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.set(key, value, expire)
        return await self.memory_cache.set(key, value, expire)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.delete(key)
        return await self.memory_cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.exists(key)
        return await self.memory_cache.exists(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.expire(key, seconds)
        return await self.memory_cache.expire(key, seconds)
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern (Redis only)."""
        if not self._initialized:
            await self.initialize()
        
        if self.use_redis and self.redis_cache:
            return await self.redis_cache.clear_pattern(pattern)
        # For in-memory, we'd need to implement pattern matching
        return 0
    
    async def close(self):
        """Close cache connections."""
        if self.redis_cache:
            await self.redis_cache.close()
        await self.memory_cache.close()
        self._initialized = False


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get or create the cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def init_cache():
    """Initialize the cache system."""
    cache = get_cache()
    await cache.initialize()


async def close_cache():
    """Close cache connections."""
    cache = get_cache()
    await cache.close()