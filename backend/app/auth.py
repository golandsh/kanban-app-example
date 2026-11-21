import hashlib
import hmac
import os
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel

SESSION_COOKIE_NAME = "kanban_session"
DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"


def _get_secret() -> bytes:
    return os.getenv("SESSION_SECRET", "kanban-mvp-dev-secret").encode("utf-8")


def _sign_username(username: str) -> str:
    sig = hmac.new(_get_secret(), username.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{username}.{sig}"


def verify_session_token(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    username, sig = token.rsplit(".", 1)
    expected = hmac.new(_get_secret(), username.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return username


def get_current_user(kanban_session: str | None = Cookie(default=None)) -> str:
    username = verify_session_token(kanban_session)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return username


class LoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    if payload.username != DEMO_USERNAME or payload.password != DEMO_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=_sign_username(payload.username),
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"username": payload.username}


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(kanban_session: str | None = Cookie(default=None)) -> dict[str, str]:
    username = get_current_user(kanban_session)
    return {"username": username}
