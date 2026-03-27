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

ALTER TABLE patient ADD COLUMN emergency_identifier VARCHAR(20) UNIQUE;
UPDATE patient SET emergency_identifier = CONCAT('EHC', LPAD(patient_id, 5, '0'));

-- =========================
-- 1b. New tables
-- =========================

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

-- Populate medical_condition from admission data (distinct conditions per patient)
-- Mark conditions like Cancer, Diabetes, Asthma as critical
INSERT INTO medical_condition (patient_id, condition_name, critical_flag)
SELECT DISTINCT patient_id, medical_condition,
    CASE WHEN medical_condition IN ('Cancer', 'Diabetes', 'Asthma') THEN TRUE ELSE FALSE END
FROM admission;

-- Populate patient_medication from admission data with synthetic dosages
INSERT INTO patient_medication (patient_id, medication_name, dosage)
SELECT DISTINCT patient_id, medication,
    CASE medication
        WHEN 'Aspirin' THEN '81mg'
        WHEN 'Ibuprofen' THEN '400mg'
        WHEN 'Paracetamol' THEN '500mg'
        WHEN 'Penicillin' THEN '250mg'
        WHEN 'Lipitor' THEN '20mg'
        ELSE '100mg'
    END
FROM admission;

-- Populate allergy: give ~33% of patients a random allergy
-- Use patient_id modulo to deterministically assign
INSERT INTO allergy (patient_id, allergy_name, severity)
SELECT patient_id,
    CASE patient_id % 5
        WHEN 0 THEN 'Penicillin'
        WHEN 1 THEN 'Latex'
        WHEN 2 THEN 'Peanuts'
        WHEN 3 THEN 'Sulfa Drugs'
        WHEN 4 THEN 'Shellfish'
    END,
    CASE patient_id % 3
        WHEN 0 THEN 'Severe'
        WHEN 1 THEN 'Moderate'
        WHEN 2 THEN 'Mild'
    END
FROM patient
WHERE patient_id % 3 = 0;  -- ~33% of patients have allergies

-- Populate device: give ~10% of patients a device
INSERT INTO device (patient_id, device_name, device_type)
SELECT patient_id,
    CASE patient_id % 4
        WHEN 0 THEN 'Pacemaker'
        WHEN 1 THEN 'Insulin Pump'
        WHEN 2 THEN 'Glucose Monitor'
        WHEN 3 THEN 'Defibrillator'
    END,
    CASE patient_id % 4
        WHEN 0 THEN 'Cardiac'
        WHEN 1 THEN 'Endocrine'
        WHEN 2 THEN 'Monitoring'
        WHEN 3 THEN 'Cardiac'
    END
FROM patient
WHERE patient_id % 10 = 0;  -- ~10% of patients have devices

-- Populate emergency_contact: give every patient one contact
INSERT INTO emergency_contact (patient_id, contact_name, relationship, phone_number)
SELECT patient_id,
    CONCAT(
        CASE patient_id % 5
            WHEN 0 THEN 'John'
            WHEN 1 THEN 'Sarah'
            WHEN 2 THEN 'Michael'
            WHEN 3 THEN 'Emily'
            WHEN 4 THEN 'David'
        END,
        ' ',
        SUBSTRING_INDEX(patient_name, ' ', -1)  -- use patient's last name
    ),
    CASE patient_id % 4
        WHEN 0 THEN 'Spouse'
        WHEN 1 THEN 'Parent'
        WHEN 2 THEN 'Sibling'
        WHEN 3 THEN 'Child'
    END,
    CONCAT('555-', LPAD(patient_id % 10000, 4, '0'))
FROM patient;

-- Populate insurance_provider_detail from existing dimension table
INSERT INTO insurance_provider_detail (provider_name, payer_phone)
SELECT insurance_provider,
    CONCAT('1-800-', LPAD(FLOOR(RAND(42) * 10000), 4, '0'))
FROM dim_insurance_provider;

-- Populate patient_insurance from admission data
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
