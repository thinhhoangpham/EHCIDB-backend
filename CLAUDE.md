# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EHCIDB-backend — FastAPI + MySQL 8.4 backend for the Emergency Healthcare Critical Information Database. Academic prototype for CS5356. Docker-provisioned MySQL populated via ETL from a Kaggle CSV dataset.

## Setup & Commands

**Start containers:**
```bash
docker compose up -d
```

**Run the full pipeline (from repo root, after container is up):**

Run SQL files 01–07 in order. The CSV load must happen between 02 and 03:

```bash
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/01_schema.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/02_staging.sql
# Load CSV (run inside the container or via exec):
docker exec -i ehcidb_mysql mysql -uroot -proot_pw ehcidb < SQL/03a_load_csv.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/03_core_tables.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/04_etl_load.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/05_indexes.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/06_security.sql
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < SQL/07_emergency_tables.sql
```

**MySQL connection:**
- Host: `127.0.0.1`, Port: `3307`
- App user: `ehci` / `ehci_pw`
- Root: `root` / `root_pw`
- Database: `ehcidb`

```bash
mysql -h 127.0.0.1 -P 3307 -u ehci -pehci_pw ehcidb
```

**API:** http://localhost:8000 — Swagger docs at http://localhost:8000/docs

## Architecture

### SQL Pipeline

| File | Purpose |
|------|---------|
| `SQL/01_schema.sql` | Creates `ehcidb` database |
| `SQL/02_staging.sql` | Creates `stg_healthcare` flat staging table |
| `SQL/03a_load_csv.sql` | Loads CSV into staging via `LOAD DATA INFILE` |
| `SQL/03_core_tables.sql` | Creates normalized dimension + fact tables |
| `SQL/04_etl_load.sql` | Inserts from staging into normalized tables |
| `SQL/05_indexes.sql` | Adds performance indexes on `admission` |
| `SQL/06_security.sql` | Creates RBAC tables, seeds roles/permissions, bulk-inserts patient and doctor users |
| `SQL/07_emergency_tables.sql` | Creates emergency tables, adds `emergency_identifier` to `patient`, populates with synthetic data |

### Database Schema

**Healthcare (from ETL):**
- `dim_blood_type`, `dim_medical_condition`, `dim_insurance_provider`, `dim_admission_type`, `dim_medication`, `dim_test_result` — dimension/lookup tables
- `patient(patient_id, patient_name, gender, blood_type_code, emergency_identifier)`
- `doctor(doctor_id, doctor_name)`
- `hospital(hospital_id, hospital_name)`
- `admission(admission_id, patient_id, doctor_id, hospital_id, medical_condition, insurance_provider, admission_type, medication, test_result, age_at_admission, room_number, date_of_admission, discharge_date, billing_amount)`

**Emergency (proposal):**
- `allergy(allergy_id, patient_id, allergy_name, severity)`
- `medical_condition(condition_id, patient_id, condition_name, critical_flag)`
- `patient_medication(medication_id, patient_id, medication_name, dosage)`
- `device(device_id, patient_id, device_name, device_type)`
- `emergency_contact(contact_id, patient_id, contact_name, relationship, phone_number)`
- `insurance_provider_detail(provider_id, provider_name, payer_phone)`
- `patient_insurance(patient_insurance_id, patient_id, provider_id, plan_type, member_id, group_number, coverage_status)`

**Security/Auth:**
- `app_user(user_id, username, password_hash, full_name, email, is_active, patient_id, doctor_id)`
- `role(role_id, role_name)`
- `permission(permission_id, permission_name)`
- `user_role(user_role_id, user_id, role_id)`
- `role_permission(role_permission_id, role_id, permission_id)`
- `doctor_patient_access(doctor_id, patient_id)` — populated from `admission` rows
- `access_log(log_id, user_id, action, target_patient_id, created_at)`

### API Endpoints

**Auth** (`api/routers/auth.py`):
- `POST /api/auth/login/`
- `POST /api/auth/logout/`

**Dashboard** (`api/routers/dashboard.py`):
- `GET /api/dashboard/admin` — requires Admin role
- `GET /api/dashboard/doctor` — requires Doctor role
- `GET /api/dashboard/patient` — requires Patient role

**Emergency — Patient** (`api/routers/emergency.py`):
- `GET /api/emergency/patient/profile`
- `POST /api/emergency/patient/allergies`
- `DELETE /api/emergency/patient/allergies/{allergy_id}`
- `POST /api/emergency/patient/conditions`
- `DELETE /api/emergency/patient/conditions/{condition_id}`
- `POST /api/emergency/patient/medications`
- `DELETE /api/emergency/patient/medications/{medication_id}`
- `POST /api/emergency/patient/devices`
- `DELETE /api/emergency/patient/devices/{device_id}`
- `POST /api/emergency/patient/emergency-contacts`
- `PUT /api/emergency/patient/emergency-contacts/{contact_id}`
- `DELETE /api/emergency/patient/emergency-contacts/{contact_id}`

**Emergency — Doctor** (`api/routers/emergency.py`):
- `GET /api/emergency/doctor/search?q=...` — search by name or emergency_identifier
- `GET /api/emergency/doctor/patient/{emergency_id}` — full emergency profile

**Emergency — Admin** (`api/routers/emergency.py`):
- `GET /api/emergency/admin/users` — paginated user list
- `PATCH /api/emergency/admin/users/{user_id}` — update is_active or role
- `GET /api/emergency/admin/access-logs` — paginated access log
- `GET /api/emergency/admin/insurance-providers`
- `POST /api/emergency/admin/insurance-providers`
- `DELETE /api/emergency/admin/insurance-providers/{provider_id}`

### Auth

- JWT (HS256), access token 60 min, refresh 7 days
- Bearer token via `HTTPBearer`; decoded in `get_current_user` dependency
- Role enforcement via `require_role(role_name)` dependency factory (`api/dependencies.py`)
- Roles: `Admin`, `Doctor`, `Patient`, `Viewer`

## Docker & Connection Details

| Item | Value |
|------|-------|
| MySQL container | `ehcidb_mysql` |
| API container | `ehcidb_api` |
| MySQL host port | `3307` → container `3306` |
| API host port | `8000` → container `8000` |
| Database | `ehcidb` |
| App user | `ehci` / `ehci_pw` |
| Root password | `root_pw` |
| Secret key (dev) | `dev-secret-key-change-in-production` |
| Volumes | `mysqldata` (persistent MySQL data), `./data` → `/data` (CSV source) |

## Test Accounts

All passwords: `password123`

| Username | Email | Role |
|----------|-------|------|
| `admin` | `admin@ehcidb.local` | Admin |
| `d_1` … `d_N` | `d_1@ehcidb.local` … | Doctor |
| `p_1` … `p_N` | `p_1@ehcidb.local` … | Patient |
