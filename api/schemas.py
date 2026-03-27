from typing import Literal
from pydantic import BaseModel

UserRoleType = Literal["patient", "doctor", "admin"]


class LoginRequest(BaseModel):
    email: str
    password: str


class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoleType
    is_active: bool
    patient_id: int | None = None
    doctor_id: int | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserSchema
