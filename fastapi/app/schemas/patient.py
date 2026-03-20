from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from typing_extensions import Literal

Severity = Literal["mild", "moderate", "severe"]
CoverageStatus = Literal["active", "inactive", "pending"]

# ---------- ALLERGY ----------
class AllergyBase(BaseModel):
    name: str
    severity: Severity
    critical_flag: Optional[bool] = False

class AllergyCreate(AllergyBase):
    pass

class Allergy(AllergyBase):
    id: int
    class Config:
        orm_mode = True


# ---------- CONDITION ----------
class ConditionBase(BaseModel):
    name: str
    severity: Severity
    critical_flag: Optional[bool] = False

class ConditionCreate(ConditionBase):
    pass

class Condition(ConditionBase):
    id: int
    class Config:
        orm_mode = True


# ---------- MEDICATION ----------
class MedicationBase(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date]

class MedicationCreate(MedicationBase):
    pass

class Medication(MedicationBase):
    id: int
    class Config:
        orm_mode = True


# ---------- DEVICE (FIXED) ----------
class DeviceBase(BaseModel):
    name: str
    device_type: str
    description: Optional[str]
    implanted_date: Optional[date]

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    class Config:
        orm_mode = True


# ---------- CONTACT (FIXED) ----------
class EmergencyContactBase(BaseModel):
    name: str
    relation: str
    phone: str

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContact(EmergencyContactBase):
    id: int
    class Config:
        orm_mode = True


# ---------- INSURANCE (FIXED) ----------
class InsuranceInfoBase(BaseModel):
    provider_id: int
    plan_type: str
    member_id: str
    group_number: str
    coverage_status: CoverageStatus

class InsuranceInfoCreate(InsuranceInfoBase):
    pass

class InsuranceInfo(InsuranceInfoBase):
    id: int
    class Config:
        orm_mode = True


# ---------- PROFILE ----------
class PatientProfileBase(BaseModel):
    emergency_id: str
    blood_type: str

class PatientProfileUpdate(BaseModel):
    emergency_id: Optional[str] = None
    blood_type: Optional[str] = None


class PatientProfile(PatientProfileBase):
    id: int
    allergies: List[Allergy] = []
    conditions: List[Condition] = []
    medications: List[Medication] = []
    devices: List[Device] = []
    contacts: List[EmergencyContact] = []
    insurance: Optional[InsuranceInfo]

    class Config:
        orm_mode = True