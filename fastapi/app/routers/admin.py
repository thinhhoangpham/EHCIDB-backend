from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import models, database
from app.schemas.admin import User, UserUpdate, AccessLog, InsuranceProvider, InsuranceProviderCreate
from app.core.security import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users/", response_model=List[User])
def get_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    return db.query(models.User).all()

@router.patch("/users/{user_id}", response_model=User)
def update_user(user_id: int, user_update: UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    for k, v in user_update.dict().items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user

@router.get("/access-logs/", response_model=List[AccessLog])
def get_access_logs(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    return db.query(models.AccessLog).all()