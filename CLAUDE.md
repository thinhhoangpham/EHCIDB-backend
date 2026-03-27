# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EHCIDB-backend is the database layer for the Emergency Healthcare Critical Information Database System. It is a MySQL 8.4 database provisioned via Docker, populated from a cleaned CSV dataset through a staged ETL pipeline.

## Setup & Commands

**Start the database:**
```bash
docker compose up -d
```

**Connect via MySQL client:**
```bash
mysql -h 127.0.0.1 -P 3307 -u ehci -pehci_pw ehcidb
# or as root:
mysql -h 127.0.0.1 -P 3307 -u root -proot_pw ehcidb
```

**Run the full ETL pipeline (from repo root, after container is up):**
```bash
for f in SQL/01_schema.sql SQL/02_staging.sql SQL/03_core_tables.sql SQL/04_etl_load.sql SQL/05_indexes.sql; do
  mysql -h 127.0.0.1 -P 3307 -u root -proot_pw < "$f"
done
```

**Load CSV into staging table** (run inside a MySQL session after `02_staging.sql`):
```sql
LOAD DATA LOCAL INFILE '/data/healthcare_dataset_cleaned.csv'
INTO TABLE stg_healthcare
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(name, age, gender, blood_type, medical_condition, date_of_admission,
 doctor, hospital, insurance_provider, billing_amount, room_number,
 admission_type, discharge_date, medication, test_results);
```
The Docker volume mounts `./data` (lowercase) as `/data` inside the container. The MySQL daemon runs with `--local-infile=1 --secure-file-priv=""`.

## Architecture

### ETL Pipeline (SQL scripts run in order)

| File | Purpose |
|------|---------|
| `SQL/01_schema.sql` | Creates `ehcidb` database |
| `SQL/02_staging.sql` | Creates `stg_healthcare` flat staging table |
| `SQL/03_core_tables.sql` | Creates normalized dimension + fact tables |
| `SQL/04_etl_load.sql` | Inserts from staging into normalized tables |
| `SQL/05_indexes.sql` | Adds performance indexes on `admission` |

### Normalized Schema

**Dimension tables** (lookup/reference values, natural PKs):
- `dim_blood_type`, `dim_medical_condition`, `dim_insurance_provider`, `dim_admission_type`, `dim_medication`, `dim_test_result`

**Entity tables** (surrogate PKs, deduplicated):
- `hospital(hospital_id, hospital_name)`
- `doctor(doctor_id, doctor_name)`
- `patient(patient_id, patient_name, gender, blood_type_code)`

**Fact table**:
- `admission` — joins all entities and dimensions; stores `age_at_admission`, `room_number`, `date_of_admission`, `discharge_date`, `billing_amount`

The `admission` table carries FK references to all dimension and entity tables, enforcing referential integrity. ETL uses `INSERT IGNORE` for dimension/entity tables to handle duplicates, then resolves surrogate keys via JOIN when populating `admission`.

## Docker & Connection Details

- Container name: `ehcidb_mysql`
- Image: `mysql:8.4`
- Host port: `3307` → container port `3306`
- Database: `ehcidb`
- App user: `ehci` / `ehci_pw`
- Root password: `root_pw`
- Data volume: `mysqldata` (persistent), `./data` → `/data` (CSV source)
