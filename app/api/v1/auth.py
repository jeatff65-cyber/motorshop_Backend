"""Authentication: register, login, forgot/reset password, current user."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.crud.user import user as crud_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if crud_user.get_by_email(db, email=payload.email):
        raise HTTPException(status_code=400, detail="Email is already registered")
    if crud_user.get_by_username(db, username=payload.username):
        raise HTTPException(status_code=400, detail="Username is already taken")
    return crud_user.create(db, obj_in=payload)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Login with OAuth2 form data (username = email, password = password)."""
    db_user = crud_user.get_by_email(db, email=form_data.username)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    token = create_access_token(subject=str(db_user.id))
    return Token(access_token=token)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    db_user = crud_user.get_by_email(db, email=payload.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="No account found for this email")
    reset_token = create_access_token(
        subject=str(db_user.id), expires_delta=timedelta(minutes=30)
    )
    # DEMO MODE: the token is returned directly so the flow can be tested.
    # In production, email this link instead:
    #   http://localhost:3000/reset-password?token=<reset_token>
    return ForgotPasswordResponse(
        message="Reset token generated. In production it would be emailed to you.",
        reset_token=reset_token,
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    user_id = decode_access_token(payload.token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    db_user = db.get(User, int(user_id))
    if db_user is None:
        raise HTTPException(status_code=400, detail="User not found")
    db_user.hashed_password = hash_password(payload.new_password)
    db.add(db_user)
    db.commit()
    return {"message": "Password has been reset successfully"}


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
