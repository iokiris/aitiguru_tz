"""
Pydantic схемы для номенклатуры
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema


class NomenclatureBase(BaseModel):
    """Базовая схема номенклатуры"""

    name: str = Field(..., min_length=1, max_length=255, description="Название товара")
    description: Optional[str] = Field(None, description="Описание товара")
    sku: Optional[str] = Field(None, max_length=100, description="Артикул")
    quantity: int = Field(0, ge=0, description="Количество на складе")
    price: Decimal = Field(..., gt=0, description="Цена")
    cost: Optional[Decimal] = Field(None, ge=0, description="Себестоимость")
    category_id: int = Field(..., description="ID категории")
    is_active: bool = Field(True, description="Активен ли товар")


class NomenclatureCreate(CreateSchema, NomenclatureBase):
    """Схема для создания номенклатуры"""

    pass


class NomenclatureUpdate(UpdateSchema):
    """Схема для обновления номенклатуры"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = Field(None, gt=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class NomenclatureResponse(BaseSchema, NomenclatureBase):
    """Схема ответа для номенклатуры"""

    category_name: Optional[str] = Field(None, description="Название категории")

    class Config:
        from_attributes = True


class NomenclatureStats(BaseModel):
    """Статистика по номенклатуре"""

    nomenclature_id: int
    name: str
    sku: Optional[str]
    category_name: str
    total_sold: int = Field(..., description="Количество продано")
    total_revenue: Decimal = Field(..., description="Общая выручка")
    orders_count: int = Field(..., description="Количество заказов")
    avg_price: Decimal = Field(..., description="Средняя цена продажи")


class NomenclatureSearch(BaseModel):
    """Параметры поиска номенклатуры"""

    query: Optional[str] = Field(None, description="Поисковый запрос")
    category_id: Optional[int] = Field(None, description="ID категории")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Минимальная цена")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Максимальная цена")
    in_stock: Optional[bool] = Field(None, description="Только в наличии")
    is_active: Optional[bool] = Field(True, description="Только активные")
