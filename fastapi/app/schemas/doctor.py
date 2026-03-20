from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from .patient import Allergy, Condition, Medication, Device, EmergencyContact, InsuranceInfo

class PatientEmergencyData(BaseModel):
    emergency_id: str
    name: str
    blood_type: str
    allergies: List[Allergy] = []
    conditions: List[Condition] = []
    medications: List[Medication] = []
    devices: List[Device] = []
    emergency_contacts: List[EmergencyContact] = []
    insurance: Optional[InsuranceInfo]

    class Config:
        orm_mode = True