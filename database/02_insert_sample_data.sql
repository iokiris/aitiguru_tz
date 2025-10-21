-- Вставка тестовых данных для демонстрации
-- Используем схему app

-- Вставка категорий (древовидная структура)
INSERT INTO app.categories (id, uuid, name, parent_id, is_active, level, created_by) VALUES
(1, gen_random_uuid(), 'Бытовая техника', NULL, TRUE, 0, 'system'),
(2, gen_random_uuid(), 'Компьютеры', NULL, TRUE, 0, 'system'),
(3, gen_random_uuid(), 'Стиральные машины', 1, TRUE, 1, 'system'),
(4, gen_random_uuid(), 'Холодильники', 1, TRUE, 1, 'system'),
(5, gen_random_uuid(), 'Телевизоры', 1, TRUE, 1, 'system'),
(6, gen_random_uuid(), 'Ноутбуки', 2, TRUE, 1, 'system'),
(7, gen_random_uuid(), 'Моноблоки', 2, TRUE, 1, 'system'),
(8, gen_random_uuid(), 'однокамерные', 4, TRUE, 2, 'system'),
(9, gen_random_uuid(), 'двухкамерные', 4, TRUE, 2, 'system'),
(10, gen_random_uuid(), '17"', 6, TRUE, 2, 'system'),
(11, gen_random_uuid(), '19"', 6, TRUE, 2, 'system');

-- Обновляем path для категорий (триггер должен сработать автоматически)
UPDATE app.categories SET parent_id = parent_id WHERE id > 0;

-- Вставка номенклатуры
INSERT INTO app.nomenclature (uuid, name, description, sku, quantity, price, cost, category_id, created_by) VALUES
(gen_random_uuid(), 'Стиральная машина Samsung WW90T4540AE', 'Автоматическая стиральная машина Samsung с загрузкой 9 кг', 'SMS-WW90T4540AE', 5, 25000.00, 20000.00, 3, 'system'),
(gen_random_uuid(), 'Стиральная машина LG F2J5TN2W', 'Стиральная машина LG с инверторным двигателем', 'SML-F2J5TN2W', 3, 30000.00, 24000.00, 3, 'system'),
(gen_random_uuid(), 'Холодильник однокамерный Bosch KGN39VLEA', 'Однокамерный холодильник Bosch с системой NoFrost', 'HBO-KGN39VLEA', 2, 35000.00, 28000.00, 8, 'system'),
(gen_random_uuid(), 'Холодильник двухкамерный Samsung RB33J3420SA', 'Двухкамерный холодильник Samsung с технологией Digital Inverter', 'HBS-RB33J3420SA', 4, 45000.00, 36000.00, 9, 'system'),
(gen_random_uuid(), 'Телевизор Samsung UE55TU8000', 'Smart TV Samsung 55" с разрешением 4K UHD', 'TVS-UE55TU8000', 6, 55000.00, 44000.00, 5, 'system'),
(gen_random_uuid(), 'Ноутбук ASUS VivoBook 17"', 'Ноутбук ASUS 17" с процессором Intel Core i5', 'NBA-VB17I5', 3, 45000.00, 36000.00, 10, 'system'),
(gen_random_uuid(), 'Ноутбук HP Pavilion 19"', 'Ноутбук HP 19" с процессором AMD Ryzen 5', 'NBH-PV19R5', 2, 50000.00, 40000.00, 11, 'system'),
(gen_random_uuid(), 'Моноблок Apple iMac 24"', 'Моноблок Apple iMac 24" с чипом M1', 'MBA-IM24M1', 1, 120000.00, 96000.00, 7, 'system');

