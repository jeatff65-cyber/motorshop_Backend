"""Users: own profile + admin user management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_admin
from app.crud.user import user as crud_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return crud_user.update(db, db_obj=current_user, obj_in=payload)


# ---- Admin only ----

@router.get("", response_model=PaginatedResponse[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    items = crud_user.get_multi(db, skip=skip, limit=limit)
    total = crud_user.count(db)
    return PaginatedResponse(total=total, items=items)


@router.patch("/{user_id}", response_model=UserOut)
def admin_update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    target = crud_user.get(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return crud_user.update(db, db_obj=target, obj_in=payload)
