"""
API endpoints для заказов
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.base import PaginationParams
from app.schemas.order import (
    OrderCreate,
    OrderDetail,
    OrderItemResponse,
    OrderResponse,
    OrderSearch,
    OrderStats,
    OrderUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    db: Session = Depends(get_db), pagination: PaginationParams = Depends(), search: OrderSearch = Depends()
):
    """Получение списка заказов"""
    where_conditions = []
    params = {}

    if search.client_id:
        where_conditions.append("o.client_id = :client_id")
        params["client_id"] = search.client_id

    if search.status:
        where_conditions.append("o.status = :status")
        params["status"] = search.status.value

    if search.payment_status:
        where_conditions.append("o.payment_status = :payment_status")
        params["payment_status"] = search.payment_status.value

    if search.date_from:
        where_conditions.append("o.order_date >= :date_from")
        params["date_from"] = search.date_from

    if search.date_to:
        where_conditions.append("o.order_date <= :date_to")
        params["date_to"] = search.date_to

    if search.min_amount is not None:
        where_conditions.append("o.total_amount >= :min_amount")
        params["min_amount"] = search.min_amount

    if search.max_amount is not None:
        where_conditions.append("o.total_amount <= :max_amount")
        params["max_amount"] = search.max_amount

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    query = text(
        f"""
        SELECT
            o.id, o.uuid, o.client_id, o.order_number, o.order_date, o.total_amount,
            o.status, o.payment_status, o.notes, o.created_at, o.updated_at, o.created_by, o.updated_by,
            c.name as client_name,
            COUNT(oi.id) as items_count
        FROM app.orders o
        JOIN app.clients c ON o.client_id = c.id
        LEFT JOIN app.order_items oi ON o.id = oi.order_id
        WHERE {where_clause}
        GROUP BY o.id, o.uuid, o.client_id, o.order_number, o.order_date, o.total_amount,
                 o.status, o.payment_status, o.notes, o.created_at, o.updated_at, o.created_by, o.updated_by,
                 c.name
        ORDER BY o.order_date DESC
        LIMIT :limit OFFSET :offset
    """
    )

    params.update({"limit": pagination.size, "offset": pagination.offset})

    result = db.execute(query, params)

    return [
        OrderResponse(
            id=row.id,
            uuid=row.uuid,
            client_id=row.client_id,
            order_number=row.order_number,
            order_date=row.order_date,
            total_amount=row.total_amount,
            status=row.status,
            payment_status=row.payment_status,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            client_name=row.client_name,
            items_count=row.items_count,
            items=[],  # Будет заполнено в детальном запросе
        )
        for row in result
    ]


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Получение заказа по ID"""
    # Получаем основную информацию о заказе
    order_query = text(
        """
        SELECT
            o.id, o.uuid, o.client_id, o.order_number, o.order_date, o.total_amount,
            o.status, o.payment_status, o.notes, o.created_at, o.updated_at, o.created_by, o.updated_by,
            c.name as client_name
        FROM app.orders o
        JOIN app.clients c ON o.client_id = c.id
        WHERE o.id = :order_id
    """
    )

    order_result = db.execute(order_query, {"order_id": order_id}).first()

    if not order_result:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Получаем позиции заказа
    items_query = text(
        """
        SELECT
            oi.id, oi.uuid, oi.order_id, oi.nomenclature_id, oi.quantity, oi.price, oi.total_price,
            oi.created_at, oi.created_by,
            n.name as nomenclature_name,
            n.sku as nomenclature_sku
        FROM app.order_items oi
        JOIN app.nomenclature n ON oi.nomenclature_id = n.id
        WHERE oi.order_id = :order_id
        ORDER BY oi.id
    """
    )

    items_result = db.execute(items_query, {"order_id": order_id})

    items = [
        OrderItemResponse(
            id=row.id,
            uuid=row.uuid,
            order_id=row.order_id,
            nomenclature_id=row.nomenclature_id,
            quantity=row.quantity,
            price=row.price,
            total_price=row.total_price,
            created_at=row.created_at,
            created_by=row.created_by,
            nomenclature_name=row.nomenclature_name,
            nomenclature_sku=row.nomenclature_sku,
        )
        for row in items_result
    ]

    return OrderDetail(
        id=order_result.id,
        uuid=order_result.uuid,
        client_id=order_result.client_id,
        order_number=order_result.order_number,
        order_date=order_result.order_date,
        total_amount=order_result.total_amount,
        status=order_result.status,
        payment_status=order_result.payment_status,
        notes=order_result.notes,
        created_at=order_result.created_at,
        updated_at=order_result.updated_at,
        created_by=order_result.created_by,
        updated_by=order_result.updated_by,
        client_name=order_result.client_name,
        items_count=len(items),
        items=items,
    )


