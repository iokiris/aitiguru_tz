"""
Базовые Pydantic схемы
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Базовая схема с общими полями"""

    id: int
    uuid: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateSchema(BaseModel):
    """Базовая схема для создания"""

    pass


class UpdateSchema(BaseModel):
    """Базовая схема для обновления"""

    pass


class ResponseSchema(BaseSchema):
    """Базовая схема для ответа"""

    pass


class PaginationParams(BaseModel):
    """Параметры пагинации"""

    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(20, ge=1, le=100, description="Размер страницы")

    @property
    def offset(self) -> int:
        """Смещение для SQL запроса"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    """Пагинированный ответ"""

    items: list
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, size: int):
        """Создание пагинированного ответа"""
        pages = (total + size - 1) // size
        return cls(items=items, total=total, page=page, size=size, pages=pages)
