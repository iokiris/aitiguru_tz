"""
Конфигурация тестов для системы управления заказами
"""
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
from typing import Generator

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Тестовая база данных
TEST_DATABASE_URL = "postgresql://app_user:app_password@postgres:5432/order_management_test"

# Создаем тестовый движок
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def setup_test_db():
    """Настройка тестовой базы данных"""
    # Создаем схему
    with test_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
        conn.commit()
    
    # Импортируем модели для создания таблиц
    from app.db import models
    
    # Создаем таблицы
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    # Очищаем после тестов
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_test_db):
    """Сессия базы данных для тестов"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Тестовый клиент FastAPI"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_categories(db_session):
    """Создание тестовых категорий"""
    categories_data = [
        {"id": 1, "name": "Бытовая техника", "parent_id": None},
        {"id": 2, "name": "Компьютеры", "parent_id": None},
        {"id": 3, "name": "Стиральные машины", "parent_id": 1},
        {"id": 4, "name": "Холодильники", "parent_id": 1},
        {"id": 5, "name": "Ноутбуки", "parent_id": 2},
    ]
    
    for cat_data in categories_data:
        db_session.execute(text("""
            INSERT INTO app.categories (id, name, parent_id, created_by)
            VALUES (:id, :name, :parent_id, 'test')
        """), cat_data)
    
    db_session.commit()
    return categories_data


@pytest.fixture
def sample_nomenclature(db_session, sample_categories):
    """Создание тестовой номенклатуры"""
    nomenclature_data = [
        {
            "id": 1, "name": "Стиральная машина Samsung", "sku": "SMS-001",
            "quantity": 5, "price": 25000.00, "category_id": 3
        },
        {
            "id": 2, "name": "Холодильник Bosch", "sku": "HBO-001",
            "quantity": 3, "price": 35000.00, "category_id": 4
        },
        {
            "id": 3, "name": "Ноутбук ASUS", "sku": "NBA-001",
            "quantity": 2, "price": 45000.00, "category_id": 5
        }
    ]
    
    for nom_data in nomenclature_data:
        db_session.execute(text("""
            INSERT INTO app.nomenclature (id, name, sku, quantity, price, category_id, created_by)
            VALUES (:id, :name, :sku, :quantity, :price, :category_id, 'test')
        """), nom_data)
    
    db_session.commit()
    return nomenclature_data


@pytest.fixture
def sample_clients(db_session):
    """Создание тестовых клиентов"""
    clients_data = [
        {
            "id": 1, "name": "Иванов Иван Иванович", "email": "ivanov@example.com",
            "phone": "+7 (495) 123-45-67", "address": "г. Москва, ул. Ленина, д. 1"
        },
        {
            "id": 2, "name": "Петров Петр Петрович", "email": "petrov@example.com",
            "phone": "+7 (812) 234-56-78", "address": "г. Санкт-Петербург, ул. Невский, д. 5"
        }
    ]
    
    for client_data in clients_data:
        db_session.execute(text("""
            INSERT INTO app.clients (id, name, email, phone, address, created_by)
            VALUES (:id, :name, :email, :phone, :address, 'test')
        """), client_data)
    
    db_session.commit()
    return clients_data


@pytest.fixture
def sample_orders(db_session, sample_clients, sample_nomenclature):
    """Создание тестовых заказов"""
    orders_data = [
        {
            "id": 1, "client_id": 1, "order_number": "ORD-000001",
            "total_amount": 60000.00, "status": "completed", "payment_status": "paid"
        },
        {
            "id": 2, "client_id": 2, "order_number": "ORD-000002",
            "total_amount": 45000.00, "status": "pending", "payment_status": "unpaid"
        }
    ]
    
    for order_data in orders_data:
        db_session.execute(text("""
            INSERT INTO app.orders (id, client_id, order_number, total_amount, status, payment_status, created_by)
            VALUES (:id, :client_id, :order_number, :total_amount, :status, :payment_status, 'test')
        """), order_data)
    
    # Создаем позиции заказов
    order_items_data = [
        {"order_id": 1, "nomenclature_id": 1, "quantity": 1, "price": 25000.00, "total_price": 25000.00},
        {"order_id": 1, "nomenclature_id": 2, "quantity": 1, "price": 35000.00, "total_price": 35000.00},
        {"order_id": 2, "nomenclature_id": 3, "quantity": 1, "price": 45000.00, "total_price": 45000.00}
    ]
    
    for item_data in order_items_data:
        db_session.execute(text("""
            INSERT INTO app.order_items (order_id, nomenclature_id, quantity, price, total_price, created_by)
            VALUES (:order_id, :nomenclature_id, :quantity, :price, :total_price, 'test')
        """), item_data)
    
    db_session.commit()
    return orders_data
