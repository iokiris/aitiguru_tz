"""
Система кэширования
"""

import json
from typing import Any, Optional

import redis
import structlog
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.monitoring import metrics_collector

logger = structlog.get_logger()


class CacheManager:
    """Менеджер кэширования"""

    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Подключение к Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Проверяем подключение
            self.redis_client.ping()
            logger.info("Redis connection established")

        except RedisError as e:
            logger.error("Failed to connect to Redis", error=str(e))
            self.redis_client = None

    def _is_connected(self) -> bool:
        """Проверка подключения к Redis"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if not self._is_connected():
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                metrics_collector.record_cache_miss("redis")
                return None

            # Пытаемся десериализовать JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Если не JSON, возвращаем как строку
                return value

        except RedisError as e:
            logger.error("Redis get error", key=key, error=str(e))
            metrics_collector.record_cache_miss("redis")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение значения в кэш"""
        if not self._is_connected():
            return False

        try:
            # Сериализуем значение
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)

            # Устанавливаем TTL
            if ttl is None:
                ttl = settings.CACHE_TTL

            result = self.redis_client.setex(key, ttl, serialized_value)

            if result:
                metrics_collector.record_cache_hit("redis")
                logger.debug("Cache set", key=key, ttl=ttl)

            return bool(result)

        except RedisError as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if not self._is_connected():
            return False

        try:
            result = self.redis_client.delete(key)
            logger.debug("Cache delete", key=key, deleted=bool(result))
            return bool(result)

        except RedisError as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Удаление значений по паттерну"""
        if not self._is_connected():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.debug("Cache delete pattern", pattern=pattern, deleted=deleted)
                return deleted
            return 0

        except RedisError as e:
            logger.error("Redis delete pattern error", pattern=pattern, error=str(e))
            return 0

    def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self._is_connected():
            return False

        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False

    def get_ttl(self, key: str) -> int:
        """Получение TTL ключа"""
        if not self._is_connected():
            return -1

        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            logger.error("Redis TTL error", key=key, error=str(e))
            return -1

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Увеличение числового значения"""
        if not self._is_connected():
            return None

        try:
            return self.redis_client.incrby(key, amount)
        except RedisError as e:
            logger.error("Redis increment error", key=key, error=str(e))
            return None

    def get_stats(self) -> dict:
        """Получение статистики кэша"""
        if not self._is_connected():
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except RedisError as e:
            logger.error("Redis stats error", error=str(e))
            return {"status": "error", "error": str(e)}


# Глобальный экземпляр менеджера кэша
cache_manager = CacheManager()


def cache_key(prefix: str, *args) -> str:
    """Генерация ключа кэша"""
    key_parts = [prefix] + [str(arg) for arg in args]
    return ":".join(key_parts)


def cached(prefix: str, ttl: Optional[int] = None):
    """Декоратор для кэширования результатов функций"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            key = cache_key(prefix, func.__name__, *args, *kwargs.values())

            # Пытаемся получить из кэша
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result

            # Выполняем функцию
            result = func(*args, **kwargs)

            # Сохраняем в кэш
            cache_manager.set(key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """Инвалидация кэша по паттерну"""
    return cache_manager.delete_pattern(pattern)
