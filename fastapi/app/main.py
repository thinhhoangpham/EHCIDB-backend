from fastapi import FastAPI
from app.db import models, database
from app.routers import auth, patients, doctors, admin, insurance

app = FastAPI(title="EHCIDB API")

models.Base.metadata.create_all(bind=database.engine)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(admin.router)
app.include_router(insurance.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}