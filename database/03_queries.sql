-- SQL запросы для задания (оптимизированные для PostgreSQL)

-- 2.1. Получение информации о сумме товаров заказанных под каждого клиента
-- (Наименование клиента, сумма)
-- Оптимизированный запрос с использованием оконных функций
SELECT 
    c.name AS "Наименование клиента",
    COALESCE(SUM(oi.total_price), 0) AS "Сумма",
    COUNT(DISTINCT o.id) AS "Количество заказов",
    MAX(o.order_date) AS "Последний заказ"
FROM app.clients c
LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
LEFT JOIN app.order_items oi ON o.id = oi.order_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name
ORDER BY "Сумма" DESC, c.name;

-- 2.2. Найти количество дочерних элементов первого уровня вложенности для категорий номенклатуры
-- Оптимизированный запрос с использованием рекурсивного CTE
WITH RECURSIVE category_hierarchy AS (
    -- Базовый случай: корневые категории
    SELECT 
        id,
        name,
        parent_id,
        level,
        0 as depth,
        name as full_path,
        ARRAY[id] as path_array
    FROM app.categories 
    WHERE parent_id IS NULL AND is_active = TRUE
    
    UNION ALL
    
    -- Рекурсивный случай: дочерние категории
    SELECT 
        c.id,
        c.name,
        c.parent_id,
        c.level,
        ch.depth + 1,
        ch.full_path || ' -> ' || c.name,
        ch.path_array || c.id
    FROM app.categories c
    INNER JOIN category_hierarchy ch ON c.parent_id = ch.id
    WHERE c.is_active = TRUE
)
SELECT 
    parent.name AS "Категория",
    COUNT(child.id) AS "Количество дочерних элементов первого уровня",
    parent.level AS "Уровень",
    parent.full_path AS "Полный путь"
FROM category_hierarchy parent
LEFT JOIN category_hierarchy child ON child.parent_id = parent.id AND child.depth = 1
WHERE parent.depth = 0
GROUP BY parent.id, parent.name, parent.level, parent.full_path
ORDER BY parent.name;

-- Дополнительные аналитические запросы

-- Топ-5 клиентов по сумме заказов
SELECT 
    c.name AS "Клиент",
    SUM(oi.total_price) AS "Общая сумма",
    COUNT(DISTINCT o.id) AS "Количество заказов",
    AVG(oi.total_price) AS "Средний чек",
    MAX(o.order_date) AS "Последний заказ"
FROM app.clients c
JOIN app.orders o ON c.id = o.client_id
JOIN app.order_items oi ON o.id = oi.order_id
WHERE o.status != 'cancelled'
GROUP BY c.id, c.name
ORDER BY "Общая сумма" DESC
LIMIT 5;

-- Статистика по категориям
SELECT 
    c.name AS "Категория",
    COUNT(n.id) AS "Количество товаров",
    SUM(n.quantity) AS "Общее количество на складе",
    AVG(n.price) AS "Средняя цена",
    MIN(n.price) AS "Минимальная цена",
    MAX(n.price) AS "Максимальная цена",
    SUM(n.price * n.quantity) AS "Общая стоимость"
FROM app.categories c
LEFT JOIN app.nomenclature n ON c.id = n.category_id AND n.is_active = TRUE
WHERE c.is_active = TRUE
GROUP BY c.id, c.name
ORDER BY "Общая стоимость" DESC NULLS LAST;

-- Анализ продаж по месяцам
SELECT 
    DATE_TRUNC('month', o.order_date) AS "Месяц",
    COUNT(DISTINCT o.id) AS "Количество заказов",
    COUNT(oi.id) AS "Количество позиций",
    SUM(oi.total_price) AS "Общая сумма",
    AVG(oi.total_price) AS "Средний чек"
FROM app.orders o
JOIN app.order_items oi ON o.id = oi.order_id
WHERE o.status != 'cancelled'
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY "Месяц" DESC;

