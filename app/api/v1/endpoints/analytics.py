"""
API endpoints для аналитики
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.base import PaginationParams
from app.schemas.order import CategoryChildrenCount, ClientOrderSummary

router = APIRouter()


@router.get("/client-summary", response_model=List[ClientOrderSummary])
async def get_client_order_summary(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    """
    Получение информации о сумме товаров заказанных под каждого клиента
    (Наименование клиента, сумма)
    """
    query = text(
        """
        SELECT
            c.name AS client_name,
            COALESCE(SUM(oi.total_price), 0) AS total_amount,
            COUNT(DISTINCT o.id) AS orders_count,
            MAX(o.order_date) AS last_order
        FROM app.clients c
        LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE c.is_active = TRUE
        GROUP BY c.id, c.name
        ORDER BY total_amount DESC, c.name
        LIMIT :limit OFFSET :offset
    """
    )

    result = db.execute(query, {"limit": pagination.size, "offset": pagination.offset})

    return [
        ClientOrderSummary(
            client_name=row.client_name,
            total_amount=row.total_amount,
            orders_count=row.orders_count,
            last_order=row.last_order,
        )
        for row in result
    ]


@router.get("/category-children", response_model=List[CategoryChildrenCount])
async def get_category_children_count(db: Session = Depends(get_db), pagination: PaginationParams = Depends()):
    """
    Найти количество дочерних элементов первого уровня вложенности для категорий номенклатуры
    """
    query = text(
        """
        WITH RECURSIVE category_hierarchy AS (
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
            parent.name AS category_name,
            COUNT(child.id) AS children_count,
            parent.level,
            parent.full_path
        FROM category_hierarchy parent
        LEFT JOIN category_hierarchy child ON child.parent_id = parent.id AND child.depth = 1
        WHERE parent.depth = 0
        GROUP BY parent.id, parent.name, parent.level, parent.full_path
        ORDER BY parent.name
        LIMIT :limit OFFSET :offset
    """
    )

    result = db.execute(query, {"limit": pagination.size, "offset": pagination.offset})

    return [
        CategoryChildrenCount(
            category_name=row.category_name, children_count=row.children_count, level=row.level, full_path=row.full_path
        )
        for row in result
    ]


@router.get("/top-clients")
async def get_top_clients(
    limit: int = Query(5, ge=1, le=50, description="Количество клиентов"), db: Session = Depends(get_db)
):
    """Топ клиентов по сумме заказов"""
    query = text(
        """
        SELECT
            c.name AS client_name,
            SUM(oi.total_price) AS total_amount,
            COUNT(DISTINCT o.id) AS orders_count,
            AVG(oi.total_price) AS avg_order,
            MAX(o.order_date) AS last_order
        FROM app.clients c
        JOIN app.orders o ON c.id = o.client_id
        JOIN app.order_items oi ON o.id = oi.order_id
        WHERE o.status != 'cancelled' AND c.is_active = TRUE
        GROUP BY c.id, c.name
        ORDER BY total_amount DESC
        LIMIT :limit
    """
    )

    result = db.execute(query, {"limit": limit})

    return [
        {
            "client_name": row.client_name,
            "total_amount": float(row.total_amount),
            "orders_count": row.orders_count,
            "avg_order": float(row.avg_order),
            "last_order": row.last_order,
        }
        for row in result
    ]


@router.get("/category-stats")
async def get_category_stats(db: Session = Depends(get_db)):
    """Статистика по категориям"""
    query = text(
        """
        SELECT
            c.name AS category_name,
            COUNT(n.id) AS products_count,
            COALESCE(SUM(n.quantity), 0) AS total_quantity,
            COALESCE(AVG(n.price), 0) AS avg_price,
            COALESCE(MIN(n.price), 0) AS min_price,
            COALESCE(MAX(n.price), 0) AS max_price,
            COALESCE(SUM(n.price * n.quantity), 0) AS total_value
        FROM app.categories c
        LEFT JOIN app.nomenclature n ON c.id = n.category_id AND n.is_active = TRUE
        WHERE c.is_active = TRUE
        GROUP BY c.id, c.name
        ORDER BY total_value DESC NULLS LAST
    """
    )

    result = db.execute(query)

    return [
        {
            "category_name": row.category_name,
            "products_count": row.products_count,
            "total_quantity": row.total_quantity,
            "avg_price": float(row.avg_price),
            "min_price": float(row.min_price),
            "max_price": float(row.max_price),
            "total_value": float(row.total_value),
        }
        for row in result
    ]


@router.get("/sales-by-month")
async def get_sales_by_month(db: Session = Depends(get_db)):
    """Продажи по месяцам"""
    query = text(
        """
        SELECT
            DATE_TRUNC('month', o.order_date) AS month,
            COUNT(DISTINCT o.id) AS orders_count,
            COUNT(oi.id) AS items_count,
            SUM(oi.total_price) AS total_amount,
            AVG(oi.total_price) AS avg_order
        FROM app.orders o
        JOIN app.order_items oi ON o.id = oi.order_id
        WHERE o.status != 'cancelled'
        GROUP BY DATE_TRUNC('month', o.order_date)
        ORDER BY month DESC
    """
    )

    result = db.execute(query)

    return [
        {
            "month": row.month,
            "orders_count": row.orders_count,
            "items_count": row.items_count,
            "total_amount": float(row.total_amount),
            "avg_order": float(row.avg_order),
        }
        for row in result
    ]


@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50, description="Количество товаров"), db: Session = Depends(get_db)
):
    """Топ товаров по продажам"""
    query = text(
        """
        SELECT
            n.name AS product_name,
            n.sku,
            cat.name AS category_name,
            SUM(oi.quantity) AS total_sold,
            SUM(oi.total_price) AS total_revenue,
            COUNT(DISTINCT o.id) AS orders_count
        FROM app.nomenclature n
        JOIN app.categories cat ON n.category_id = cat.id
        JOIN app.order_items oi ON n.id = oi.nomenclature_id
        JOIN app.orders o ON oi.order_id = o.id
        WHERE o.status != 'cancelled' AND n.is_active = TRUE
        GROUP BY n.id, n.name, n.sku, cat.name
        ORDER BY total_revenue DESC
        LIMIT :limit
    """
    )

    result = db.execute(query, {"limit": limit})

    return [
        {
            "product_name": row.product_name,
            "sku": row.sku,
            "category_name": row.category_name,
            "total_sold": row.total_sold,
            "total_revenue": float(row.total_revenue),
            "orders_count": row.orders_count,
        }
        for row in result
    ]
