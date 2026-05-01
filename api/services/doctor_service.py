# api/services/doctor_service.py
# doctor service functions added here. admin creates doctor account.

from api.database import SessionLocal
from api.models import AppUser, Role, UserRole, Doctor
from api.auth import hash_password


def create_doctor (username, email, password, full_name, doctor_name):
    db = SessionLocal()

    try:
        # ======================
        # CHECK EXISTING USER
        # ======================
        existing = db.query(AppUser).filter(AppUser.username == username).first()
        if existing:
            return {"success": False, "message": "Doctor already exists"}

        # ======================
        # CREATE DOCTOR ENTITY
        # ======================
        doctor = Doctor(
            doctor_name=doctor_name
        )

        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        # ======================
        # CREATE USER ACCOUNT
        # ======================
        user = AppUser(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            doctor_id=doctor.doctor_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # ======================
        # ASSIGN ROLE
        # ======================
        role = db.query(Role).filter(Role.role_name == "Doctor").first()

        if role:
            db.add(
                UserRole(
                    user_id=user.user_id,
                    role_id=role.role_id
                )
            )
            db.commit()
        else:
            return {"success": False, "message": "Doctor role not found in DB"}

        return {
            "success": True,
            "message": "Doctor created successfully",
            "doctor_id": doctor.doctor_id,
            "user_id": user.user_id
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()