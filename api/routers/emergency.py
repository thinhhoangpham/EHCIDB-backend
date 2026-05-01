from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from api.dependencies import get_db, require_role
from api.models import (
    AccessLog,
    Allergy,
    AppUser,
    Device,
    EmergencyContact,
    InsuranceProviderDetail,
    MedicalCondition,
    Patient,
    PatientInsurance,
    PatientMedication,
    Role,
    UserRole,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AllergyIn(BaseModel):
    allergy_name: str
    severity: Literal["Mild", "Moderate", "Severe"]


class AllergyOut(BaseModel):
    allergy_id: int
    allergy_name: str
    severity: str

    model_config = {"from_attributes": True}


class ConditionIn(BaseModel):
    condition_name: str
    critical_flag: bool = False


class ConditionOut(BaseModel):
    condition_id: int
    condition_name: str
    critical_flag: bool

    model_config = {"from_attributes": True}


class MedicationIn(BaseModel):
    medication_name: str
    dosage: str | None = None


class MedicationOut(BaseModel):
    medication_id: int
    medication_name: str
    dosage: str | None

    model_config = {"from_attributes": True}


class DeviceIn(BaseModel):
    device_name: str
    device_type: str | None = None


class DeviceOut(BaseModel):
    device_id: int
    device_name: str
    device_type: str | None

    model_config = {"from_attributes": True}


class ContactIn(BaseModel):
    contact_name: str
    relationship: str | None = None
    phone_number: str | None = None


class ContactOut(BaseModel):
    contact_id: int
    contact_name: str
    relationship: str | None
    phone_number: str | None

    model_config = {"from_attributes": True}


class InsuranceOut(BaseModel):
    provider_name: str
    plan_type: str | None
    member_id: str | None
    coverage_status: str


class EmergencyProfileOut(BaseModel):
    emergency_identifier: str | None
    patient_name: str
    gender: str
    blood_type: str
    allergies: list[AllergyOut]
    conditions: list[ConditionOut]
    medications: list[MedicationOut]
    devices: list[DeviceOut]
    emergency_contacts: list[ContactOut]
    insurance: InsuranceOut | None


class PatientSearchResult(BaseModel):
    patient_id: int
    emergency_identifier: str | None
    patient_name: str
    blood_type: str


class UserAdminOut(BaseModel):
    user_id: int
    username: str
    full_name: str
    email: str | None
    role: str
    is_active: bool


class UserListOut(BaseModel):
    users: list[UserAdminOut]
    total: int


class UserPatchIn(BaseModel):
    is_active: bool | None = None
    role: str | None = None


class AccessLogOut(BaseModel):
    log_id: int
    user_name: str
    action: str
    target_patient_name: str | None
    created_at: str


class AccessLogListOut(BaseModel):
    logs: list[AccessLogOut]
    total: int


class InsuranceProviderIn(BaseModel):
    provider_name: str
    payer_phone: str | None = None


class InsuranceProviderOut(BaseModel):
    provider_id: int
    provider_name: str
    payer_phone: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_emergency_profile(patient: Patient) -> EmergencyProfileOut:
    """Build the emergency profile dict from a loaded Patient ORM object."""
    first_insurance: InsuranceOut | None = None
    if patient.insurances:
        pi = patient.insurances[0]
        first_insurance = InsuranceOut(
            provider_name=pi.provider.provider_name,
            plan_type=pi.plan_type,
            member_id=pi.member_id,
            coverage_status=pi.coverage_status,
        )

    return EmergencyProfileOut(
        emergency_identifier=patient.emergency_identifier,
        patient_name=patient.patient_name,
        gender=patient.gender,
        blood_type=patient.blood_type_code,
        allergies=[AllergyOut.model_validate(a) for a in patient.allergies],
        conditions=[ConditionOut.model_validate(c) for c in patient.conditions],
        medications=[MedicationOut.model_validate(m) for m in patient.medications],
        devices=[DeviceOut.model_validate(d) for d in patient.devices],
        emergency_contacts=[ContactOut.model_validate(ec) for ec in patient.emergency_contacts],
        insurance=first_insurance,
    )


def _load_patient_full(patient_id: int, db: Session) -> Patient:
    """Load a patient with all emergency relationships eager-loaded."""
    from sqlalchemy.orm import joinedload

    patient = (
        db.query(Patient)
        .options(
            joinedload(Patient.allergies),
            joinedload(Patient.conditions),
            joinedload(Patient.medications),
            joinedload(Patient.devices),
            joinedload(Patient.emergency_contacts),
            joinedload(Patient.insurances).joinedload(PatientInsurance.provider),
        )
        .filter(Patient.patient_id == patient_id)
        .first()
    )
    return patient


def _log_access(db: Session, user_id: int, action: str, target_patient_id: int | None = None) -> None:
    entry = AccessLog(user_id=user_id, action=action, target_patient_id=target_patient_id)
    db.add(entry)
    db.commit()


# ---------------------------------------------------------------------------
# Patient endpoints
# ---------------------------------------------------------------------------

@router.get("/emergency/patient/profile", response_model=EmergencyProfileOut)
def get_patient_profile(
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> EmergencyProfileOut:
    if user.patient_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not linked to a patient record",
        )

    patient = _load_patient_full(user.patient_id, db)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found")

    return _get_emergency_profile(patient)


@router.post("/emergency/patient/allergies", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def add_allergy(
    body: AllergyIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> AllergyOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    allergy = Allergy(patient_id=user.patient_id, allergy_name=body.allergy_name, severity=body.severity)
    db.add(allergy)
    db.commit()
    db.refresh(allergy)
    return AllergyOut.model_validate(allergy)


@router.delete("/emergency/patient/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allergy(
    allergy_id: int,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> None:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    allergy = db.query(Allergy).filter(Allergy.allergy_id == allergy_id).first()
    if allergy is None or allergy.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")

    db.delete(allergy)
    db.commit()


@router.post("/emergency/patient/conditions", response_model=ConditionOut, status_code=status.HTTP_201_CREATED)
def add_condition(
    body: ConditionIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> ConditionOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    condition = MedicalCondition(
        patient_id=user.patient_id,
        condition_name=body.condition_name,
        critical_flag=body.critical_flag,
    )
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return ConditionOut.model_validate(condition)


@router.delete("/emergency/patient/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition(
    condition_id: int,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> None:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    condition = db.query(MedicalCondition).filter(MedicalCondition.condition_id == condition_id).first()
    if condition is None or condition.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")

    db.delete(condition)
    db.commit()


@router.post("/emergency/patient/medications", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
def add_medication(
    body: MedicationIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> MedicationOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    medication = PatientMedication(
        patient_id=user.patient_id,
        medication_name=body.medication_name,
        dosage=body.dosage,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return MedicationOut.model_validate(medication)


@router.delete("/emergency/patient/medications/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> None:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    medication = db.query(PatientMedication).filter(PatientMedication.medication_id == medication_id).first()
    if medication is None or medication.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    db.delete(medication)
    db.commit()


@router.post("/emergency/patient/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def add_device(
    body: DeviceIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> DeviceOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    device = Device(patient_id=user.patient_id, device_name=body.device_name, device_type=body.device_type)
    db.add(device)
    db.commit()
    db.refresh(device)
    return DeviceOut.model_validate(device)


@router.delete("/emergency/patient/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> None:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device is None or device.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.delete(device)
    db.commit()


@router.post("/emergency/patient/emergency-contacts", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def add_emergency_contact(
    body: ContactIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> ContactOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    contact = EmergencyContact(
        patient_id=user.patient_id,
        contact_name=body.contact_name,
        relationship=body.relationship,
        phone_number=body.phone_number,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.put("/emergency/patient/emergency-contacts/{contact_id}", response_model=ContactOut)
def update_emergency_contact(
    contact_id: int,
    body: ContactIn,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> ContactOut:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    contact = db.query(EmergencyContact).filter(EmergencyContact.contact_id == contact_id).first()
    if contact is None or contact.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact.contact_name = body.contact_name
    contact.relationship = body.relationship
    contact.phone_number = body.phone_number
    db.commit()
    db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.delete("/emergency/patient/emergency-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(
    contact_id: int,
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> None:
    if user.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not linked to a patient record")

    contact = db.query(EmergencyContact).filter(EmergencyContact.contact_id == contact_id).first()
    if contact is None or contact.patient_id != user.patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    db.delete(contact)
    db.commit()


# ---------------------------------------------------------------------------
# Doctor endpoints
# ---------------------------------------------------------------------------

@router.get("/emergency/doctor/search", response_model=list[PatientSearchResult])
def doctor_search(
    q: str = Query(..., min_length=1),
    user: AppUser = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
) -> list[PatientSearchResult]:
    patients = (
        db.query(Patient)
        .filter(
            (Patient.emergency_identifier == q) | (Patient.patient_name.ilike(f"%{q}%"))
        )
        .limit(20)
        .all()
    )

    _log_access(db, user.user_id, f"Searched patients: {q}")

    return [
        PatientSearchResult(
            patient_id=p.patient_id,
            emergency_identifier=p.emergency_identifier,
            patient_name=p.patient_name,
            blood_type=p.blood_type_code,
        )
        for p in patients
    ]


@router.get("/emergency/doctor/patient/{emergency_id}", response_model=EmergencyProfileOut)
def doctor_get_patient(
    emergency_id: str,
    user: AppUser = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
) -> EmergencyProfileOut:
    patient_stub = (
        db.query(Patient)
        .filter(Patient.emergency_identifier == emergency_id)
        .first()
    )
    if patient_stub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient = _load_patient_full(patient_stub.patient_id, db)

    _log_access(db, user.user_id, f"Viewed patient {emergency_id}", target_patient_id=patient.patient_id)

    return _get_emergency_profile(patient)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@router.get("/emergency/admin/users", response_model=UserListOut)
def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    q: str | None = Query(None, description="Search users by name, username, or email"),
    user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> UserListOut:
    from sqlalchemy.orm import joinedload

    offset = (page - 1) * limit

    query = db.query(AppUser)

    if q and q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                AppUser.full_name.ilike(search),
                AppUser.username.ilike(search),
                AppUser.email.ilike(search),
            )
        )

    total = query.count()

    users = (
        query
        .options(joinedload(AppUser.user_roles).joinedload(UserRole.role))
        .order_by(AppUser.full_name.asc(), AppUser.user_id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for u in users:
        role_name = u.user_roles[0].role.role_name if u.user_roles else "Unknown"
        result.append(
            UserAdminOut(
                user_id=u.user_id,
                username=u.username,
                full_name=u.full_name,
                email=u.email,
                role=role_name,
                is_active=u.is_active,
            )
        )

    return UserListOut(users=result, total=total)


@router.patch("/emergency/admin/users/{user_id}", response_model=UserAdminOut)
def admin_patch_user(
    user_id: int,
    body: UserPatchIn,
    current_user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> UserAdminOut:
    from sqlalchemy.orm import joinedload

    target = (
        db.query(AppUser)
        .options(joinedload(AppUser.user_roles).joinedload(UserRole.role))
        .filter(AppUser.user_id == user_id)
        .first()
    )
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.is_active is not None:
        target.is_active = body.is_active

    if body.role is not None:
        new_role = db.query(Role).filter(Role.role_name == body.role).first()
        if new_role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{body.role}' does not exist")

        # Remove existing roles then assign the new one
        for ur in target.user_roles:
            db.delete(ur)
        db.flush()

        db.add(UserRole(user_id=target.user_id, role_id=new_role.role_id))

    db.commit()
    db.refresh(target)

    # Reload relationships after commit
    target = (
        db.query(AppUser)
        .options(joinedload(AppUser.user_roles).joinedload(UserRole.role))
        .filter(AppUser.user_id == user_id)
        .first()
    )

    role_name = target.user_roles[0].role.role_name if target.user_roles else "Unknown"
    return UserAdminOut(
        user_id=target.user_id,
        username=target.username,
        full_name=target.full_name,
        email=target.email,
        role=role_name,
        is_active=target.is_active,
    )


@router.get("/emergency/admin/access-logs", response_model=AccessLogListOut)
def admin_access_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> AccessLogListOut:
    from sqlalchemy.orm import joinedload

    offset = (page - 1) * limit

    total = db.query(AccessLog).count()

    logs = (
        db.query(AccessLog)
        .options(
            joinedload(AccessLog.user),
            joinedload(AccessLog.target_patient),
        )
        .order_by(AccessLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = [
        AccessLogOut(
            log_id=log.log_id,
            user_name=log.user.full_name,
            action=log.action,
            target_patient_name=log.target_patient.patient_name if log.target_patient else None,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]

    return AccessLogListOut(logs=result, total=total)


@router.get("/emergency/admin/insurance-providers", response_model=list[InsuranceProviderOut])
def list_insurance_providers(
    current_user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> list[InsuranceProviderOut]:
    providers = db.query(InsuranceProviderDetail).order_by(InsuranceProviderDetail.provider_name).all()
    return [InsuranceProviderOut.model_validate(p) for p in providers]


@router.post("/emergency/admin/insurance-providers", response_model=InsuranceProviderOut, status_code=status.HTTP_201_CREATED)
def add_insurance_provider(
    body: InsuranceProviderIn,
    current_user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> InsuranceProviderOut:
    existing = (
        db.query(InsuranceProviderDetail)
        .filter(InsuranceProviderDetail.provider_name == body.provider_name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider '{body.provider_name}' already exists",
        )

    provider = InsuranceProviderDetail(provider_name=body.provider_name, payer_phone=body.payer_phone)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return InsuranceProviderOut.model_validate(provider)


@router.delete("/emergency/admin/insurance-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insurance_provider(
    provider_id: int,
    current_user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> None:
    provider = db.query(InsuranceProviderDetail).filter(InsuranceProviderDetail.provider_id == provider_id).first()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    db.delete(provider)
    db.commit()



#added create doctor route for admin to create doctor account
# backend/api/routers/emergency.py

@router.post("/admin/create-doctor")
def admin_create_doctor(payload: dict, user=Depends(require_role("Admin"))):

    return create_doctor(
        username=payload["username"],
        email=payload["email"],
        password=payload["password"],
        full_name=payload["full_name"],
        doctor_name=payload["doctor_name"]
    )