from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import models, database
from app.schemas import patient as schemas
from app.core.security import get_current_user

router = APIRouter(prefix="/patients/me", tags=["patients"])


# ---------- DB ----------
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- HELPER ----------
def get_profile(db: Session, current_user: models.User):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Forbidden")

    profile = db.query(models.PatientProfile).filter(
        models.PatientProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


# ---------- PROFILE ----------
@router.get("/", response_model=schemas.PatientProfile)
def get_profile_data(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user)


@router.put("/", response_model=schemas.PatientProfile)
def update_profile(data: schemas.PatientProfileUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)

    for key, value in data.dict(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


# ---------- GENERIC CRUD ----------
def create_item(model, data, profile_id):
    return model(patient_id=profile_id, **data.dict())


def update_item(item, data):
    for key, value in data.dict().items():
        setattr(item, key, value)


def get_item(db, model, item_id, profile_id):
    item = db.query(model).filter(
        model.id == item_id,
        model.patient_id == profile_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    return item


# ---------- ALLERGIES ----------
@router.get("/allergies/", response_model=List[schemas.Allergy])
def get_allergies(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).allergies


@router.post("/allergies/", response_model=schemas.Allergy)
def create_allergy(data: schemas.AllergyCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = create_item(models.Allergy, data, profile.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/allergies/{id}", response_model=schemas.Allergy)
def update_allergy(id: int, data: schemas.AllergyCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Allergy, id, profile.id)
    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/allergies/{id}")
def delete_allergy(id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Allergy, id, profile.id)
    db.delete(item); db.commit()
    return {"detail": "Deleted"}


# ---------- CONDITIONS ----------
@router.get("/conditions/", response_model=List[schemas.Condition])
def get_conditions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).conditions


@router.post("/conditions/", response_model=schemas.Condition)
def create_condition(data: schemas.ConditionCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = create_item(models.Condition, data, profile.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/conditions/{id}", response_model=schemas.Condition)
def update_condition(id: int, data: schemas.ConditionCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Condition, id, profile.id)
    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/conditions/{id}")
def delete_condition(id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Condition, id, profile.id)
    db.delete(item); db.commit()
    return {"detail": "Deleted"}


# ---------- MEDICATIONS ----------
@router.get("/medications/", response_model=List[schemas.Medication])
def get_medications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).medications


@router.post("/medications/", response_model=schemas.Medication)
def create_medication(data: schemas.MedicationCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = create_item(models.Medication, data, profile.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/medications/{id}", response_model=schemas.Medication)
def update_medication(id: int, data: schemas.MedicationCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Medication, id, profile.id)
    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/medications/{id}")
def delete_medication(id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Medication, id, profile.id)
    db.delete(item); db.commit()
    return {"detail": "Deleted"}


# ---------- DEVICES ----------
@router.get("/devices/", response_model=List[schemas.Device])
def get_devices(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).devices


@router.post("/devices/", response_model=schemas.Device)
def create_device(data: schemas.DeviceCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = create_item(models.Device, data, profile.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/devices/{id}", response_model=schemas.Device)
def update_device(id: int, data: schemas.DeviceCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Device, id, profile.id)
    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/devices/{id}")
def delete_device(id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.Device, id, profile.id)
    db.delete(item); db.commit()
    return {"detail": "Deleted"}


# ---------- CONTACTS ----------
@router.get("/contacts/", response_model=List[schemas.EmergencyContact])
def get_contacts(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).contacts


@router.post("/contacts/", response_model=schemas.EmergencyContact)
def create_contact(data: schemas.EmergencyContactCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = create_item(models.EmergencyContact, data, profile.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/contacts/{id}", response_model=schemas.EmergencyContact)
def update_contact(id: int, data: schemas.EmergencyContactCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.EmergencyContact, id, profile.id)
    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/contacts/{id}")
def delete_contact(id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)
    item = get_item(db, models.EmergencyContact, id, profile.id)
    db.delete(item); db.commit()
    return {"detail": "Deleted"}


# ---------- INSURANCE (ONE RECORD) ----------
@router.get("/insurance/", response_model=schemas.InsuranceInfo)
def get_insurance(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_profile(db, current_user).insurance


@router.post("/insurance/", response_model=schemas.InsuranceInfo)
def create_insurance(data: schemas.InsuranceInfoCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)

    item = models.InsuranceInfo(patient_id=profile.id, **data.dict())

    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/insurance/", response_model=schemas.InsuranceInfo)
def update_insurance(data: schemas.InsuranceInfoCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)

    item = profile.insurance
    if not item:
        raise HTTPException(status_code=404, detail="Insurance not found")

    update_item(item, data)
    db.commit(); db.refresh(item)
    return item


@router.delete("/insurance/")
def delete_insurance(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_profile(db, current_user)

    item = profile.insurance
    if not item:
        raise HTTPException(status_code=404, detail="Insurance not found")

    db.delete(item); db.commit()
    return {"detail": "Deleted"}