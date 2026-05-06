"""Authentication API routes: login, logout, session check."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.auth.password import hash_password, verify_password
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


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("新密码长度不能少于 6 位")
        return v


@router.patch("/password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    result = await db.execute(select(User).where(User.id == int(current_user["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于 6 位")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"message": "密码修改成功"}
