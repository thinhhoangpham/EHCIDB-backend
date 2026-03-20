from pydantic import BaseModel, EmailStr
from typing import Literal

UserRole = Literal["patient", "doctor", "admin"]

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: str
    role: UserRole
    is_active: bool

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

class AccessLog(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: str
    class Config:
        orm_mode = True

class InsuranceProviderBase(BaseModel):
    name: str

class InsuranceProviderCreate(InsuranceProviderBase):
    pass

class InsuranceProvider(InsuranceProviderBase):
    id: int
    class Config:
        orm_mode = True