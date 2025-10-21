"""
API endpoints для категорий
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.base import PaginationParams
from app.schemas.category import (
    CategoryCreate,
    CategoryHierarchy,
    CategoryResponse,
    CategoryStats,
    CategoryTree,
    CategoryUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
):
    """Получение списка категорий"""
    query = text(
        """
        SELECT
            c.id, c.uuid, c.name, c.parent_id, c.level, c.path, c.is_active,
            c.created_at, c.updated_at, c.created_by, c.updated_by,
            COUNT(child.id) as children_count
        FROM app.categories c
        LEFT JOIN app.categories child ON c.id = child.parent_id AND child.is_active = TRUE
        WHERE c.is_active = :is_active OR :is_active IS NULL
        GROUP BY c.id, c.uuid, c.name, c.parent_id, c.level, c.path, c.is_active,
                 c.created_at, c.updated_at, c.created_by, c.updated_by
        ORDER BY c.name
        LIMIT :limit OFFSET :offset
    """
    )

    result = db.execute(query, {"is_active": is_active, "limit": pagination.size, "offset": pagination.offset})

    return [
        CategoryResponse(
            id=row.id,
            uuid=row.uuid,
            name=row.name,
            parent_id=row.parent_id,
            level=row.level,
            path=row.path,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            children_count=row.children_count,
        )
        for row in result
    ]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Получение категории по ID"""
    query = text(
        """
        SELECT
            c.id, c.uuid, c.name, c.parent_id, c.level, c.path, c.is_active,
            c.created_at, c.updated_at, c.created_by, c.updated_by,
            COUNT(child.id) as children_count
        FROM app.categories c
        LEFT JOIN app.categories child ON c.id = child.parent_id AND child.is_active = TRUE
        WHERE c.id = :category_id
        GROUP BY c.id, c.uuid, c.name, c.parent_id, c.level, c.path, c.is_active,
                 c.created_at, c.updated_at, c.created_by, c.updated_by
    """
    )

    result = db.execute(query, {"category_id": category_id}).first()

    if not result:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    return CategoryResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        parent_id=result.parent_id,
        level=result.level,
        path=result.path,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        children_count=result.children_count,
    )


