"""
Тесты API для заказов
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestOrdersAPI:
    """Тесты API заказов"""
    
    def test_get_orders(self, client: TestClient, sample_orders):
        """Тест получения списка заказов"""
        response = client.get("/api/v1/orders/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["order_number"] == "ORD-000002"  # Сортировка по дате DESC
        assert data[0]["client_name"] == "Петров Петр Петрович"
        assert data[0]["items_count"] == 1
    
    def test_get_order_by_id(self, client: TestClient, sample_orders):
        """Тест получения заказа по ID"""
        response = client.get("/api/v1/orders/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["order_number"] == "ORD-000001"
        assert data["client_name"] == "Иванов Иван Иванович"
        assert data["total_amount"] == 60000.0
        assert len(data["items"]) == 2  # Две позиции
    
    def test_get_order_not_found(self, client: TestClient):
        """Тест получения несуществующего заказа"""
        response = client.get("/api/v1/orders/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_create_order(self, client: TestClient, sample_clients, sample_nomenclature):
        """Тест создания заказа"""
        order_data = {
            "client_id": 1,
            "order_date": "2024-01-20T10:00:00",
            "status": "pending",
            "payment_status": "unpaid",
            "notes": "Тестовый заказ",
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 1,
                    "price": 25000.0,
                    "total_price": 25000.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["client_id"] == 1
        assert data["status"] == "pending"
        assert data["payment_status"] == "unpaid"
        assert data["items_count"] == 1
        assert data["total_amount"] == 25000.0
    
    def test_create_order_invalid_client(self, client: TestClient, sample_nomenclature):
        """Тест создания заказа с несуществующим клиентом"""
        order_data = {
            "client_id": 999,  # Не существует
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 1,
                    "price": 25000.0,
                    "total_price": 25000.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        assert response.status_code == 400
        assert "не найден" in response.json()["detail"]
    
    def test_create_order_invalid_nomenclature(self, client: TestClient, sample_clients):
        """Тест создания заказа с несуществующим товаром"""
        order_data = {
            "client_id": 1,
            "items": [
                {
                    "nomenclature_id": 999,  # Не существует
                    "quantity": 1,
                    "price": 25000.0,
                    "total_price": 25000.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        assert response.status_code == 400
        assert "не найден" in response.json()["detail"]
    
    def test_create_order_insufficient_quantity(self, client: TestClient, sample_clients, sample_nomenclature):
        """Тест создания заказа с недостаточным количеством товара"""
        order_data = {
            "client_id": 1,
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 100,  # Больше чем на складе (5)
                    "price": 25000.0,
                    "total_price": 2500000.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        assert response.status_code == 400
        assert "Недостаточно товара" in response.json()["detail"]
    
    def test_create_order_price_mismatch(self, client: TestClient, sample_clients, sample_nomenclature):
        """Тест создания заказа с неверной ценой"""
        order_data = {
            "client_id": 1,
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 1,
                    "price": 20000.0,  # Неверная цена (должна быть 25000.0)
                    "total_price": 20000.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        assert response.status_code == 400
        assert "изменилась" in response.json()["detail"]
    
    def test_update_order(self, client: TestClient, sample_orders):
        """Тест обновления заказа"""
        update_data = {
            "status": "processing",
            "payment_status": "paid",
            "notes": "Обновленные примечания"
        }
        
        response = client.put("/api/v1/orders/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"
        assert data["payment_status"] == "paid"
        assert data["notes"] == "Обновленные примечания"
    
    def test_update_order_not_found(self, client: TestClient):
        """Тест обновления несуществующего заказа"""
        update_data = {"status": "processing"}
        
        response = client.put("/api/v1/orders/999", json=update_data)
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_delete_order(self, client: TestClient, sample_clients, sample_nomenclature):
        """Тест удаления заказа в статусе pending"""
        # Создаем заказ в статусе pending
        order_data = {
            "client_id": 1,
            "status": "pending",
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 1,
                    "price": 25000.0,
                    "total_price": 25000.0
                }
            ]
        }
        create_response = client.post("/api/v1/orders/", json=order_data)
        order_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        assert "удален" in response.json()["message"]
    
    def test_delete_order_completed(self, client: TestClient, sample_orders):
        """Тест удаления выполненного заказа"""
        response = client.delete("/api/v1/orders/1")  # Статус completed
        assert response.status_code == 400
        assert "completed" in response.json()["detail"]
    
    def test_delete_order_not_found(self, client: TestClient):
        """Тест удаления несуществующего заказа"""
        response = client.delete("/api/v1/orders/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_get_order_stats(self, client: TestClient, sample_orders):
        """Тест получения статистики по заказам"""
        response = client.get("/api/v1/orders/stats/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 2
        assert data["total_amount"] == 105000.0  # 60000 + 45000
        assert data["pending_orders"] == 1
        assert data["completed_orders"] == 1
    
    def test_get_orders_with_pagination(self, client: TestClient, sample_orders):
        """Тест пагинации заказов"""
        response = client.get("/api/v1/orders/?page=1&size=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
    
    def test_get_orders_with_filters(self, client: TestClient, sample_orders):
        """Тест фильтрации заказов"""
        # Фильтр по клиенту
        response = client.get("/api/v1/orders/?client_id=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["client_id"] == 1
        
        # Фильтр по статусу
        response = client.get("/api/v1/orders/?status=completed")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"
        
        # Фильтр по статусу оплаты
        response = client.get("/api/v1/orders/?payment_status=paid")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["payment_status"] == "paid"
    
    def test_order_validation(self, client: TestClient, sample_clients, sample_nomenclature):
        """Тест валидации данных заказа"""
        # Пустой список товаров
        response = client.post("/api/v1/orders/", json={
            "client_id": 1,
            "items": []
        })
        assert response.status_code == 422
        
        # Отрицательное количество
        response = client.post("/api/v1/orders/", json={
            "client_id": 1,
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": -1,
                    "price": 25000.0,
                    "total_price": -25000.0
                }
            ]
        })
        assert response.status_code == 422
        
        # Отрицательная цена
        response = client.post("/api/v1/orders/", json={
            "client_id": 1,
            "items": [
                {
                    "nomenclature_id": 1,
                    "quantity": 1,
                    "price": -25000.0,
                    "total_price": -25000.0
                }
            ]
        })
        assert response.status_code == 422
