#!/bin/bash

# Скрипт для проверки и исправления кода
set -e

echo "🔍 Проверка и исправление кода..."

# Активируем виртуальное окружение
source venv/bin/activate

# 1. Форматирование кода
echo "📝 Форматирование кода с black..."
black app/ --line-length=120

# 2. Сортировка импортов
echo "📦 Сортировка импортов с isort..."
isort app/ --profile black

# 3. Исправление стиля кода
echo "🧹 Исправление стиля кода с autopep8..."
autopep8 --in-place --recursive --aggressive --aggressive app/

# 4. Проверка с flake8
echo "🔍 Проверка с flake8..."
python -m flake8 app/ --max-line-length=120 --ignore=E501,W503 || {
    echo "❌ Найдены ошибки flake8"
    exit 1
}

# 5. Проверка типов с mypy (игнорируем ошибки для быстрой проверки)
echo "🔍 Проверка типов с mypy..."
python -m mypy app/ --ignore-missing-imports || {
    echo "⚠️  Найдены предупреждения mypy (не критично)"
}

echo "✅ Проверка кода завершена успешно!"
