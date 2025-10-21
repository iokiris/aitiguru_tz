"""
Тесты API для аналитики
"""
import pytest
from fastapi.testclient import TestClient


class TestAnalyticsAPI:
    """Тесты API аналитики"""
    
    def test_get_client_order_summary(self, client: TestClient, sample_clients, sample_orders):
        """Тест получения суммы заказов по клиентам"""
        response = client.get("/api/v1/analytics/client-summary")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Проверяем данные первого клиента
        client_1 = next(
            item for item in data if item["client_name"] == "Иванов Иван Иванович"
        )
        assert client_1["total_amount"] == 60000.0
        assert client_1["orders_count"] == 1
        
        # Проверяем данные второго клиента
        client_2 = next(
            item for item in data if item["client_name"] == "Петров Петр Петрович"
        )
        assert client_2["total_amount"] == 45000.0
        assert client_2["orders_count"] == 1
    
    def test_get_category_children_count(self, client: TestClient, sample_categories):
        """Тест получения количества дочерних категорий"""
        response = client.get("/api/v1/analytics/category-children")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2  # Две корневые категории
        
        # Проверяем категорию "Бытовая техника"
        household_tech = next(
            item for item in data if item["category_name"] == "Бытовая техника"
        )
        assert household_tech["children_count"] == 2  # Стиральные машины, Холодильники
        assert household_tech["level"] == 0
        
        # Проверяем категорию "Компьютеры"
        computers = next(
            item for item in data if item["category_name"] == "Компьютеры"
        )
        assert computers["children_count"] == 1  # Ноутбуки
        assert computers["level"] == 0
    
    def test_get_top_clients(self, client: TestClient, sample_clients, sample_orders):
        """Тест получения топ клиентов"""
        response = client.get("/api/v1/analytics/top-clients?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Проверяем сортировку по сумме (по убыванию)
        assert data[0]["total_amount"] >= data[1]["total_amount"]
        assert data[0]["client_name"] == "Иванов Иван Иванович"
        assert data[0]["total_amount"] == 60000.0
    
    def test_get_category_stats(self, client: TestClient, sample_categories, sample_nomenclature):
        """Тест получения статистики по категориям"""
        response = client.get("/api/v1/analytics/category-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 5  # Все категории
        
        # Проверяем статистику для категории с товарами
        category_with_products = next(
            item for item in data if item["category_name"] == "Стиральные машины"
        )
        assert category_with_products["products_count"] == 1
        assert category_with_products["total_quantity"] == 5
        assert category_with_products["avg_price"] == 25000.0
        assert category_with_products["min_price"] == 25000.0
        assert category_with_products["max_price"] == 25000.0
        assert category_with_products["total_value"] == 125000.0  # 25000 * 5
    
    def test_get_sales_by_month(self, client: TestClient, sample_orders):
        """Тест получения продаж по месяцам"""
        response = client.get("/api/v1/analytics/sales-by-month")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1  # Как минимум один месяц
        
        # Проверяем структуру данных
        month_data = data[0]
        assert "month" in month_data
        assert "orders_count" in month_data
        assert "items_count" in month_data
        assert "total_amount" in month_data
        assert "avg_order" in month_data
    
    def test_get_top_products(self, client: TestClient, sample_nomenclature, sample_orders):
        """Тест получения топ товаров"""
        response = client.get("/api/v1/analytics/top-products?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3  # Все товары
        
        # Проверяем сортировку по выручке (по убыванию)
        assert data[0]["total_revenue"] >= data[1]["total_revenue"]
        assert data[1]["total_revenue"] >= data[2]["total_revenue"]
        
        # Проверяем данные для товара с продажами
        product_with_sales = next(
            item for item in data if item["product_name"] == "Стиральная машина Samsung"
        )
        assert product_with_sales["total_sold"] == 1
        assert product_with_sales["total_revenue"] == 25000.0
        assert product_with_sales["orders_count"] == 1
    
    def test_analytics_pagination(self, client: TestClient, sample_clients, sample_orders):
        """Тест пагинации в аналитике"""
        response = client.get("/api/v1/analytics/client-summary?page=1&size=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
    
    def test_analytics_empty_data(self, client: TestClient):
        """Тест аналитики с пустыми данными"""
        # Тест без данных
        response = client.get("/api/v1/analytics/client-summary")
        assert response.status_code == 200
        assert response.json() == []
        
        response = client.get("/api/v1/analytics/category-children")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_analytics_parameters_validation(self, client: TestClient):
        """Тест валидации параметров аналитики"""
        # Неверный лимит для топ клиентов
        response = client.get("/api/v1/analytics/top-clients?limit=0")
        assert response.status_code == 422
        
        response = client.get("/api/v1/analytics/top-clients?limit=100")
        assert response.status_code == 422
        
        # Неверный лимит для топ товаров
        response = client.get("/api/v1/analytics/top-products?limit=0")
        assert response.status_code == 422
        
        response = client.get("/api/v1/analytics/top-products?limit=100")
        assert response.status_code == 422
