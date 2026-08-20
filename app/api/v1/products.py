"""Products: public read + admin CRUD."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_optional_user, require_admin
from app.crud.product import product as crud_product
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Public visitors only see active products; admins see everything.
    only_active = not (current_user is not None and current_user.role == "admin")
    items = crud_product.get_multi(db, skip=skip, limit=limit, only_active=only_active)
    total = crud_product.count(db, only_active=only_active)
    return PaginatedResponse(total=total, items=items)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud_product.get(db, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---- Admin CRUD ----

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return crud_product.create(db, obj_in=payload)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = crud_product.get(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud_product.update(db, db_obj=product, obj_in=payload)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = crud_product.get(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud_product.remove(db, obj_id=product_id)
    return MessageResponse(message="Product deleted successfully")
