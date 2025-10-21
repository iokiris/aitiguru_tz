"""
API endpoints для номенклатуры
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.base import PaginationParams
from app.schemas.nomenclature import (
    NomenclatureCreate,
    NomenclatureResponse,
    NomenclatureSearch,
    NomenclatureStats,
    NomenclatureUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[NomenclatureResponse])
async def get_nomenclature(
    db: Session = Depends(get_db), pagination: PaginationParams = Depends(), search: NomenclatureSearch = Depends()
):
    """Получение списка номенклатуры"""
    where_conditions = ["n.is_active = :is_active"]
    params = {"is_active": search.is_active}

    if search.query:
        where_conditions.append("(n.name ILIKE :query OR n.sku ILIKE :query OR n.description ILIKE :query)")
        params["query"] = f"%{search.query}%"

    if search.category_id:
        where_conditions.append("n.category_id = :category_id")
        params["category_id"] = search.category_id

    if search.min_price is not None:
        where_conditions.append("n.price >= :min_price")
        params["min_price"] = search.min_price

    if search.max_price is not None:
        where_conditions.append("n.price <= :max_price")
        params["max_price"] = search.max_price

    if search.in_stock:
        where_conditions.append("n.quantity > 0")

    where_clause = " AND ".join(where_conditions)

    query = text(
        f"""
        SELECT
            n.id, n.uuid, n.name, n.description, n.sku, n.quantity, n.price, n.cost,
            n.category_id, n.is_active, n.created_at, n.updated_at, n.created_by, n.updated_by,
            c.name as category_name
        FROM app.nomenclature n
        JOIN app.categories c ON n.category_id = c.id
        WHERE {where_clause}
        ORDER BY n.name
        LIMIT :limit OFFSET :offset
    """
    )

    params.update({"limit": pagination.size, "offset": pagination.offset})

    result = db.execute(query, params)

    return [
        NomenclatureResponse(
            id=row.id,
            uuid=row.uuid,
            name=row.name,
            description=row.description,
            sku=row.sku,
            quantity=row.quantity,
            price=row.price,
            cost=row.cost,
            category_id=row.category_id,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            category_name=row.category_name,
        )
        for row in result
    ]


@router.get("/{nomenclature_id}", response_model=NomenclatureResponse)
async def get_nomenclature_item(nomenclature_id: int, db: Session = Depends(get_db)):
    """Получение товара по ID"""
    query = text(
        """
        SELECT
            n.id, n.uuid, n.name, n.description, n.sku, n.quantity, n.price, n.cost,
            n.category_id, n.is_active, n.created_at, n.updated_at, n.created_by, n.updated_by,
            c.name as category_name
        FROM app.nomenclature n
        JOIN app.categories c ON n.category_id = c.id
        WHERE n.id = :nomenclature_id
    """
    )

    result = db.execute(query, {"nomenclature_id": nomenclature_id}).first()

    if not result:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return NomenclatureResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        description=result.description,
        sku=result.sku,
        quantity=result.quantity,
        price=result.price,
        cost=result.cost,
        category_id=result.category_id,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        category_name=result.category_name,
    )


@router.post("/", response_model=NomenclatureResponse)
async def create_nomenclature(nomenclature: NomenclatureCreate, db: Session = Depends(get_db)):
    """Создание нового товара"""
    # Проверяем существование категории
    category_query = text("SELECT id FROM app.categories WHERE id = :category_id AND is_active = TRUE")
    category_result = db.execute(category_query, {"category_id": nomenclature.category_id}).first()
    if not category_result:
        raise HTTPException(status_code=400, detail="Категория не найдена")

    # Проверяем уникальность SKU
    if nomenclature.sku:
        sku_query = text("SELECT id FROM app.nomenclature WHERE sku = :sku")
        existing_sku = db.execute(sku_query, {"sku": nomenclature.sku}).first()
        if existing_sku:
            raise HTTPException(status_code=400, detail="Товар с таким артикулом уже существует")

    # Создаем товар
    insert_query = text(
        """
        INSERT INTO app.nomenclature (name, description, sku, quantity, price, cost, category_id, created_by)
        VALUES (:name, :description, :sku, :quantity, :price, :cost, :category_id, :created_by)
        RETURNING id, uuid, name, description, sku, quantity, price, cost, category_id, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    result = db.execute(
        insert_query,
        {
            "name": nomenclature.name,
            "description": nomenclature.description,
            "sku": nomenclature.sku,
            "quantity": nomenclature.quantity,
            "price": nomenclature.price,
            "cost": nomenclature.cost,
            "category_id": nomenclature.category_id,
            "created_by": "api_user",
        },
    ).first()

    db.commit()

    # Получаем название категории
    category_name_query = text("SELECT name FROM app.categories WHERE id = :category_id")
    category_name = db.execute(category_name_query, {"category_id": nomenclature.category_id}).scalar()

    return NomenclatureResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        description=result.description,
        sku=result.sku,
        quantity=result.quantity,
        price=result.price,
        cost=result.cost,
        category_id=result.category_id,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        category_name=category_name,
    )


