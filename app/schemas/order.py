"""
Pydantic схемы для заказов
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema


class OrderStatus(str, Enum):
    """Статусы заказа"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Статусы оплаты"""

    UNPAID = "unpaid"
    PAID = "paid"
    PARTIAL = "partial"
    REFUNDED = "refunded"


class OrderItemBase(BaseModel):
    """Базовая схема позиции заказа"""

    nomenclature_id: int = Field(..., description="ID номенклатуры")
    quantity: int = Field(..., gt=0, description="Количество")
    price: Decimal = Field(..., gt=0, description="Цена за единицу")
    total_price: Decimal = Field(..., gt=0, description="Общая стоимость")


class OrderItemCreate(OrderItemBase):
    """Схема для создания позиции заказа"""

    pass


class OrderItemResponse(BaseSchema, OrderItemBase):
    """Схема ответа для позиции заказа"""

    nomenclature_name: Optional[str] = Field(None, description="Название товара")
    nomenclature_sku: Optional[str] = Field(None, description="Артикул товара")

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Базовая схема заказа"""

    client_id: int = Field(..., description="ID клиента")
    order_date: Optional[datetime] = Field(None, description="Дата заказа")
    status: OrderStatus = Field(OrderStatus.PENDING, description="Статус заказа")
    payment_status: PaymentStatus = Field(PaymentStatus.UNPAID, description="Статус оплаты")
    notes: Optional[str] = Field(None, description="Примечания")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Позиции заказа")


class OrderCreate(CreateSchema, OrderBase):
    """Схема для создания заказа"""

    pass


class OrderUpdate(UpdateSchema):
    """Схема для обновления заказа"""

    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class OrderResponse(BaseSchema, OrderBase):
    """Схема ответа для заказа"""

    order_number: str = Field(..., description="Номер заказа")
    total_amount: Decimal = Field(..., description="Общая сумма заказа")
    client_name: Optional[str] = Field(None, description="Имя клиента")
    items_count: Optional[int] = Field(None, description="Количество позиций")

    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    """Детальная схема заказа"""

    items: List[OrderItemResponse] = Field(..., description="Позиции заказа")


class OrderStats(BaseModel):
    """Статистика по заказам"""

    total_orders: int = Field(..., description="Общее количество заказов")
    total_amount: Decimal = Field(..., description="Общая сумма заказов")
    avg_order: Decimal = Field(..., description="Средний чек")
    pending_orders: int = Field(..., description="Количество ожидающих заказов")
    completed_orders: int = Field(..., description="Количество выполненных заказов")


class ClientOrderSummary(BaseModel):
    """Сумма заказов по клиентам"""

    client_name: str = Field(..., description="Имя клиента")
    total_amount: Decimal = Field(..., description="Общая сумма заказов")
    orders_count: int = Field(..., description="Количество заказов")
    last_order: Optional[datetime] = Field(None, description="Последний заказ")


class CategoryChildrenCount(BaseModel):
    """Количество дочерних категорий"""

    category_name: str = Field(..., description="Название категории")
    children_count: int = Field(..., description="Количество дочерних элементов первого уровня")
    level: int = Field(..., description="Уровень вложенности")
    full_path: str = Field(..., description="Полный путь")


class OrderSearch(BaseModel):
    """Параметры поиска заказов"""

    client_id: Optional[int] = Field(None, description="ID клиента")
    status: Optional[OrderStatus] = Field(None, description="Статус заказа")
    payment_status: Optional[PaymentStatus] = Field(None, description="Статус оплаты")
    date_from: Optional[datetime] = Field(None, description="Дата от")
    date_to: Optional[datetime] = Field(None, description="Дата до")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Минимальная сумма")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Максимальная сумма")