@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Создание нового заказа"""
    # Проверяем существование клиента
    client_query = text("SELECT id FROM app.clients WHERE id = :client_id AND is_active = TRUE")
    client_result = db.execute(client_query, {"client_id": order.client_id}).first()
    if not client_result:
        raise HTTPException(status_code=400, detail="Клиент не найден")

    # Проверяем товары
    for item in order.items:
        nomenclature_query = text(
            """
            SELECT id, quantity, price FROM app.nomenclature
            WHERE id = :nomenclature_id AND is_active = TRUE
        """
        )
        nomenclature_result = db.execute(nomenclature_query, {"nomenclature_id": item.nomenclature_id}).first()

        if not nomenclature_result:
            raise HTTPException(
                status_code=400,
                detail=f"Товар с ID {item.nomenclature_id} не найден",
            )

        if nomenclature_result.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара {item.nomenclature_id} на складе",
            )

        # Проверяем цену
        if item.price != nomenclature_result.price:
            raise HTTPException(
                status_code=400,
                detail=f"Цена товара {item.nomenclature_id} изменилась",
            )

    # Создаем заказ
    order_insert_query = text(
        """
        INSERT INTO app.orders (client_id, order_date, status, payment_status, notes, created_by)
        VALUES (:client_id, :order_date, :status, :payment_status, :notes, :created_by)
        RETURNING id, uuid, client_id, order_number, order_date, total_amount, status, payment_status, notes, created_at, updated_at, created_by, updated_by
    """
    )

    order_result = db.execute(
        order_insert_query,
        {
            "client_id": order.client_id,
            "order_date": order.order_date or datetime.now(),
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "notes": order.notes,
            "created_by": "api_user",
        },
    ).first()

    # Создаем позиции заказа
    for item in order.items:
        item_insert_query = text(
            """
            INSERT INTO app.order_items (order_id, nomenclature_id, quantity, price, total_price, created_by)
            VALUES (:order_id, :nomenclature_id, :quantity, :price, :total_price, :created_by)
        """
        )

        db.execute(
            item_insert_query,
            {
                "order_id": order_result.id,
                "nomenclature_id": item.nomenclature_id,
                "quantity": item.quantity,
                "price": item.price,
                "total_price": item.total_price,
                "created_by": "api_user",
            },
        )

        # Обновляем количество товара на складе
        update_quantity_query = text(
            """
            UPDATE app.nomenclature
            SET quantity = quantity - :quantity, updated_by = :updated_by
            WHERE id = :nomenclature_id
        """
        )

        db.execute(
            update_quantity_query,
            {"quantity": item.quantity, "nomenclature_id": item.nomenclature_id, "updated_by": "api_user"},
        )

    db.commit()

    # Получаем имя клиента
    client_name_query = text("SELECT name FROM app.clients WHERE id = :client_id")
    client_name = db.execute(client_name_query, {"client_id": order.client_id}).scalar()

    return OrderResponse(
        id=order_result.id,
        uuid=order_result.uuid,
        client_id=order_result.client_id,
        order_number=order_result.order_number,
        order_date=order_result.order_date,
        total_amount=order_result.total_amount,
        status=order_result.status,
        payment_status=order_result.payment_status,
        notes=order_result.notes,
        created_at=order_result.created_at,
        updated_at=order_result.updated_at,
        created_by=order_result.created_by,
        updated_by=order_result.updated_by,
        client_name=client_name,
        items_count=len(order.items),
        items=[],
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    """Обновление заказа"""
    # Проверяем существование заказа
    check_query = text("SELECT id FROM app.orders WHERE id = :order_id")
    existing = db.execute(check_query, {"order_id": order_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Обновляем заказ
    update_fields = []
    update_values = {"order_id": order_id}

    if order_update.status is not None:
        update_fields.append("status = :status")
        update_values["status"] = order_update.status.value

    if order_update.payment_status is not None:
        update_fields.append("payment_status = :payment_status")
        update_values["payment_status"] = order_update.payment_status.value

    if order_update.notes is not None:
        update_fields.append("notes = :notes")
        update_values["notes"] = order_update.notes

    if not update_fields:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    update_query = text(
        f"""
        UPDATE app.orders
        SET {', '.join(update_fields)}, updated_by = :updated_by
        WHERE id = :order_id
        RETURNING id, uuid, client_id, order_number, order_date, total_amount, status, payment_status, notes, created_at, updated_at, created_by, updated_by
    """
    )

    update_values["updated_by"] = "api_user"

    result = db.execute(update_query, update_values).first()
    db.commit()

    # Получаем имя клиента и количество позиций
    client_info_query = text(
        """
        SELECT c.name as client_name, COUNT(oi.id) as items_count
        FROM app.clients c
        LEFT JOIN app.order_items oi ON oi.order_id = :order_id
        WHERE c.id = :client_id
        GROUP BY c.name
    """
    )

    client_info = db.execute(client_info_query, {"order_id": order_id, "client_id": result.client_id}).first()

    return OrderResponse(
        id=result.id,
        uuid=result.uuid,
        client_id=result.client_id,
        order_number=result.order_number,
        order_date=result.order_date,
        total_amount=result.total_amount,
        status=result.status,
        payment_status=result.payment_status,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        client_name=client_info.client_name,
        items_count=client_info.items_count,
        items=[],
    )


@router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Удаление заказа"""
    # Проверяем существование заказа
    check_query = text("SELECT id, status FROM app.orders WHERE id = :order_id")
    existing = db.execute(check_query, {"order_id": order_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Проверяем статус заказа
    if existing.status in ["completed", "processing"]:
        raise HTTPException(status_code=400, detail="Нельзя удалить заказ в статусе 'completed' или 'processing'")

    # Возвращаем товары на склад
    items_query = text(
        """
        SELECT nomenclature_id, quantity
        FROM app.order_items
        WHERE order_id = :order_id
    """
    )

    items = db.execute(items_query, {"order_id": order_id})

    for item in items:
        return_quantity_query = text(
            """
            UPDATE app.nomenclature
            SET quantity = quantity + :quantity, updated_by = :updated_by
            WHERE id = :nomenclature_id
        """
        )

        db.execute(
            return_quantity_query,
            {"quantity": item.quantity, "nomenclature_id": item.nomenclature_id, "updated_by": "api_user"},
        )

    # Удаляем заказ (позиции удалятся каскадно)
    delete_query = text("DELETE FROM app.orders WHERE id = :order_id")
    db.execute(delete_query, {"order_id": order_id})
    db.commit()

    return {"message": "Заказ удален"}


@router.get("/stats/", response_model=OrderStats)
async def get_order_stats(db: Session = Depends(get_db)):
    """Статистика по заказам"""
    query = text(
        """
        SELECT
            COUNT(*) as total_orders,
            COALESCE(SUM(total_amount), 0) as total_amount,
            COALESCE(AVG(total_amount), 0) as avg_order,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
        FROM app.orders
        WHERE status != 'cancelled'
    """
    )

    result = db.execute(query).first()

    return OrderStats(
        total_orders=result.total_orders,
        total_amount=result.total_amount,
        avg_order=result.avg_order,
        pending_orders=result.pending_orders,
        completed_orders=result.completed_orders,
    )
