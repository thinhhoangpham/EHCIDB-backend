from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from api.dependencies import get_db
from ..models import Patient, AppUser, DoctorPatientAssignment
from ..dependencies import require_role

router = APIRouter(prefix="/admission", tags=["admission"])
@router.post("/assign")
def assign_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("Doctor")),
):

    assignment = DoctorPatientAssignment(
        doctor_id=current_user.doctor_id,
        patient_id=patient_id
        # date_of_admission auto-handled by DB
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "message": "Patient assigned successfully",
        "assigned_at": assignment.date_of_admission
    }

# @router.get("/admission/assigned")
# def get_assigned_patients(
#     user: AppUser = Depends(require_role("Doctor")),
#     db: Session = Depends(get_db),
# ):

#     assignments = (
#         db.query(DoctorPatientAssignment)
#         .options(joinedload(DoctorPatientAssignment.patient))
#         .filter(DoctorPatientAssignment.doctor_id == user.doctor_id)
#         .order_by(DoctorPatientAssignment.date_of_admission.desc())
#         .all()
#     )

#     return [
#         {
#             "assignment_id": a.id,
#             "doctor_id": a.doctor_id,
#             "patient_id": a.patient_id,
#             "patient_name": a.patient.patient_name,
#             "emergency_identifier": a.patient.emergency_identifier,
#             "blood_type": a.patient.blood_type_code,
#             "date_of_admission": a.date_of_admission,
#         }
#         for a in assignments
#     ]