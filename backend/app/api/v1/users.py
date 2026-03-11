from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
from app.database import get_session
from app.models.db import User
from app.api.deps import get_current_user
from app.core.security import get_password_hash, verify_password

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str
    avatar_url: str | None = None


class UpdateProfileRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, created_at=str(current_user.created_at), avatar_url=current_user.avatar_url)


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="Email already in use")
    current_user.email = body.email
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return UserResponse(id=current_user.id, email=current_user.email, created_at=str(current_user.created_at), avatar_url=current_user.avatar_url)


@router.post("/me/password", status_code=204)
def change_password(
    body: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    current_user.password_hash = get_password_hash(body.new_password)
    session.add(current_user)
    session.commit()
