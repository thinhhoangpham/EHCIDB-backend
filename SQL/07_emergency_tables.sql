-- ========================================
-- EMERGENCY TABLES
-- Creates patient-centric emergency data
-- tables and populates them with synthetic
-- data derived from existing admission data.
-- ========================================

USE ehcidb;

-- =========================
-- 1a. Add emergency_identifier to patient
-- =========================

SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'ehcidb' AND TABLE_NAME = 'patient' AND COLUMN_NAME = 'emergency_identifier');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE patient ADD COLUMN emergency_identifier VARCHAR(20) UNIQUE',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
UPDATE patient SET emergency_identifier = CONCAT('EHC', LPAD(patient_id, 5, '0'))
WHERE emergency_identifier IS NULL;

-- =========================
-- 1b. New tables (drop first for idempotency)
-- =========================

DROP TABLE IF EXISTS patient_insurance;
DROP TABLE IF EXISTS insurance_provider_detail;
DROP TABLE IF EXISTS access_log;
DROP TABLE IF EXISTS emergency_contact;
DROP TABLE IF EXISTS device;
DROP TABLE IF EXISTS patient_medication;
DROP TABLE IF EXISTS medical_condition;
DROP TABLE IF EXISTS allergy;

CREATE TABLE allergy (
    allergy_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    allergy_name VARCHAR(255) NOT NULL,
    severity ENUM('Mild','Moderate','Severe') NOT NULL DEFAULT 'Moderate',
    CONSTRAINT fk_allergy_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE medical_condition (
    condition_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    condition_name VARCHAR(255) NOT NULL,
    critical_flag BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_condition_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE patient_medication (
    medication_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    CONSTRAINT fk_med_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE device (
    device_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100),
    CONSTRAINT fk_device_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE emergency_contact (
    contact_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    relationship VARCHAR(100),
    phone_number VARCHAR(20),
    CONSTRAINT fk_ec_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE insurance_provider_detail (
    provider_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider_name VARCHAR(255) NOT NULL UNIQUE,
    payer_phone VARCHAR(20)
);

CREATE TABLE patient_insurance (
    patient_insurance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    provider_id BIGINT NOT NULL,
    plan_type ENUM('PPO','HMO','Medicaid','Medicare') DEFAULT 'PPO',
    member_id VARCHAR(50),
    group_number VARCHAR(50),
    coverage_status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    CONSTRAINT fk_pi_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    CONSTRAINT fk_pi_provider FOREIGN KEY (provider_id) REFERENCES insurance_provider_detail(provider_id)
);

CREATE TABLE access_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action VARCHAR(255) NOT NULL,
    target_patient_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES app_user(user_id),
    CONSTRAINT fk_log_patient FOREIGN KEY (target_patient_id) REFERENCES patient(patient_id)
);

-- =========================
-- 1c. Populate with synthetic data
-- =========================

-- -------------------------
-- medical_condition
-- Derived from admission; critical_flag follows condition rules:
--   Cancer, Diabetes, Asthma → critical; Hypertension, Obesity, Arthritis → not critical
-- -------------------------
INSERT INTO medical_condition (patient_id, condition_name, critical_flag)
SELECT DISTINCT patient_id, medical_condition,
    CASE
        WHEN medical_condition IN ('Cancer', 'Diabetes', 'Asthma') THEN TRUE
        ELSE FALSE
    END
FROM admission;

-- -------------------------
-- patient_medication
-- Each patient gets 1–2 condition-appropriate medications.
-- First medication: every patient with that condition.
-- Second medication: patients where patient_id % 2 = 0 (~50%).
-- -------------------------

-- Cancer – first med (all Cancer patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Tamoxifen', '20mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Cancer';

-- Cancer – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Methotrexate', '15mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Cancer'
  AND mc.patient_id % 2 = 0;

-- Diabetes – first med (all Diabetes patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Metformin', '500mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Diabetes';

-- Diabetes – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Insulin Glargine', '10 units'
FROM medical_condition mc
WHERE mc.condition_name = 'Diabetes'
  AND mc.patient_id % 2 = 0;

-- Asthma – first med (all Asthma patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Albuterol Inhaler', '90mcg'
FROM medical_condition mc
WHERE mc.condition_name = 'Asthma';

-- Asthma – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Prednisone', '10mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Asthma'
  AND mc.patient_id % 2 = 0;

-- Hypertension – first med (all Hypertension patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Lisinopril', '10mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Hypertension';

-- Hypertension – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Amlodipine', '5mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Hypertension'
  AND mc.patient_id % 2 = 0;

-- Obesity – first med (all Obesity patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Orlistat', '120mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Obesity';

-- Obesity – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Metformin', '500mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Obesity'
  AND mc.patient_id % 2 = 0;

-- Arthritis – first med (all Arthritis patients)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Ibuprofen', '400mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Arthritis';

-- Arthritis – second med (~50%)
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT mc.patient_id, 'Methotrexate', '7.5mg'
FROM medical_condition mc
WHERE mc.condition_name = 'Arthritis'
  AND mc.patient_id % 2 = 0;

-- -------------------------
-- device
-- Only assigned to patients with specific conditions, at defined rates.
-- Percentages approximated via patient_id modulo:
--   ~15% → % 7 = 0, ~25% → % 4 = 0, ~20% → % 5 = 0, ~10% → % 10 = 0
-- -------------------------

-- Diabetes – Insulin Pump (~15%)
INSERT INTO device (patient_id, device_name, device_type)
SELECT DISTINCT mc.patient_id, 'Insulin Pump', 'Endocrine'
FROM medical_condition mc
WHERE mc.condition_name = 'Diabetes'
  AND mc.patient_id % 7 = 0;

-- Diabetes – Glucose Monitor (~25%)
INSERT INTO device (patient_id, device_name, device_type)
SELECT DISTINCT mc.patient_id, 'Glucose Monitor', 'Monitoring'
FROM medical_condition mc
WHERE mc.condition_name = 'Diabetes'
  AND mc.patient_id % 4 = 0;

-- Asthma – Nebulizer (~10%)
INSERT INTO device (patient_id, device_name, device_type)
SELECT DISTINCT mc.patient_id, 'Nebulizer', 'Respiratory'
FROM medical_condition mc
WHERE mc.condition_name = 'Asthma'
  AND mc.patient_id % 10 = 0;

-- Hypertension – Blood Pressure Monitor (~20%)
INSERT INTO device (patient_id, device_name, device_type)
SELECT DISTINCT mc.patient_id, 'Blood Pressure Monitor', 'Monitoring'
FROM medical_condition mc
WHERE mc.condition_name = 'Hypertension'
  AND mc.patient_id % 5 = 0;

-- Cancer – Infusion Port (~15%)
INSERT INTO device (patient_id, device_name, device_type)
SELECT DISTINCT mc.patient_id, 'Infusion Port', 'Oncology'
FROM medical_condition mc
WHERE mc.condition_name = 'Cancer'
  AND mc.patient_id % 7 = 0;

-- -------------------------
-- allergy
-- ~10 allergens with realistic severity; patients can match multiple criteria.
-- Selection uses distinct patient_id % N = remainder patterns.
-- -------------------------

-- Penicillin – Severe (~10%)
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Penicillin', 'Severe'
FROM patient
WHERE patient_id % 10 = 0;

-- Sulfa Drugs – Moderate
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Sulfa Drugs', 'Moderate'
FROM patient
WHERE patient_id % 12 = 1;

-- Latex – Mild
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Latex', 'Mild'
FROM patient
WHERE patient_id % 15 = 2;

-- Peanuts – Severe
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Peanuts', 'Severe'
FROM patient
WHERE patient_id % 11 = 3;

-- Shellfish – Moderate
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Shellfish', 'Moderate'
FROM patient
WHERE patient_id % 13 = 4;

-- Aspirin – Mild
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Aspirin', 'Mild'
FROM patient
WHERE patient_id % 14 = 5;

-- Iodine – Severe
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Iodine', 'Severe'
FROM patient
WHERE patient_id % 16 = 6;

-- Codeine – Moderate
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Codeine', 'Moderate'
FROM patient
WHERE patient_id % 17 = 7;

-- Bee Stings – Severe
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Bee Stings', 'Severe'
FROM patient
WHERE patient_id % 18 = 8;

-- Eggs – Mild
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id, 'Eggs', 'Mild'
FROM patient
WHERE patient_id % 20 = 9;

-- -------------------------
-- emergency_contact
-- Every patient gets one contact.
-- 10 first names, 5 relationships; contact uses patient's last name.
-- -------------------------
INSERT INTO emergency_contact (patient_id, contact_name, relationship, phone_number)
SELECT patient_id,
    CONCAT(
        CASE patient_id % 10
            WHEN 0 THEN 'John'
            WHEN 1 THEN 'Sarah'
            WHEN 2 THEN 'Michael'
            WHEN 3 THEN 'Emily'
            WHEN 4 THEN 'David'
            WHEN 5 THEN 'Lisa'
            WHEN 6 THEN 'James'
            WHEN 7 THEN 'Maria'
            WHEN 8 THEN 'Robert'
            WHEN 9 THEN 'Jennifer'
        END,
        ' ',
        SUBSTRING_INDEX(patient_name, ' ', -1)
    ),
    CASE patient_id % 5
        WHEN 0 THEN 'Spouse'
        WHEN 1 THEN 'Parent'
        WHEN 2 THEN 'Sibling'
        WHEN 3 THEN 'Child'
        WHEN 4 THEN 'Partner'
    END,
    CONCAT('555-', LPAD(patient_id % 10000, 4, '0'))
FROM patient;

-- -------------------------
-- insurance_provider_detail
-- Derived from the dimension table seeded during ETL.
-- -------------------------
INSERT INTO insurance_provider_detail (provider_name, payer_phone)
SELECT insurance_provider,
    CONCAT('1-800-', LPAD(FLOOR(RAND(42) * 10000), 4, '0'))
FROM dim_insurance_provider;

-- -------------------------
-- patient_insurance
-- Derived from admission data; plan type inferred from provider name or patient_id parity.
-- -------------------------
INSERT INTO patient_insurance (patient_id, provider_id, plan_type, member_id, group_number, coverage_status)
SELECT DISTINCT a.patient_id, ipd.provider_id,
    CASE
        WHEN a.insurance_provider = 'Medicare' THEN 'Medicare'
        WHEN a.insurance_provider = 'Medicaid' THEN 'Medicaid'
        WHEN a.patient_id % 2 = 0 THEN 'PPO'
        ELSE 'HMO'
    END,
    CONCAT('MEM', LPAD(a.patient_id, 8, '0')),
    CONCAT('GRP', LPAD(ipd.provider_id * 1000 + (a.patient_id % 100), 6, '0')),
    'Active'
FROM admission a
JOIN insurance_provider_detail ipd ON ipd.provider_name = a.insurance_provider;
