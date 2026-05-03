from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.dependencies import get_db, require_role
from api.models import AppUser

router = APIRouter()


def _fmt_float(value: Any) -> float:
    """Convert Decimal or None to a rounded float."""
    if value is None:
        return 0.0
    return round(float(value), 2)


def _fmt_date(value: Any) -> str:
    """Convert a date object or None to ISO string."""
    if value is None:
        return ""
    return value.isoformat()


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard/admin")
def admin_dashboard(
    user: AppUser = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
) -> dict:
    # --- stats ---
    stats_row = db.execute(text("""
        SELECT
            COUNT(DISTINCT a.patient_id)                                   AS total_patients,
            COUNT(*)                                                        AS total_admissions,
            COUNT(DISTINCT a.doctor_id)                                     AS total_doctors,
            AVG(a.billing_amount)                                           AS avg_billing,
            AVG(DATEDIFF(a.discharge_date, a.date_of_admission))            AS avg_length_of_stay
        FROM admission a
    """)).fetchone()

    stats = {
        "total_patients": stats_row.total_patients or 0,
        "total_admissions": stats_row.total_admissions or 0,
        "total_doctors": stats_row.total_doctors or 0,
        "avg_billing": _fmt_float(stats_row.avg_billing),
        "avg_length_of_stay": _fmt_float(stats_row.avg_length_of_stay),
    }

    # --- admissions over time ---
    time_rows = db.execute(text("""
        SELECT DATE_FORMAT(date_of_admission, '%Y-%m') AS month, COUNT(*) AS cnt
        FROM admission
        GROUP BY month
        ORDER BY month
    """)).fetchall()
    admissions_over_time = [{"month": r.month, "count": r.cnt} for r in time_rows]

    # --- admissions by type ---
    type_rows = db.execute(text("""
        SELECT admission_type AS type, COUNT(*) AS cnt
        FROM admission
        GROUP BY admission_type
        ORDER BY cnt DESC
    """)).fetchall()
    admissions_by_type = [{"type": r.type, "count": r.cnt} for r in type_rows]

    # --- top 10 conditions ---
    cond_rows = db.execute(text("""
        SELECT medical_condition AS condition_name, COUNT(*) AS cnt
        FROM admission
        GROUP BY medical_condition
        ORDER BY cnt DESC
        LIMIT 10
    """)).fetchall()
    top_conditions = [{"condition": r.condition_name, "count": r.cnt} for r in cond_rows]

    # --- billing by insurance provider ---
    ins_rows = db.execute(text("""
        SELECT insurance_provider AS provider, SUM(billing_amount) AS total
        FROM admission
        GROUP BY insurance_provider
        ORDER BY total DESC
    """)).fetchall()
    billing_by_insurance = [
        {"provider": r.provider, "total": _fmt_float(r.total)} for r in ins_rows
    ]

    # --- demographics ---
    gender_rows = db.execute(text("""
        SELECT p.gender, COUNT(DISTINCT p.patient_id) AS cnt
        FROM patient p
        GROUP BY p.gender
        ORDER BY cnt DESC
    """)).fetchall()
    gender = [{"gender": r.gender, "count": r.cnt} for r in gender_rows]

    age_rows = db.execute(text("""
        SELECT
            CASE
                WHEN age_at_admission <= 17 THEN '0-17'
                WHEN age_at_admission <= 30 THEN '18-30'
                WHEN age_at_admission <= 45 THEN '31-45'
                WHEN age_at_admission <= 60 THEN '46-60'
                WHEN age_at_admission <= 75 THEN '61-75'
                ELSE '76+'
            END AS age_group,
            COUNT(*) AS cnt
        FROM admission
        GROUP BY age_group
        ORDER BY FIELD(age_group, '0-17', '18-30', '31-45', '46-60', '61-75', '76+')
    """)).fetchall()
    age_groups = [{"group": r.age_group, "count": r.cnt} for r in age_rows]

    demographics = {"gender": gender, "age_groups": age_groups}

    # --- test results ---
    test_rows = db.execute(text("""
        SELECT test_result AS result, COUNT(*) AS cnt
        FROM admission
        GROUP BY test_result
        ORDER BY cnt DESC
    """)).fetchall()
    test_results = [{"result": r.result, "count": r.cnt} for r in test_rows]

    # --- top 10 medications ---
    med_rows = db.execute(text("""
        SELECT medication, COUNT(*) AS cnt
        FROM admission
        GROUP BY medication
        ORDER BY cnt DESC
        LIMIT 10
    """)).fetchall()
    medication_usage = [{"medication": r.medication, "count": r.cnt} for r in med_rows]

    # --- last 20 admissions ---
    recent_rows = db.execute(text("""
        SELECT
            a.admission_id,
            p.patient_name,
            d.doctor_name,
            h.hospital_name,
            a.medical_condition,
            a.admission_type,
            a.date_of_admission,
            a.discharge_date,
            a.billing_amount
        FROM admission a
        JOIN patient  p ON p.patient_id  = a.patient_id
        JOIN doctor   d ON d.doctor_id   = a.doctor_id
        JOIN hospital h ON h.hospital_id = a.hospital_id
        ORDER BY a.date_of_admission DESC, a.admission_id DESC
        LIMIT 20
    """)).fetchall()
    recent_admissions = [
        {
            "admission_id":     r.admission_id,
            "patient_name":     r.patient_name,
            "doctor_name":      r.doctor_name,
            "hospital_name":    r.hospital_name,
            "medical_condition": r.medical_condition,
            "admission_type":   r.admission_type,
            "date_of_admission": _fmt_date(r.date_of_admission),
            "discharge_date":   _fmt_date(r.discharge_date),
            "billing_amount":   _fmt_float(r.billing_amount),
        }
        for r in recent_rows
    ]

    return {
        "stats":                stats,
        "admissions_over_time": admissions_over_time,
        "admissions_by_type":   admissions_by_type,
        "top_conditions":       top_conditions,
        "billing_by_insurance": billing_by_insurance,
        "demographics":         demographics,
        "test_results":         test_results,
        "medication_usage":     medication_usage,
        "recent_admissions":    recent_admissions,
    }


