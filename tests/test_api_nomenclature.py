"""
Тесты API для номенклатуры
"""
import pytest
from fastapi.testclient import TestClient


class TestNomenclatureAPI:
    """Тесты API номенклатуры"""
    
    def test_get_nomenclature(self, client: TestClient, sample_nomenclature):
        """Тест получения списка номенклатуры"""
        response = client.get("/api/v1/nomenclature/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Стиральная машина Samsung"
        assert data[0]["sku"] == "SMS-001"
        assert data[0]["category_name"] == "Стиральные машины"
    
    def test_get_nomenclature_by_id(self, client: TestClient, sample_nomenclature):
        """Тест получения товара по ID"""
        response = client.get("/api/v1/nomenclature/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Стиральная машина Samsung"
        assert data["quantity"] == 5
        assert data["price"] == 25000.0
    
    def test_get_nomenclature_not_found(self, client: TestClient):
        """Тест получения несуществующего товара"""
        response = client.get("/api/v1/nomenclature/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_create_nomenclature(self, client: TestClient, sample_categories):
        """Тест создания товара"""
        nomenclature_data = {
            "name": "Новый товар",
            "description": "Описание товара",
            "sku": "NEW-001",
            "quantity": 10,
            "price": 10000.0,
            "cost": 8000.0,
            "category_id": 1,
            "is_active": True
        }
        
        response = client.post("/api/v1/nomenclature/", json=nomenclature_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Новый товар"
        assert data["sku"] == "NEW-001"
        assert data["quantity"] == 10
        assert data["price"] == 10000.0
        assert data["category_name"] == "Бытовая техника"
    
    def test_create_nomenclature_invalid_category(self, client: TestClient):
        """Тест создания товара с несуществующей категорией"""
        nomenclature_data = {
            "name": "Товар",
            "quantity": 1,
            "price": 1000.0,
            "category_id": 999  # Не существует
        }
        
        response = client.post("/api/v1/nomenclature/", json=nomenclature_data)
        assert response.status_code == 400
        assert "не найдена" in response.json()["detail"]
    
    def test_create_nomenclature_duplicate_sku(self, client: TestClient, sample_nomenclature):
        """Тест создания товара с дублирующимся SKU"""
        nomenclature_data = {
            "name": "Новый товар",
            "sku": "SMS-001",  # Уже существует
            "quantity": 1,
            "price": 1000.0,
            "category_id": 1
        }
        
        response = client.post("/api/v1/nomenclature/", json=nomenclature_data)
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]
    
    def test_update_nomenclature(self, client: TestClient, sample_nomenclature):
        """Тест обновления товара"""
        update_data = {
            "name": "Обновленное название",
            "price": 30000.0,
            "quantity": 8
        }
        
        response = client.put("/api/v1/nomenclature/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Обновленное название"
        assert data["price"] == 30000.0
        assert data["quantity"] == 8
    
    def test_update_nomenclature_not_found(self, client: TestClient):
        """Тест обновления несуществующего товара"""
        update_data = {"name": "Новое название"}
        
        response = client.put("/api/v1/nomenclature/999", json=update_data)
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_delete_nomenclature(self, client: TestClient, sample_nomenclature):
        """Тест удаления товара без заказов"""
        # Создаем товар без заказов
        nomenclature_data = {
            "name": "Товар для удаления",
            "quantity": 1,
            "price": 1000.0,
            "category_id": 1
        }
        create_response = client.post("/api/v1/nomenclature/", json=nomenclature_data)
        nomenclature_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/nomenclature/{nomenclature_id}")
        assert response.status_code == 200
        assert "удален" in response.json()["message"]
    
    def test_delete_nomenclature_with_orders(self, client: TestClient, sample_nomenclature, sample_orders):
        """Тест удаления товара с заказами"""
        response = client.delete("/api/v1/nomenclature/1")  # Товар есть в заказах
        assert response.status_code == 400
        assert "в заказах" in response.json()["detail"]
    
    def test_delete_nomenclature_not_found(self, client: TestClient):
        """Тест удаления несуществующего товара"""
        response = client.delete("/api/v1/nomenclature/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_get_nomenclature_stats(self, client: TestClient, sample_nomenclature, sample_orders):
        """Тест получения статистики по номенклатуре"""
        response = client.get("/api/v1/nomenclature/stats/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        
        # Проверяем статистику для товара с продажами
        product_stats = next(
            stats for stats in data if stats["name"] == "Стиральная машина Samsung"
        )
        assert product_stats["total_sold"] == 1
        assert product_stats["total_revenue"] == 25000.0
        assert product_stats["orders_count"] == 1
    
    def test_get_nomenclature_with_pagination(self, client: TestClient, sample_nomenclature):
        """Тест пагинации номенклатуры"""
        response = client.get("/api/v1/nomenclature/?page=1&size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
    
    def test_get_nomenclature_with_search(self, client: TestClient, sample_nomenclature):
        """Тест поиска номенклатуры"""
        response = client.get("/api/v1/nomenclature/?query=Samsung")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert "Samsung" in data[0]["name"]
    
    def test_get_nomenclature_with_filters(self, client: TestClient, sample_nomenclature):
        """Тест фильтрации номенклатуры"""
        # Фильтр по категории
        response = client.get("/api/v1/nomenclature/?category_id=3")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["category_id"] == 3
        
        # Фильтр по цене
        response = client.get("/api/v1/nomenclature/?min_price=30000")
        assert response.status_code == 200
        
        data = response.json()
        assert all(item["price"] >= 30000 for item in data)
        
        # Фильтр по наличию
        response = client.get("/api/v1/nomenclature/?in_stock=true")
        assert response.status_code == 200
        
        data = response.json()
        assert all(item["quantity"] > 0 for item in data)
    
    def test_nomenclature_validation(self, client: TestClient, sample_categories):
        """Тест валидации данных номенклатуры"""
        # Отрицательная цена
        response = client.post("/api/v1/nomenclature/", json={
            "name": "Товар",
            "price": -1000.0,
            "quantity": 1,
            "category_id": 1
        })
        assert response.status_code == 422
        
        # Отрицательное количество
        response = client.post("/api/v1/nomenclature/", json={
            "name": "Товар",
            "price": 1000.0,
            "quantity": -1,
            "category_id": 1
        })
        assert response.status_code == 422
        
        # Пустое имя
        response = client.post("/api/v1/nomenclature/", json={
            "name": "",
            "price": 1000.0,
            "quantity": 1,
            "category_id": 1
        })
        assert response.status_code == 422
