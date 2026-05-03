from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date
from api.dependencies import get_db
from api.models import AppUser, Role, UserRole, Patient, DimBloodType
from api.schemas import LoginRequest, AuthResponse, UserCreate, UserSchema
from api.auth import verify_password, hash_password, create_access_token, create_refresh_token

router = APIRouter()

# Maps DB role_name -> frontend UserRole string. Viewer is not a supported
# frontend role, so it is intentionally absent — users with only a Viewer
# role will receive a 403 on login.
_ROLE_MAP: dict[str, str] = {
    "Admin": "admin",
    "Doctor": "doctor",
    "Patient": "patient",
}




@router.post("/auth/register/", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(AppUser)
        .filter((AppUser.email == body.email) | (AppUser.username == body.email))
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    patient_role = db.query(Role).filter(Role.role_name == "Patient").first()
    if patient_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient role not found. Run the security seed SQL first.",
        )

    new_patient = Patient(
        patient_name=body.full_name,
        email=body.email,
        gender=body.gender,
        blood_type_code=body.blood_type_code,
        date_of_birth=body.date_of_birth,
    )
    db.add(new_patient)
    db.flush()

    # Auto-generate a non-enumerable emergency_identifier
    from api.routers.emergency import _new_emergency_identifier
    new_patient.emergency_identifier = _new_emergency_identifier()


    new_user = AppUser(
        username=body.email,
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        is_active=True,
        patient_id=new_patient.patient_id,
    )
    db.add(new_user)
    db.flush()

    db.add(UserRole(user_id=new_user.user_id, role_id=patient_role.role_id))
    db.commit()
    db.refresh(new_user)

    token_data = {"sub": str(new_user.user_id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserSchema(
            id=str(new_user.user_id),
            name=new_user.full_name,
            email=new_user.email or "",
            role="patient",
            is_active=new_user.is_active,
            patient_id=new_user.patient_id,
            doctor_id=new_user.doctor_id,
        ),
    )


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
