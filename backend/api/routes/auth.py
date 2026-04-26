"""Authentication API routes: login, logout, session check."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.auth.password import verify_password
from backend.db.models.user import User
from backend.api.deps import get_current_user, get_db
from config import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response Schemas ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with username and password.

    On success:
    - Returns access_token in response body (stored in memory by frontend)
    - Sets refresh_token as HttpOnly cookie (persists across refresh)
    """
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.role.value)

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api",
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role.value,
        ),
    )


@router.post("/logout")
async def logout(response: Response):
    """Log out: clear the refresh token cookie."""
    response.delete_cookie(key="refresh_token", path="/api")
    return {"message": "已登出"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return current user info from valid token or cookie."""
    return current_user
