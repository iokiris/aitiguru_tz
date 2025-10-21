#!/bin/bash

# Скрипт для синхронизации кода с контейнером
set -e

echo "🔄 Синхронизация кода с контейнером..."

# Проверяем, что контейнер запущен
if ! docker ps | grep -q order_management_fastapi; then
    echo "❌ Контейнер FastAPI не запущен. Запустите docker-compose up -d"
    exit 1
fi

# Синхронизируем код
echo "📁 Копирование кода в контейнер..."
docker cp . order_management_fastapi:/app/

echo "✅ Код синхронизирован!"
echo ""
echo "🔄 Для применения изменений перезапустите контейнер:"
echo "   docker-compose restart fastapi"
echo ""
echo "📝 Или перезапустите только FastAPI:"
echo "   docker restart order_management_fastapi"
