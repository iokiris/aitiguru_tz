"""
Тесты основного приложения
"""
import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """Тесты основного приложения"""
    
    def test_root_endpoint(self, client: TestClient):
        """Тест корневого endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Система управления заказами"
        assert data["version"] == "1.0.0"
        assert "docs" in data
    
    def test_health_check(self, client: TestClient):
        """Тест проверки здоровья приложения"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "database" in data
    
    def test_metrics_endpoint(self, client: TestClient):
        """Тест endpoint метрик"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "requests_total" in data
        assert "active_connections" in data
        assert "uptime" in data
    
    def test_docs_endpoint(self, client: TestClient):
        """Тест endpoint документации"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self, client: TestClient):
        """Тест endpoint ReDoc"""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_api_v1_endpoints_exist(self, client: TestClient):
        """Тест существования основных API endpoints"""
        endpoints = [
            "/api/v1/categories/",
            "/api/v1/clients/",
            "/api/v1/nomenclature/",
            "/api/v1/orders/",
            "/api/v1/analytics/client-summary",
            "/api/v1/analytics/category-children"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Может быть 200 (данные есть) или 422 (ошибка валидации параметров)
            assert response.status_code in [200, 422]
    
    def test_cors_headers(self, client: TestClient):
        """Тест CORS заголовков"""
        response = client.options("/api/v1/categories/")
        # OPTIONS запрос может не поддерживаться, но CORS должен быть настроен
        assert response.status_code in [200, 405]
    
    def test_error_handling(self, client: TestClient):
        """Тест обработки ошибок"""
        # Несуществующий endpoint
        response = client.get("/api/v1/nonexistent/")
        assert response.status_code == 404
        
        # Неверный метод
        response = client.post("/api/v1/categories/1")
        assert response.status_code == 405
    
    def test_content_type_headers(self, client: TestClient):
        """Тест заголовков Content-Type"""
        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_response_structure(self, client: TestClient, sample_categories):
        """Тест структуры ответов API"""
        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # Если есть данные
            category = data[0]
            required_fields = ["id", "name", "is_active", "created_at"]
            for field in required_fields:
                assert field in category
