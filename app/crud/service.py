"""Service CRUD operations."""
from app.crud.base import CRUDBase
from app.models.service import Service

service = CRUDBase(Service)
