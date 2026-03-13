"""API Key management — for CI/CD and programmatic access."""
import hashlib
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models.db import User, ApiKey
from app.api.deps import get_current_user

router = APIRouter()


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: str | None
    created_at: str


class ApiKeyCreated(ApiKeyResponse):
    token: str   # shown only once at creation


def _make_token() -> str:
    return "ark_" + uuid.uuid4().hex


@router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    keys = session.exec(select(ApiKey).where(ApiKey.user_id == current_user.id)).all()
    return [
        ApiKeyResponse(
            id=k.id, name=k.name, key_prefix=k.key_prefix,
            is_active=k.is_active,
            last_used_at=str(k.last_used_at) if k.last_used_at else None,
            created_at=str(k.created_at),
        )
        for k in keys
    ]


@router.post("", response_model=ApiKeyCreated, status_code=201)
def create_api_key(
    body: ApiKeyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    token = _make_token()
    key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=hashlib.sha256(token.encode()).hexdigest(),
        key_prefix=token[:12],
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    return ApiKeyCreated(
        id=key.id, name=key.name, key_prefix=key.key_prefix,
        is_active=key.is_active,
        last_used_at=None,
        created_at=str(key.created_at),
        token=token,
    )


@router.delete("/{key_id}", status_code=204)
def revoke_api_key(
    key_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    key = session.exec(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    ).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    session.add(key)
    session.commit()
