"""
Главный роутер API v1
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analytics, categories, clients, nomenclature, orders

# Создание главного роутера
api_router = APIRouter()

# Подключение всех роутеров
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])

api_router.include_router(nomenclature.router, prefix="/nomenclature", tags=["nomenclature"])

api_router.include_router(clients.router, prefix="/clients", tags=["clients"])

api_router.include_router(orders.router, prefix="/orders", tags=["orders"])

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
