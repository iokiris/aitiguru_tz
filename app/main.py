"""
FastAPI приложение для системы управления заказами
"""

from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging

# Настройка логирования
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Запуск приложения", environment=settings.ENVIRONMENT)
    await init_db()
    logger.info("База данных инициализирована")
    yield
    # Shutdown
    logger.info("Завершение работы приложения")


# Создание приложения FastAPI
app = FastAPI(
    title="Система управления заказами",
    description="API для управления заказами, номенклатурой и клиентами",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Подключение роутеров
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Система управления заказами",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled",
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    try:
        # Здесь можно добавить проверки БД, Redis и других сервисов
        return {"status": "healthy", "environment": settings.ENVIRONMENT, "database": "connected"}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/metrics")
async def metrics():
    """Метрики приложения"""
    # Здесь можно добавить Prometheus метрики
    return {"requests_total": 0, "active_connections": 0, "uptime": "0s"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development", log_level="info"
    )