-- Вставка клиентов
INSERT INTO app.clients (uuid, name, email, phone, address, created_by) VALUES
(gen_random_uuid(), 'Иванов Иван Иванович', 'ivanov@example.com', '+7 (495) 123-45-67', 'г. Москва, ул. Ленина, д. 1, кв. 10', 'system'),
(gen_random_uuid(), 'Петров Петр Петрович', 'petrov@example.com', '+7 (812) 234-56-78', 'г. Санкт-Петербург, ул. Невский проспект, д. 5, кв. 20', 'system'),
(gen_random_uuid(), 'Сидоров Сидор Сидорович', 'sidorov@example.com', '+7 (343) 345-67-89', 'г. Екатеринбург, ул. Мира, д. 15, кв. 30', 'system'),
(gen_random_uuid(), 'Козлова Анна Сергеевна', 'kozlov@example.com', '+7 (495) 456-78-90', 'г. Москва, ул. Тверская, д. 10, кв. 5', 'system'),
(gen_random_uuid(), 'Смирнов Алексей Владимирович', 'smirnov@example.com', '+7 (812) 567-89-01', 'г. Санкт-Петербург, ул. Садовая, д. 20, кв. 15', 'system');

-- Вставка заказов
INSERT INTO app.orders (uuid, order_number, client_id, order_date, total_amount, status, payment_status, notes, created_by) VALUES
(gen_random_uuid(), 'ORD-000001', 1, '2024-01-15 10:30:00+03', 105000.00, 'completed', 'paid', 'Заказ выполнен в срок', 'system'),
(gen_random_uuid(), 'ORD-000002', 2, '2024-01-16 14:20:00+03', 130000.00, 'processing', 'partial', 'Ожидается поступление товара', 'system'),
(gen_random_uuid(), 'ORD-000003', 3, '2024-01-17 09:15:00+03', 120000.00, 'pending', 'unpaid', 'Новый заказ', 'system'),
(gen_random_uuid(), 'ORD-000004', 4, '2024-01-18 11:45:00+03', 80000.00, 'completed', 'paid', 'Быстрая доставка', 'system'),
(gen_random_uuid(), 'ORD-000005', 5, '2024-01-19 16:30:00+03', 95000.00, 'processing', 'paid', 'В обработке', 'system');

-- Вставка позиций заказов
INSERT INTO app.order_items (uuid, order_id, nomenclature_id, quantity, price, total_price, created_by) VALUES
-- Заказ 1 (Иванов)
(gen_random_uuid(), 1, 1, 1, 25000.00, 25000.00, 'system'),  -- Стиральная машина Samsung
(gen_random_uuid(), 1, 3, 1, 35000.00, 35000.00, 'system'),  -- Холодильник однокамерный
(gen_random_uuid(), 1, 4, 1, 45000.00, 45000.00, 'system'),  -- Холодильник двухкамерный

-- Заказ 2 (Петров)
(gen_random_uuid(), 2, 2, 1, 30000.00, 30000.00, 'system'),  -- Стиральная машина LG
(gen_random_uuid(), 2, 5, 1, 55000.00, 55000.00, 'system'),  -- Телевизор Samsung
(gen_random_uuid(), 2, 6, 1, 45000.00, 45000.00, 'system'),  -- Ноутбук ASUS 17"

-- Заказ 3 (Сидоров)
(gen_random_uuid(), 3, 8, 1, 120000.00, 120000.00, 'system'), -- Моноблок Apple iMac

-- Заказ 4 (Козлова)
(gen_random_uuid(), 4, 1, 1, 25000.00, 25000.00, 'system'),  -- Стиральная машина Samsung
(gen_random_uuid(), 4, 3, 1, 35000.00, 35000.00, 'system'),  -- Холодильник однокамерный
(gen_random_uuid(), 4, 5, 1, 55000.00, 55000.00, 'system'),  -- Телевизор Samsung

-- Заказ 5 (Смирнов)
(gen_random_uuid(), 5, 2, 1, 30000.00, 30000.00, 'system'),  -- Стиральная машина LG
(gen_random_uuid(), 5, 4, 1, 45000.00, 45000.00, 'system'),  -- Холодильник двухкамерный
(gen_random_uuid(), 5, 7, 1, 50000.00, 50000.00, 'system');  -- Ноутбук HP 19"

-- Обновляем статистику
ANALYZE app.categories;
ANALYZE app.nomenclature;
ANALYZE app.clients;
ANALYZE app.orders;
ANALYZE app.order_items;
