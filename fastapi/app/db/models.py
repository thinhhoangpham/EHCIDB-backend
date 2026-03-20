from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum


# ENUMS

class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class Severity(str, enum.Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class CoverageStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


# USERS

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password = Column(String(200))
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)

    patient = relationship("PatientProfile", back_populates="user", uselist=False)
    doctor = relationship("Doctor", back_populates="user", uselist=False)


# HOSPITALS

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(String(200))
    contact_number = Column(String(20))
    type = Column(String(50))

    doctors = relationship("Doctor", back_populates="hospital")


# DOCTORS

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    specialty = Column(String(100))
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    contact_info = Column(String(200))

    user = relationship("User", back_populates="doctor")
    hospital = relationship("Hospital", back_populates="doctors")


# PATIENTS

class PatientProfile(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    emergency_id = Column(String(20), unique=True)
    blood_type = Column(String(3))

    user = relationship("User", back_populates="patient")

    allergies = relationship("Allergy", back_populates="patient")
    conditions = relationship("Condition", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    devices = relationship("Device", back_populates="patient")
    contacts = relationship("EmergencyContact", back_populates="patient")
    insurance = relationship("InsuranceInfo", back_populates="patient", uselist=False)


# ALLERGIES

class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String(100))
    severity = Column(Enum(Severity))
    critical_flag = Column(Boolean, default=False)

    patient = relationship("PatientProfile", back_populates="allergies")


# CONDITIONS

class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String(100))
    severity = Column(Enum(Severity))
    critical_flag = Column(Boolean, default=False)

    patient = relationship("PatientProfile", back_populates="conditions")


# MEDICATIONS

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String(100))
    dosage = Column(String(50))
    frequency = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)

    patient = relationship("PatientProfile", back_populates="medications")


# DEVICES

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String(100))
    device_type = Column(String(100))
    description = Column(String(200), nullable=True)
    implanted_date = Column(Date, nullable=True)

    patient = relationship("PatientProfile", back_populates="devices")


# EMERGENCY CONTACTS

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String(100))
    relation = Column(String(50))
    phone = Column(String(20))

    patient = relationship("PatientProfile", back_populates="contacts")


# INSURANCE PROVIDERS

class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    payer_phone = Column(String(20))


# PATIENT INSURANCE

class InsuranceInfo(Base):
    __tablename__ = "insurance_info"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    provider_id = Column(Integer, ForeignKey("insurance_providers.id"))

    plan_type = Column(String(50))
    member_id = Column(String(50))
    group_number = Column(String(50))

    coverage_status = Column(Enum(CoverageStatus))

    patient = relationship("PatientProfile", back_populates="insurance")
    provider = relationship("InsuranceProvider")


# ACCESS LOGS (AUDIT TRAIL)

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    timestamp = Column(Date)