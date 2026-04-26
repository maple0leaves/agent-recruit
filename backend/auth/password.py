"""Password hashing and verification using bcrypt (not passlib).

Per RESEARCH.md: passlib 1.7.4 is incompatible with bcrypt 5.0.0.
Using bcrypt directly per verified runtime compatibility.
"""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Returns the encoded hash string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash. Returns bool."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
