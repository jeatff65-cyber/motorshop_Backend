"""Contacts: public submit + admin manage."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import require_admin
from app.crud.contact import contact as crud_contact
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.contact import ContactCreate, ContactOut

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def submit_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    return crud_contact.create(db, obj_in=payload)


# ---- Admin only ----

@router.get("", response_model=PaginatedResponse[ContactOut])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    items = crud_contact.get_multi(db, skip=skip, limit=limit)
    total = crud_contact.count(db)
    return PaginatedResponse(total=total, items=items)


@router.delete("/{contact_id}", response_model=MessageResponse)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    contact = crud_contact.get(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    crud_contact.remove(db, obj_id=contact_id)
    return MessageResponse(message="Contact deleted successfully")
