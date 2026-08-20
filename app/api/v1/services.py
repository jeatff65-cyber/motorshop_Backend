"""Services: public read + admin CRUD."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_optional_user, require_admin
from app.crud.service import service as crud_service
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=PaginatedResponse[ServiceOut])
def list_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Public visitors only see active services; admins see everything.
    only_active = not (current_user is not None and current_user.role == "admin")
    items = crud_service.get_multi(db, skip=skip, limit=limit, only_active=only_active)
    total = crud_service.count(db, only_active=only_active)
    return PaginatedResponse(total=total, items=items)


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = crud_service.get(db, service_id)
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


# ---- Admin CRUD ----

@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return crud_service.create(db, obj_in=payload)


@router.put("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = crud_service.get(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return crud_service.update(db, db_obj=service, obj_in=payload)


@router.delete("/{service_id}", response_model=MessageResponse)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = crud_service.get(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    crud_service.remove(db, obj_id=service_id)
    return MessageResponse(message="Service deleted successfully")
