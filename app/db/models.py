"""
SQLAlchemy модели для базы данных
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Category(Base):
    """Модель категорий"""

    __tablename__ = "categories"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("app.categories.id", ondelete="CASCADE"), nullable=True)
    path = Column(String(255), nullable=True, index=True)
    level = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Связи
    parent = relationship("Category", remote_side=[id], backref="children")
    nomenclature = relationship("Nomenclature", back_populates="category")


class Nomenclature(Base):
    """Модель номенклатуры"""

    __tablename__ = "nomenclature"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    sku = Column(String(100), unique=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(12, 2), nullable=False)
    cost = Column(Numeric(12, 2))
    category_id = Column(Integer, ForeignKey("app.categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Связи
    category = relationship("Category", back_populates="nomenclature")
    order_items = relationship("OrderItem", back_populates="nomenclature")


class Client(Base):
    """Модель клиентов"""

    __tablename__ = "clients"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20), index=True)
    address = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Связи
    orders = relationship("Order", back_populates="client")


class Order(Base):
    """Модель заказов"""

    __tablename__ = "orders"
    __table_args__ = {"schema": "app"}

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    client_id = Column(Integer, ForeignKey("app.clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_amount = Column(Numeric(12, 2), default=0.00, index=True)
    status = Column(String(20), default="pending", index=True)
    payment_status = Column(String(20), default="unpaid", index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Связи
    client = relationship("Client", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Модель позиций заказа"""

    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "nomenclature_id", name="unique_order_nomenclature"),
        {"schema": "app"},
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    order_id = Column(Integer, ForeignKey("app.orders.id", ondelete="CASCADE"), nullable=False, index=True)
    nomenclature_id = Column(
        Integer, ForeignKey("app.nomenclature.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))

    # Связи
    order = relationship("Order", back_populates="order_items")
    nomenclature = relationship("Nomenclature", back_populates="order_items")
