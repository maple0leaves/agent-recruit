"""CLI script to create initial admin user.

Usage:
    ADMIN_PASSWORD=<password> python -m backend.db.seed
    python -m backend.db.seed <password>
"""
import asyncio
import os
import sys
from sqlalchemy import select
from backend.db.engine import engine, async_session
from backend.db.models.user import User, UserRole
from backend.auth.password import hash_password


async def seed(username: str, password: str, role: UserRole = UserRole.ADMIN):
    """Create a user if not exists. Creates tables first if needed."""
    from backend.db.engine import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            print(f"用户 '{username}' 已存在，跳过创建。")
            return

        user = User(
            username=username,
            hashed_password=hash_password(password),
            role=role,
        )
        session.add(user)
        await session.commit()
        print(f"管理员用户 '{username}' 创建成功。")


if __name__ == "__main__":
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD") or (
        sys.argv[1] if len(sys.argv) > 1 else None
    )
    if not password:
        print("用法: ADMIN_PASSWORD=<密码> python -m backend.db.seed")
        print("   或: python -m backend.db.seed <密码>")
        sys.exit(1)
    asyncio.run(seed(username, password))
