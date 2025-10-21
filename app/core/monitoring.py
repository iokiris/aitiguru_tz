"""
Мониторинг и метрики приложения
"""

import time
from typing import Any, Dict

import structlog
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = structlog.get_logger()

# Метрики Prometheus
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"])

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

ACTIVE_CONNECTIONS = Gauge("active_connections", "Number of active connections")

DATABASE_CONNECTIONS = Gauge("database_connections", "Number of database connections")

CACHE_HITS = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

CACHE_MISSES = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

ERROR_COUNT = Counter("errors_total", "Total errors", ["error_type", "endpoint"])


class MetricsCollector:
    """Сборщик метрик"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Запись метрики запроса"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        self.request_count += 1

        logger.info("Request processed", method=method, endpoint=endpoint, status_code=status_code, duration=duration)

    def record_error(self, error_type: str, endpoint: str):
        """Запись метрики ошибки"""
        ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()

        self.error_count += 1

        logger.error("Error recorded", error_type=error_type, endpoint=endpoint)

    def record_cache_hit(self, cache_type: str):
        """Запись попадания в кэш"""
        CACHE_HITS.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Запись промаха кэша"""
        CACHE_MISSES.labels(cache_type=cache_type).inc()

    def get_uptime(self) -> float:
        """Получение времени работы"""
        return time.time() - self.start_time

    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            "uptime_seconds": self.get_uptime(),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "requests_per_second": self.request_count / max(self.get_uptime(), 1),
            "error_rate": self.error_count / max(self.request_count, 1),
        }


# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()


async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик"""
    start_time = time.time()

    # Получаем информацию о запросе
    method = request.method
    endpoint = request.url.path

    try:
        # Выполняем запрос
        response = await call_next(request)

        # Записываем метрики
        duration = time.time() - start_time
        metrics_collector.record_request(method, endpoint, response.status_code, duration)

        return response

    except Exception as e:
        # Записываем ошибку
        metrics_collector.record_error(type(e).__name__, endpoint)
        raise


def get_metrics() -> str:
    """Получение метрик в формате Prometheus"""
    return generate_latest()


def get_metrics_response() -> Response:
    """Получение ответа с метриками"""
    return PlainTextResponse(get_metrics(), media_type=CONTENT_TYPE_LATEST)


def get_health_stats() -> Dict[str, Any]:
    """Получение статистики здоровья системы"""
    stats = metrics_collector.get_stats()

    return {
        "status": "healthy",
        "uptime_seconds": stats["uptime_seconds"],
        "total_requests": stats["total_requests"],
        "requests_per_second": stats["requests_per_second"],
        "error_rate": stats["error_rate"],
        "active_connections": ACTIVE_CONNECTIONS._value.get(),
        "database_connections": DATABASE_CONNECTIONS._value.get(),
    }
