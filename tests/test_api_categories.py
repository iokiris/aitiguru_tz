"""
Тесты API для категорий
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.category import CategoryCreate, CategoryUpdate


class TestCategoriesAPI:
    """Тесты API категорий"""
    
    def test_get_categories(self, client: TestClient, sample_categories):
        """Тест получения списка категорий"""
        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 5
        assert data[0]["name"] == "Бытовая техника"
        assert data[0]["level"] == 0
        assert data[0]["children_count"] == 2  # Стиральные машины, Холодильники
    
    def test_get_category_by_id(self, client: TestClient, sample_categories):
        """Тест получения категории по ID"""
        response = client.get("/api/v1/categories/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Бытовая техника"
        assert data["parent_id"] is None
    
    def test_get_category_not_found(self, client: TestClient):
        """Тест получения несуществующей категории"""
        response = client.get("/api/v1/categories/999")
        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]
    
    def test_create_category(self, client: TestClient, sample_categories):
        """Тест создания категории"""
        category_data = {
            "name": "Телевизоры",
            "parent_id": 1,
            "is_active": True
        }
        
        response = client.post("/api/v1/categories/", json=category_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Телевизоры"
        assert data["parent_id"] == 1
        assert data["level"] == 1
    
    def test_create_category_duplicate_name(self, client: TestClient, sample_categories):
        """Тест создания категории с дублирующимся именем"""
        category_data = {
            "name": "Бытовая техника",  # Уже существует
            "parent_id": None,
            "is_active": True
        }
        
        response = client.post("/api/v1/categories/", json=category_data)
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]
    
    def test_create_category_invalid_parent(self, client: TestClient):
        """Тест создания категории с несуществующим родителем"""
        category_data = {
            "name": "Новая категория",
            "parent_id": 999,  # Не существует
            "is_active": True
        }
        
        response = client.post("/api/v1/categories/", json=category_data)
        assert response.status_code == 400
        assert "не найдена" in response.json()["detail"]
    
    def test_update_category(self, client: TestClient, sample_categories):
        """Тест обновления категории"""
        update_data = {
            "name": "Обновленная категория",
            "is_active": False
        }
        
        response = client.put("/api/v1/categories/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Обновленная категория"
        assert data["is_active"] is False
    
    def test_update_category_not_found(self, client: TestClient):
        """Тест обновления несуществующей категории"""
        update_data = {"name": "Новое имя"}
        
        response = client.put("/api/v1/categories/999", json=update_data)
        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]
    
    def test_delete_category(self, client: TestClient, sample_categories):
        """Тест удаления категории"""
        response = client.delete("/api/v1/categories/5")  # Ноутбуки
        assert response.status_code == 200
        assert "удалена" in response.json()["message"]
    
    def test_delete_category_with_children(self, client: TestClient, sample_categories):
        """Тест удаления категории с дочерними элементами"""
        response = client.delete("/api/v1/categories/1")  # Бытовая техника
        assert response.status_code == 400
        assert "дочерними элементами" in response.json()["detail"]
    
    def test_delete_category_not_found(self, client: TestClient):
        """Тест удаления несуществующей категории"""
        response = client.delete("/api/v1/categories/999")
        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]
    
    def test_get_category_tree(self, client: TestClient, sample_categories):
        """Тест получения дерева категорий"""
        response = client.get("/api/v1/categories/tree/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2  # Две корневые категории
        
        # Проверяем структуру дерева
        household_tech = next(cat for cat in data if cat["name"] == "Бытовая техника")
        assert len(household_tech["children"]) == 2  # Стиральные машины, Холодильники
    
    def test_get_category_hierarchy(self, client: TestClient, sample_categories):
        """Тест получения иерархии категорий"""
        response = client.get("/api/v1/categories/hierarchy/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 5  # Все категории
        
        # Проверяем отступы в дереве
        root_categories = [cat for cat in data if cat["level"] == 0]
        assert len(root_categories) == 2
    
    def test_get_category_stats(self, client: TestClient, sample_categories, sample_nomenclature):
        """Тест получения статистики по категориям"""
        response = client.get("/api/v1/categories/stats/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 5  # Все категории
        
        # Проверяем статистику для категории с товарами
        category_with_products = next(
            cat for cat in data if cat["category_name"] == "Стиральные машины"
        )
        assert category_with_products["products_count"] == 1
        assert category_with_products["total_quantity"] == 5
    
    def test_get_categories_with_pagination(self, client: TestClient, sample_categories):
        """Тест пагинации категорий"""
        response = client.get("/api/v1/categories/?page=1&size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
    
    def test_get_categories_with_filters(self, client: TestClient, sample_categories):
        """Тест фильтрации категорий"""
        # Тест фильтра по активности
        response = client.get("/api/v1/categories/?is_active=true")
        assert response.status_code == 200
        
        data = response.json()
        assert all(cat["is_active"] for cat in data)
    
    def test_category_validation(self, client: TestClient):
        """Тест валидации данных категории"""
        # Пустое имя
        response = client.post("/api/v1/categories/", json={"name": ""})
        assert response.status_code == 422
        
        # Слишком длинное имя
        response = client.post("/api/v1/categories/", json={"name": "x" * 300})
        assert response.status_code == 422
