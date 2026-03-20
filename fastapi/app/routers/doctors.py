from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import models, database
from app.schemas.doctor import PatientEmergencyData
from app.core.security import get_current_user

router = APIRouter(prefix="/patients/emergency", tags=["doctor"])

@router.get("/{emergency_id}", response_model=PatientEmergencyData)
def get_patient_by_emergency_id(emergency_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Forbidden")
    profile = db.query(models.PatientProfile).filter(models.PatientProfile.emergency_id == emergency_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientEmergencyData(
        emergency_id=profile.emergency_id,
        name=profile.user.name,
        blood_type=profile.blood_type,
        allergies=profile.allergies,
        conditions=profile.conditions,
        medications=profile.medications,
        devices=profile.devices,
        emergency_contacts=profile.contacts,
        insurance=profile.insurance
    )