-- Создание базы данных и пользователя (выполняется автоматически через Docker)
-- CREATE DATABASE order_management;
-- CREATE USER app_user WITH PASSWORD 'app_password';
-- GRANT ALL PRIVILEGES ON DATABASE order_management TO app_user;

-- Включаем расширения для оптимизации
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Создание схемы для приложения
CREATE SCHEMA IF NOT EXISTS app;

-- Таблица категорий номенклатуры (древовидная структура)
CREATE TABLE app.categories (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES app.categories(id) ON DELETE CASCADE,
    path LTREE, -- Для быстрого поиска по иерархии
    level INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Индексы для оптимизации запросов по категориям
CREATE INDEX CONCURRENTLY idx_categories_parent_id ON app.categories(parent_id);
CREATE INDEX CONCURRENTLY idx_categories_name ON app.categories(name);
CREATE INDEX CONCURRENTLY idx_categories_path ON app.categories USING GIST(path);
CREATE INDEX CONCURRENTLY idx_categories_level ON app.categories(level);
CREATE INDEX CONCURRENTLY idx_categories_active ON app.categories(is_active) WHERE is_active = TRUE;

-- Таблица номенклатуры товаров
CREATE TABLE app.nomenclature (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100) UNIQUE,
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

-- Индексы для номенклатуры
CREATE INDEX CONCURRENTLY idx_nomenclature_category_id ON app.nomenclature(category_id);
CREATE INDEX CONCURRENTLY idx_nomenclature_name ON app.nomenclature(name);
CREATE INDEX CONCURRENTLY idx_nomenclature_sku ON app.nomenclature(sku);
CREATE INDEX CONCURRENTLY idx_nomenclature_price ON app.nomenclature(price);
CREATE INDEX CONCURRENTLY idx_nomenclature_active ON app.nomenclature(is_active) WHERE is_active = TRUE;
CREATE INDEX CONCURRENTLY idx_nomenclature_quantity ON app.nomenclature(quantity) WHERE quantity > 0;

-- Таблица клиентов
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

-- Индексы для клиентов
CREATE INDEX CONCURRENTLY idx_clients_name ON app.clients(name);
CREATE INDEX CONCURRENTLY idx_clients_email ON app.clients(email);
CREATE INDEX CONCURRENTLY idx_clients_phone ON app.clients(phone);
CREATE INDEX CONCURRENTLY idx_clients_active ON app.clients(is_active) WHERE is_active = TRUE;

-- Таблица заказов
CREATE TABLE app.orders (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    client_id INTEGER NOT NULL REFERENCES app.clients(id) ON DELETE RESTRICT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
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

-- Индексы для заказов
CREATE INDEX CONCURRENTLY idx_orders_client_id ON app.orders(client_id);
CREATE INDEX CONCURRENTLY idx_orders_order_number ON app.orders(order_number);
CREATE INDEX CONCURRENTLY idx_orders_order_date ON app.orders(order_date);
CREATE INDEX CONCURRENTLY idx_orders_status ON app.orders(status);
CREATE INDEX CONCURRENTLY idx_orders_payment_status ON app.orders(payment_status);
CREATE INDEX CONCURRENTLY idx_orders_total_amount ON app.orders(total_amount);

-- Таблица позиций заказа
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

-- Индексы для позиций заказа
CREATE INDEX CONCURRENTLY idx_order_items_order_id ON app.order_items(order_id);
CREATE INDEX CONCURRENTLY idx_order_items_nomenclature_id ON app.order_items(nomenclature_id);
CREATE INDEX CONCURRENTLY idx_order_items_quantity ON app.order_items(quantity);
CREATE INDEX CONCURRENTLY idx_order_items_total_price ON app.order_items(total_price);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_categories_updated_at 
    BEFORE UPDATE ON app.categories 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_nomenclature_updated_at 
    BEFORE UPDATE ON app.nomenclature 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON app.clients 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON app.orders 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

-- Функция для обновления path в категориях
CREATE OR REPLACE FUNCTION app.update_category_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path = NEW.id::text::ltree;
        NEW.level = 0;
    ELSE
        SELECT path || NEW.id::text::ltree, level + 1
        INTO NEW.path, NEW.level
        FROM app.categories
        WHERE id = NEW.parent_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для обновления path
CREATE TRIGGER update_category_path_trigger
    BEFORE INSERT OR UPDATE ON app.categories
    FOR EACH ROW EXECUTE FUNCTION app.update_category_path();

-- Функция для генерации номера заказа
CREATE OR REPLACE FUNCTION app.generate_order_number()
RETURNS TEXT AS $$
DECLARE
    new_number TEXT;
    counter INTEGER;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(order_number FROM '^ORD-(\d+)$') AS INTEGER)), 0) + 1
    INTO counter
    FROM app.orders
    WHERE order_number ~ '^ORD-\d+$';
    
    new_number := 'ORD-' || LPAD(counter::TEXT, 6, '0');
    RETURN new_number;
END;
$$ language 'plpgsql';

-- Триггер для автоматической генерации номера заказа
CREATE OR REPLACE FUNCTION app.set_order_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
        NEW.order_number := app.generate_order_number();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_order_number_trigger
    BEFORE INSERT ON app.orders
    FOR EACH ROW EXECUTE FUNCTION app.set_order_number();

-- Функция для обновления общей суммы заказа
CREATE OR REPLACE FUNCTION app.update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE app.orders
    SET total_amount = (
        SELECT COALESCE(SUM(total_price), 0)
        FROM app.order_items
        WHERE order_id = COALESCE(NEW.order_id, OLD.order_id)
    )
    WHERE id = COALESCE(NEW.order_id, OLD.order_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Триггеры для обновления суммы заказа
CREATE TRIGGER update_order_total_after_insert
    AFTER INSERT ON app.order_items
    FOR EACH ROW EXECUTE FUNCTION app.update_order_total();

CREATE TRIGGER update_order_total_after_update
    AFTER UPDATE ON app.order_items
    FOR EACH ROW EXECUTE FUNCTION app.update_order_total();

CREATE TRIGGER update_order_total_after_delete
    AFTER DELETE ON app.order_items
    FOR EACH ROW EXECUTE FUNCTION app.update_order_total();

-- Представления для аналитики
CREATE VIEW app.order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.order_date,
    c.name as client_name,
    o.total_amount,
    o.status,
    o.payment_status,
    COUNT(oi.id) as items_count
FROM app.orders o
JOIN app.clients c ON o.client_id = c.id
LEFT JOIN app.order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.order_number, o.order_date, c.name, o.total_amount, o.status, o.payment_status;

-- Представление для иерархии категорий
CREATE VIEW app.category_hierarchy AS
WITH RECURSIVE category_tree AS (
    SELECT 
        id,
        name,
        parent_id,
        path,
        level,
        0 as depth,
        name as full_path
    FROM app.categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT 
        c.id,
        c.name,
        c.parent_id,
        c.path,
        c.level,
        ct.depth + 1,
        ct.full_path || ' -> ' || c.name
    FROM app.categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;

-- Настройки для оптимизации
ALTER TABLE app.categories SET (fillfactor = 90);
ALTER TABLE app.nomenclature SET (fillfactor = 90);
ALTER TABLE app.clients SET (fillfactor = 90);
ALTER TABLE app.orders SET (fillfactor = 90);
ALTER TABLE app.order_items SET (fillfactor = 90);

-- Статистика для планировщика
ANALYZE app.categories;
ANALYZE app.nomenclature;
ANALYZE app.clients;
ANALYZE app.orders;
ANALYZE app.order_items;
