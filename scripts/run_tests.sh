#!/bin/bash

# Скрипт для запуска тестов
set -e

echo "🚀 Запуск тестов системы управления заказами"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Останавливаем контейнеры если они запущены
echo "🛑 Остановка существующих контейнеров..."
docker-compose down -v

# Запускаем базу данных для тестов
echo "🐘 Запуск PostgreSQL для тестов..."
docker-compose up -d postgres

# Ждем готовности базы данных
echo "⏳ Ожидание готовности базы данных..."
sleep 10

# Проверяем подключение к базе данных
echo "🔍 Проверка подключения к базе данных..."
until docker-compose exec postgres pg_isready -U app_user -d order_management; do
    echo "Ожидание PostgreSQL..."
    sleep 2
done

# Устанавливаем зависимости Python
echo "📦 Установка зависимостей Python..."
pip install -r requirements.txt

# Запускаем тесты
echo "🧪 Запуск тестов..."

# Быстрые тесты
echo "⚡ Запуск быстрых тестов..."
pytest tests/test_main.py tests/test_api_*.py -v --cov=app --cov-report=term-missing

# Интеграционные тесты
echo "🔗 Запуск интеграционных тестов..."
pytest tests/test_database_queries.py -v --cov=app --cov-report=term-missing

# Полный набор тестов с покрытием
echo "📊 Запуск всех тестов с полным покрытием..."
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=100

# Генерируем отчет о покрытии
echo "📈 Отчет о покрытии создан в htmlcov/index.html"

# Останавливаем контейнеры
echo "🛑 Остановка контейнеров..."
docker-compose down -v

echo "✅ Тесты завершены успешно!"
echo "📊 Отчет о покрытии: htmlcov/index.html"
echo "📋 Логи тестов: pytest.log"
