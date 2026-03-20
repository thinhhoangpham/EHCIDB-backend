## Database Models Overview
- **Users**: `patient`, `doctor`, `admin` roles; linked to profiles  
- **Patients**: emergency ID, blood type, relationships to all patient data  
- **Doctors** & **Hospitals**: specialties, contact info, hospital affiliation  
- **Patient Data**:  
  - Allergies, Conditions, Medications, Devices, Emergency Contacts, Insurance  
- **Insurance Providers**: provider details  
- **Access Logs**: audit trail for user actions  
- **Relationships**:  
  - One user → one patient/doctor  
  - One patient → many allergies, conditions, medications, devices, contacts  
  - One patient → one insurance  
- **Enums**: UserRole, Severity, CoverageStatus

# Auth & Security - FastAPI

- **Password hashing**: `hash_password` / `verify_password` (bcrypt)  
- **JWT tokens**: `create_access_token` for access with expiry  
- **Current user**: `get_current_user` validates token and fetches user  
- **OAuth2PasswordBearer** used for Bearer token authentication  
- **Config via `.env`**: MySQL creds, `SECRET_KEY`, token expiry

# FastAPI + MySQL Setup

- Loads MySQL credentials from `.env` (user, password, host, port, database)  
- Creates SQLAlchemy **engine**, **Base**, and **SessionLocal** for database access  
- `get_db()` provides a **session for dependency injection** in routes  
- Auto-creates all tables on startup: `models.Base.metadata.create_all(bind=engine)`  
- FastAPI app with routers: `auth`, `patients`, `doctors`, `admin`, `insurance`  
- Health check endpoint: `GET /health` → `{"status": "ok"}`  
- Connection URL: `mysql+mysqlconnector://user:pass@host:port/db_name`

# Admin API - FastAPI

- **Users**: view all, update info (`GET /admin/users/`, `PATCH /admin/users/{id}`)  
- **Access Logs**: view all actions (`GET /admin/access-logs/`)  
- **Insurance Providers**: create/view (`POST/GET /admin/insurance-providers/`)  
- **Schemas**: User, UserUpdate, AccessLog, InsuranceProvider  
- **Security**: only accessible by `admin` role  

# Doctor Emergency API - FastAPI

- **Endpoint**: `GET /patients/emergency/{emergency_id}`  
- **Access**: only `doctor` role  
- **Returns**: patient emergency data including  
  - Name, blood type  
  - Allergies, conditions, medications, devices  
  - Emergency contacts, insurance  
- **Schema**: `PatientEmergencyData` (reuses patient schemas)  


# Patient API - FastAPI

Patients can securely **create, read, update, delete** all their own medical data.

## Schemas
- Profile: emergency ID, blood type  
- Allergies, Conditions, Medications, Devices  
- Emergency Contacts, Insurance Info  

## Endpoints (CRUD)
- `/patients/me/` → profile  
- `/patients/me/allergies/` → allergies  
- `/patients/me/conditions/` → conditions  
- `/patients/me/medications/` → medications  
- `/patients/me/devices/` → devices  
- `/patients/me/contacts/` → contacts  
- `/patients/me/insurance/` → insurance  

## Notes
- Only accessible by the logged-in patient  
- All actions restricted to their own records  