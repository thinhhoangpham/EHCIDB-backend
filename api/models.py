from decimal import Decimal
from sqlalchemy import BigInteger, Boolean, Date, Enum, Integer, Numeric, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from datetime import date, datetime
from api.database import Base
from sqlalchemy import Column, String



class Patient(Base):
    __tablename__ = "patient"

    patient_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(50), nullable=False)
    blood_type_code: Mapped[str] = mapped_column(String(10), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_identifier: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)

    admissions: Mapped[list["Admission"]] = sa_relationship("Admission", back_populates="patient")
    allergies: Mapped[list["Allergy"]] = sa_relationship("Allergy", back_populates="patient")
    conditions: Mapped[list["MedicalCondition"]] = sa_relationship("MedicalCondition", back_populates="patient")
    medications: Mapped[list["PatientMedication"]] = sa_relationship("PatientMedication", back_populates="patient")
    devices: Mapped[list["Device"]] = sa_relationship("Device", back_populates="patient")
    emergency_contacts: Mapped[list["EmergencyContact"]] = sa_relationship("EmergencyContact", back_populates="patient")
    insurances: Mapped[list["PatientInsurance"]] = sa_relationship("PatientInsurance", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctor"

    doctor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doctor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    admissions: Mapped[list["Admission"]] = sa_relationship("Admission", back_populates="doctor")


class AppUser(Base):
    __tablename__ = "app_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    patient_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=True)
    doctor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("doctor.doctor_id"), nullable=True)

    user_roles: Mapped[list["UserRole"]] = sa_relationship("UserRole", back_populates="user")
    patient: Mapped["Patient | None"] = sa_relationship("Patient")
    doctor: Mapped["Doctor | None"] = sa_relationship("Doctor")


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user_roles: Mapped[list["UserRole"]] = sa_relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.role_id"), nullable=False)

    user: Mapped["AppUser"] = sa_relationship("AppUser", back_populates="user_roles")
    role: Mapped["Role"] = sa_relationship("Role", back_populates="user_roles")


class Hospital(Base):
    __tablename__ = "hospital"

    hospital_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hospital_name: Mapped[str] = mapped_column(String(255), nullable=False)

    admissions: Mapped[list["Admission"]] = sa_relationship("Admission", back_populates="hospital")


class Admission(Base):
    __tablename__ = "admission"

    admission_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("doctor.doctor_id"), nullable=False)
    hospital_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hospital.hospital_id"), nullable=False)

    # FK strings pointing to dim tables
    medical_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    insurance_provider: Mapped[str] = mapped_column(String(255), nullable=False)
    admission_type: Mapped[str] = mapped_column(String(100), nullable=False)
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    test_result: Mapped[str] = mapped_column(String(100), nullable=False)

    age_at_admission: Mapped[int] = mapped_column(Integer, nullable=False)
    room_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_admission: Mapped[Date] = mapped_column(Date, nullable=False)
    discharge_date: Mapped[Date] = mapped_column(Date, nullable=False)
    billing_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="admissions")
    doctor: Mapped["Doctor"] = sa_relationship("Doctor", back_populates="admissions")
    hospital: Mapped["Hospital"] = sa_relationship("Hospital", back_populates="admissions")


# ---------------------------------------------------------------------------
# Emergency tables
# ---------------------------------------------------------------------------

class Allergy(Base):
    __tablename__ = "allergy"

    allergy_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    allergy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(Enum("Mild", "Moderate", "Severe"), nullable=False, default="Moderate")

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="allergies")


class MedicalCondition(Base):
    __tablename__ = "medical_condition"

    condition_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    critical_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="conditions")


class PatientMedication(Base):
    __tablename__ = "patient_medication"

    medication_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="medications")


class Device(Base):
    __tablename__ = "device"

    device_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="devices")


class EmergencyContact(Base):
    __tablename__ = "emergency_contact"

    contact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="emergency_contacts")


class InsuranceProviderDetail(Base):
    __tablename__ = "insurance_provider_detail"

    provider_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    payer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    patient_insurances: Mapped[list["PatientInsurance"]] = sa_relationship("PatientInsurance", back_populates="provider")


class PatientInsurance(Base):
    __tablename__ = "patient_insurance"

    patient_insurance_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)
    provider_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("insurance_provider_detail.provider_id"), nullable=False)
    plan_type: Mapped[str | None] = mapped_column(Enum("PPO", "HMO", "Medicaid", "Medicare"), nullable=True, default="PPO")
    member_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    group_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coverage_status: Mapped[str] = mapped_column(Enum("Active", "Inactive"), nullable=False, default="Active")

    patient: Mapped["Patient"] = sa_relationship("Patient", back_populates="insurances")
    provider: Mapped["InsuranceProviderDetail"] = sa_relationship("InsuranceProviderDetail", back_populates="patient_insurances")


class AccessLog(Base):
    __tablename__ = "access_log"

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_patient_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("patient.patient_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped["AppUser"] = sa_relationship("AppUser")
    target_patient: Mapped["Patient | None"] = sa_relationship("Patient")


class DimBloodType(Base):
    __tablename__ = "dim_blood_type"
    blood_type_code = Column(String(10), primary_key=True)


class DoctorPatientAssignment(Base):
    __tablename__ = "doctor_patient_assignment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    doctor_id = Column(BigInteger, ForeignKey("doctor.doctor_id"), nullable=False)
    patient_id = Column(BigInteger, ForeignKey("patient.patient_id"), nullable=False)

    date_of_admission = Column(DateTime, default=datetime.utcnow)