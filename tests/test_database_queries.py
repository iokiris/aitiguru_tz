"""
Тесты SQL запросов из задания
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text


class TestDatabaseQueries:
    """Тесты SQL запросов"""
    
    def test_query_2_1_client_order_summary(self, db_session: Session, sample_clients, sample_orders):
        """Тест запроса 2.1: Сумма товаров заказанных под каждого клиента"""
        query = text("""
            SELECT 
                c.name AS "Наименование клиента",
                COALESCE(SUM(oi.total_price), 0) AS "Сумма"
            FROM app.clients c
            LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
            LEFT JOIN app.order_items oi ON o.id = oi.order_id
            WHERE c.is_active = TRUE
            GROUP BY c.id, c.name
            ORDER BY c.name
        """)
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        assert len(rows) == 2
        
        # Проверяем данные первого клиента
        client_1 = next(row for row in rows if row[0] == "Иванов Иван Иванович")
        assert client_1[1] == 60000.0  # Сумма заказов
        
        # Проверяем данные второго клиента
        client_2 = next(row for row in rows if row[0] == "Петров Петр Петрович")
        assert client_2[1] == 45000.0  # Сумма заказов
    
    def test_query_2_2_category_children_count(self, db_session: Session, sample_categories):
        """Тест запроса 2.2: Количество дочерних элементов первого уровня"""
        query = text("""
            WITH RECURSIVE category_hierarchy AS (
                SELECT 
                    id, name, parent_id, level,
                    0 as depth,
                    name as full_path,
                    ARRAY[id] as path_array
                FROM app.categories 
                WHERE parent_id IS NULL AND is_active = TRUE
                
                UNION ALL
                
                SELECT 
                    c.id, c.name, c.parent_id, c.level,
                    ch.depth + 1,
                    ch.full_path || ' -> ' || c.name,
                    ch.path_array || c.id
                FROM app.categories c
                INNER JOIN category_hierarchy ch ON c.parent_id = ch.id
                WHERE c.is_active = TRUE
            )
            SELECT 
                parent.name AS "Категория",
                COUNT(child.id) AS "Количество дочерних элементов первого уровня"
            FROM category_hierarchy parent
            LEFT JOIN category_hierarchy child ON child.parent_id = parent.id AND child.depth = 1
            WHERE parent.depth = 0
            GROUP BY parent.id, parent.name
            ORDER BY parent.name
        """)
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        assert len(rows) == 2
        
        # Проверяем категорию "Бытовая техника"
        household_tech = next(row for row in rows if row[0] == "Бытовая техника")
        assert household_tech[1] == 2  # Стиральные машины, Холодильники
        
        # Проверяем категорию "Компьютеры"
        computers = next(row for row in rows if row[0] == "Компьютеры")
        assert computers[1] == 1  # Ноутбуки
    
    def test_category_hierarchy_query(self, db_session: Session, sample_categories):
        """Тест запроса иерархии категорий"""
        query = text("""
            WITH RECURSIVE category_hierarchy AS (
                SELECT 
                    id, name, parent_id, level,
                    0 as depth,
                    name as full_path
                FROM app.categories 
                WHERE parent_id IS NULL AND is_active = TRUE
                
                UNION ALL
                
                SELECT 
                    c.id, c.name, c.parent_id, c.level,
                    ch.depth + 1,
                    ch.full_path || ' -> ' || c.name
                FROM app.categories c
                INNER JOIN category_hierarchy ch ON c.parent_id = ch.id
                WHERE c.is_active = TRUE
            )
            SELECT 
                id, name, level, depth, full_path
            FROM category_hierarchy
            ORDER BY full_path
        """)
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        assert len(rows) == 5  # Все категории
        
        # Проверяем корневые категории
        root_categories = [row for row in rows if row[3] == 0]  # depth = 0
        assert len(root_categories) == 2
        
        # Проверяем категории первого уровня
        first_level = [row for row in rows if row[3] == 1]  # depth = 1
        assert len(first_level) == 3  # Стиральные машины, Холодильники, Ноутбуки
    
    def test_tree_structure_query(self, db_session: Session, sample_categories):
        """Тест запроса структуры дерева"""
        query = text("""
            SELECT 
                c1.name AS "Родительская категория",
                c2.name AS "Дочерняя категория",
                c3.name AS "Внучатая категория"
            FROM app.categories c1
            LEFT JOIN app.categories c2 ON c1.id = c2.parent_id
            LEFT JOIN app.categories c3 ON c2.id = c3.parent_id
            WHERE c1.parent_id IS NULL AND c1.is_active = TRUE
            ORDER BY c1.name, c2.name, c3.name
        """)
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        # Проверяем, что запрос выполняется без ошибок
        assert result is not None
        
        # Проверяем наличие корневых категорий
        root_categories = set(row[0] for row in rows if row[0] is not None)
        expected_roots = {"Бытовая техника", "Компьютеры"}
        assert root_categories == expected_roots
    
    def test_order_summary_view(self, db_session: Session, sample_orders):
        """Тест представления order_summary"""
        query = text("SELECT * FROM app.order_summary ORDER BY order_date DESC")
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        assert len(rows) == 2
        
        # Проверяем структуру данных
        for row in rows:
            assert hasattr(row, 'id')
            assert hasattr(row, 'order_number')
            assert hasattr(row, 'client_name')
            assert hasattr(row, 'total_amount')
            assert hasattr(row, 'status')
            assert hasattr(row, 'items_count')
    
    def test_category_hierarchy_view(self, db_session: Session, sample_categories):
        """Тест представления category_hierarchy"""
        query = text("SELECT * FROM app.category_hierarchy ORDER BY path")
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        assert len(rows) == 5  # Все категории
        
        # Проверяем структуру данных
        for row in rows:
            assert hasattr(row, 'id')
            assert hasattr(row, 'name')
            assert hasattr(row, 'level')
            assert hasattr(row, 'path')
    
    def test_foreign_key_constraints(self, db_session: Session):
        """Тест внешних ключей"""
        # Проверяем внешние ключи для categories
        query = text("""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'categories' AND REFERENCED_TABLE_NAME IS NOT NULL
            AND TABLE_SCHEMA = 'app'
        """)
        
        result = db_session.execute(query)
        fk_categories = result.fetchall()
        assert len(fk_categories) > 0
        
        # Проверяем внешние ключи для nomenclature
        query = text("""
            SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'nomenclature' AND REFERENCED_TABLE_NAME IS NOT NULL
            AND TABLE_SCHEMA = 'app'
        """)
        
        result = db_session.execute(query)
        fk_nomenclature = result.fetchall()
        assert len(fk_nomenclature) > 0
    
    def test_indexes_exist(self, db_session: Session):
        """Тест существования индексов"""
        query = text("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'app' 
            AND indexname LIKE 'idx_%'
        """)
        
        result = db_session.execute(query)
        indexes = result.fetchall()
        
        # Проверяем наличие основных индексов
        index_names = [idx[0] for idx in indexes]
        expected_indexes = [
            'idx_categories_parent_id',
            'idx_categories_name',
            'idx_nomenclature_category_id',
            'idx_nomenclature_name',
            'idx_clients_name',
            'idx_orders_client_id'
        ]
        
        for expected_idx in expected_indexes:
            assert expected_idx in index_names
    
    def test_triggers_exist(self, db_session: Session):
        """Тест существования триггеров"""
        query = text("""
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'app'
        """)
        
        result = db_session.execute(query)
        triggers = result.fetchall()
        
        # Проверяем наличие основных триггеров
        trigger_names = [trigger[0] for trigger in triggers]
        expected_triggers = [
            'update_categories_updated_at',
            'update_nomenclature_updated_at',
            'update_clients_updated_at',
            'update_orders_updated_at',
            'update_category_path_trigger',
            'set_order_number_trigger'
        ]
        
        for expected_trigger in expected_triggers:
            assert expected_trigger in trigger_names
    
    def test_functions_exist(self, db_session: Session):
        """Тест существования функций"""
        query = text("""
            SELECT routine_name, routine_type
            FROM information_schema.routines
            WHERE routine_schema = 'app'
        """)
        
        result = db_session.execute(query)
        functions = result.fetchall()
        
        # Проверяем наличие основных функций
        function_names = [func[0] for func in functions]
        expected_functions = [
            'update_updated_at_column',
            'update_category_path',
            'generate_order_number',
            'set_order_number',
            'update_order_total'
        ]
        
        for expected_function in expected_functions:
            assert expected_function in function_names
