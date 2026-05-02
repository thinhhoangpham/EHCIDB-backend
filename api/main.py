from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth
from api.routers import dashboard
from api.routers import emergency

app = FastAPI(title="EHCIDB API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://localhost:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(emergency.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])