# ---------------------------------------------------------------------------
# Doctor dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard/doctor")
def doctor_dashboard(
    user: AppUser = Depends(require_role("Doctor")),
    db: Session = Depends(get_db),
) -> dict:
    if user.doctor_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not linked to a doctor record",
        )

    doctor_id = user.doctor_id

    # --- stats ---
    stats_row = db.execute(text("""
        SELECT
            (SELECT COUNT(DISTINCT patient_id)
             FROM (
                 SELECT patient_id FROM doctor_patient_access WHERE doctor_id = :doctor_id
                 UNION
                 SELECT patient_id FROM doctor_patient_assignment WHERE doctor_id = :doctor_id
             ) AS combined_patients)                                         AS my_patients,
            COUNT(*)                                                         AS total_admissions,
            AVG(billing_amount)                                              AS avg_billing,
            AVG(DATEDIFF(discharge_date, date_of_admission))                 AS avg_length_of_stay
        FROM admission
        WHERE doctor_id = :doctor_id
    """), {"doctor_id": doctor_id}).fetchone()

    stats = {
        "my_patients":        stats_row.my_patients or 0,
        "total_admissions":   stats_row.total_admissions or 0,
        "avg_billing":        _fmt_float(stats_row.avg_billing),
        "avg_length_of_stay": _fmt_float(stats_row.avg_length_of_stay),
    }

    # --- patients accessible to this doctor ---
    patient_rows = db.execute(text("""
        SELECT p.patient_id, p.patient_name, p.gender, p.blood_type_code AS blood_type
        FROM (
            SELECT patient_id FROM doctor_patient_access WHERE doctor_id = :doctor_id
            UNION
            SELECT patient_id FROM doctor_patient_assignment WHERE doctor_id = :doctor_id
        ) dpa
        JOIN patient p ON p.patient_id = dpa.patient_id
        ORDER BY p.patient_name
    """), {"doctor_id": doctor_id}).fetchall()
    patients = [
        {
            "patient_id":   r.patient_id,
            "patient_name": r.patient_name,
            "gender":       r.gender,
            "blood_type":   r.blood_type,
        }
        for r in patient_rows
    ]

    # --- admissions over time ---
    time_rows = db.execute(text("""
        SELECT DATE_FORMAT(date_of_admission, '%Y-%m') AS month, COUNT(*) AS cnt
        FROM admission
        WHERE doctor_id = :doctor_id
        GROUP BY month
        ORDER BY month
    """), {"doctor_id": doctor_id}).fetchall()
    admissions_over_time = [{"month": r.month, "count": r.cnt} for r in time_rows]

    # --- conditions breakdown ---
    cond_rows = db.execute(text("""
        SELECT medical_condition AS condition_name, COUNT(*) AS cnt
        FROM admission
        WHERE doctor_id = :doctor_id
        GROUP BY medical_condition
        ORDER BY cnt DESC
    """), {"doctor_id": doctor_id}).fetchall()
    conditions_breakdown = [{"condition": r.condition_name, "count": r.cnt} for r in cond_rows]

    # --- test results ---
    test_rows = db.execute(text("""
        SELECT test_result AS result, COUNT(*) AS cnt
        FROM admission
        WHERE doctor_id = :doctor_id
        GROUP BY test_result
        ORDER BY cnt DESC
    """), {"doctor_id": doctor_id}).fetchall()
    test_results = [{"result": r.result, "count": r.cnt} for r in test_rows]

    # --- last 20 admissions for this doctor ---
    recent_rows = db.execute(text("""
        SELECT
            dpa.id AS admission_id,
            p.patient_name,
            'Not Specified' AS hospital_name,
            'Pending' AS medical_condition,
            'Emergency' AS admission_type,
            'Pending' AS medication,
            'Pending' AS test_result,
            DATE(dpa.date_of_admission) AS date_of_admission,
            NULL AS discharge_date,
            0.0 AS billing_amount
        FROM doctor_patient_assignment dpa
        JOIN patient p ON p.patient_id = dpa.patient_id
        WHERE dpa.doctor_id = :doctor_id

        UNION ALL

        SELECT
            a.admission_id,
            p.patient_name,
            h.hospital_name,
            a.medical_condition,
            a.admission_type,
            a.medication,
            a.test_result,
            a.date_of_admission,
            a.discharge_date,
            a.billing_amount
        FROM admission a
        JOIN patient p ON p.patient_id = a.patient_id
        JOIN hospital h ON h.hospital_id = a.hospital_id
        WHERE a.doctor_id = :doctor_id
        
        ORDER BY date_of_admission DESC, admission_id DESC
        LIMIT 20
    """), {"doctor_id": doctor_id}).fetchall()
    recent_admissions = [
        {
            "admission_id":      r.admission_id,
            "patient_name":      r.patient_name,
            "hospital_name":     r.hospital_name,
            "medical_condition": r.medical_condition,
            "admission_type":    r.admission_type,
            "medication":        r.medication,
            "test_result":       r.test_result,
            "date_of_admission": _fmt_date(r.date_of_admission),
            "discharge_date":    _fmt_date(r.discharge_date),
            "billing_amount":    _fmt_float(r.billing_amount),
        }
        for r in recent_rows
    ]

    return {
        "stats":               stats,
        "patients":            patients,
        "admissions_over_time": admissions_over_time,
        "conditions_breakdown": conditions_breakdown,
        "test_results":        test_results,
        "recent_admissions":   recent_admissions,
    }


