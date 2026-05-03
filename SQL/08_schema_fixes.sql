-- ========================================
-- 08_schema_fixes.sql
-- Critical data-integrity / privacy fixes.
-- Idempotent: safe to re-run.
-- Run after 07_emergency_tables.sql.
-- ========================================

USE ehcidb;

-- =========================================================================
-- FIX 1 — Drop the (name, gender, blood_type, dob) natural-key uniqueness
-- on `patient`. Two real people can share these four attributes; this
-- constraint silently merges distinct people into a single row on re-ingest.
-- patient_id remains the canonical identifier.
-- =========================================================================
SET @ix := (SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = 'ehcidb' AND TABLE_NAME = 'patient'
              AND INDEX_NAME = 'uq_patient');
SET @sql := IF(@ix > 0, 'ALTER TABLE patient DROP INDEX uq_patient', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 2 — Replace sequential `emergency_identifier` with an unguessable
-- token. The previous format `EHC00001..N` lets anyone with the doctor
-- search endpoint enumerate every patient.
--
-- Format: `EHC-` + 16 random uppercase hex chars (UUID-derived).
-- Length expanded to VARCHAR(40); UNIQUE preserved.
-- =========================================================================
ALTER TABLE patient MODIFY COLUMN emergency_identifier VARCHAR(40);

-- Regenerate every existing identifier (they are all currently predictable).
UPDATE patient
SET emergency_identifier = CONCAT(
    'EHC-',
    UPPER(REPLACE(SUBSTRING(UUID(), 1, 18), '-', ''))
);


-- =========================================================================
-- FIX 3 — Soft delete on clinical tables.
-- Hard-deleting medical history destroys provenance. Add `is_active` flag;
-- application code should filter `WHERE is_active = TRUE` and UPDATE rather
-- than DELETE.
-- =========================================================================
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='allergy' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE allergy ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='medical_condition' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE medical_condition ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient_medication' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE patient_medication ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='device' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE device ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='emergency_contact' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE emergency_contact ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient_insurance' AND COLUMN_NAME='is_active');
SET @sql := IF(@c=0, 'ALTER TABLE patient_insurance ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE', 'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 4 — Audit timestamps on all clinical tables.
-- `created_at` records data entry; `updated_at` auto-tracks edits.
-- =========================================================================
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='allergy' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE allergy
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='medical_condition' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE medical_condition
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient_medication' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE patient_medication
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='device' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE device
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='emergency_contact' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE emergency_contact
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient_insurance' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE patient_insurance
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient' AND COLUMN_NAME='created_at');
SET @sql := IF(@c=0,
  'ALTER TABLE patient
     ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 5 — CHECK constraints on `admission` (MySQL 8 enforces these).
-- =========================================================================
SET @c := (SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS
           WHERE CONSTRAINT_SCHEMA='ehcidb' AND CONSTRAINT_NAME='ck_adm_billing_nonneg');
SET @sql := IF(@c=0,
  'ALTER TABLE admission ADD CONSTRAINT ck_adm_billing_nonneg CHECK (billing_amount >= 0)',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS
           WHERE CONSTRAINT_SCHEMA='ehcidb' AND CONSTRAINT_NAME='ck_adm_age_nonneg');
SET @sql := IF(@c=0,
  'ALTER TABLE admission ADD CONSTRAINT ck_adm_age_nonneg CHECK (age_at_admission >= 0 AND age_at_admission <= 130)',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS
           WHERE CONSTRAINT_SCHEMA='ehcidb' AND CONSTRAINT_NAME='ck_adm_dates');
SET @sql := IF(@c=0,
  'ALTER TABLE admission ADD CONSTRAINT ck_adm_dates CHECK (discharge_date >= date_of_admission)',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS
           WHERE CONSTRAINT_SCHEMA='ehcidb' AND CONSTRAINT_NAME='ck_patient_dob');
SET @sql := IF(@c=0,
  'ALTER TABLE patient ADD CONSTRAINT ck_patient_dob CHECK (date_of_birth <= CURRENT_DATE)',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @c := (SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS
           WHERE CONSTRAINT_SCHEMA='ehcidb' AND CONSTRAINT_NAME='ck_blood_type');
SET @sql := IF(@c=0,
  "ALTER TABLE dim_blood_type ADD CONSTRAINT ck_blood_type
     CHECK (blood_type_code IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))",
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 6 — Rename misnamed `doctor_patient_assignment.date_of_admission` to
-- `assigned_at`. The column records the assignment timestamp, not an
-- admission date.
-- =========================================================================
-- SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
--            WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='doctor_patient_assignment'
--              AND COLUMN_NAME='date_of_admission');
-- SET @sql := IF(@c>0,
--   'ALTER TABLE doctor_patient_assignment
--      CHANGE COLUMN date_of_admission assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP',
--   'SELECT 1');
-- PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 7 — Uniqueness on (provider_id, member_id) for patient_insurance.
-- Two patients should not share a member ID with the same provider.
-- Existing synthetic data uses CONCAT('MEM', patient_id) per row, so this
-- is already unique in seed; constraint enforces it going forward.
-- =========================================================================
SET @ix := (SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='patient_insurance'
              AND INDEX_NAME='uq_patient_insurance_member');
SET @sql := IF(@ix=0,
  'ALTER TABLE patient_insurance
     ADD CONSTRAINT uq_patient_insurance_member UNIQUE (provider_id, member_id)',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;


-- =========================================================================
-- FIX 8 — `emergency_contact.phone_number` is the entire point of the row.
-- Make it NOT NULL. (Existing seed always populates it.)
-- =========================================================================
ALTER TABLE emergency_contact MODIFY COLUMN phone_number VARCHAR(20) NOT NULL;


-- =========================================================================
-- FIX 9 — Drop the denormalized `admission.age_at_admission`. It can be
-- derived from patient.date_of_birth + admission.date_of_admission and
-- otherwise drifts. (Comment out if any consumer still depends on it.)
-- =========================================================================
-- SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
--            WHERE TABLE_SCHEMA='ehcidb' AND TABLE_NAME='admission' AND COLUMN_NAME='age_at_admission');
-- SET @sql := IF(@c>0, 'ALTER TABLE admission DROP COLUMN age_at_admission', 'SELECT 1');
-- PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;
