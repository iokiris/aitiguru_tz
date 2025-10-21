"""
Конфигурация приложения
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # База данных
    DATABASE_URL: str = "postgresql://app_user:app_password@localhost:5434/order_management"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_POOL_SIZE: int = 10

    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]

    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Система управления заказами"

    # Пагинация
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Кэширование
    CACHE_TTL: int = 300  # 5 минут

    # Безопасность
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Создаем экземпляр настроек
settings = Settings()

# Настройки для разных окружений
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
elif settings.ENVIRONMENT == "testing":
    settings.DATABASE_URL = "postgresql://app_user:app_password@localhost:5434/order_management_test"
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
