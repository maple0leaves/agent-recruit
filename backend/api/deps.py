"""FastAPI dependency injection for authentication and authorization."""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.jwt import decode_token
from backend.db.engine import get_session

# Bearer token scheme (from Authorization header)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Yield an async database session."""
    async for session in get_session():
        yield session


async def get_current_user(
    credentials=Depends(bearer_scheme),
    request: Request = None,
    _db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the current user from JWT.

    Priority:
    1. Authorization: Bearer header (standard API calls)
    2. access_token cookie (SSE endpoints that can't set headers)

    Returns payload dict with "sub" (user_id) and "role".
    Raises 401 if no valid token found.
    """
    token = None

    # Try Authorization header first
    if credentials:
        token = credentials.credentials

    # Fallback: read from cookie (for SSE / EventSource)
    if not token and request:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
        )

    try:
        payload = decode_token(token)
        return {"sub": payload.get("sub"), "role": payload.get("role")}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        )


def require_role(required_role: str):
    """Dependency factory: require a specific role to access the endpoint.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user=Depends(require_role("admin"))):
            ...
    """
    async def _role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_user
    return _role_checker
