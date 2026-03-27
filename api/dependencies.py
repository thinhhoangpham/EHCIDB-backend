from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from jose import JWTError
from api.database import SessionLocal
from api.auth import decode_token
from api.models import AppUser, UserRole

bearer_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AppUser:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = (
        db.query(AppUser)
        .options(joinedload(AppUser.user_roles).joinedload(UserRole.role))
        .filter(AppUser.user_id == user_id)
        .first()
    )
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(role_name: str) -> Callable:
    """Return a FastAPI dependency that enforces the user has the given role."""
    def dependency(user: AppUser = Depends(get_current_user)) -> AppUser:
        for ur in user.user_roles:
            if ur.role.role_name == role_name:
                return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires {role_name} role",
        )
    return dependency
