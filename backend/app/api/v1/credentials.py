from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import httpx
from app.database import get_session
from app.models.db import UserCredential
from app.api.deps import get_current_user, User
from app.core.crypto import encrypt, decrypt, mask
from app.config import settings

router = APIRouter()


class ModelsRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@router.post("/models")
async def fetch_models(body: ModelsRequest, current_user: User = Depends(get_current_user)):
    provider = body.provider
    key = body.api_key or ""
    base = body.base_url or ""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if provider == "anthropic":
                r = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                )
                r.raise_for_status()
                ids = [m["id"] for m in r.json().get("data", [])]

            elif provider == "openai":
                r = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
                r.raise_for_status()
                data = r.json().get("data", [])
                ids = sorted(
                    [m["id"] for m in data if "gpt" in m["id"]],
                    reverse=True,
                )

            elif provider == "gemini":
                r = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                )
                r.raise_for_status()
                ids = [
                    m["name"].replace("models/", "")
                    for m in r.json().get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]

            elif provider == "groq":
                r = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
                r.raise_for_status()
                ids = [m["id"] for m in r.json().get("data", [])]

            elif provider == "mistral":
                r = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
                r.raise_for_status()
                ids = [m["id"] for m in r.json().get("data", [])]

            elif provider == "ollama":
                url = base.rstrip("/") or "http://localhost:11434"
                r = await client.get(f"{url}/api/tags")
                r.raise_for_status()
                ids = [m["name"] for m in r.json().get("models", [])]

            elif provider == "custom":
                url = base.rstrip("/")
                if not url:
                    return {"models": []}
                r = await client.get(
                    f"{url}/models",
                    headers={"Authorization": f"Bearer {key}"} if key else {},
                )
                r.raise_for_status()
                data = r.json()
                ids = [m["id"] for m in data.get("data", data.get("models", []))]

            else:
                return {"models": []}

        return {"models": ids}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Provider returned {e.response.status_code}: invalid API key or permissions")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CredentialCreate(BaseModel):
    provider: str
    label: Optional[str] = None
    api_key: Optional[str] = None
    model: str
    base_url: Optional[str] = None


class CredentialUpdate(BaseModel):
    label: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None


class CredentialResponse(BaseModel):
    id: str
    provider: str
    label: Optional[str]
    api_key_masked: Optional[str]
    model: str
    base_url: Optional[str]
    is_active: bool
    created_at: str


def _to_response(c: UserCredential) -> CredentialResponse:
    masked = None
    if c.api_key_encrypted:
        try:
            raw = decrypt(c.api_key_encrypted, settings.SECRET_KEY)
            masked = mask(raw)
        except Exception:
            masked = "••••••••"
    return CredentialResponse(
        id=c.id,
        provider=c.provider,
        label=c.label,
        api_key_masked=masked,
        model=c.model,
        base_url=c.base_url,
        is_active=c.is_active,
        created_at=str(c.created_at),
    )


@router.get("", response_model=list[CredentialResponse])
def list_credentials(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    rows = session.exec(
        select(UserCredential).where(UserCredential.user_id == current_user.id)
    ).all()
    return [_to_response(c) for c in rows]


@router.post("", response_model=CredentialResponse, status_code=201)
def create_credential(
    body: CredentialCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    encrypted = None
    if body.api_key:
        encrypted = encrypt(body.api_key, settings.SECRET_KEY)

    cred = UserCredential(
        user_id=current_user.id,
        provider=body.provider,
        label=body.label,
        api_key_encrypted=encrypted,
        model=body.model,
        base_url=body.base_url,
        is_active=False,
    )
    session.add(cred)
    session.commit()
    session.refresh(cred)
    return _to_response(cred)


@router.patch("/{cred_id}", response_model=CredentialResponse)
def update_credential(
    cred_id: str,
    body: CredentialUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cred = session.get(UserCredential, cred_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    if body.label is not None:
        cred.label = body.label
    if body.api_key is not None:
        cred.api_key_encrypted = encrypt(body.api_key, settings.SECRET_KEY)
    if body.model is not None:
        cred.model = body.model
    if body.base_url is not None:
        cred.base_url = body.base_url
    session.add(cred)
    session.commit()
    session.refresh(cred)
    return _to_response(cred)


@router.delete("/{cred_id}", status_code=204)
def delete_credential(
    cred_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cred = session.get(UserCredential, cred_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    session.delete(cred)
    session.commit()


@router.post("/{cred_id}/deactivate", response_model=CredentialResponse)
def deactivate_credential(
    cred_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cred = session.get(UserCredential, cred_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.is_active = False
    session.add(cred)
    session.commit()
    session.refresh(cred)
    return _to_response(cred)


@router.post("/{cred_id}/activate", response_model=CredentialResponse)
def activate_credential(
    cred_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    cred = session.get(UserCredential, cred_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Credential not found")

    # deactivate all others
    others = session.exec(
        select(UserCredential).where(
            UserCredential.user_id == current_user.id,
            UserCredential.is_active == True,
        )
    ).all()
    for other in others:
        other.is_active = False
        session.add(other)

    cred.is_active = True
    session.add(cred)
    session.commit()
    session.refresh(cred)
    return _to_response(cred)
