"""Authentication and profile routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_access_token, hash_password, verify_password
from ..config import VISA_CATEGORIES
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import (
    LoginRequest,
    ProfileUpdate,
    SignupRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _validate_category(category: str) -> str:
    return category if category in VISA_CATEGORIES else "Other"


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already in use")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        visa_category=_validate_category(payload.visa_category),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user.visa_category = _validate_category(payload.visa_category)
    db.commit()
    db.refresh(user)
    return user
