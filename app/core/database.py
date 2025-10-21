"""
Настройка подключения к базе данных
"""

import structlog
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = structlog.get_logger()

# Создание движка базы данных
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Метаданные для миграций
metadata = MetaData()


async def init_db():
    """Инициализация базы данных"""
    try:
        # Проверяем подключение
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Подключение к базе данных установлено")
        
        # Создаем таблицы (если не существуют)
        from app.db import models
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Таблицы базы данных созданы")
        except Exception as create_error:
            logger.warning("Таблицы уже существуют или ошибка создания", error=str(create_error))
        
    except Exception as e:
        logger.error("Ошибка подключения к базе данных", error=str(e))
        raise


def get_db():
    """Dependency для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Async dependency для получения сессии базы данных"""
    # Для async операций можно использовать asyncpg
    # Пока используем синхронную версию
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
