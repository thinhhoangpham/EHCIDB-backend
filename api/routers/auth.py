from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from api.dependencies import get_db
from api.models import AppUser, UserRole
from api.schemas import LoginRequest, AuthResponse, UserSchema
from api.auth import verify_password, create_access_token, create_refresh_token

router = APIRouter()

# Maps DB role_name -> frontend UserRole string. Viewer is not a supported
# frontend role, so it is intentionally absent — users with only a Viewer
# role will receive a 403 on login.
_ROLE_MAP: dict[str, str] = {
    "Admin": "admin",
    "Doctor": "doctor",
    "Patient": "patient",
}


@router.post("/auth/login/", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(AppUser)
        .filter(AppUser.email == body.email, AppUser.is_active == True)  # noqa: E712
        .options(joinedload(AppUser.user_roles).joinedload(UserRole.role))
        .first()
    )

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Resolve the first supported frontend role for this user
    frontend_role: str | None = None
    for ur in user.user_roles:
        mapped = _ROLE_MAP.get(ur.role.role_name)
        if mapped:
            frontend_role = mapped
            break

    if frontend_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not supported by this application",
        )

    token_data = {"sub": str(user.user_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_schema = UserSchema(
        id=str(user.user_id),
        name=user.full_name,
        email=user.email or "",
        role=frontend_role,  # type: ignore[arg-type]
        is_active=user.is_active,
        patient_id=user.patient_id,
        doctor_id=user.doctor_id,
    )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_schema,
    )


@router.post("/auth/logout/", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # JWT is stateless — the client simply discards its tokens
    return None
