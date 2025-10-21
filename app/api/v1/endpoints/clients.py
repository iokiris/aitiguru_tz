"""
API endpoints для клиентов
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.base import PaginationParams
from app.schemas.client import (
    ClientCreate,
    ClientResponse,
    ClientSearch,
    ClientStats,
    ClientUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ClientResponse])
async def get_clients(
    db: Session = Depends(get_db), pagination: PaginationParams = Depends(), search: ClientSearch = Depends()
):
    """Получение списка клиентов"""
    where_conditions = ["c.is_active = :is_active"]
    params = {"is_active": search.is_active}

    if search.query:
        where_conditions.append("(c.name ILIKE :query OR c.email ILIKE :query OR c.phone ILIKE :query)")
        params["query"] = f"%{search.query}%"

    where_clause = " AND ".join(where_conditions)

    query = text(
        f"""
        SELECT
            c.id, c.uuid, c.name, c.email, c.phone, c.address, c.is_active,
            c.created_at, c.updated_at, c.created_by, c.updated_by,
            COUNT(DISTINCT o.id) as orders_count,
            COALESCE(SUM(oi.total_price), 0) as total_spent
        FROM app.clients c
        LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE {where_clause}
        GROUP BY c.id, c.uuid, c.name, c.email, c.phone, c.address, c.is_active,
                 c.created_at, c.updated_at, c.created_by, c.updated_by
        ORDER BY c.name
        LIMIT :limit OFFSET :offset
    """
    )

    params.update({"limit": pagination.size, "offset": pagination.offset})

    result = db.execute(query, params)

    return [
        ClientResponse(
            id=row.id,
            uuid=row.uuid,
            name=row.name,
            email=row.email,
            phone=row.phone,
            address=row.address,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            orders_count=row.orders_count,
            total_spent=float(row.total_spent),
        )
        for row in result
    ]


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """Получение клиента по ID"""
    query = text(
        """
        SELECT
            c.id, c.uuid, c.name, c.email, c.phone, c.address, c.is_active,
            c.created_at, c.updated_at, c.created_by, c.updated_by,
            COUNT(DISTINCT o.id) as orders_count,
            COALESCE(SUM(oi.total_price), 0) as total_spent
        FROM app.clients c
        LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE c.id = :client_id
        GROUP BY c.id, c.uuid, c.name, c.email, c.phone, c.address, c.is_active,
                 c.created_at, c.updated_at, c.created_by, c.updated_by
    """
    )

    result = db.execute(query, {"client_id": client_id}).first()

    if not result:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    return ClientResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        email=result.email,
        phone=result.phone,
        address=result.address,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        orders_count=result.orders_count,
        total_spent=float(result.total_spent),
    )


@router.post("/", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Создание нового клиента"""
    # Проверяем уникальность email
    if client.email:
        email_query = text("SELECT id FROM app.clients WHERE email = :email")
        existing_email = db.execute(email_query, {"email": client.email}).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Клиент с таким email уже существует")

    # Создаем клиента
    insert_query = text(
        """
        INSERT INTO app.clients (name, email, phone, address, created_by)
        VALUES (:name, :email, :phone, :address, :created_by)
        RETURNING id, uuid, name, email, phone, address, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    result = db.execute(
        insert_query,
        {
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "created_by": "api_user",
        },
    ).first()

    db.commit()

    return ClientResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        email=result.email,
        phone=result.phone,
        address=result.address,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        orders_count=0,
        total_spent=0.0,
    )


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    """Обновление клиента"""
    # Проверяем существование клиента
    check_query = text("SELECT id FROM app.clients WHERE id = :client_id")
    existing = db.execute(check_query, {"client_id": client_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Проверяем уникальность email
    if client_update.email:
        email_query = text("SELECT id FROM app.clients WHERE email = :email AND id != :client_id")
        existing_email = db.execute(email_query, {"email": client_update.email, "client_id": client_id}).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Клиент с таким email уже существует")

    # Обновляем клиента
    update_fields = []
    update_values = {"client_id": client_id}

    if client_update.name is not None:
        update_fields.append("name = :name")
        update_values["name"] = client_update.name

    if client_update.email is not None:
        update_fields.append("email = :email")
        update_values["email"] = client_update.email

    if client_update.phone is not None:
        update_fields.append("phone = :phone")
        update_values["phone"] = client_update.phone

    if client_update.address is not None:
        update_fields.append("address = :address")
        update_values["address"] = client_update.address

    if client_update.is_active is not None:
        update_fields.append("is_active = :is_active")
        update_values["is_active"] = client_update.is_active

    if not update_fields:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    update_query = text(
        f"""
        UPDATE app.clients
        SET {', '.join(update_fields)}, updated_by = :updated_by
        WHERE id = :client_id
        RETURNING id, uuid, name, email, phone, address, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    update_values["updated_by"] = "api_user"

    result = db.execute(update_query, update_values).first()
    db.commit()

    # Получаем статистику
    stats_query = text(
        """
        SELECT
            COUNT(DISTINCT o.id) as orders_count,
            COALESCE(SUM(oi.total_price), 0) as total_spent
        FROM app.orders o
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE o.client_id = :client_id AND o.status != 'cancelled'
    """
    )

    stats = db.execute(stats_query, {"client_id": client_id}).first()

    return ClientResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        email=result.email,
        phone=result.phone,
        address=result.address,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        orders_count=stats.orders_count,
        total_spent=float(stats.total_spent),
    )


@router.delete("/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Удаление клиента"""
    # Проверяем существование клиента
    check_query = text("SELECT id FROM app.clients WHERE id = :client_id")
    existing = db.execute(check_query, {"client_id": client_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Проверяем наличие заказов
    orders_query = text("SELECT COUNT(*) FROM app.orders WHERE client_id = :client_id")
    orders_count = db.execute(orders_query, {"client_id": client_id}).scalar()

    if orders_count > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить клиента с заказами")

    # Удаляем клиента
    delete_query = text("DELETE FROM app.clients WHERE id = :client_id")
    db.execute(delete_query, {"client_id": client_id})
    db.commit()

    return {"message": "Клиент удален"}


@router.get("/stats/", response_model=List[ClientStats])
async def get_client_stats(db: Session = Depends(get_db)):
    """Статистика по клиентам"""
    query = text(
        """
        SELECT
            c.id as client_id,
            c.name as client_name,
            COALESCE(SUM(oi.total_price), 0) AS total_amount,
            COUNT(DISTINCT o.id) AS orders_count,
            COALESCE(AVG(oi.total_price), 0) AS avg_order,
            MAX(o.order_date) AS last_order
        FROM app.clients c
        LEFT JOIN app.orders o ON c.id = o.client_id AND o.status != 'cancelled'
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE c.is_active = TRUE
        GROUP BY c.id, c.name
        ORDER BY total_amount DESC
    """
    )

    result = db.execute(query)

    return [
        ClientStats(
            client_id=row.client_id,
            client_name=row.client_name,
            total_amount=float(row.total_amount),
            orders_count=row.orders_count,
            avg_order=float(row.avg_order),
            last_order=row.last_order,
        )
        for row in result
    ]
