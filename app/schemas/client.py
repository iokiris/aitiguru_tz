"""
Pydantic схемы для клиентов
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema


class ClientBase(BaseModel):
    """Базовая схема клиента"""

    name: str = Field(..., min_length=1, max_length=255, description="ФИО клиента")
    email: Optional[EmailStr] = Field(None, description="Email клиента")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон клиента")
    address: str = Field(..., min_length=1, description="Адрес клиента")
    is_active: bool = Field(True, description="Активен ли клиент")


class ClientCreate(CreateSchema, ClientBase):
    """Схема для создания клиента"""

    pass


class ClientUpdate(UpdateSchema):
    """Схема для обновления клиента"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class ClientResponse(BaseSchema, ClientBase):
    """Схема ответа для клиента"""

    orders_count: Optional[int] = Field(None, description="Количество заказов")
    total_spent: Optional[float] = Field(None, description="Общая сумма заказов")

    class Config:
        from_attributes = True


class ClientStats(BaseModel):
    """Статистика по клиенту"""

    client_id: int
    client_name: str
    total_amount: float = Field(..., description="Общая сумма заказов")
    orders_count: int = Field(..., description="Количество заказов")
    avg_order: float = Field(..., description="Средний чек")
    last_order: Optional[str] = Field(None, description="Последний заказ")


class ClientSearch(BaseModel):
    """Параметры поиска клиентов"""

    query: Optional[str] = Field(None, description="Поисковый запрос")
    is_active: Optional[bool] = Field(True, description="Только активные")
