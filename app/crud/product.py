"""Product CRUD operations."""
from app.crud.base import CRUDBase
from app.models.product import Product

product = CRUDBase(Product)
