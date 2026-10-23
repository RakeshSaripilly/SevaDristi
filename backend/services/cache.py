"""
Redis Ephemeral Session Cache Manager
Provides 7-day TTL caching for ephemeral pre-verification session tokens.
Fallbacks to local memory cache if Redis is unavailable or offline.
"""

import os
import json
import logging
from typing import Optional, Any
import redis

logger = logging.getLogger("sevadristi.cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SEVEN_DAYS_SECONDS = 7 * 24 * 3600

class SessionCache:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._in_memory: dict = {}
        try:
            client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=1.0)
            client.ping()
            self.redis_client = client
            logger.info("Connected to Redis ephemeral cache server.")
        except Exception as e:
            logger.info(f"Redis unavailable ({e}). Using in-memory ephemeral fallback cache.")

    def set_session(self, session_id: str, data: dict, ttl: int = SEVEN_DAYS_SECONDS) -> bool:
        try:
            payload = json.dumps(data)
            if self.redis_client:
                self.redis_client.setex(f"session:{session_id}", ttl, payload)
                return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

        # Fallback to in-memory
        self._in_memory[session_id] = data
        return True

    def get_session(self, session_id: str) -> Optional[dict]:
        try:
            if self.redis_client:
                raw = self.redis_client.get(f"session:{session_id}")
                if raw:
                    return json.loads(raw)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")

    def delete_session(self, session_id: str) -> bool:
        try:
            if self.redis_client:
                self.redis_client.delete(f"session:{session_id}")
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

        self._in_memory.pop(session_id, None)
        return True

    def is_redis_connected(self) -> bool:
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.ping())
        except Exception:
            return False

session_cache = SessionCache()