-- Топ товаров по продажам
SELECT 
    n.name AS "Товар",
    n.sku AS "Артикул",
    c.name AS "Категория",
    SUM(oi.quantity) AS "Количество продано",
    SUM(oi.total_price) AS "Общая сумма продаж",
    COUNT(DISTINCT o.id) AS "Количество заказов"
FROM app.nomenclature n
JOIN app.categories c ON n.category_id = c.id
JOIN app.order_items oi ON n.id = oi.nomenclature_id
JOIN app.orders o ON oi.order_id = o.id
WHERE o.status != 'cancelled'
GROUP BY n.id, n.name, n.sku, c.name
ORDER BY "Общая сумма продаж" DESC
LIMIT 10;

-- Иерархия категорий с полным путем
SELECT 
    id,
    name,
    level,
    path,
    CASE 
        WHEN level = 0 THEN name
        WHEN level = 1 THEN '  ' || name
        WHEN level = 2 THEN '    ' || name
        WHEN level = 3 THEN '      ' || name
        ELSE REPEAT('  ', level) || name
    END AS "Дерево категорий"
FROM app.category_hierarchy
ORDER BY path;

-- Анализ эффективности категорий
SELECT 
    c.name AS "Категория",
    c.level AS "Уровень",
    COUNT(n.id) AS "Товаров в категории",
    COUNT(oi.id) AS "Позиций в заказах",
    COALESCE(SUM(oi.total_price), 0) AS "Сумма продаж",
    CASE 
        WHEN COUNT(n.id) > 0 THEN ROUND(COUNT(oi.id)::DECIMAL / COUNT(n.id), 2)
        ELSE 0
    END AS "Коэффициент продаж"
FROM app.categories c
LEFT JOIN app.nomenclature n ON c.id = n.category_id AND n.is_active = TRUE
LEFT JOIN app.order_items oi ON n.id = oi.nomenclature_id
LEFT JOIN app.orders o ON oi.order_id = o.id AND o.status != 'cancelled'
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.level
ORDER BY "Сумма продаж" DESC;

-- Детальный анализ заказов
SELECT 
    o.order_number AS "Номер заказа",
    c.name AS "Клиент",
    o.order_date AS "Дата заказа",
    o.total_amount AS "Сумма заказа",
    o.status AS "Статус",
    o.payment_status AS "Статус оплаты",
    COUNT(oi.id) AS "Количество позиций",
    STRING_AGG(n.name, ', ' ORDER BY oi.id) AS "Товары"
FROM app.orders o
JOIN app.clients c ON o.client_id = c.id
JOIN app.order_items oi ON o.id = oi.order_id
JOIN app.nomenclature n ON oi.nomenclature_id = n.id
GROUP BY o.id, o.order_number, c.name, o.order_date, o.total_amount, o.status, o.payment_status
ORDER BY o.order_date DESC;

-- Статистика по статусам заказов
SELECT 
    status AS "Статус",
    COUNT(*) AS "Количество",
    SUM(total_amount) AS "Общая сумма",
    AVG(total_amount) AS "Средняя сумма",
    MIN(order_date) AS "Первый заказ",
    MAX(order_date) AS "Последний заказ"
FROM app.orders
GROUP BY status
ORDER BY "Общая сумма" DESC;

-- Анализ сезонности (если есть данные за разные месяцы)
SELECT 
    EXTRACT(MONTH FROM order_date) AS "Месяц",
    EXTRACT(QUARTER FROM order_date) AS "Квартал",
    COUNT(*) AS "Количество заказов",
    SUM(total_amount) AS "Общая сумма",
    AVG(total_amount) AS "Средний чек"
FROM app.orders
WHERE status != 'cancelled'
GROUP BY EXTRACT(MONTH FROM order_date), EXTRACT(QUARTER FROM order_date)
ORDER BY "Месяц";
