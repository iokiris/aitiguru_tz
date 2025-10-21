"""
Pydantic схемы для категорий
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema


class CategoryBase(BaseModel):
    """Базовая схема категории"""

    name: str = Field(..., min_length=1, max_length=255, description="Название категории")
    parent_id: Optional[int] = Field(None, description="ID родительской категории")
    is_active: bool = Field(True, description="Активна ли категория")


class CategoryCreate(CreateSchema, CategoryBase):
    """Схема для создания категории"""

    pass


class CategoryUpdate(UpdateSchema):
    """Схема для обновления категории"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseSchema, CategoryBase):
    """Схема ответа для категории"""

    level: int = Field(..., description="Уровень вложенности")
    path: Optional[str] = Field(None, description="Путь в дереве")
    children_count: Optional[int] = Field(None, description="Количество дочерних элементов")

    class Config:
        from_attributes = True


class CategoryTree(CategoryResponse):
    """Схема дерева категорий"""

    children: List["CategoryTree"] = Field(default_factory=list, description="Дочерние категории")

    class Config:
        from_attributes = True


class CategoryHierarchy(BaseModel):
    """Схема иерархии категорий"""

    id: int
    name: str
    level: int
    path: Optional[str]
    full_path: str = Field(..., description="Полный путь в дереве")


class CategoryStats(BaseModel):
    """Статистика по категории"""

    category_id: int
    category_name: str
    products_count: int = Field(..., description="Количество товаров")
    total_quantity: int = Field(..., description="Общее количество на складе")
    avg_price: float = Field(..., description="Средняя цена")
    min_price: float = Field(..., description="Минимальная цена")
    max_price: float = Field(..., description="Максимальная цена")
    total_value: float = Field(..., description="Общая стоимость")


# Разрешаем forward references
CategoryTree.model_rebuild()
