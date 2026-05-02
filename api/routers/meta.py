from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.models import DimBloodType

router = APIRouter()


@router.get("/blood-types/")
def get_blood_types(db: Session = Depends(get_db)):
    return [
        {"blood_type_code": b.blood_type_code}
        for b in db.query(DimBloodType).all()
    ]