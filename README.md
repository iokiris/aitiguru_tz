# Система управления заказами

## Быстрый старт

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd aitiguru_tz
```

2. **Запустите систему:**
```bash
docker-compose up -d
```

3. **Добавьте тестовые данные:**
```bash
# Выполните скрипт инициализации данных
docker exec order_management_postgres psql -U app_user -d order_management -f /docker-entrypoint-initdb.d/02_insert_sample_data.sql
```

4. **Swagger API:**
```bash

http://localhost:8000/docs#

```

## Запуск тестов

```bash
# Запуск всех тестов
docker exec order_management_fastapi python -m pytest tests/ -v

# Запуск тестов с покрытием
docker exec order_management_fastapi python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## Остановка системы

```bash
docker-compose down
```

Для полной очистки (включая данные):
```bash
docker-compose down -v
```
