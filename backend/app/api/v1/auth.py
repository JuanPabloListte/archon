from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
from pydantic import BaseModel
import httpx
from app.database import get_session
from app.models.db import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, password_hash=get_password_hash(body.password))
    session.add(user)
    session.commit()
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


@router.get("/google")
def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.BACKEND_URL}/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/google/callback")
async def google_callback(code: str, session: Session = Depends(get_session)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{settings.BACKEND_URL}/api/v1/auth/google/callback",
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()
        if "access_token" not in token_data:
            return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

        userinfo_resp = await client.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {token_data['access_token']}"
        })
        userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    google_id = userinfo.get("id")
    avatar_url = userinfo.get("picture")
    if not email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(email=email, google_id=google_id, avatar_url=avatar_url)
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        if not user.google_id:
            user.google_id = google_id
        if avatar_url:
            user.avatar_url = avatar_url
        session.add(user)
        session.commit()

    token = create_access_token({"sub": user.email})
    html = f"""<!DOCTYPE html><html><body><script>
      if (window.opener) {{
        window.opener.postMessage({{type:"oauth_success",token:"{token}"}}, "{settings.FRONTEND_URL}");
        window.close();
      }} else {{
        window.location.href = "{settings.FRONTEND_URL}/auth/callback?token={token}";
      }}
    </script></body></html>"""
    return HTMLResponse(content=html)