# ---------------------------------------------------------------------------
# Patient dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard/patient")
def patient_dashboard(
    user: AppUser = Depends(require_role("Patient")),
    db: Session = Depends(get_db),
) -> dict:
    if user.patient_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not linked to a patient record",
        )

    patient_id = user.patient_id

    # --- profile ---
    profile_row = db.execute(text("""
        SELECT
            p.patient_name,
            p.gender,
            p.blood_type_code AS blood_type,
            COUNT(a.admission_id) AS total_admissions
        FROM patient p
        LEFT JOIN admission a ON a.patient_id = p.patient_id
        WHERE p.patient_id = :patient_id
        GROUP BY p.patient_id, p.patient_name, p.gender, p.blood_type_code
    """), {"patient_id": patient_id}).fetchone()

    if profile_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )

    profile = {
        "patient_name":     profile_row.patient_name,
        "gender":           profile_row.gender,
        "blood_type":       profile_row.blood_type,
        "total_admissions": profile_row.total_admissions or 0,
    }

    # --- all admissions, newest first ---
    adm_rows = db.execute(text("""
        SELECT
            a.admission_id,
            d.doctor_name,
            h.hospital_name,
            a.medical_condition,
            a.admission_type,
            a.medication,
            a.test_result,
            a.date_of_admission,
            a.discharge_date,
            a.billing_amount,
            a.age_at_admission,
            a.room_number
        FROM admission a
        JOIN doctor   d ON d.doctor_id   = a.doctor_id
        JOIN hospital h ON h.hospital_id = a.hospital_id
        WHERE a.patient_id = :patient_id
        ORDER BY a.date_of_admission DESC, a.admission_id DESC
    """), {"patient_id": patient_id}).fetchall()

    admissions = [
        {
            "admission_id":      r.admission_id,
            "doctor_name":       r.doctor_name,
            "hospital_name":     r.hospital_name,
            "medical_condition": r.medical_condition,
            "admission_type":    r.admission_type,
            "medication":        r.medication,
            "test_result":       r.test_result,
            "date_of_admission": _fmt_date(r.date_of_admission),
            "discharge_date":    _fmt_date(r.discharge_date),
            "billing_amount":    _fmt_float(r.billing_amount),
            "age_at_admission":  r.age_at_admission,
            "room_number":       r.room_number,
        }
        for r in adm_rows
    ]

    # --- distinct doctors ---
    doc_rows = db.execute(text("""
        SELECT DISTINCT d.doctor_id, d.doctor_name
        FROM admission a
        JOIN doctor d ON d.doctor_id = a.doctor_id
        WHERE a.patient_id = :patient_id
        ORDER BY d.doctor_name
    """), {"patient_id": patient_id}).fetchall()
    doctors = [{"doctor_id": r.doctor_id, "doctor_name": r.doctor_name} for r in doc_rows]

    # --- distinct conditions ---
    cond_rows = db.execute(text("""
        SELECT DISTINCT medical_condition
        FROM admission
        WHERE patient_id = :patient_id
        ORDER BY medical_condition
    """), {"patient_id": patient_id}).fetchall()
    conditions = [r.medical_condition for r in cond_rows]

    # --- distinct medications ---
    med_rows = db.execute(text("""
        SELECT DISTINCT medication
        FROM admission
        WHERE patient_id = :patient_id
        ORDER BY medication
    """), {"patient_id": patient_id}).fetchall()
    medications = [r.medication for r in med_rows]

    # --- billing summary ---
    billing_row = db.execute(text("""
        SELECT SUM(billing_amount) AS total_billed
        FROM admission
        WHERE patient_id = :patient_id
    """), {"patient_id": patient_id}).fetchone()

    ins_rows = db.execute(text("""
        SELECT insurance_provider AS provider, SUM(billing_amount) AS total
        FROM admission
        WHERE patient_id = :patient_id
        GROUP BY insurance_provider
        ORDER BY total DESC
    """), {"patient_id": patient_id}).fetchall()

    billing_summary = {
        "total_billed": _fmt_float(billing_row.total_billed if billing_row else None),
        "by_insurance": [
            {"provider": r.provider, "total": _fmt_float(r.total)} for r in ins_rows
        ],
    }

    # --- test results ---
    test_rows = db.execute(text("""
        SELECT test_result AS result, COUNT(*) AS cnt
        FROM admission
        WHERE patient_id = :patient_id
        GROUP BY test_result
        ORDER BY cnt DESC
    """), {"patient_id": patient_id}).fetchall()
    test_results = [{"result": r.result, "count": r.cnt} for r in test_rows]

    return {
        "profile":         profile,
        "admissions":      admissions,
        "doctors":         doctors,
        "conditions":      conditions,
        "medications":     medications,
        "billing_summary": billing_summary,
        "test_results":    test_results,
    }