@router.post("/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Создание новой категории"""
    # Проверяем существование родительской категории
    if category.parent_id:
        parent_query = text("SELECT id FROM app.categories WHERE id = :parent_id AND is_active = TRUE")
        parent_result = db.execute(parent_query, {"parent_id": category.parent_id}).first()
        if not parent_result:
            raise HTTPException(status_code=400, detail="Родительская категория не найдена")

    # Проверяем уникальность имени в рамках одного уровня
    name_query = text(
        """
        SELECT id FROM app.categories
        WHERE name = :name AND parent_id = :parent_id AND is_active = TRUE
    """
    )
    existing = db.execute(name_query, {"name": category.name, "parent_id": category.parent_id}).first()

    if existing:
        raise HTTPException(status_code=400, detail="Категория с таким именем уже существует")

    # Создаем категорию
    insert_query = text(
        """
        INSERT INTO app.categories (name, parent_id, created_by)
        VALUES (:name, :parent_id, :created_by)
        RETURNING id, uuid, name, parent_id, level, path, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    result = db.execute(
        insert_query, {"name": category.name, "parent_id": category.parent_id, "created_by": "api_user"}
    ).first()

    db.commit()

    return CategoryResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        parent_id=result.parent_id,
        level=result.level,
        path=result.path,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        children_count=0,
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    """Обновление категории"""
    # Проверяем существование категории
    check_query = text("SELECT id FROM app.categories WHERE id = :category_id")
    existing = db.execute(check_query, {"category_id": category_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    # Проверяем родительскую категорию
    if category_update.parent_id:
        parent_query = text("SELECT id FROM app.categories WHERE id = :parent_id AND is_active = TRUE")
        parent_result = db.execute(parent_query, {"parent_id": category_update.parent_id}).first()
        if not parent_result:
            raise HTTPException(status_code=400, detail="Родительская категория не найдена")

    # Обновляем категорию
    update_fields = []
    update_values = {"category_id": category_id}

    if category_update.name is not None:
        update_fields.append("name = :name")
        update_values["name"] = category_update.name

    if category_update.parent_id is not None:
        update_fields.append("parent_id = :parent_id")
        update_values["parent_id"] = category_update.parent_id

    if category_update.is_active is not None:
        update_fields.append("is_active = :is_active")
        update_values["is_active"] = category_update.is_active

    if not update_fields:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    update_query = text(
        f"""
        UPDATE app.categories
        SET {', '.join(update_fields)}, updated_by = :updated_by
        WHERE id = :category_id
        RETURNING id, uuid, name, parent_id, level, path, is_active, created_at, updated_at, created_by, updated_by
    """
    )

    update_values["updated_by"] = "api_user"

    result = db.execute(update_query, update_values).first()
    db.commit()

    # Получаем количество дочерних элементов
    children_query = text("SELECT COUNT(*) FROM app.categories WHERE parent_id = :category_id AND is_active = TRUE")
    children_count = db.execute(children_query, {"category_id": category_id}).scalar()

    return CategoryResponse(
        id=result.id,
        uuid=result.uuid,
        name=result.name,
        parent_id=result.parent_id,
        level=result.level,
        path=result.path,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        children_count=children_count,
    )


@router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Удаление категории"""
    # Проверяем существование категории
    check_query = text("SELECT id FROM app.categories WHERE id = :category_id")
    existing = db.execute(check_query, {"category_id": category_id}).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    # Проверяем наличие дочерних категорий
    children_query = text("SELECT COUNT(*) FROM app.categories WHERE parent_id = :category_id")
    children_count = db.execute(children_query, {"category_id": category_id}).scalar()

    if children_count > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить категорию с дочерними элементами")

    # Проверяем наличие товаров в категории
    products_query = text("SELECT COUNT(*) FROM app.nomenclature WHERE category_id = :category_id")
    products_count = db.execute(products_query, {"category_id": category_id}).scalar()

    if products_count > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить категорию с товарами")

    # Удаляем категорию
    delete_query = text("DELETE FROM app.categories WHERE id = :category_id")
    db.execute(delete_query, {"category_id": category_id})
    db.commit()

    return {"message": "Категория удалена"}


@router.get("/tree/", response_model=List[CategoryTree])
async def get_category_tree(db: Session = Depends(get_db)):
    """Получение дерева категорий"""
    query = text(
        """
        WITH RECURSIVE category_tree AS (
            SELECT
                id, name, parent_id, level, path,
                0 as depth,
                name as full_path
            FROM app.categories
            WHERE parent_id IS NULL AND is_active = TRUE

            UNION ALL

            SELECT
                c.id, c.name, c.parent_id, c.level, c.path,
                ct.depth + 1,
                ct.full_path || ' -> ' || c.name
            FROM app.categories c
            JOIN category_tree ct ON c.parent_id = ct.id
            WHERE c.is_active = TRUE
        )
        SELECT
            id, name, parent_id, level, path, depth, full_path
        FROM category_tree
        ORDER BY path
    """
    )

    result = db.execute(query)

    # Строим дерево
    categories_dict = {}
    root_categories = []

    for row in result:
        category_data = {
            "id": row.id,
            "name": row.name,
            "parent_id": row.parent_id,
            "level": row.level,
            "path": row.path,
            "children": [],
        }

        categories_dict[row.id] = category_data

        if row.parent_id is None:
            root_categories.append(category_data)
        else:
            if row.parent_id in categories_dict:
                categories_dict[row.parent_id]["children"].append(category_data)

    return root_categories


@router.get("/hierarchy/", response_model=List[CategoryHierarchy])
async def get_category_hierarchy(db: Session = Depends(get_db)):
    """Получение иерархии категорий"""
    query = text(
        """
        SELECT
            id, name, level, path,
            CASE
                WHEN level = 0 THEN name
                WHEN level = 1 THEN '  ' || name
                WHEN level = 2 THEN '    ' || name
                WHEN level = 3 THEN '      ' || name
                ELSE REPEAT('  ', level) || name
            END AS tree_display
        FROM app.category_hierarchy
        ORDER BY path
    """
    )

    result = db.execute(query)

    return [
        CategoryHierarchy(id=row.id, name=row.name, level=row.level, path=row.path, full_path=row.tree_display)
        for row in result
    ]


@router.get("/stats/", response_model=List[CategoryStats])
async def get_category_stats(db: Session = Depends(get_db)):
    """Статистика по категориям"""
    query = text(
        """
        SELECT
            c.id as category_id,
            c.name as category_name,
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
        CategoryStats(
            category_id=row.category_id,
            category_name=row.category_name,
            products_count=row.products_count,
            total_quantity=row.total_quantity,
            avg_price=float(row.avg_price),
            min_price=float(row.min_price),
            max_price=float(row.max_price),
            total_value=float(row.total_value),
        )
        for row in result
    ]
