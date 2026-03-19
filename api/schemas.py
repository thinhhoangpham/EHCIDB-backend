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

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserSchema
