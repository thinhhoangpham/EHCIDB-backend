from decimal import Decimal
from sqlalchemy import BigInteger, Boolean, Date, Integer, Numeric, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


class Patient(Base):
    __tablename__ = "patient"

    patient_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(50), nullable=False)
    blood_type_code: Mapped[str] = mapped_column(String(10), nullable=False)

    admissions: Mapped[list["Admission"]] = relationship("Admission", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctor"

    doctor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doctor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    admissions: Mapped[list["Admission"]] = relationship("Admission", back_populates="doctor")


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

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user")
    patient: Mapped["Patient | None"] = relationship("Patient")
    doctor: Mapped["Doctor | None"] = relationship("Doctor")


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.role_id"), nullable=False)

    user: Mapped["AppUser"] = relationship("AppUser", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")


class Hospital(Base):
    __tablename__ = "hospital"

    hospital_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hospital_name: Mapped[str] = mapped_column(String(255), nullable=False)

    admissions: Mapped[list["Admission"]] = relationship("Admission", back_populates="hospital")


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

    patient: Mapped["Patient"] = relationship("Patient", back_populates="admissions")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="admissions")
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="admissions")
