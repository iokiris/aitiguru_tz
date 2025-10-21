"""
Тесты API для клиентов
"""
import pytest
from fastapi.testclient import TestClient


class TestClientsAPI:
    """Тесты API клиентов"""
    
    def test_get_clients(self, client: TestClient, sample_clients):
        """Тест получения списка клиентов"""
        response = client.get("/api/v1/clients/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Иванов Иван Иванович"
        assert data[0]["email"] == "ivanov@example.com"
    
    def test_get_client_by_id(self, client: TestClient, sample_clients):
        """Тест получения клиента по ID"""
        response = client.get("/api/v1/clients/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Иванов Иван Иванович"
        assert data["orders_count"] == 1  # Из sample_orders
        assert data["total_spent"] == 60000.0
    
    def test_get_client_not_found(self, client: TestClient):
        """Тест получения несуществующего клиента"""
        response = client.get("/api/v1/clients/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_create_client(self, client: TestClient):
        """Тест создания клиента"""
        client_data = {
            "name": "Сидоров Сидор Сидорович",
            "email": "sidorov@example.com",
            "phone": "+7 (343) 345-67-89",
            "address": "г. Екатеринбург, ул. Мира, д. 15",
            "is_active": True
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Сидоров Сидор Сидорович"
        assert data["email"] == "sidorov@example.com"
        assert data["orders_count"] == 0
        assert data["total_spent"] == 0.0
    
    def test_create_client_duplicate_email(self, client: TestClient, sample_clients):
        """Тест создания клиента с дублирующимся email"""
        client_data = {
            "name": "Новый клиент",
            "email": "ivanov@example.com",  # Уже существует
            "address": "Адрес"
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]
    
    def test_update_client(self, client: TestClient, sample_clients):
        """Тест обновления клиента"""
        update_data = {
            "name": "Обновленное имя",
            "email": "new_email@example.com"
        }
        
        response = client.put("/api/v1/clients/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Обновленное имя"
        assert data["email"] == "new_email@example.com"
    
    def test_update_client_not_found(self, client: TestClient):
        """Тест обновления несуществующего клиента"""
        update_data = {"name": "Новое имя"}
        
        response = client.put("/api/v1/clients/999", json=update_data)
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_delete_client(self, client: TestClient, sample_clients):
        """Тест удаления клиента без заказов"""
        # Сначала создаем клиента без заказов
        client_data = {
            "name": "Клиент без заказов",
            "address": "Адрес"
        }
        create_response = client.post("/api/v1/clients/", json=client_data)
        client_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/clients/{client_id}")
        assert response.status_code == 200
        assert "удален" in response.json()["message"]
    
    def test_delete_client_with_orders(self, client: TestClient, sample_clients, sample_orders):
        """Тест удаления клиента с заказами"""
        response = client.delete("/api/v1/clients/1")  # У клиента есть заказы
        assert response.status_code == 400
        assert "с заказами" in response.json()["detail"]
    
    def test_delete_client_not_found(self, client: TestClient):
        """Тест удаления несуществующего клиента"""
        response = client.delete("/api/v1/clients/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_get_client_stats(self, client: TestClient, sample_clients, sample_orders):
        """Тест получения статистики по клиентам"""
        response = client.get("/api/v1/clients/stats/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Проверяем статистику первого клиента
        client_1_stats = next(
            stats for stats in data if stats["client_name"] == "Иванов Иван Иванович"
        )
        assert client_1_stats["total_amount"] == 60000.0
        assert client_1_stats["orders_count"] == 1
    
    def test_get_clients_with_pagination(self, client: TestClient, sample_clients):
        """Тест пагинации клиентов"""
        response = client.get("/api/v1/clients/?page=1&size=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
    
    def test_get_clients_with_search(self, client: TestClient, sample_clients):
        """Тест поиска клиентов"""
        response = client.get("/api/v1/clients/?query=Иванов")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert "Иванов" in data[0]["name"]
    
    def test_client_validation(self, client: TestClient):
        """Тест валидации данных клиента"""
        # Пустое имя
        response = client.post("/api/v1/clients/", json={"name": "", "address": "Адрес"})
        assert response.status_code == 422
        
        # Неверный email
        response = client.post("/api/v1/clients/", json={
            "name": "Клиент",
            "email": "неверный-email",
            "address": "Адрес"
        })
        assert response.status_code == 422
        
        # Пустой адрес
        response = client.post("/api/v1/clients/", json={"name": "Клиент", "address": ""})
        assert response.status_code == 422
