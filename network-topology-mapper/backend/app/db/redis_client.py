import json
import logging
from typing import Any, Optional
import redis

from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        settings = get_settings()
        try:
            self._client = redis.from_url(settings.redis_url, decode_responses=True)
            self._client.ping()
            logger.info("Connected to Redis at %s", settings.redis_url)
        except Exception as e:
            logger.warning("Redis not available: %s. Using in-memory fallback.", e)
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def close(self):
        if self._client:
            self._client.close()

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self._client:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._client.setex(key, ttl, value)

    def get(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        return self._client.get(key)

    def get_json(self, key: str) -> Optional[Any]:
        val = self.get(key)
        if val:
            return json.loads(val)
        return None

    def delete(self, key: str) -> None:
        if not self._client:
            return
        self._client.delete(key)

    def publish(self, channel: str, message: dict) -> None:
        if not self._client:
            return
        self._client.publish(channel, json.dumps(message))

    def subscribe(self, channel: str):
        if not self._client:
            return None
        pubsub = self._client.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def set_scan_progress(self, scan_id: str, progress: dict) -> None:
        self.set(f"scan:progress:{scan_id}", progress, ttl=3600)

    def get_scan_progress(self, scan_id: str) -> Optional[dict]:
        return self.get_json(f"scan:progress:{scan_id}")


redis_client = RedisClient()
