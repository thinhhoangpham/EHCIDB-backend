from pydantic import BaseModel, EmailStr
from typing import Literal

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    id: int
    name: str
    role: Literal["patient","doctor","admin"]

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserInfo