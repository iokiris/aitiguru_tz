#!/bin/bash

# Скрипт для настройки среды разработки
set -e

echo "🚀 Настройка среды разработки для системы управления заказами"

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo "📝 Создание файла .env..."
    cp env.example .env
    echo "✅ Файл .env создан. Отредактируйте его под ваше окружение."
fi

# Создаем директории для логов
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p htmlcov

# Устанавливаем зависимости Python
echo "📦 Установка зависимостей Python..."
pip install -r requirements.txt

# Запускаем базу данных
echo "🐘 Запуск PostgreSQL..."
docker-compose up -d postgres

# Ждем готовности базы данных
echo "⏳ Ожидание готовности базы данных..."
sleep 15

# Проверяем подключение
echo "🔍 Проверка подключения к базе данных..."
until docker-compose exec postgres pg_isready -U app_user -d order_management; do
    echo "Ожидание PostgreSQL..."
    sleep 2
done

echo "✅ Среда разработки настроена!"
echo ""
echo "📋 Доступные команды:"
echo "  docker-compose up -d          # Запуск всех сервисов"
echo "  docker-compose down           # Остановка сервисов"
echo "  python -m pytest tests/ -v    # Запуск тестов"
echo "  ./scripts/run_tests.sh        # Полный набор тестов"
echo ""
echo "🌐 После запуска сервисов:"
echo "  FastAPI: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  PostgreSQL: localhost:5434"
echo "  pgAdmin: http://localhost:5050"
