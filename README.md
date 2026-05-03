# EHCIDB Backend

Backend for the Emergency Healthcare Critical Information Database System. Built with FastAPI and MySQL 8.4, provisioned via Docker. 

## Prerequisites

- Docker Desktop
- Python 3.12+
- MySQL client (for running SQL scripts)

## Setup & Running

### 1. Start MySQL

```bash
docker compose up -d db
```

This starts a MySQL 8.4 container on port **3307**.

### 2. Run SQL scripts

```bash
for f in SQL/01_schema.sql SQL/02_staging.sql SQL/03_core_tables.sql SQL/04_etl_load.sql SQL/05_indexes.sql; do mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < "$f"; done
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API server

```bash
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Test Accounts

All accounts use password `password123`.

| Email | Role |
|---|---|
| admin1@example.com | Admin |
| doctor1@example.com | Doctor |
| patient1@example.com | Patient |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login/` | Authenticate and receive access + refresh tokens |
| POST | `/api/auth/logout/` | Logout (client discards tokens; returns 204) |

### Login request body

```json
{
  "email": "admin1@example.com",
  "password": "password123"
}
```

### Login response

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": "1",
    "name": "Admin User",
    "email": "admin1@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

## Database Connection

| Setting | Value |
|---|---|
| Host | localhost |
| Port | 3307 |
| Database | ehcidb |
| User | ehci |
| Password | ehci_pw |

Connect via MySQL client:

```bash
mysql -h 127.0.0.1 -P 3307 -u ehci -pehci_pw ehcidb
```
Access Database MYSQL:
```bash
docker exec -it ehcidb_mysql mysql -u ehci -pehci_pw ehcidb
```