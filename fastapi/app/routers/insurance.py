from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import models, database
from app.schemas.admin import InsuranceProvider, InsuranceProviderCreate
from app.core.security import get_current_user

router = APIRouter(prefix="/admin/insurance-providers", tags=["insurance"])

@router.get("/", response_model=List[InsuranceProvider])
def get_providers(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    return db.query(models.InsuranceProvider).all()

@router.post("/", response_model=InsuranceProvider)
def create_provider(provider: InsuranceProviderCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)
    new_provider = models.InsuranceProvider(**provider.dict())
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return new_provider