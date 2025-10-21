# Схема базы данных - Система управления заказами

## Обзор

Система использует PostgreSQL с оптимизированной схемой для продакшн-уровня производительности. Схема включает древовидную структуру категорий, управление номенклатурой, клиентами и заказами.

## Архитектура

### Основные принципы
- **Нормализация**: Минимизация дублирования данных
- **Индексы**: Оптимизация запросов для высокой производительности
- **Ограничения**: Обеспечение целостности данных
- **Триггеры**: Автоматическое обновление связанных данных
- **Представления**: Упрощение сложных запросов

## Схема базы данных

### Схема `app`
Все таблицы находятся в схеме `app` для изоляции от системных таблиц PostgreSQL.

## Таблицы

### 1. categories - Категории товаров

Древовидная структура категорий с неограниченным уровнем вложенности.

```sql
CREATE TABLE app.categories (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES app.categories(id) ON DELETE CASCADE,
    path LTREE,                    -- Для быстрого поиска по иерархии
    level INTEGER DEFAULT 0,      -- Уровень вложенности
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);
```

**Особенности:**
- Рекурсивная ссылка на родительскую категорию
- LTREE для эффективного поиска по иерархии
- Автоматическое обновление path и level через триггеры

**Индексы:**
- `idx_categories_parent_id` - поиск дочерних категорий
- `idx_categories_name` - поиск по имени
- `idx_categories_path` - поиск по иерархии (GIST)
- `idx_categories_level` - фильтрация по уровню
- `idx_categories_active` - только активные категории

### 2. nomenclature - Номенклатура товаров

```sql
CREATE TABLE app.nomenclature (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100) UNIQUE,       -- Артикул
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    price DECIMAL(12, 2) NOT NULL CHECK (price >= 0),
    cost DECIMAL(12, 2) CHECK (cost >= 0),
    category_id INTEGER NOT NULL REFERENCES app.categories(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);
```

**Особенности:**
- Уникальный артикул (SKU)
- Проверка неотрицательных значений
- Связь с категорией через внешний ключ

**Индексы:**
- `idx_nomenclature_category_id` - поиск по категории
- `idx_nomenclature_name` - поиск по имени
- `idx_nomenclature_sku` - поиск по артикулу
- `idx_nomenclature_price` - сортировка по цене
- `idx_nomenclature_active` - только активные товары
- `idx_nomenclature_quantity` - товары в наличии

### 3. clients - Клиенты

```sql
CREATE TABLE app.clients (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    address TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);
```

**Особенности:**
- Уникальный email
- Обязательный адрес
- Мягкое удаление через is_active

**Индексы:**
- `idx_clients_name` - поиск по имени
- `idx_clients_email` - поиск по email
- `idx_clients_phone` - поиск по телефону
- `idx_clients_active` - только активные клиенты

### 4. orders - Заказы

```sql
CREATE TABLE app.orders (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    client_id INTEGER NOT NULL REFERENCES app.clients(id) ON DELETE RESTRICT,
    order_number VARCHAR(50) UNIQUE NOT NULL,  -- Автогенерация
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) DEFAULT 0.00 CHECK (total_amount >= 0),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled', 'refunded')),
    payment_status VARCHAR(20) DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'paid', 'partial', 'refunded')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);
```

**Особенности:**
- Автоматическая генерация номера заказа
- Статусы заказа и оплаты с проверкой
- Автоматический пересчет суммы через триггеры

**Индексы:**
- `idx_orders_client_id` - поиск по клиенту
- `idx_orders_order_number` - поиск по номеру
- `idx_orders_order_date` - сортировка по дате
- `idx_orders_status` - фильтрация по статусу
- `idx_orders_payment_status` - фильтрация по оплате
- `idx_orders_total_amount` - сортировка по сумме

### 5. order_items - Позиции заказа

```sql
CREATE TABLE app.order_items (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    order_id INTEGER NOT NULL REFERENCES app.orders(id) ON DELETE CASCADE,
    nomenclature_id INTEGER NOT NULL REFERENCES app.nomenclature(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(12, 2) NOT NULL CHECK (price >= 0),
    total_price DECIMAL(12, 2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT unique_order_nomenclature UNIQUE (order_id, nomenclature_id)
);
```

**Особенности:**
- Уникальность товара в заказе
- Проверка положительных значений
- Автоматический пересчет суммы заказа

**Индексы:**
- `idx_order_items_order_id` - поиск по заказу
- `idx_order_items_nomenclature_id` - поиск по товару
- `idx_order_items_quantity` - анализ количества
- `idx_order_items_total_price` - анализ сумм

## Функции и триггеры

### 1. update_updated_at_column()
Автоматическое обновление поля `updated_at` при изменении записи.

### 2. update_category_path()
Автоматическое обновление `path` и `level` при изменении иерархии категорий.

### 3. generate_order_number()
Генерация уникального номера заказа в формате "ORD-000001".

### 4. update_order_total()
Автоматический пересчет общей суммы заказа при изменении позиций.

## Представления

### 1. order_summary
Сводная информация по заказам с клиентами и количеством позиций.

### 2. category_hierarchy
Рекурсивное представление иерархии категорий.

## Оптимизация производительности

### Индексы
- **B-tree** для точных поисков и сортировки
- **GIST** для пространственных данных (LTREE)
- **Частичные индексы** для фильтрации по активности

### Настройки PostgreSQL
- `shared_buffers = 256MB`
- `effective_cache_size = 1GB`
- `maintenance_work_mem = 64MB`
- `checkpoint_completion_target = 0.9`
- `wal_buffers = 16MB`
- `default_statistics_target = 100`

### Мониторинг
- Расширение `pg_stat_statements` для анализа запросов
- Автоматический `ANALYZE` для обновления статистики

## Ограничения целостности

### Внешние ключи
- Каскадное удаление для связанных данных
- Ограничение удаления для критических связей

### Проверочные ограничения
- Неотрицательные значения для цен и количеств
- Валидация статусов через ENUM-подобные проверки
- Уникальность критических полей

### Триггеры
- Автоматическое обновление временных меток
- Поддержание целостности иерархии
- Пересчет агрегированных значений

## Безопасность

### Права доступа
- Отдельная схема `app` для изоляции
- Ограниченные права для приложения
- Аудит через поля `created_by` и `updated_by`

### Валидация
- Проверка на уровне базы данных
- Типизированные поля
- Ограничения длины и формата

## Масштабирование

### Партиционирование
Готовность к партиционированию больших таблиц по датам.

### Репликация
Поддержка чтения с реплик для аналитических запросов.

### Кэширование
Интеграция с Redis для кэширования часто запрашиваемых данных.

## Миграции

Схема поддерживает миграции через Alembic для версионирования изменений структуры.
