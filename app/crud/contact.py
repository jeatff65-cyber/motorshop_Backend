"""Contact CRUD operations."""
from app.crud.base import CRUDBase
from app.models.contact import Contact

contact = CRUDBase(Contact)