@router.put("/{nomenclature_id}", response_model=NomenclatureResponse)
async def update_nomenclature(
    nomenclature_id: int, nomenclature_update: NomenclatureUpdate, db: Session = Depends(get_db)
):
    """Обновление товара"""
    # Проверяем существование товара
    check_query = text("SELECT id FROM app.nomenclature WHERE id = :nomenclature_id")
    existing = db.execute(check_query, {"nomenclature_id": nomenclature_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Проверяем категорию
    if nomenclature_update.category_id:
        category_query = text("SELECT id FROM app.categories WHERE id = :category_id AND is_active = TRUE")
        category_result = db.execute(category_query, {"category_id": nomenclature_update.category_id}).first()
        if not category_result:
            raise HTTPException(status_code=400, detail="Категория не найдена")

    # Проверяем уникальность SKU
    if nomenclature_update.sku:
        sku_query = text("SELECT id FROM app.nomenclature WHERE sku = :sku AND id != :nomenclature_id")
        existing_sku = db.execute(
            sku_query, {"sku": nomenclature_update.sku, "nomenclature_id": nomenclature_id}
        ).first()
        if existing_sku:
            raise HTTPException(status_code=400, detail="Товар с таким артикулом уже существует")

    # Обновляем товар
    update_fields = []
    update_values = {"nomenclature_id": nomenclature_id}

    if nomenclature_update.name is not None:
        update_fields.append("name = :name")
        update_values["name"] = nomenclature_update.name

    if nomenclature_update.description is not None:
        update_fields.append("description = :description")
        update_values["description"] = nomenclature_update.description

    if nomenclature_update.sku is not None:
        update_fields.append("sku = :sku")
        update_values["sku"] = nomenclature_update.sku

    if nomenclature_update.quantity is not None:
        update_fields.append("quantity = :quantity")
        update_values["quantity"] = nomenclature_update.quantity

    if nomenclature_update.price is not None:
        update_fields.append("price = :price")
        update_values["price"] = nomenclature_update.price

    if nomenclature_update.cost is not None:
        update_fields.append("cost = :cost")
        update_values["cost"] = nomenclature_update.cost

    if nomenclature_update.category_id is not None:
        update_fields.append("category_id = :category_id")
        update_values["category_id"] = nomenclature_update.category_id

    if nomenclature_update.is_active is not None:
        update_fields.append("is_active = :is_active")
        update_values["is_active"] = nomenclature_update.is_active

    if not update_fields:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    update_query = text(
        f"""
        UPDATE app.nomenclature
        SET {', '.join(update_fields)}, updated_by = :updated_by
        WHERE id = :nomenclature_id
        RETURNING id, uuid, name, description, sku, quantity, price, cost, category_id, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    update_values["updated_by"] = "api_user"

    result = db.execute(update_query, update_values).first()
    db.commit()

    # Получаем название категории
    category_name_query = text("SELECT name FROM app.categories WHERE id = :category_id")
    category_name = db.execute(category_name_query, {"category_id": result.category_id}).scalar()

    return NomenclatureResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        description=result.description,
        sku=result.sku,
        quantity=result.quantity,
        price=result.price,
        cost=result.cost,
        category_id=result.category_id,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        category_name=category_name,
    )


@router.delete("/{nomenclature_id}")
async def delete_nomenclature(nomenclature_id: int, db: Session = Depends(get_db)):
    """Удаление товара"""
    # Проверяем существование товара
    check_query = text("SELECT id FROM app.nomenclature WHERE id = :nomenclature_id")
    existing = db.execute(check_query, {"nomenclature_id": nomenclature_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Проверяем наличие в заказах
    orders_query = text("SELECT COUNT(*) FROM app.order_items WHERE nomenclature_id = :nomenclature_id")
    orders_count = db.execute(orders_query, {"nomenclature_id": nomenclature_id}).scalar()

    if orders_count > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить товар, который есть в заказах")

    # Удаляем товар
    delete_query = text("DELETE FROM app.nomenclature WHERE id = :nomenclature_id")
    db.execute(delete_query, {"nomenclature_id": nomenclature_id})
    db.commit()

    return {"message": "Товар удален"}


@router.get("/stats/", response_model=List[NomenclatureStats])
async def get_nomenclature_stats(db: Session = Depends(get_db)):
    """Статистика по номенклатуре"""
    query = text(
        """
        SELECT
            n.id as nomenclature_id,
            n.name,
            n.sku,
            c.name as category_name,
            COALESCE(SUM(oi.quantity), 0) AS total_sold,
            COALESCE(SUM(oi.total_price), 0) AS total_revenue,
            COUNT(DISTINCT o.id) AS orders_count
        FROM app.nomenclature n
        JOIN app.categories c ON n.category_id = c.id
        LEFT JOIN app.order_items oi ON n.id = oi.nomenclature_id
        LEFT JOIN app.orders o ON oi.order_id = o.id AND o.status != 'cancelled'
        WHERE n.is_active = TRUE
        GROUP BY n.id, n.name, n.sku, c.name
        ORDER BY total_revenue DESC
    """
    )

    result = db.execute(query)

    return [
        NomenclatureStats(
            nomenclature_id=row.nomenclature_id,
            name=row.name,
            sku=row.sku,
            category_name=row.category_name,
            total_sold=row.total_sold,
            total_revenue=row.total_revenue,
            orders_count=row.orders_count,
        )
        for row in result
    ]
