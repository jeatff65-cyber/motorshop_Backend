"""Admin dashboard statistics."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import require_admin
from app.crud.contact import contact as crud_contact
from app.crud.product import product as crud_product
from app.crud.service import service as crud_service
from app.crud.user import user as crud_user
from app.db.base import get_db
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_services: int
    total_contacts: int
    active_products: int
    active_services: int


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> DashboardStats:
    return DashboardStats(
        total_users=crud_user.count(db),
        total_products=crud_product.count(db),
        total_services=crud_service.count(db),
        total_contacts=crud_contact.count(db),
        active_products=crud_product.count(db, only_active=True),
        active_services=crud_service.count(db, only_active=True),
    )
